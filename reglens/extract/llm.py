"""LLM provider adapters.

Inputs: source text chunks. Outputs: validated :class:`ExtractionResult` plus a
:class:`RunMeta` determinism record. Failure mode: HTTP errors propagate; a
response that fails schema validation raises ``ValidationError`` — fail-closed,
the chunk yields no obligations rather than unvalidated ones.

The model never executes tools and never sees a URL to fetch: extraction is a
closed, schema-constrained transform (docs/SECURITY.md, prompt injection).
"""

import hashlib
from importlib import resources
from typing import Protocol

import httpx

from reglens.config import Settings
from reglens.extract.schema import ExtractionResult, RunMeta, prompt_sha256

USER_TEMPLATE = "<document>\n{document}\n</document>"


def neutralize_delimiters(document_text: str) -> str:
    """Prevent source text from closing the data block and reading as instructions.

    A literal ``</document>`` in fetched text is broken with a zero-width-free
    escape; the provenance gate is unaffected because it verifies against the
    original snapshot text, not the prompt payload.
    """
    return document_text.replace("</document>", "<\\/document>")


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
                "format": ExtractionResult.model_json_schema(),
                "stream": False,
                "think": False,
                "options": {"temperature": 0, "seed": 31, "num_ctx": 16384, "num_predict": 3072},
            },
            timeout=1800.0,
        )
        response.raise_for_status()
        content: str = response.json()["message"]["content"]
        # Fail-closed: schema-invalid output raises rather than passing unvalidated.
        return ExtractionResult.model_validate_json(content)

    def run_meta(self, input_sha256: str) -> RunMeta:
        return RunMeta(
            model_tag=self._settings.model_tag,
            prompt_sha256=prompt_sha256(self._system_prompt, USER_TEMPLATE),
            input_sha256=input_sha256,
        )


def input_sha256(text: str) -> str:
    """Hex SHA-256 of the exact text handed to the model."""
    return hashlib.sha256(text.encode()).hexdigest()
