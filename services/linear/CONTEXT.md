# Linear Service — Agent Context

Read this file at the start of any session involving Linear operations.
It is the single source of truth for how this service fits together; you
should not need to search elsewhere in the repo.

## What lives here

| File | Purpose |
|------|---------|
| `api.py` | `LinearAPI` client (GraphQL, inherits `BaseAPI`) + CLI entrypoint; includes consultancy helpers (`list_clients`, `client_overview`, `create_client`) |
| `query_helpers.py` | Pre-built GraphQL queries/fragments — import these instead of inlining query strings |
| `examples.py` | Runnable example workflows |
| `README.md` | Full method reference, patterns, troubleshooting |
| `../../tests/test_linear.py` | Test suite (`python tests/test_linear.py`) |

## Setup checklist for a new project

1. Toolkit `.env` must contain `LINEAR_API_KEY=lin_api_...`
   (lookup order: project root → toolkit dir → `~/.api-toolkit.env`)
2. Verify: `python -c "from services.linear.api import LinearAPI; print(LinearAPI().test_connection())"`
3. Discover teams before writing any team-specific code: `LinearAPI().list_teams()`

## Workspace structure (multi-client consultancy)

Smoothed is the **organization** (this workspace). Clients never access it —
it's fully internal. Structure:

- **One team per client** (e.g., team "EZO" → issue IDs `EZO-123`). Each
  client team owns its own statuses, labels, and templates.
- **A general "Operations" team** for Smoothed's own business admin
  (invoicing, marketing, tooling).
- Within a client team: **one project per deliverable/workstream**, issues
  underneath. Recurring work (weekly calls) as recurring issues or skipped.
- Initiatives are optional roll-ups across a client's projects — skip them
  until a client has enough concurrent projects to need a summary view.

Adding a new client = create a team. Use the generic methods with the
team name:

```python
api.list_teams()                          # see all clients
ezo_issues = api.list_issues(team="EZO") # client-scoped queries
api.create_issue(team="EZO", title="...")
api.health_check()                        # cross-client health rollup
```

The consultancy helpers (`list_clients`, `client_overview`) model clients
as initiatives — only relevant if you later adopt that layer.

## Non-obvious constraints

- **Auth header**: raw key, no `Bearer` prefix. Linear rejects Bearer for personal keys.
- **GraphQL only**: there is no REST endpoint; everything goes through
  `https://api.linear.app/graphql`.
- **IDs vs names**: write methods accept human-readable team/state/project/assignee
  names and resolve them internally via `_resolve_*` helpers. Don't hardcode UUIDs.
- **Stale detection** filters dates Python-side because Linear's DateTime filter
  types have compatibility issues with the API version this was built against.
- **Blocked detection** depends on workspace labels named exactly `blocked` or `on-hold`.
- **Rate limit**: 10 rps, handled by `BaseAPI`. Don't add ad-hoc sleeps.

## Multi-workspace note

The client reads one key per process (`LINEAR_API_KEY`, falling back to legacy
per-workspace vars). If a task spans multiple Linear workspaces, instantiate
separate clients with explicit keys:

```python
from services.linear.api import LinearAPI
client_a = LinearAPI(api_key=os.environ["CLIENT_A_LINEAR_API_KEY"])
```

## Known test behavior

- `tests/base_test.py` calls `teardown()` after standard tests, so
  `test_linear.py` re-runs `setup()` before its service-specific tests.
- The base "Token Efficiency" check counts full class source (~7.9k chars) and
  will report FAIL for Linear; the registered lazy-load cost in
  `core/config.py` is ~800 tokens, which is the number that matters.
