"""Shared fixtures: build a tiny fake brain repo in a temp directory."""

from __future__ import annotations

import tempfile
from pathlib import Path

NODE_A = """---
id: "node-alpha"
aliases: ["node-alpha", "alpha"]
type: "Knowledge"
namespace: "demo"
lifecycle_state: "canon"
summary: "Doctrine for session startup and retrieval order."
confidence: 0.9
retrieval_class: "identity"
export_class: "internal"
edges:
  - target: "[[node-beta]]"
    relation: "references"
    confidence: 0.8
created: "2026-10-12"
---

Read this card first in every non-trivial session.
"""

NODE_B = """---
id: "node-beta"
aliases: ["node-beta"]
type: "Skill"
namespace: "demo"
lifecycle_state: "scratch"
summary: "How to close out a session and write the review."
confidence: 0.6
retrieval_class: "domain"
export_class: "internal"
created: "2026-10-12"
---

Steps for closeout.
"""

PLAIN_MD = "# No frontmatter here\n\nShould be skipped by the indexer.\n"


def make_repo() -> tempfile.TemporaryDirectory:
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    (root / "knowledge" / "demo" / "canon").mkdir(parents=True)
    (root / "knowledge" / "demo" / "canon" / "agent-load-order.md").write_text(
        "# Load order\n\n1. canon first\n", encoding="utf-8"
    )
    (root / "knowledge" / "demo" / "a.md").write_text(NODE_A, encoding="utf-8")
    (root / "knowledge" / "demo" / "b.md").write_text(NODE_B, encoding="utf-8")
    (root / "README.md").write_text(PLAIN_MD, encoding="utf-8")
    hidden = root / ".claude"
    hidden.mkdir()
    (hidden / "shim.md").write_text(NODE_A, encoding="utf-8")
    return tmp
