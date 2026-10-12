---
id: "project-infinite-brain-plugin"
aliases: ["project-infinite-brain-plugin", "infinite-brain-plugin"]
type: "Project"
namespace: "ai-architecture"
lifecycle_state: "scratch"
summary: "Build the Infinite Brain as a standalone, pip-installable Python plugin that serves this repo's knowledge and entity graph to any web-based agentic OS over HTTP."
confidence: 0.7
retrieval_class: "domain"
export_class: "internal"
state_stored_at: "git://projects/infinite-brain-plugin/PLAN.md"
analytical_view: "none"
updated: "2026-10-12"
project_status: "active"
owner_department: "none"
owner_agent: "the-operator"
parent_initiative: "none"
review_cadence: "weekly"
linked_swarm_id: "none"
party_slugs: []
client_slug: null
brand_slug: null
edges:
  - target: "[[doctrine-card]]"
    relation: "implements"
    confidence: 0.8
created: "2026-10-12"
---

# Project: Infinite Brain Plugin

## Goal

Package the Infinite Brain as installable software: a zero-dependency Python package that
reads this repo's ontology (frontmatter nodes, namespaces, entity types, retrieval order)
directly from the git working tree and serves it over HTTP with a plugin manifest, so a
web-based agentic OS can install it and give its agents retrieval access to the brain.

## Why this matters

The doctrine is git-native and tool-agnostic, but today only CLI coding agents (Claude
Code, Codex) can operate the brain through the `.claude/` and `.codex/` shims. A web-based
agentic OS has no filesystem shim contract. A standalone HTTP plugin turns the brain into
a service any host can mount, without forking the ontology or moving canon out of git.

## Scope

In scope:

- Python package `infinite-brain` under `projects/infinite-brain-plugin/`.
- Stdlib-only core: frontmatter parsing, repo indexing, token-scored retrieval, HTTP API.
- Plugin manifest (`/plugin.json`) and OpenAPI description for host OS installation.
- CLI (`serve`, `search`, `stats`, `manifest`).
- Optional FastAPI adapter for hosts that already run FastAPI.
- Unit tests runnable with the standard library.

Out of scope:

- Vendor-specific integrations (OpenWebUI tools, Suna extensions) until the operator names
  a target host.
- Write paths that mutate canon; the plugin is read-only against the repo in v1.
- Live queue or session state; that stays with the runtime surface per the three-plane
  truth split.

## Success criteria

1. `python -m infinite_brain serve` starts an HTTP server from a fresh checkout with no
   third-party packages installed.
2. `GET /v1/search?q=...` returns ranked nodes with ids, types, namespaces, and summaries.
3. `GET /plugin.json` returns a manifest a host OS can consume to register the plugin.
4. The test suite passes with `python -m unittest` on Python 3.11.
5. No file in the project violates the repo style rule (no em dashes, no en dashes).

## Ownership and rollup

- Owning department: `none`
- Owner agent or human: `the-operator`
- Parent initiative: `none`
- Review cadence: `weekly`
- Linked swarm: `none`
- Related parties: none
- Primary client: `none`
- Primary brand: `none`

## Dependencies and links

- Depends on: the frontmatter contract in `_system/` (validator-enforced keys).
- Related repos: none
- Related namespaces: `ai-architecture`
- Related tools: none yet

## Swarms

- No active swarms yet.

## Tasks

- [ ] `task-scaffold-package` Scaffold pyproject, package layout, README
  - mode: manual
  - status: completed
  - depends_on: none
  - blocks: task-core-index, task-http-api
  - acceptance: Package imports and `pip install -e .` metadata is valid.
  - anchored_sprint: none
- [ ] `task-core-index` Frontmatter parser, repo index, retrieval scoring
  - mode: manual
  - status: completed
  - depends_on: task-scaffold-package
  - blocks: task-http-api
  - acceptance: Index builds over the real repo; search returns ranked results.
  - anchored_sprint: none
- [ ] `task-http-api` HTTP server, plugin manifest, CLI
  - mode: manual
  - status: completed
  - depends_on: task-core-index
  - blocks: task-tests
  - acceptance: All v1 endpoints respond; manifest endpoint validates as JSON.
  - anchored_sprint: none
- [ ] `task-tests` Stdlib unittest suite
  - mode: manual
  - status: completed
  - depends_on: task-http-api
  - blocks: none
  - acceptance: `python -m unittest` passes on Python 3.11.
  - anchored_sprint: none
- [ ] `task-fastapi-adapter` Optional FastAPI app factory
  - mode: manual
  - status: completed
  - depends_on: task-http-api
  - blocks: none
  - acceptance: Adapter module imports cleanly when FastAPI is present, skipped otherwise.
  - anchored_sprint: none

## Outputs

- `projects/infinite-brain-plugin/src/infinite_brain/`: the plugin package (v0.1.0).
- `projects/infinite-brain-plugin/tests/`: unittest suite, 25 tests passing.
- `projects/infinite-brain-plugin/README.md`: install and host-integration guide.

## Notes

- Sandbox has no PyPI access; the zero-dependency constraint is load-bearing, not a taste
  call. FastAPI support must stay an optional extra.
- The plugin is a surface in doctrine terms: it reads the working tree, owns no canon, and
  never becomes the only durable home of approved knowledge.

## Change log

- 2026-10-12: Created project during session `session-2026-10-12-infinite-brain-plugin`.
- 2026-10-12: v0.1.0 built and verified: 25 tests passing, live smoke test against the
  real repo served 237 nodes with all endpoints green.
