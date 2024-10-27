# 🚀 API Toolkit Quick Reference Card

## 🔴 CLAUDE: READ THIS FIRST!

When starting in ANY project, follow this exact sequence:

```bash
# 1. CHECK IF ALREADY INSTALLED (most important step!)
bash /path/to/api-toolkit/check-installation.sh

# OR manual check:
ls -la api-toolkit/

# If you see output like "lrwxr-xr-x" or files listed:
# ✅ IT'S ALREADY INSTALLED! Skip to step 3 below.
# ❌ DO NOT run install.sh if you see the directory!

# 2. ONLY if step 1 shows "No installation found", install it:
echo "1" | /path/to/api-toolkit/install.sh

# 3. Check which services are active for THIS project
cat .api-toolkit-config.md

# Look for services marked with ✅ Active
# ONLY use those services (ignore ⚪ Not Configured)

# 4. FASTEST START - Shows everything in 5 seconds!
python -c "
from api_toolkit.services.supabase.api import SupabaseAPI
api = SupabaseAPI('project1')  # or 'project2' or 'project3'
api.quick_start()  # Shows tables, columns, filters, everything!
"

# No .api-toolkit-config.md file? Create one:
/path/to/api-toolkit/init-project.sh
```

## 📊 Services Reference

### Supabase Projects
| Project | Description | Common Tables | Usage |
|---------|-------------|---------------|-------|
| **smoothed** | Lead Generation | brands, leads, scraping_results | `SupabaseAPI('project1')` |
| **blingsting** | CRM System | customers, orders, products | `SupabaseAPI('project2')` |
| **scraping** | Web Project 3 | scrape_guide, scrape_results | `SupabaseAPI('project3')` |

### Metabase Analytics
| Feature | Description | Usage |
|---------|-------------|-------|
| **Queries** | Run SQL queries and MBQL | `MetabaseAPI().run_query(sql, db_id)` |
| **Cards** | Manage saved questions | `api.query_card(card_id)` |
| **Dashboards** | Create and manage dashboards | `api.create_dashboard(name)` |
| **Export** | Export data (CSV, JSON, XLSX) | `api.export_card(id, format='csv')` |

### Smartlead Cold Email
| Feature | Description | Usage |
|---------|-------------|-------|
| **Campaigns** | Create and manage email campaigns | `SmartleadAPI().create_campaign(name, client_id)` |
| **Leads** | Add and track leads | `api.add_leads_to_campaign(id, leads)` |
| **Analytics** | Campaign performance metrics | `api.get_campaign_analytics(id)` |
| **Webhooks** | Real-time event notifications | `api.register_webhook(url, events)` |

## 🎯 Essential Code Patterns

### Pattern 1: ALWAYS Start with Discovery
```python
from api_toolkit.services.supabase.api import SupabaseAPI

api = SupabaseAPI('project1')
api.quick_start()                # 🚀 Shows EVERYTHING in 5 seconds!

# Or use discover() for programmatic access
info = api.discover()            # Returns dict with all tables
info = api.discover('table')     # Returns dict with columns, types, samples

# API returns LIST directly, not {'data': [...]}
results = api.query('table')     # results is a list, NOT dict
for row in results:              # NOT results['data']
    print(row)
```

### Pattern 2: Use QueryBuilder
```python
from api_toolkit.services.supabase.query_helpers import QueryBuilder

query = (QueryBuilder('table_name')
         .select('col1', 'col2')
         .where('status', '=', 'active')
         .where('score', '>=', 80)
         .order('created_at', desc=True)
         .limit(10))

results = query.execute(api)
```

### Pattern 3: Raw SQL for Complex Queries
```python
# When filters aren't enough, use raw SQL (SELECT only, auto-limited)
results = api.raw_query("""
    SELECT u.*, COUNT(o.id) as order_count
    FROM users u
    LEFT JOIN orders o ON u.id = o.user_id
    GROUP BY u.id
    HAVING COUNT(o.id) > 5
""")  # Auto-adds LIMIT 1000 if not specified
```

## 🤔 When to Use What

### Use `api.query()` when:
✅ Simple filters (1-3 conditions)
✅ Need type safety and autocomplete
✅ Working with < 1,000 rows
✅ Standard CRUD operations

```python
# Perfect for: Quick lookups, standard filtering
leads = api.query('leads',
    filters={'score': 'gte.80', 'status': 'eq.new'},
    limit=100
)
```

**Default limit**: 1,000 rows (configurable with `max_row_limit` parameter)
⚠️ **Warning**: Returns max 1,000 rows by default. Use `fetch_all()` for larger datasets.

---

### Use `api.fetch_all()` when:
✅ Need ALL records (>1,000 rows)
✅ Don't know total count beforehand
✅ Want automatic pagination
✅ Can handle large datasets in memory

```python
# Perfect for: Full exports, comprehensive analysis
all_leads = api.fetch_all('leads',
    filters={'status': 'eq.active'},
    verbose=True  # Shows progress
)
# Automatically paginates in 1,000-row chunks
# Shows progress: "... fetched 5,000 records so far"
```

**Token cost**: Same as `query()` but handles pagination automatically
**Memory**: Loads all results into memory (use wisely!)

---

### Use `api.raw_query()` when:
✅ Complex SQL (JOINs, GROUP BY, subqueries)
✅ Database-specific functions (NOW(), AGE(), etc.)
✅ Performance-critical operations
✅ Need full SQL expressiveness

```python
# Perfect for: Analytics, complex joins, aggregations
results = api.raw_query("""
    SELECT
        brands.name,
        COUNT(leads.id) as lead_count,
        AVG(leads.score) as avg_score
    FROM brands
    LEFT JOIN leads ON brands.id = leads.brand_id
    WHERE brands.status = 'active'
    GROUP BY brands.id, brands.name
    HAVING COUNT(leads.id) > 10
    ORDER BY avg_score DESC
""")
```

**Auto-limit**: Adds `LIMIT 1000` if you don't specify one
**Read-only**: Only SELECT queries allowed (INSERT/UPDATE/DELETE blocked)

---

### Use `api.count()` when:
✅ Only need the count, not the data
✅ Checking dataset size before fetching
✅ Performance matters (fast!)

```python
# Perfect for: Validation, metrics, pagination prep
total = api.count('leads', filters={'score': 'gte.90'})
print(f"Found {total:,} high-quality leads")

# Much faster than:
# len(api.query('leads', filters={'score': 'gte.90'}))  # ❌ Fetches all data!
```

**Token cost**: Minimal (just returns a number)
**Speed**: ~10-100x faster than fetching all rows

---

### Use `api.exists()` when:
✅ Checking if ANY record matches
✅ Validation before operations
✅ Conditional logic

```python
# Perfect for: Checks, guards, conditional flows
if api.exists('users', {'email': 'eq.john@example.com'}):
    print("User already exists!")
else:
    # Create new user
    pass

# Much faster than:
# if len(api.query('users', filters={'email': 'eq.john@example.com'})) > 0  # ❌
```

**Token cost**: Minimal (just returns True/False)
**Speed**: Uses `LIMIT 1` internally (very fast!)

---

### Decision Tree

```
Need to...
│
├─ Count records only?
│  └─ api.count('table', filters={...})
│
├─ Check if exists?
│  └─ api.exists('table', filters={...})
│
├─ Get data with simple filters?
│  ├─ < 1,000 rows?
│  │  └─ api.query('table', filters={...}, limit=100)
│  │
│  └─ > 1,000 rows or unknown?
│     └─ api.fetch_all('table', filters={...})
│
└─ Need complex SQL (JOINs, GROUP BY)?
   └─ api.raw_query("SELECT ... FROM ... WHERE ...")
```

---

### Token Cost Comparison

| Method | Typical Token Cost | Speed | Use Case |
|--------|-------------------|-------|----------|
| `count()` | ~50 tokens | ⚡⚡⚡ Fastest | Get count only |
| `exists()` | ~100 tokens | ⚡⚡⚡ Fastest | Check if any match |
| `query()` | ~500-5,000 | ⚡⚡ Fast | Standard queries (<1k rows) |
| `fetch_all()` | ~5,000-50,000 | ⚡ Slower | Large datasets (auto-paginates) |
| `raw_query()` | ~1,000-10,000 | ⚡⚡ Fast | Complex SQL |

**Pro tip**: Always start with `count()` or `exists()` to check dataset size before fetching!

---

### Common Patterns

#### Pattern: Safe Large Dataset Handling
```python
# 1. Check size first
total = api.count('leads', filters={'score': 'gte.80'})
print(f"Found {total:,} leads matching criteria")

# 2. Decide approach based on size
if total < 100:
    # Small dataset - fetch directly
    leads = api.query('leads', filters={'score': 'gte.80'})
elif total < 10000:
    # Medium dataset - fetch all with progress
    leads = api.fetch_all('leads', filters={'score': 'gte.80'}, verbose=True)
else:
    # Large dataset - process in chunks or use raw SQL
    print("Too large! Consider processing in batches or using raw_query()")
```

#### Pattern: Existence Check Before Insert
```python
# Fast check before expensive operation
if not api.exists('users', {'email': 'eq.john@example.com'}):
    # Safe to insert
    api.insert('users', {'email': 'john@example.com', 'name': 'John'})
else:
    print("User already exists - skipping")
```

#### Pattern: Pagination Info
```python
# Get pagination details
total = api.count('leads')
page_size = 50
total_pages = (total + page_size - 1) // page_size

print(f"Total records: {total:,}")
print(f"Pages: {total_pages} (showing {page_size} per page)")

# Fetch first page
page_1 = api.query('leads', limit=page_size, offset=0)
```

## 🔍 Filter Operators Cheat Sheet

```python
# OPERATOR -> SUPABASE FILTER
'='   -> 'eq.value'      # equals
'!='  -> 'neq.value'     # not equals
'>'   -> 'gt.value'      # greater than
'>='  -> 'gte.value'     # greater or equal
'<'   -> 'lt.value'      # less than
'<='  -> 'lte.value'     # less or equal

# PATTERN MATCHING
'like.%text%'            # contains (case-sensitive)
'ilike.%text%'           # contains (case-insensitive)

# SPECIAL
'is.null'                # IS NULL
'is.true'                # IS TRUE
'in.(val1,val2)'         # IN array
```

## 🛠 Common Queries by Project

### Project1 (Lead Gen)
```python
api = SupabaseAPI('project1')

# High-quality leads
hot_leads = api.query('leads', 
    filters={'score': 'gte.85', 'status': 'eq.new'},
    order='-score',
    limit=20
)

# Active brands
brands = api.query('brands',
    filters={'status': 'eq.active'},
    select='name,domain,industry'
)
```

### Project2 (CRM)
```python
api = SupabaseAPI('project2')

# Recent orders
orders = api.query('orders',
    filters={'status': 'eq.pending'},
    order='-created_at',
    limit=25
)

# Customer lookup
customer = api.get_by_id('customers', 'cust_123')
```

### Project 3
```python
api = SupabaseAPI('project3')

# Priority targets
targets = api.query('scrape_guide',
    filters={'priority': 'gte.8'},
    order='-priority'
)

# Failed scrapes
failed = api.query('scrape_results',
    filters={'status': 'eq.failed'},
    limit=20
)
```

### Metabase (Analytics)
```python
api = MetabaseAPI()

# Run SQL query
results = api.run_query(
    'SELECT * FROM sales WHERE date > ?',
    database_id=1,
    parameters=[{"type": "date", "value": "2024-01-01"}]
)

# Query saved card/question
data = api.query_card(123)

# Export to CSV
csv_data = api.export_card(123, format='csv')

# Create dashboard
dashboard = api.create_dashboard('Monthly KPIs')
```

### Smartlead (Cold Email)
```python
api = SmartleadAPI()

# Create campaign
campaign = api.create_campaign(
    'Q1 Outreach',
    client_id=1,
    settings={'track_opens': True, 'stop_on_reply': True}
)

# Add leads
leads = [
    {'email': 'john@example.com', 'first_name': 'John', 'company_name': 'Example Inc'}
]
api.add_leads_to_campaign(campaign['id'], leads)

# Get analytics
stats = api.get_campaign_analytics(campaign['id'])
print(f"Reply rate: {stats['reply_rate']}%")

# Process webhooks
from api_toolkit.services.smartlead.webhooks import SmartleadWebhookHandler
handler = SmartleadWebhookHandler()
result = handler.handle_event(webhook_payload)
```

## 🚨 Error Solutions

| Error | Solution |
|-------|----------|
| "relation does not exist" | Wrong table name. Use `api.explore()` |
| "column does not exist" | Wrong column. Use `api.get_schema('table')` |
| "JWT expired" | Bad API key. Check `.env` file location with `test-env-loading.py` |
| "Connection failed" | Missing env vars. Run `python api-toolkit/test-env-loading.py` |
| Empty results | Filter too strict. Remove filters one by one |
| Wrong .env loaded | Put `.env` in project root, not api-toolkit/ subdirectory |

## 📝 Debug Commands

```bash
# Check which .env file is being used
python api-toolkit/test-env-loading.py
# Shows: env source + all service credentials status

# Test all connections
for proj in smoothed blingsting scraping; do
    python -c "from api_toolkit.services.supabase.api import SupabaseAPI; \
               api = SupabaseAPI('$proj'); \
               print('$proj:', 'OK' if api.test_connection() else 'FAIL')"
done

# Show all tables for a project
python -c "
from api_toolkit.services.supabase.api import SupabaseAPI
api = SupabaseAPI('project1')
api.explore()
"

# Get table schema
python -c "
from api_toolkit.services.supabase.api import SupabaseAPI
api = SupabaseAPI('project1')
schema = api.get_schema('leads')
for col in schema:
    print(f\"{col['column']}: {col['type']}\")
"
```

## 🎓 Learning Resources

1. **Examples**: `python api-toolkit/services/supabase/examples.py [topic]`
   - Topics: basic, builder, patterns, advanced, smoothed, blingsting, scraping

2. **Table Docs**: `python api-toolkit/services/supabase/table_docs.py info [project] [table]`

3. **Query Helpers**: See `services/supabase/query_helpers.py` for QueryBuilder

4. **Full Guide**: Read `INTEGRATION_DETAILED.md` for complete patterns

## ⚡ Quick Test

```python
# Copy-paste this to test everything works:
from api_toolkit.services.supabase.api import SupabaseAPI
from api_toolkit.services.supabase.query_helpers import QueryBuilder

# Test connection
api = SupabaseAPI('project1')
if api.test_connection():
    print("✓ Connected to Project1")
    
    # Show tables
    api.explore()
    
    # Try a query
    query = QueryBuilder('leads').limit(5)
    results = query.execute(api)
    print(f"✓ Query worked: {len(results)} results")
else:
    print("✗ Connection failed - check .env")
```

## 💡 Remember

1. **Token Savings**: This toolkit uses 600 tokens vs 90,000 for MCP
2. **Always Explore**: Use `api.explore()` before writing queries
3. **Use Helpers**: QueryBuilder and table_docs make life easier
4. **Check Schema**: `api.get_schema()` prevents column errors
5. **Test Small**: Start with `limit=5` then increase

---
**Toolkit Location**: `/path/to/api-toolkit`
**Install Command**: `/path/to/api-toolkit/install.sh`