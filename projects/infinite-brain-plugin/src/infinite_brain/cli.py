"""Command line interface for the Infinite Brain plugin."""

from __future__ import annotations

import argparse
import json
import sys

from . import __version__
from .index import RepoIndex
from .manifest import build_manifest
from .retrieval import search


def _add_root(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--root",
        default=".",
        help="Path to the Infinite Brain repo working tree (default: current directory).",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="infinite-brain",
        description="Serve an Infinite Brain knowledge repo to a web-based agentic OS.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_serve = sub.add_parser("serve", help="Start the HTTP plugin server.")
    _add_root(p_serve)
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8377)

    p_search = sub.add_parser("search", help="Search the index and print ranked results.")
    _add_root(p_search)
    p_search.add_argument("query")
    p_search.add_argument("--type", default=None)
    p_search.add_argument("--namespace", default=None)
    p_search.add_argument("--limit", type=int, default=10)

    p_stats = sub.add_parser("stats", help="Print index statistics.")
    _add_root(p_stats)

    p_manifest = sub.add_parser("manifest", help="Print the plugin manifest (plugin.json).")
    _add_root(p_manifest)
    p_manifest.add_argument("--base-url", default="", help="URL where the server is reachable.")

    p_get = sub.add_parser("get", help="Fetch one node by id or alias.")
    _add_root(p_get)
    p_get.add_argument("id")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "serve":
        from .server import serve

        serve(args.root, host=args.host, port=args.port)
        return 0

    index = RepoIndex(args.root).build()

    if args.command == "search":
        results = search(
            index,
            args.query,
            type=args.type,
            namespace=args.namespace,
            limit=args.limit,
        )
        print(json.dumps({"query": args.query, "count": len(results), "results": results}, indent=2))
        return 0

    if args.command == "stats":
        print(json.dumps(index.stats(), indent=2))
        return 0

    if args.command == "manifest":
        print(json.dumps(build_manifest(base_url=args.base_url, repo_root=str(index.root)), indent=2))
        return 0

    if args.command == "get":
        node = index.get(args.id)
        if node is None:
            print(f"not found: {args.id}", file=sys.stderr)
            return 1
        print(json.dumps(node.to_dict(include_body=True), indent=2))
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
