# Safe DDL: Direct Postgres Access for Schema Operations

**Date:** 2026-01-29
**Status:** Approved
**Author:** Claude Code + Brent Bartosch

## Problem Statement

The API Toolkit currently only supports read operations via the Supabase REST API. This blocks autonomous workflows where Claude Code needs to create or modify database schemas (CREATE TABLE, ALTER TABLE, etc.).

The Supabase JS SDK and REST API don't support DDL (Data Definition Language) statements. Users must manually run migrations via the Supabase Dashboard, creating friction in development workflows.

### Constraints

- **Safety is paramount**: Previous concerns about Claude Code hallucinating and accidentally deleting data are valid
- **Automation is the goal**: Requiring manual intervention for every schema change defeats the purpose
- **Existing patterns should be preserved**: REST API for reads is efficient and should remain the default

## Solution: Safe DDL

Add direct Postgres connection support with built-in safety classification. SQL statements are categorized into three tiers:

| Tier | Operations | Behavior |
|------|------------|----------|
| **Safe** | CREATE TABLE, CREATE INDEX, ALTER TABLE ADD COLUMN | Execute immediately |
| **Cautious** | ALTER TABLE DROP COLUMN, TRUNCATE | Require `confirm=True` parameter |
| **Destructive** | DROP TABLE, DROP DATABASE, DELETE without WHERE | Blocked unless `i_know_what_im_doing=True` |

This provides creative power (schema creation) without destructive risk (accidental deletion).

## Architecture

### File Structure

```
services/supabase/
├── api.py           # Existing REST-based queries (unchanged)
├── postgres.py      # NEW: Direct Postgres connection for DDL
├── query_helpers.py # Existing (unchanged)
└── safety.py        # NEW: SQL classification and guardrails
```

### Class Responsibilities

| Class | Connection | Purpose |
|-------|------------|---------|
| `SupabaseAPI` | REST API | Queries, inserts, updates (current behavior) |
| `PostgresAPI` | Direct Postgres | DDL, migrations, raw SQL when REST can't do it |

### Environment Configuration

One new variable per project (existing variables unchanged):

```bash
# Existing (unchanged)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-key

# NEW: Direct Postgres connection
SUPABASE_POSTGRES_URL=postgres://postgres:password@db.xxx.supabase.co:5432/postgres
SUPABASE_POSTGRES_URL_2=postgres://postgres:password@db.xxx.supabase.co:5432/postgres
SUPABASE_POSTGRES_URL_3=postgres://postgres:password@db.xxx.supabase.co:5432/postgres
```

Connection strings are available from: Supabase Dashboard → Settings → Database → Connection string.

## Safety Classification Logic

### Pattern Matching

```python
SAFE_PATTERNS = [
    r'^CREATE\s+TABLE',
    r'^CREATE\s+INDEX',
    r'^CREATE\s+TYPE',
    r'^CREATE\s+EXTENSION',
    r'^CREATE\s+FUNCTION',
    r'^ALTER\s+TABLE\s+\w+\s+ADD',
    r'^ALTER\s+TABLE\s+\w+\s+RENAME',
    r'^COMMENT\s+ON',
]

CAUTIOUS_PATTERNS = [
    r'^ALTER\s+TABLE\s+\w+\s+DROP\s+COLUMN',
    r'^TRUNCATE',
    r'^DELETE\s+FROM\s+\w+\s+WHERE',  # DELETE with WHERE clause
]

DESTRUCTIVE_PATTERNS = [
    r'^DROP\s+TABLE',
    r'^DROP\s+DATABASE',
    r'^DROP\s+SCHEMA',
    r'^DROP\s+FUNCTION',
    r'^DELETE\s+FROM\s+\w+$',  # DELETE without WHERE (wipes entire table)
    r'^ALTER\s+TABLE\s+\w+\s+DROP\s+CONSTRAINT',
]
```

### Behavior by Tier

| Tier | Parameter Required | Error if Missing |
|------|-------------------|------------------|
| Safe | None | N/A - executes immediately |
| Cautious | `confirm=True` | `SafetyError: This operation requires confirm=True` |
| Destructive | `i_know_what_im_doing=True` | `SafetyError: Destructive operation blocked` |

### Audit Logging

All DDL operations logged to `~/.api-toolkit/ddl_audit.log`:

```
2026-01-29 10:15:32 | smoothed | SAFE | CREATE TABLE users (id uuid PRIMARY KEY)
2026-01-29 10:16:01 | smoothed | CAUTIOUS | TRUNCATE users | confirm=True
2026-01-29 10:20:45 | smoothed | DESTRUCTIVE | DROP TABLE old_users | override=True
```

## API Design

### PostgresAPI Class

```python
from api_toolkit.services.supabase.postgres import PostgresAPI

db = PostgresAPI('smoothed')  # or 'blingsting' or 'scraping'

# Core methods
db.execute(sql, confirm=False, i_know_what_im_doing=False, dry_run=False)
db.query(sql)                    # Run SELECT, return results
db.run_migration(file_path)      # Run a .sql file
db.run_migrations_from_dir(dir)  # Run all .sql files in order
db.get_schema(table_name)        # Show table structure
db.table_exists(table_name)      # Check if table exists
db.transaction()                 # Context manager for explicit transactions
```

### Usage Patterns

**Pattern 1: Creating tables for a new feature**

```python
db = PostgresAPI('smoothed')

if not db.table_exists('campaigns'):
    db.execute("""
        CREATE TABLE campaigns (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            name text NOT NULL,
            status text DEFAULT 'draft',
            created_at timestamptz DEFAULT now()
        )
    """)
    db.execute("CREATE INDEX campaigns_status_idx ON campaigns(status)")
```

**Pattern 2: Running migration files**

```python
db.run_migration('migrations/001_add_users_table.sql')
db.run_migrations_from_dir('migrations/')
```

**Pattern 3: Adding columns to existing tables**

```python
db.execute("ALTER TABLE users ADD COLUMN phone text")
db.execute("ALTER TABLE users ADD COLUMN verified boolean DEFAULT false")
```

**Pattern 4: Cleaning up (requires confirmation)**

```python
db.execute("TRUNCATE test_data", confirm=True)
db.execute("DROP TABLE old_backup", i_know_what_im_doing=True)
```

**Pattern 5: Debugging/inspection**

```python
schema = db.get_schema('users')
for col in schema:
    print(f"{col['name']}: {col['type']}")

results = db.query("SELECT count(*) FROM users WHERE created_at > '2026-01-01'")
```

**Pattern 6: Dry-run mode**

```python
db.execute("CREATE TABLE test (id int)", dry_run=True)
# Output: "[DRY RUN] Would execute: CREATE TABLE test (id int)"
# Output: "Classification: SAFE"
# Output: "No changes made"
```

## Transaction Handling

### Default Behavior

All DDL runs inside a transaction. If anything fails, automatic rollback prevents partial state.

### Explicit Transactions

```python
with db.transaction() as tx:
    tx.execute("CREATE TABLE orders (id uuid PRIMARY KEY)")
    tx.execute("CREATE TABLE order_items (id uuid, order_id uuid REFERENCES orders)")
    tx.execute("CREATE INDEX order_items_order_idx ON order_items(order_id)")
    # All succeed together, or none do
```

## Error Handling

### Error Types

| Error | When | Resolution |
|-------|------|------------|
| `SafetyError` | Blocked by classification | Add required parameter |
| `ConnectionError` | Can't reach Postgres | Check `SUPABASE_POSTGRES_URL` in .env |
| `PostgresError` | SQL syntax or constraint error | Fix SQL, transaction auto-rolls back |

### Example Error Flow

```python
from api_toolkit.services.supabase.postgres import PostgresAPI, SafetyError

db = PostgresAPI('smoothed')

try:
    db.execute("DROP TABLE users")
except SafetyError as e:
    print(e)
    # "Destructive operation blocked: DROP TABLE users"
    # "Use i_know_what_im_doing=True to override"
```

## Implementation Plan

### Dependencies

Add to `requirements.txt`:

```
psycopg2-binary>=2.9.9
```

### Files to Create

| File | Purpose | Estimated Lines |
|------|---------|-----------------|
| `services/supabase/postgres.py` | PostgresAPI class | ~200 |
| `services/supabase/safety.py` | SQL classification logic | ~80 |
| `tests/test_postgres.py` | Test suite | ~150 |

### Files to Modify

| File | Change |
|------|--------|
| `core/config.py` | Add `SUPABASE_POSTGRES_URL` patterns |
| `.env.example` | Add Postgres URL examples |
| `requirements.txt` | Add psycopg2-binary |
| `README.md` | Document new capability |
| `CLAUDE.md` | Add usage patterns |

### Implementation Order

1. **safety.py** - Classification logic (testable independently)
2. **postgres.py** - Core API with safety integration
3. **test_postgres.py** - Tests against real Supabase project
4. **Config updates** - Environment variable support
5. **Documentation** - README, CLAUDE.md updates
6. **Manual testing** - Real migrations on test project

## Integration with Existing Toolkit

The two APIs work together:

```python
# Use REST for reads (efficient, cached)
api = SupabaseAPI('smoothed')
users = api.query('users', limit=10)

# Use Postgres for schema changes
db = PostgresAPI('smoothed')
db.execute("ALTER TABLE users ADD COLUMN phone text")

# Back to REST for queries
users = api.query('users')  # Now includes phone column
```

## Security Considerations

1. **Connection strings contain passwords** - Never commit to git, always use .env
2. **Audit log contains SQL** - May contain sensitive table/column names
3. **Destructive operations require explicit opt-in** - Defense in depth
4. **Transactions prevent partial state** - No half-applied migrations

## Success Criteria

- [ ] Can CREATE TABLE without any confirmation
- [ ] Can ALTER TABLE ADD COLUMN without confirmation
- [ ] TRUNCATE requires `confirm=True`
- [ ] DROP TABLE blocked without `i_know_what_im_doing=True`
- [ ] All operations logged to audit file
- [ ] Dry-run mode shows SQL without executing
- [ ] Transaction rollback on error
- [ ] Works with all 3 Supabase projects (smoothed, blingsting, scraping)

## Future Enhancements (Not in Scope)

- Migration tracking table (which migrations have run)
- Schema diffing (compare local vs remote)
- Automatic backup before destructive operations
- Slack/webhook notifications for destructive operations
