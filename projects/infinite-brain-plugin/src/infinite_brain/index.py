"""Repo index: walk the working tree and index every frontmatter-bearing node.

The working tree is the retrieval surface per doctrine; this module simply makes it
queryable over HTTP. The index is read-only and rebuilt on demand, so canon never
moves into a private runtime schema.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Iterable

from .frontmatter import parse_frontmatter

SKIP_DIRS = {
    ".git",
    ".claude",
    ".codex",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
}

REQUIRED_KEYS = ("id", "type", "namespace", "lifecycle_state", "summary")


@dataclass
class Node:
    """One indexed markdown node."""

    id: str
    type: str
    namespace: str
    lifecycle_state: str
    summary: str
    path: str
    aliases: list[str] = field(default_factory=list)
    confidence: float | None = None
    retrieval_class: str | None = None
    export_class: str | None = None
    edges: list[dict[str, Any]] = field(default_factory=list)
    body: str = ""

    def to_dict(self, include_body: bool = True) -> dict[str, Any]:
        data = asdict(self)
        if not include_body:
            data.pop("body", None)
        return data


class RepoIndex:
    """In-memory index over the markdown nodes of an Infinite Brain repo."""

    def __init__(self, root: str | os.PathLike[str]):
        self.root = Path(root).resolve()
        self._nodes: dict[str, Node] = {}
        self._alias_to_id: dict[str, str] = {}
        self._built = False

    def build(self) -> "RepoIndex":
        self._nodes.clear()
        self._alias_to_id.clear()
        for path in self._iter_markdown():
            node = self._node_from_file(path)
            if node is None:
                continue
            self._nodes[node.id] = node
            for alias in node.aliases:
                self._alias_to_id.setdefault(alias, node.id)
        self._built = True
        return self

    def _ensure_built(self) -> None:
        if not self._built:
            self.build()

    def _iter_markdown(self) -> Iterable[Path]:
        for dirpath, dirnames, filenames in os.walk(self.root):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for name in sorted(filenames):
                if name.endswith(".md"):
                    yield Path(dirpath) / name

    def _node_from_file(self, path: Path) -> Node | None:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None
        meta, body = parse_frontmatter(text)
        if not isinstance(meta, dict) or not meta.get("id") or not meta.get("type"):
            return None
        rel = str(path.relative_to(self.root))
        edges = meta.get("edges") if isinstance(meta.get("edges"), list) else []
        aliases = meta.get("aliases")
        if not isinstance(aliases, list):
            aliases = [meta["id"]]
        return Node(
            id=str(meta["id"]),
            type=str(meta.get("type", "Knowledge")),
            namespace=str(meta.get("namespace", "unscoped")),
            lifecycle_state=str(meta.get("lifecycle_state", "scratch")),
            summary=str(meta.get("summary", "")),
            path=rel,
            aliases=[str(a) for a in aliases],
            confidence=_as_float(meta.get("confidence")),
            retrieval_class=_as_str(meta.get("retrieval_class")),
            export_class=_as_str(meta.get("export_class")),
            edges=[e for e in edges if isinstance(e, dict)],
            body=body,
        )

    def get(self, id_or_alias: str) -> Node | None:
        self._ensure_built()
        node = self._nodes.get(id_or_alias)
        if node is None:
            resolved = self._alias_to_id.get(id_or_alias)
            if resolved is not None:
                node = self._nodes.get(resolved)
        return node

    def all_nodes(self) -> list[Node]:
        self._ensure_built()
        return list(self._nodes.values())

    def namespaces(self) -> list[dict[str, Any]]:
        self._ensure_built()
        counts: dict[str, int] = {}
        for node in self._nodes.values():
            counts[node.namespace] = counts.get(node.namespace, 0) + 1
        return [
            {"namespace": ns, "node_count": count}
            for ns, count in sorted(counts.items())
        ]

    def stats(self) -> dict[str, Any]:
        self._ensure_built()
        by_type: dict[str, int] = {}
        by_state: dict[str, int] = {}
        for node in self._nodes.values():
            by_type[node.type] = by_type.get(node.type, 0) + 1
            by_state[node.lifecycle_state] = by_state.get(node.lifecycle_state, 0) + 1
        return {
            "root": str(self.root),
            "node_count": len(self._nodes),
            "alias_count": len(self._alias_to_id),
            "by_type": dict(sorted(by_type.items())),
            "by_lifecycle_state": dict(sorted(by_state.items())),
            "namespace_count": len({n.namespace for n in self._nodes.values()}),
        }

    def read_repo_file(self, rel_path: str) -> str | None:
        """Read a file inside the repo, refusing path escapes."""
        candidate = (self.root / rel_path).resolve()
        if self.root not in candidate.parents and candidate != self.root:
            return None
        if not candidate.is_file():
            return None
        try:
            return candidate.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None


def _as_float(value: Any) -> float | None:
    try:
        return None if value is None else float(value)
    except (TypeError, ValueError):
        return None


def _as_str(value: Any) -> str | None:
    return None if value is None else str(value)
