# API Toolkit Codex Guidance

## Purpose

API Toolkit is a lightweight, lazy-loaded alternative to large MCP integrations. Preserve its token-efficient service architecture and load only the service context needed for the current task.

## Repository map

- `core/base_api.py`: retries, rate limiting, sessions, and `APIError`
- `core/config.py`: service configuration and `.env` discovery
- `services/<name>/api.py`: service implementation
- `services/<name>/query_helpers.py`: focused query utilities
- `services/<name>/examples.py`: runnable workflows
- `tests/base_test.py`: shared service contract
- `toolkit.py`: dynamic service discovery and CLI
- `mcp-servers/`: canonical MCP server configs (manifest.json + sync.py) — propagates to Hermes, Claude Code, and Codex

Read the relevant service README and implementation before changing a service. Use `README.md`, `QUICK_REFERENCE.md`, `tests/TESTING_GUIDE.md`, and `mcp-servers/README.md` for broader details.

## Core conventions

- Services inherit from `BaseAPI`.
- Return service data directly; do not introduce `{"data": ...}` wrappers.
- Raise `APIError` for service failures.
- Keep retry and rate-limit behavior centralized unless a provider requires a documented exception.
- Preserve lazy loading and progressive documentation.
- Keep service documentation focused and under the existing token budget.

## Supabase

- Discover tables and schemas before writing queries.
- Use `QueryBuilder` for complex REST queries.
- Use `PostgresAPI` only for operations the REST API cannot perform.
- Treat destructive DDL and production mutations as consequential external actions requiring explicit authorization.

## Configuration and secrets

Configuration lookup priority is project root, toolkit directory, then `~/.api-toolkit.env`.

- Never read, print, log, or commit credential values unless the user explicitly provides a safe fixture.
- `.env.example` may be edited; real `.env` files must remain untracked.
- Support modern provider key formats while preserving documented legacy compatibility.

## Implementation workflow

- Inspect relevant code and tests, then implement bounded changes autonomously.
- Follow existing architecture; do not duplicate toolkit functionality.
- Add or update tests for behavior changes and bug fixes.
- Use test-first development when it materially clarifies a contract or reproduces a bug. Do not add ceremonial tests for documentation-only or mechanical configuration changes.
- Preserve unrelated user changes in a dirty worktree.
- Do not stage, commit, push, deploy, or mutate remote services unless the request authorizes that action.

## Verification

Use the narrowest meaningful checks first:

```bash
python tests/test_<service>.py
python tests/run_all_tests.py <service>
python tests/run_all_tests.py --markdown
python toolkit.py list
python test-env-loading.py
```

Before claiming completion, run proportionate tests and report exact failures or limitations.

## MCP Server Management

MCP server configs live in `mcp-servers/manifest.json` (source of truth). `mcp-servers/sync.py` propagates to each tool's native config. Refined for token efficiency:

- **Hermes**: `~/.hermes/config.yaml` — 12 of 23 Playwright tools via `tools.include` filter (~2,532 tokens). Built-in browser toolset disabled.
- **Claude Code**: project-level `.claude/mcp.json` only — all 23 tools but only loads when working in api-toolkit.
- **Codex**: NOT configured — uses its own `browser@openai-bundled` + `chrome@openai-bundled` plugins. No Playwright overhead.

Shared persistent browser profile at `~/.hermes/browser-profiles/playwright` — login sessions persist across restarts, shared between Hermes and Claude Code.

To add or update an MCP server: edit `manifest.json`, then run `python mcp-servers/sync.py --server <name>`. See `mcp-servers/README.md` for details.

## Audits

For review-only requests, do not edit files. Lead with prioritized, evidence-backed findings using exact file and line references. Verify agent-authored plans and completion claims against implementation, tests, and repository state.
