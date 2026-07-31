"""Generation-constraint and per-claim validation contracts for the local provider.

These lock in a real regression: Ollama 0.30.x silently stops honouring a schema
that contains ``maxLength``, returning objects that omit every required field.
"""

import json
from typing import Any, cast

import respx
from httpx import Response
from pytest import MonkeyPatch

from reglens.extract.llm import (
    chat_json_openai,
    generation_schema,
    parse_obligations,
    strict_schema,
)
from reglens.extract.schema import ExtractionResult


def test_generation_schema_drops_length_bounds() -> None:
    """The runtime cannot compile maxLength; Pydantic still enforces it later."""
    original = ExtractionResult.model_json_schema()
    assert "maxLength" in json.dumps(original), "fixture assumes the model declares maxLength"

    constrained = generation_schema(original)

    assert "maxLength" not in json.dumps(constrained)
    assert "minLength" not in json.dumps(constrained)


def test_generation_schema_preserves_the_contract() -> None:
    """Only length bounds are stripped — required fields and enums must survive."""
    constrained = json.dumps(generation_schema(ExtractionResult.model_json_schema()))

    assert "obligation_type" in constrained
    assert "affected_party" in constrained
    assert "required" in constrained
    assert "enum" in constrained


def test_length_bounds_are_still_enforced_at_validation() -> None:
    """Stripping the generation constraint must not weaken the accepted contract."""
    over_long = json.dumps(
        {
            "obligations": [
                {
                    "quote": "x" * 5000,
                    "obligation_type": "reporting",
                    "affected_party": "banks",
                    "summary": "Too long to be a valid quote.",
                    "effective_date": None,
                }
            ]
        }
    )

    assert parse_obligations(over_long) == []


def test_one_malformed_obligation_does_not_discard_its_siblings() -> None:
    """Fail-closed per claim, not per chunk: a bad object must not cost good ones."""
    mixed = json.dumps(
        {
            "obligations": [
                {"quote": "missing every other required field"},
                {
                    "quote": "Each institution must file a report.",
                    "obligation_type": "reporting",
                    "affected_party": "institutions",
                    "summary": "File a report.",
                    "effective_date": None,
                },
            ]
        }
    )

    obligations = parse_obligations(mixed)

    assert len(obligations) == 1
    assert obligations[0].quote == "Each institution must file a report."


def test_unusable_responses_yield_nothing() -> None:
    """Fail-closed: nothing parseable means no claims, never a guess."""
    assert parse_obligations("not json at all") == []
    assert parse_obligations("[1, 2, 3]") == []
    assert parse_obligations(json.dumps({"obligations": "not a list"})) == []
    assert parse_obligations(json.dumps({})) == []


def test_strict_schema_recurses_and_preserves_length_bounds() -> None:
    original: dict[str, Any] = {
        "type": "object",
        "properties": {
            "nested": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "maxLength": 12},
                },
            },
            "entries": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "value": {"type": "string", "maxLength": 24},
                    },
                },
            },
        },
    }

    constrained = strict_schema(original)

    assert constrained["additionalProperties"] is False
    properties = cast(dict[str, Any], constrained["properties"])
    nested = cast(dict[str, Any], properties["nested"])
    assert nested["additionalProperties"] is False
    nested_properties = cast(dict[str, Any], nested["properties"])
    nested_name = cast(dict[str, Any], nested_properties["name"])
    assert nested_name["maxLength"] == 12
    entries = cast(dict[str, Any], properties["entries"])
    item_schema = cast(dict[str, Any], entries["items"])
    assert item_schema["additionalProperties"] is False
    item_properties = cast(dict[str, Any], item_schema["properties"])
    item_value = cast(dict[str, Any], item_properties["value"])
    assert item_value["maxLength"] == 24


@respx.mock(assert_all_mocked=True)
def test_chat_json_openai_retries_rate_limit_then_succeeds(
    respx_mock: respx.MockRouter,
    monkeypatch: MonkeyPatch,
) -> None:
    slept_for: list[float] = []

    def record_sleep(delay: float) -> None:
        slept_for.append(delay)

    monkeypatch.setattr("reglens.extract.llm.time.sleep", record_sleep)
    success_content = json.dumps({"answer": "ok"})
    route = respx_mock.post("https://api.groq.com/openai/v1/chat/completions").mock(
        side_effect=[
            Response(429, headers={"retry-after": "0"}),
            Response(
                200,
                json={"choices": [{"message": {"content": success_content}}]},
            ),
        ]
    )

    content = chat_json_openai(
        "https://api.groq.com/openai/v1",
        api_key="test",
        model="test-model",
        system_prompt="Return JSON.",
        user_prompt="Give an answer.",
        schema={
            "type": "object",
            "properties": {"answer": {"type": "string"}},
            "required": ["answer"],
        },
        temperature=0.0,
        seed=31,
        max_tokens=64,
        reasoning_effort=None,
        timeout=1.0,
    )

    assert json.loads(content) == {"answer": "ok"}
    assert route.call_count == 2
    assert slept_for == [1.0]
