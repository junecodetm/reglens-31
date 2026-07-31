"""OpenAPI 3.1 description of the read API, generated from the response models.

Inputs: the pydantic models in :mod:`reglens.api.schemas`. Output: an OpenAPI
3.1 document. Failure mode: none at runtime — the document is derived, so a
model that changes shape changes the document on the next export rather than
drifting away from it.

Generated from pydantic rather than a web framework: OpenAPI 3.1 embeds JSON
Schema 2020-12 natively, which is exactly what pydantic v2 emits, so a server
framework would add a dependency (and a running service) to produce a document
this project can derive from the models it already validates against. The
zero-cost invariant and the "no live backend" rule both make that the wrong
trade — see CLAUDE.md section 2 and docs/STACK.md.
"""

import re
from typing import Any, Final

from pydantic import BaseModel
from pydantic.json_schema import GenerateJsonSchema, models_json_schema

from reglens.api.schemas import (
    API_VERSION,
    ClaimPage,
    Currency,
    DocumentCollection,
    DocumentDetail,
    Metrics,
    SectionCollection,
    ServiceIndex,
)

OPENAPI_VERSION: Final = "3.1.1"
REF_TEMPLATE: Final = "#/components/schemas/{model}"

DISCLAIMER: Final = (
    "RegLens-31 is an independent prototype. It is not affiliated with, endorsed by, "
    "or an official product of the U.S. Department of the Treasury. Every claim is "
    "assistive and must be verified against the primary source."
)

_ENDPOINTS: Final[tuple[tuple[str, str, type[BaseModel], str], ...]] = (
    (
        "/index.json",
        "serviceIndex",
        ServiceIndex,
        "Entry point: what this API is, what it is not, and where everything lives.",
    ),
    (
        "/documents.json",
        "documentCollection",
        DocumentCollection,
        "Every extracted document with its snapshot digest and coverage counts.",
    ),
    (
        "/documents/{document_number}.json",
        "documentDetail",
        DocumentDetail,
        "One document and every claim extracted from it, accepted and rejected alike.",
    ),
    (
        "/claims/page-{page}.json",
        "claimPage",
        ClaimPage,
        "One materialized page of claims across the whole extracted sample.",
    ),
    (
        "/sections.json",
        "sectionCollection",
        SectionCollection,
        "CFR section spans located in the committed part texts.",
    ),
    (
        "/currency.json",
        "currency",
        Currency,
        "Whether the pinned corpus has drifted from the live regulation.",
    ),
    (
        "/metrics.json",
        "metrics",
        Metrics,
        "Evaluation metrics, carrying the provisional label verbatim.",
    ),
)


def component_schemas() -> dict[str, Any]:
    """JSON Schema for every published model, keyed by model name."""
    _, definitions = models_json_schema(
        [(model, "serialization") for _, _, model, _ in _ENDPOINTS],
        ref_template=REF_TEMPLATE,
        schema_generator=GenerateJsonSchema,
    )
    return dict(sorted(definitions.get("$defs", {}).items()))


_TEMPLATE_PARAMETER: Final = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")


def _path_parameters(path: str) -> list[dict[str, Any]]:
    """Path templates are file names here, so every parameter is a required string."""
    names = _TEMPLATE_PARAMETER.findall(path)
    return [
        {
            "name": name,
            "in": "path",
            "required": True,
            "schema": {"type": "string"},
        }
        for name in names
    ]


def build_openapi(*, server_url: str = f"/api/{API_VERSION}") -> dict[str, Any]:
    """The OpenAPI 3.1 document describing every materialized endpoint."""
    paths: dict[str, Any] = {}
    for path, operation_id, model, summary in _ENDPOINTS:
        operation: dict[str, Any] = {
            "operationId": operation_id,
            "summary": summary,
            "responses": {
                "200": {
                    "description": summary,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": REF_TEMPLATE.format(model=model.__name__)}
                        }
                    },
                }
            },
        }
        parameters = _path_parameters(path)
        if parameters:
            operation["parameters"] = parameters
        paths[path] = {"get": operation}
    return {
        "openapi": OPENAPI_VERSION,
        "info": {
            "title": "RegLens-31 read API",
            "version": API_VERSION,
            "description": (
                "Read-only static JSON. No authentication, no key, no rate limit, no "
                "server: every path below is a file in the same pre-computed export the "
                "site itself reads."
            ),
            "license": {"name": "Apache-2.0", "identifier": "Apache-2.0"},
        },
        "servers": [{"url": server_url}],
        "paths": paths,
        "components": {"schemas": component_schemas()},
    }
