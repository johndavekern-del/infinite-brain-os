"""Standard-library HTTP server exposing the brain to a web-based agentic OS.

Runs anywhere Python 3.10+ runs, with no third-party packages. Hosts that already
use FastAPI can mount ``fastapi_app.create_app`` instead; the routes mirror these.
"""

from __future__ import annotations

import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse, parse_qs, unquote

from . import __version__
from .index import RepoIndex
from .manifest import build_manifest
from .openapi import build_openapi
from .retrieval import search

_NS_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")

DOCTRINE_CARD_PATH = "knowledge/ai-architecture/canon/doctrine-card.md"


def _json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, indent=2, sort_keys=False).encode("utf-8")


class BrainHTTPServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address: tuple[str, int], index: RepoIndex):
        super().__init__(address, BrainRequestHandler)
        self.index = index


class BrainRequestHandler(BaseHTTPRequestHandler):
    server: BrainHTTPServer
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args: Any) -> None:  # quieter default
        pass

    def do_GET(self) -> None:  # noqa: N802 (stdlib naming)
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        params = parse_qs(parsed.query)
        try:
            payload, status = self._route(path, params)
        except Exception as exc:  # defensive: never leak a traceback to the host
            payload, status = {"error": "internal", "detail": str(exc)}, 500
        body = _json_bytes(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _route(self, path: str, params: dict[str, list[str]]) -> tuple[Any, int]:
        index = self.server.index

        if path == "/health":
            stats = index.stats()
            return {"status": "ok", "version": __version__, "node_count": stats["node_count"]}, 200

        if path == "/plugin.json":
            return build_manifest(repo_root=str(index.root)), 200

        if path == "/openapi.json":
            return build_openapi(), 200

        if path == "/v1/stats":
            return index.stats(), 200

        if path == "/v1/search":
            query = _first(params, "q", "")
            if not query:
                return {"error": "missing required query parameter: q"}, 400
            results = search(
                index,
                query,
                type=_first(params, "type"),
                namespace=_first(params, "namespace"),
                lifecycle_state=_first(params, "lifecycle_state"),
                limit=int(_first(params, "limit", "10")),
            )
            return {"query": query, "count": len(results), "results": results}, 200

        if path.startswith("/v1/nodes/"):
            node_id = unquote(path[len("/v1/nodes/"):])
            node = index.get(node_id)
            if node is None:
                return {"error": "not_found", "id": node_id}, 404
            return node.to_dict(include_body=True), 200

        if path == "/v1/namespaces":
            return {"namespaces": index.namespaces()}, 200

        if path.startswith("/v1/namespaces/") and path.endswith("/load_order"):
            ns = unquote(path[len("/v1/namespaces/"):-len("/load_order")].strip("/"))
            return self._load_order(ns)

        if path == "/v1/doctrine-card":
            content = index.read_repo_file(DOCTRINE_CARD_PATH)
            if content is None:
                return {"error": "not_found", "path": DOCTRINE_CARD_PATH}, 404
            return {"path": DOCTRINE_CARD_PATH, "content": content}, 200

        return {"error": "not_found", "path": path}, 404

    def _load_order(self, namespace: str) -> tuple[Any, int]:
        index = self.server.index
        if not _NS_RE.match(namespace):
            return {"error": "invalid namespace"}, 400
        candidates = [
            f"knowledge/{namespace}/canon/agent-load-order.md",
            f"knowledge/{namespace}/INDEX.md",
        ]
        for rel in candidates:
            content = index.read_repo_file(rel)
            if content is not None:
                return {"namespace": namespace, "path": rel, "content": content}, 200
        known = {entry["namespace"] for entry in index.namespaces()}
        if namespace not in known:
            return {"error": "not_found", "namespace": namespace}, 404
        return {
            "namespace": namespace,
            "path": None,
            "content": None,
            "note": "Namespace is indexed but ships no load-order document.",
        }, 200


def _first(params: dict[str, list[str]], key: str, default: str | None = None) -> str | None:
    values = params.get(key)
    if not values:
        return default
    return values[0]


def serve(root: str, host: str = "127.0.0.1", port: int = 8377) -> None:
    """Build the index and serve until interrupted."""
    index = RepoIndex(root).build()
    server = BrainHTTPServer((host, port), index)
    stats = index.stats()
    print(f"infinite-brain {__version__} serving {stats['node_count']} nodes "
          f"from {stats['root']} on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
