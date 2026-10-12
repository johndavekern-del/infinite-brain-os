"""Infinite Brain plugin: serve a git-backed knowledge repo to agentic OS hosts.

The package reads the working tree of an Infinite Brain OS repository, indexes every
frontmatter-bearing markdown node, and exposes search, lookup, and namespace load-order
endpoints over HTTP. The core runs on the Python standard library alone; a FastAPI
adapter is available as the optional ``web`` extra.
"""

__version__ = "0.1.0"

from .index import Node, RepoIndex  # noqa: E402
from .retrieval import search  # noqa: E402
from .manifest import build_manifest  # noqa: E402

__all__ = ["Node", "RepoIndex", "search", "build_manifest", "__version__"]
