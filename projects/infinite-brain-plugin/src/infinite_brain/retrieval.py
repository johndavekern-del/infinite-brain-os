"""Token-scored retrieval over the repo index.

Deliberately simple and deterministic: tokens are matched against id and aliases
(highest weight), then summary, then body. This mirrors the doctrine's retrieval
posture (minimal sufficient set, working tree as surface) and keeps the plugin
dependency-free. Hosts that want embeddings can layer them on top of the same
endpoints later.
"""

from __future__ import annotations

import re
from typing import Any

from .index import Node, RepoIndex

_TOKEN_RE = re.compile(r"[a-z0-9]+")

WEIGHT_ID = 4.0
WEIGHT_SUMMARY = 2.0
WEIGHT_BODY = 1.0
SUBSTRING_BONUS = 2.0


def _tokens(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def _token_set(text: str) -> set[str]:
    return set(_tokens(text))


def score_node(node: Node, query_tokens: set[str], raw_query: str) -> float:
    if not query_tokens:
        return 0.0
    id_tokens = _token_set(node.id)
    for alias in node.aliases:
        id_tokens |= _token_set(alias)
    id_tokens |= _token_set(node.type)
    summary_tokens = _token_set(node.summary)
    body_tokens = _token_set(node.body[:4000]) if node.body else set()

    score = 0.0
    for token in query_tokens:
        if token in id_tokens:
            score += WEIGHT_ID
        if token in summary_tokens:
            score += WEIGHT_SUMMARY
        if token in body_tokens:
            score += WEIGHT_BODY
    raw = raw_query.strip().lower()
    if raw and (raw in node.id.lower() or raw in node.summary.lower()):
        score += SUBSTRING_BONUS
    return score


def search(
    index: RepoIndex,
    query: str,
    *,
    type: str | None = None,
    namespace: str | None = None,
    lifecycle_state: str | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Return ranked node summaries matching the query and optional filters."""
    query_tokens = _token_set(query)
    limit = max(1, min(int(limit), 100))
    scored: list[tuple[float, Node]] = []
    for node in index.all_nodes():
        if type and node.type.lower() != type.lower():
            continue
        if namespace and node.namespace.lower() != namespace.lower():
            continue
        if lifecycle_state and node.lifecycle_state.lower() != lifecycle_state.lower():
            continue
        score = score_node(node, query_tokens, query)
        if score > 0:
            scored.append((score, node))
    scored.sort(key=lambda pair: (-pair[0], pair[1].id))
    results = []
    for score, node in scored[:limit]:
        entry = node.to_dict(include_body=False)
        entry["score"] = round(score, 3)
        results.append(entry)
    return results
