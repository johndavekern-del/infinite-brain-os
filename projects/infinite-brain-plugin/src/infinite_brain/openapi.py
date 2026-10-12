"""Hand-written minimal OpenAPI 3 description of the plugin API."""

from __future__ import annotations

from typing import Any

from . import __version__
from .manifest import ENDPOINTS


def build_openapi() -> dict[str, Any]:
    paths: dict[str, Any] = {}
    for ep in ENDPOINTS:
        if ep["path"] in ("/health", "/plugin.json", "/openapi.json"):
            continue
        parameters = []
        if ep["path"] == "/v1/search":
            parameters = [
                {"name": "q", "in": "query", "required": True, "schema": {"type": "string"}},
                {"name": "type", "in": "query", "required": False, "schema": {"type": "string"}},
                {"name": "namespace", "in": "query", "required": False, "schema": {"type": "string"}},
                {"name": "lifecycle_state", "in": "query", "required": False, "schema": {"type": "string"}},
                {"name": "limit", "in": "query", "required": False, "schema": {"type": "integer", "default": 10}},
            ]
        for part in ep["path"].split("/"):
            if part.startswith("{") and part.endswith("}"):
                parameters.append(
                    {"name": part[1:-1], "in": "path", "required": True, "schema": {"type": "string"}}
                )
        paths[ep["path"]] = {
            ep["method"].lower(): {
                "summary": ep["description"],
                "parameters": parameters,
                "responses": {"200": {"description": "JSON response"}},
            }
        }
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "Infinite Brain Plugin",
            "version": __version__,
            "description": "Read-only HTTP access to an Infinite Brain knowledge repo.",
        },
        "paths": paths,
    }
