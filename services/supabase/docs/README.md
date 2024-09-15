# Supabase API

## Quick Reference (~500 tokens)

### Capabilities
- Query tables with complex filters and joins
- Insert, update, delete with conflict handling
- Call PostgreSQL functions (RPC)
- Multi-project support (3 configured projects)

### Your Projects
- **project1**: `your-project-1-ref` (primary database)
- **project2**: `your-project-2-ref` (secondary)
- **project3**: `your-project-3-ref` (tertiary)

### Common Patterns
```python
from services.supabase.api import SupabaseAPI

# Initialize for specific project
api = SupabaseAPI('main')  # or 'project2', 'project3'

# Query with filters
users = api.query('users', filters={'status': 'eq.active'}, limit=10)

# Insert with conflict handling
api.insert('profiles', {'email': 'user@example.com'}, on_conflict='email')

# Update records
api.update('users', {'last_seen': 'now()'}, {'id': f'eq.{user_id}'})

# Call PostgreSQL function
total = api.rpc('calculate_revenue', {'year': 2024})
```

### Filter Operations
- `eq`: equals (`{'status': 'eq.active'}`)
- `neq`: not equals
- `gt`/`gte`: greater than (or equal)
- `lt`/`lte`: less than (or equal)  
- `like`/`ilike`: pattern matching
- `in`: in list (`{'id': 'in.(1,2,3)'}`)
- `is`: null check (`{'deleted_at': 'is.null'}`)

### Authentication
- **Method**: Service role key (full access)
- **Environment Variables**: 
  - Main: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
  - Project2: `SUPABASE_URL_2`, `SUPABASE_SERVICE_ROLE_KEY_2`
  - Project3: `SUPABASE_URL_3`, `SUPABASE_SERVICE_ROLE_KEY_3`

### Rate Limits
- **Requests**: 1000/minute
- **Payload**: 2MB max
- **Response**: 10MB max

### When to Use
✅ Use for:
- Database CRUD operations
- Calling stored procedures
- Complex queries with joins
- Bulk data operations

❌ Don't use for:
- File storage (use Storage API)
- Authentication (use Auth API)
- Realtime subscriptions (use Realtime)

### Your Common Tables
**Project 3 (scraping)**:
- `scrape_guide`: Category and keyword data
- `brands`: Scraped brand information

### Error Handling
- `400`: Bad request - check query syntax
- `401`: Unauthorized - check API key
- `404`: Table/function not found
- `409`: Conflict - check unique constraints

### Most Used Methods
1. `query(table, filters, limit)` - Query with filters
2. `insert(table, data, on_conflict)` - Insert with upsert
3. `update(table, data, filters)` - Update records
4. `rpc(function_name, params)` - Call PostgreSQL function
5. `get_by_id(table, id)` - Get single record