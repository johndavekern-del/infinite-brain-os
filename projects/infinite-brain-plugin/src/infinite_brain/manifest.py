"""Plugin manifest generation.

The manifest is what a web-based agentic OS reads to install the plugin: who it is,
what it can do, and which endpoints to call. It is served at ``/plugin.json`` and can
also be emitted from the CLI for static registration flows.
"""

from __future__ import annotations

from typing import Any

from . import __version__

ENDPOINTS = [
    {"method": "GET", "path": "/health", "description": "Liveness and index status."},
    {"method": "GET", "path": "/plugin.json", "description": "This manifest."},
    {"method": "GET", "path": "/openapi.json", "description": "OpenAPI 3 description of the API."},
    {"method": "GET", "path": "/v1/stats", "description": "Index statistics: node, alias, type, and namespace counts."},
    {"method": "GET", "path": "/v1/search", "description": "Ranked node search. Params: q, type, namespace, lifecycle_state, limit."},
    {"method": "GET", "path": "/v1/nodes/{id}", "description": "Fetch one node by id or alias, including body."},
    {"method": "GET", "path": "/v1/namespaces", "description": "List namespaces with node counts."},
    {"method": "GET", "path": "/v1/namespaces/{namespace}/load_order", "description": "Agent load-order document for a namespace (canon first)."},
    {"method": "GET", "path": "/v1/doctrine-card", "description": "The compressed startup doctrine card an agent reads first."},
]

CAPABILITIES = [
    "knowledge.search",
    "knowledge.read",
    "knowledge.namespaces",
    "knowledge.load_order",
    "doctrine.startup_card",
]


def build_manifest(*, base_url: str = "", repo_root: str = "") -> dict[str, Any]:
    """Return the plugin manifest as a JSON-serialisable dict."""
    return {
        "schema_version": "1.0",
        "kind": "agentic-os-plugin",
        "name": "infinite-brain",
        "version": __version__,
        "display_name": "Infinite Brain",
        "description": (
            "Serves a git-backed Infinite Brain knowledge repo (entities, namespaces, "
            "canon, retrieval order) to a web-based agentic OS over a small HTTP API."
        ),
        "homepage": "https://example.invalid/infinite-brain",
        "license": "MIT",
        "runtime": {"language": "python", "requires_python": ">=3.10", "dependencies": []},
        "repo_root": repo_root,
        "base_url": base_url,
        "capabilities": CAPABILITIES,
        "endpoints": ENDPOINTS,
        "auth": {"scheme": "none", "note": "Bind to localhost or put the host's auth proxy in front."},
        "mutability": "read-only",
    }
