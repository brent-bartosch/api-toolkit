# Linear API Service

GraphQL-based client for Linear project management. Inherits from `BaseAPI`
(retries, rate limiting, sessions) and raises `APIError` on failures.

## Quick Start

```python
from services.linear.api import LinearAPI

api = LinearAPI()
api.quick_start()  # Formatted workspace overview
```

## Authentication

Uses a Linear personal API key (create at linear.app → Settings → Security & Access).
Set in `.env` — checked in this order:

```bash
LINEAR_API_KEY=lin_api_xxxxx              # Preferred (shared across projects)
GOVSIGNALS_LINEAR_API_KEY=lin_api_xxxxx   # Legacy fallback
SMOOTHED_LINEAR_API_KEY=lin_api_xxxxx     # Legacy fallback
```

No Bearer prefix — the key is passed directly in the `Authorization` header.
Linear explicitly rejects `Bearer <key>` for personal API keys.

## Workspace Context

**Transport**: GraphQL (`https://api.linear.app/graphql`)
**Token cost**: ~800 tokens when loaded
**Rate limit**: 10 requests/second
**Teams**: discovered at runtime via `list_teams()` — do not hardcode team IDs;
use team names or keys and let `_resolve_team_id` handle lookup.

## Available Methods

### Discovery
| Method | Description |
|--------|-------------|
| `quick_start()` | Formatted workspace overview (teams, projects, commands) |
| `discover(resource?)` | Programmatic discovery ("teams", "projects", "issues", or all) |
| `explore(resource?)` | Interactive exploration (prints formatted output) |

### Read Operations
| Method | Description |
|--------|-------------|
| `list_teams()` | All teams with id, name, key, description |
| `list_projects(status?, limit?)` | Projects with optional status filter |
| `list_issues(team?, status?, assignee?, priority?, limit?)` | Filtered issue listing |
| `list_cycles(team)` | Cycles/sprints for a team (id, number, name, dates, active) |
| `get_issue(identifier)` | Single issue with full detail (e.g., `"ENG-123"`) |
| `search_issues(query, limit?)` | Text search across issues |

### Health & Detection
| Method | Description |
|--------|-------------|
| `health_check()` | Overdue projects, stale issues, blocked work summary |
| `stale_issues(days=7)` | In-progress issues with no update in N days |
| `blocked_issues()` | Issues labeled blocked or on-hold |
| `get_sprint_status()` | Active cycle status with issue counts by state |

### Write Operations
| Method | Description |
|--------|-------------|
| `create_issue(team, title, ...)` | Create new issue (priority, project, assignee) |
| `update_issue(identifier, ...)` | Update status, priority, assignee, title, description |
| `add_comment(identifier, body)` | Add markdown comment to an issue |
| `subscribe_to_issue(identifier, users)` | Subscribe users to an issue |
| `log_milestone(project, note)` | Log project update/milestone |
| `update_team(team, name?, key?, description?)` | Rename a team or change its key/description |
| `create_project(name, team, ...)` | Create a project under a team |
| `create_cycle(team, name, starts_at, ends_at)` | Create a cycle/sprint for a team |
| `create_label(name, color?, team?)` | Create an issue label (workspace or team-scoped) |

### Consultancy Helpers (multi-client)
Model: one **team per client** (see CONTEXT.md). These roll up across teams:

| Method | Description |
|--------|-------------|
| `list_clients()` | Client initiatives with projects + open-issue counts (initiative-based model) |
| `client_overview(name)` | One client's projects and issues by state (raises APIError if unknown) |
| `create_client(name)` | Create client initiative — WRITES to Linear, requires authorization |

For the team-per-client model (recommended), use the standard methods with
`team="EZO"` etc. instead.

## Common Patterns

### List issues for a team
```python
api = LinearAPI()
issues = api.list_issues(team="Engineering", status="In Progress", limit=10)
for i in issues:
    print(f"{i['identifier']} [{i['state']['name']}] {i['title']}")
```

### Get a specific issue with comments
```python
issue = api.get_issue("ENG-123")
print(issue['title'])
print(issue['description'])
for c in issue['comments']['nodes']:
    print(f"  {c['user']['name']}: {c['body'][:80]}")
```

### Health check
```python
report = api.health_check()
print(report['summary'])
```

### Sprint status
```python
sprint = api.get_sprint_status()
for cycle in sprint['active_cycles']:
    print(f"{cycle['team']} - {cycle['name']}: {cycle['total_issues']} issues")
    for state, count in cycle['by_state'].items():
        print(f"  {state}: {count}")
```

## CLI Usage

```bash
python services/linear/api.py test              # Test connection
python services/linear/api.py teams             # List teams
python services/linear/api.py projects          # List projects
python services/linear/api.py issues [team]     # List issues
python services/linear/api.py issue ENG-123     # Get single issue
python services/linear/api.py search 'query'    # Search issues
python services/linear/api.py health            # Health check
python services/linear/api.py sprint            # Sprint status
python services/linear/api.py explore           # Full overview
```

## Priority Levels

| Value | Meaning |
|-------|---------|
| 1 | Urgent |
| 2 | High |
| 3 | Medium |
| 4 | Low |

## Architecture Notes

- **GraphQL-based**: All operations are GraphQL queries/mutations against Linear's API
- **Inherits BaseAPI**: Retry logic, rate limiting (10 rps), error handling
- **Stale detection**: Python-side date filtering (Linear's DateTime filter types have compatibility issues)
- **Blocked detection**: Searches for `label:blocked` and `label:on-hold` labels
- **Team/state resolution**: Write operations resolve human-readable names to Linear IDs internally
- **Pre-built queries**: Common GraphQL fragments live in `query_helpers.py`

## Troubleshooting

### "No Linear API key found"
Set `LINEAR_API_KEY` (or a legacy var) in your `.env`. Config lookup order:
project root `.env` → toolkit directory `.env` → `~/.api-toolkit.env`.

### 401 AUTHENTICATION_ERROR
Key is revoked/expired. Generate a new one at linear.app → Settings →
Security & Access → Personal API keys. Keys are only shown once at creation.

### "It looks like you're trying to use an API key as a Bearer token"
Remove the `Bearer ` prefix — Linear wants the raw key in the header.

### "Team not found" on create_issue
Run `api.list_teams()` to see available names/keys. Pass either.

### Empty results from list_issues
Try without filters first: `api.list_issues(limit=5)`, then add filters one at a time.
