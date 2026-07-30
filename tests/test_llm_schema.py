"""Generation-constraint and per-claim validation contracts for the local provider.

These lock in a real regression: Ollama 0.30.x silently stops honouring a schema
that contains ``maxLength``, returning objects that omit every required field.
"""

import json

from reglens.extract.llm import generation_schema, parse_obligations
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
