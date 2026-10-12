# infinite-brain

A standalone, pip-installable Python plugin that serves an Infinite Brain OS
repository to any web-based agentic OS over a small HTTP API.

The brain stays in git. This plugin is a read-only surface over the working tree:
it indexes every frontmatter-bearing markdown node (entities, knowledge, projects,
sessions) and exposes search, lookup, and namespace load-order endpoints plus a
`plugin.json` manifest that a host OS consumes at install time.

## Design constraints

- Zero required dependencies: the core runs on Python 3.10+ standard library alone,
  so installation into any host is a single `pip install` with no supply-chain risk.
- Read-only by contract: the plugin never mutates canon or repo state. It is a
  surface in doctrine terms, never the durable home of approved knowledge.
- Host-agnostic: no vendor SDK. Any agentic OS that can make HTTP calls can install
  it. An optional FastAPI adapter is included for hosts that already run FastAPI.

## Install

```bash
pip install -e .            # from this directory
pip install -e '.[web]'     # adds the FastAPI adapter dependencies
```

Or run without installing:

```bash
PYTHONPATH=src python3 -m infinite_brain --help
```

## Quickstart

```bash
# Serve a brain repo (defaults to the current directory)
infinite-brain serve --root /path/to/infinite-brain-os --host 127.0.0.1 --port 8377

# Or use the CLI directly against the index
infinite-brain stats  --root /path/to/infinite-brain-os
infinite-brain search "session closeout review" --root /path/to/infinite-brain-os
infinite-brain get doctrine-card --root /path/to/infinite-brain-os
infinite-brain manifest --base-url http://127.0.0.1:8377
```

## HTTP API

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Liveness and node count. |
| `GET /plugin.json` | Plugin manifest for host installation. |
| `GET /openapi.json` | OpenAPI 3 description of the API. |
| `GET /v1/stats` | Index statistics. |
| `GET /v1/search?q=...&type=&namespace=&lifecycle_state=&limit=` | Ranked node search. |
| `GET /v1/nodes/{id}` | One node by id or alias, body included. |
| `GET /v1/namespaces` | Namespaces with node counts. |
| `GET /v1/namespaces/{ns}/load_order` | Canon-first load-order document for a namespace. |
| `GET /v1/doctrine-card` | The startup doctrine card an agent reads first. |

## Installing into a web-based agentic OS

1. Run the server somewhere the host can reach it (`infinite-brain serve`).
2. Point the host's plugin or tool registration at
   `http://<host>:<port>/plugin.json`. The manifest declares capabilities,
   endpoints, auth posture, and read-only mutability.
3. Hosts that consume OpenAPI directly can register `/openapi.json` instead.

For FastAPI-based hosts, mount the app in-process:

```python
from infinite_brain.fastapi_app import create_app
app = create_app("/path/to/infinite-brain-os")
```

## Recommended agent startup flow through the plugin

1. `GET /v1/doctrine-card` for the compressed operating doctrine.
2. `GET /v1/namespaces/{ns}/load_order` for the domain being touched.
3. `GET /v1/search?q=...` for the minimal sufficient node set.
4. `GET /v1/nodes/{id}` to read specific nodes in full.

## Development

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Tests use only the standard library and build a fixture repo in a temp directory.

## Layout

```
pyproject.toml              package metadata, zero required dependencies
src/infinite_brain/
  frontmatter.py            YAML-subset frontmatter parser (stdlib only)
  index.py                  working-tree indexer over markdown nodes
  retrieval.py              token-scored search
  manifest.py               plugin.json generation
  openapi.py                OpenAPI 3 description
  server.py                 stdlib HTTP server
  fastapi_app.py            optional FastAPI adapter
  cli.py                    serve / search / stats / manifest / get
tests/                      unittest suite with fixture repo
```
