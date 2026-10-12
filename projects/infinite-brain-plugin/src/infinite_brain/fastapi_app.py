"""Optional FastAPI adapter.

Hosts that already run FastAPI can do::

    from infinite_brain.fastapi_app import create_app
    app = create_app("/path/to/infinite-brain-repo")

and mount the result under their own server. The routes mirror the stdlib server.
This module imports FastAPI lazily so the core package stays dependency-free.
"""

from __future__ import annotations

from . import __version__
from .index import RepoIndex
from .manifest import build_manifest
from .openapi import build_openapi
from .retrieval import search
from .server import DOCTRINE_CARD_PATH, _NS_RE


def create_app(root: str):
    try:
        from fastapi import FastAPI, HTTPException, Query
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "FastAPI is not installed. Use the stdlib server (infinite-brain serve) "
            "or install the optional extra: pip install infinite-brain[web]"
        ) from exc

    index = RepoIndex(root).build()
    app = FastAPI(title="Infinite Brain Plugin", version=__version__)

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "version": __version__, "node_count": index.stats()["node_count"]}

    @app.get("/plugin.json")
    def manifest() -> dict:
        return build_manifest(repo_root=str(index.root))

    @app.get("/openapi-override.json")
    def openapi_override() -> dict:
        return build_openapi()

    @app.get("/v1/stats")
    def stats() -> dict:
        return index.stats()

    @app.get("/v1/search")
    def search_endpoint(
        q: str,
        type: str | None = Query(default=None),
        namespace: str | None = Query(default=None),
        lifecycle_state: str | None = Query(default=None),
        limit: int = 10,
    ) -> dict:
        results = search(
            index, q, type=type, namespace=namespace,
            lifecycle_state=lifecycle_state, limit=limit,
        )
        return {"query": q, "count": len(results), "results": results}

    @app.get("/v1/nodes/{node_id}")
    def get_node(node_id: str) -> dict:
        node = index.get(node_id)
        if node is None:
            raise HTTPException(status_code=404, detail=f"not found: {node_id}")
        return node.to_dict(include_body=True)

    @app.get("/v1/namespaces")
    def namespaces() -> dict:
        return {"namespaces": index.namespaces()}

    @app.get("/v1/namespaces/{namespace}/load_order")
    def load_order(namespace: str) -> dict:
        if not _NS_RE.match(namespace):
            raise HTTPException(status_code=400, detail="invalid namespace")
        for rel in (
            f"knowledge/{namespace}/canon/agent-load-order.md",
            f"knowledge/{namespace}/INDEX.md",
        ):
            content = index.read_repo_file(rel)
            if content is not None:
                return {"namespace": namespace, "path": rel, "content": content}
        raise HTTPException(status_code=404, detail=f"no load-order document for {namespace}")

    @app.get("/v1/doctrine-card")
    def doctrine_card() -> dict:
        content = index.read_repo_file(DOCTRINE_CARD_PATH)
        if content is None:
            raise HTTPException(status_code=404, detail=DOCTRINE_CARD_PATH)
        return {"path": DOCTRINE_CARD_PATH, "content": content}

    return app
