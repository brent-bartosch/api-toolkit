# Supabase API Service

## Quick Start

```python
from services.supabase.api import SupabaseAPI

# Initialize for your project
api = SupabaseAPI('project1')    # or 'project2' or 'project3'

# Quick query
users = api.query('users', filters={'status': 'eq.active'})
```

## Available Helpers

### 1. Query Builder (`query_helpers.py`)
```python
from services.supabase.query_helpers import QueryBuilder

query = (QueryBuilder('users')
         .select('id', 'email', 'name')
         .where('status', '=', 'active')
         .order('created_at', desc=True)
         .limit(10))

results = query.execute(api)
```

### 2. Table Documentation (`table_docs.py`)
```python
from services.supabase.table_docs import get_table_info

# Get info about a table
info = get_table_info('project1', 'leads')
print(info['description'])
print(info['key_columns'])
print(info['sample_queries'])
```

### 3. Complete Examples (`examples.py`)
```python
# Run examples directly
python services/supabase/examples.py basic
python services/supabase/examples.py explore
python services/supabase/examples.py smoothed
```

## Projects Configuration

| Project | Description | Key Tables |
|---------|-------------|------------|
| **smoothed** | Lead Generation | brands, leads, scraping_results |
| **blingsting** | CRM System | customers, orders, products |
| **scraping** | Web Project 3 | scrape_guide, scrape_results, scrape_queue |

## Common Operations

### Explore Database
```bash
# List tables in a project
python services/supabase/api.py tables smoothed

# Get schema for a table
python services/supabase/api.py schema smoothed leads

# Explore interactively
python services/supabase/api.py explore smoothed
```

### Query Patterns
```python
# Recent records
from services.supabase.query_helpers import CommonQueries

params = CommonQueries.recent_records('orders', days=7)
recent = api.query('orders', **params)

# Pagination
params = CommonQueries.paginated('users', page=2, per_page=20)
page_2 = api.query('users', **params)
```

### Filter Operations

| Operation | Syntax | Example |
|-----------|--------|---------|
| Equals | `eq` | `{'status': 'eq.active'}` |
| Not equals | `neq` | `{'status': 'neq.deleted'}` |
| Greater than | `gt` | `{'age': 'gt.18'}` |
| Greater or equal | `gte` | `{'score': 'gte.80'}` |
| Less than | `lt` | `{'price': 'lt.100'}` |
| Less or equal | `lte` | `{'quantity': 'lte.10'}` |
| Like (pattern) | `like` | `{'email': 'like.%@gmail.com'}` |
| Case-insensitive | `ilike` | `{'name': 'ilike.%john%'}` |
| Is null/true/false | `is` | `{'deleted_at': 'is.null'}` |
| In array | `in` | `{'status': 'in.(active,pending)'}` |

## Troubleshooting

### Connection Issues
```python
# Test connection
api = SupabaseAPI('project1')
if not api.test_connection():
    print("Check your .env configuration")

# Check environment
python services/supabase/api.py test smoothed
```

### Query Debugging
```python
# Get table schema first
schema = api.get_schema('table_name')
for col in schema:
    print(f"{col['column']}: {col['type']}")

# Check row count
count = api.count('table_name')
print(f"Total rows: {count}")

# Get sample data
sample = api.query('table_name', limit=3)
```

### Common Errors

1. **"relation does not exist"** - Table name is wrong
   - Solution: Use `api.get_tables()` to list available tables

2. **"column does not exist"** - Column name is wrong
   - Solution: Use `api.get_schema('table')` to see columns

3. **"JWT expired"** or **"Invalid API key"** - API key is invalid
   - Solution: Check your .env file has correct keys
   - Note: Supabase introduced new key formats in 2025 (see below)

4. **Empty results** - Filters too restrictive
   - Solution: Remove filters one by one to debug

## API Key Format Changes (2025+)

Supabase introduced new API key formats in 2025:

| Old Format (Legacy) | New Format (2025+) |
|---------------------|-------------------|
| `anon` key (JWT: `eyJ...`) | `sb_publishable_...` |
| `service_role` key (JWT: `eyJ...`) | `sb_secret_...` |

**Timeline:**
- June 2025: New format available (opt-in)
- November 2025: Legacy keys disabled for restored projects
- Late 2026: Legacy keys fully removed

**Both formats work during transition.** The toolkit accepts either format.

Key differences with new format:
- Secret keys (`sb_secret_...`) cannot be used in browsers (returns 401)
- Secret keys can be instantly revoked
- Zero-downtime rotation supported

See: https://github.com/orgs/supabase/discussions/29260

## Best Practices

1. **Always check schema first** when working with new tables
2. **Use limit** for exploration to avoid large responses
3. **Count before querying** large tables
4. **Use the QueryBuilder** for complex queries
5. **Reference table_docs.py** for known table structures
6. **Check examples.py** for working code patterns

## Token Efficiency

This service uses ~600 tokens when loaded, compared to 90,000 for MCP servers.

To keep it efficient:
- Only import what you need
- Use lazy loading for helpers
- Reference documentation files instead of loading them