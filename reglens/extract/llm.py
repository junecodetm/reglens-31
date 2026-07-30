"""LLM provider adapters.

Inputs: source text chunks. Outputs: validated :class:`ExtractionResult` plus a
:class:`RunMeta` determinism record. Failure mode: HTTP errors propagate;
obligations are validated one at a time, so a malformed obligation is dropped
while its well-formed siblings survive — fail-closed per claim, never passing
anything unvalidated.

The model never executes tools and never sees a URL to fetch: extraction is a
closed, schema-constrained transform (docs/SECURITY.md, prompt injection).
"""

import hashlib
import json
import re
from importlib import resources
from typing import Any, Protocol, cast

import httpx
from pydantic import ValidationError

from reglens.config import Settings
from reglens.extract.schema import (
    ExtractedObligation,
    ExtractionResult,
    RunMeta,
    prompt_sha256,
)

USER_TEMPLATE = "<document>\n{document}\n</document>"

_UNCOMPILABLE_KEYWORDS = ("maxLength", "minLength")


_DELIMITER_PATTERN = re.compile(r"<(/?)\s*document\b([^>]*)>", re.IGNORECASE)


def neutralize_delimiters(document_text: str) -> str:
    """Prevent source text from closing the data block and reading as instructions.

    Any ``<document ...>`` / ``</document>`` tag variant (case-insensitive,
    whitespace/attribute-tolerant) in fetched text is broken with an escape;
    the provenance gate is unaffected because it verifies against the
    original snapshot text, not the prompt payload. Defense-in-depth: the
    schema-constrained output, fabrication scan, and quote gate backstop this.
    """
    return _DELIMITER_PATTERN.sub(r"<\\\1document\2>", document_text)


def generation_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """A copy of ``schema`` that the local runtime can actually compile to a grammar.

    Ollama 0.30.x fails to build a constraint grammar from a schema containing
    ``maxLength``/``minLength``: instead of erroring it silently returns
    unconstrained output — in practice objects carrying only ``quote`` — which
    the strict model then rejects, losing the whole chunk. Length bounds are
    therefore stripped from the GENERATION constraint only; they remain enforced
    by Pydantic when the response is validated, so an over-long quote is still
    rejected fail-closed. Verified against Ollama 0.30.7 with qwen3:8b: with
    ``maxLength`` present every returned object omitted its required fields;
    with it stripped the same chunks validate.
    """
    return _strip_uncompilable(schema)


def _strip_uncompilable(node: Any) -> Any:
    if isinstance(node, dict):
        return {
            key: _strip_uncompilable(value)
            for key, value in cast(dict[str, Any], node).items()
            if key not in _UNCOMPILABLE_KEYWORDS
        }
    if isinstance(node, list):
        return [_strip_uncompilable(item) for item in cast(list[Any], node)]
    return node


def parse_obligations(content: str) -> list[ExtractedObligation]:
    """Validate a model response one obligation at a time.

    Failure mode: fail-closed per claim rather than per chunk. A response that is
    not JSON, or whose top level does not match the contract, yields nothing; a
    single malformed obligation is dropped while its well-formed siblings are
    kept, so one over-long quote can no longer discard a chunk's other findings.
    Every surviving obligation is still a fully validated
    :class:`ExtractedObligation` and still faces the provenance gate.
    """
    try:
        payload: Any = json.loads(content)
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, dict):
        return []
    items: Any = cast(dict[str, Any], payload).get("obligations")
    if not isinstance(items, list):
        return []
    obligations: list[ExtractedObligation] = []
    for item in cast(list[Any], items):
        try:
            obligations.append(ExtractedObligation.model_validate(item))
        except ValidationError:
            continue
    return obligations


def load_system_prompt() -> str:
    """The pinned system prompt shipped with the package."""
    return (resources.files("reglens.extract") / "prompts" / "system.txt").read_text()


class LLMProvider(Protocol):
    """Swappable inference backend (docs/STACK.md adapter pattern)."""

    def extract(self, document_text: str) -> ExtractionResult: ...

    def run_meta(self, input_sha256: str) -> RunMeta: ...


class OllamaProvider:
    """Local inference via Ollama's /api/chat with a JSON-schema ``format`` constraint."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._system_prompt = load_system_prompt()
        self._runtime_version: str | None = None

    def extract(self, document_text: str) -> ExtractionResult:
        response = httpx.post(
            f"{self._settings.ollama_base_url}/api/chat",
            json={
                "model": self._settings.model_tag,
                "messages": [
                    {"role": "system", "content": self._system_prompt},
                    {
                        "role": "user",
                        "content": USER_TEMPLATE.format(
                            document=neutralize_delimiters(document_text)
                        ),
                    },
                ],
                "format": generation_schema(ExtractionResult.model_json_schema()),
                "stream": False,
                "think": False,
                "options": {"temperature": 0, "seed": 31, "num_ctx": 16384, "num_predict": 3072},
            },
            timeout=1800.0,
        )
        response.raise_for_status()
        content: str = response.json()["message"]["content"]
        # Fail-closed per claim: malformed obligations are dropped, never passed unvalidated.
        return ExtractionResult(obligations=parse_obligations(content))

    def runtime_version(self) -> str:
        """The local inference runtime's version, memoised for the process.

        Recorded in every :class:`RunMeta` because the runtime is a real input to
        the output: an Ollama upgrade silently changed structured-output
        behaviour once already (see :func:`generation_schema`), and a determinism
        record that omits it cannot detect that class of drift. Failure mode: an
        unreachable runtime records ``"unknown"`` rather than blocking a run.
        """
        if self._runtime_version is None:
            try:
                response = httpx.get(f"{self._settings.ollama_base_url}/api/version", timeout=10.0)
                response.raise_for_status()
                self._runtime_version = f"ollama/{response.json()['version']}"
            except (httpx.HTTPError, KeyError):
                self._runtime_version = "unknown"
        return self._runtime_version

    def run_meta(self, input_sha256: str) -> RunMeta:
        return RunMeta(
            model_tag=self._settings.model_tag,
            prompt_sha256=prompt_sha256(self._system_prompt, USER_TEMPLATE),
            input_sha256=input_sha256,
            runtime=self.runtime_version(),
        )


def input_sha256(text: str) -> str:
    """Hex SHA-256 of the exact text handed to the model."""
    return hashlib.sha256(text.encode()).hexdigest()
