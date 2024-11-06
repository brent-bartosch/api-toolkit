---
description: Load Supabase API toolkit context and check installation
---

# Supabase API Toolkit Context

**CRITICAL INSTRUCTIONS:**

1. **CHECK INSTALLATION FIRST** - The API toolkit may already be installed in this project:
   ```bash
   ls -la api-toolkit/ || ls -la .toolkit-installed
   ```
   - ✅ If you see output: **TOOLKIT IS ALREADY INSTALLED!** Use it, don't recreate it.
   - ❌ If "No such file": Not installed yet, offer to install it.

2. **USE EXISTING CODE** - This toolkit is a mature, tested system:
   - DO NOT write new Supabase connection code
   - DO NOT create new query helpers
   - DO NOT duplicate existing functionality
   - ALWAYS use the existing SupabaseAPI class

3. **REVIEW THE IMPLEMENTATION** - Read these files to understand the toolkit:

**Core Supabase Files to Review:**
- `api-toolkit/services/supabase/api.py` - Main SupabaseAPI class with methods
- `api-toolkit/services/supabase/query_helpers.py` - QueryBuilder and helpers
- `api-toolkit/services/supabase/README.md` - Supabase-specific documentation
- `api-toolkit/QUICK_REFERENCE.md` - Quick reference (filter for Supabase sections)

**Key Methods to Know:**

After reviewing the files above, you should understand:
- `SupabaseAPI(project)` - Initialize with 'project1', 'project2', or 'project3'
- `.quick_start()` - Shows everything in 5 seconds (tables, columns, filters)
- `.discover()` / `.discover(table)` - Get schema info programmatically
- `.explore()` / `.explore(table)` - Interactive exploration
- `.query(table, filters, select, order, limit)` - Query tables
- `.raw_query(sql)` - Run raw SQL (SELECT only, auto-limited)
- `.get_schema(table)` - Get column definitions
- `.test_connection()` - Test if connection works

**QueryBuilder Pattern:**
```python
from api_toolkit.services.supabase.query_helpers import QueryBuilder

query = (QueryBuilder('table_name')
         .select('col1', 'col2')
         .where('column', 'operator', 'value')
         .order('column', desc=True)
         .limit(10))
results = query.execute(api)
```

**Common Workflow:**
```python
from api_toolkit.services.supabase.api import SupabaseAPI

# 1. Connect
api = SupabaseAPI('project1')  # or 'project2' or 'project3'

# 2. Discover (ALWAYS do this first!)
api.quick_start()  # or api.discover() or api.explore()

# 3. Query
results = api.query('table_name', limit=10)

# 4. Use QueryBuilder for complex queries
from api_toolkit.services.supabase.query_helpers import QueryBuilder
query = QueryBuilder('leads').where('score', '>=', 80).limit(20)
leads = query.execute(api)
```

**Three Supabase Projects Available:**
- `smoothed` - Lead generation (brands, leads, scraping_results)
- `blingsting` - CRM system (customers, orders, products)
- `scraping` - Web scraping (scrape_guide, scrape_results, scrape_queue)

**Environment Requirements:**
Ensure `.env` file exists in project root with:
```bash
# For project1 project
SUPABASE_URL=https://your-project-1.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-key

# For blingsting project
SUPABASE_URL_2=https://your-project-2.supabase.co
SUPABASE_SERVICE_ROLE_KEY_2=your-key

# For scraping project
SUPABASE_URL_3=https://your-project-3.supabase.co
SUPABASE_SERVICE_ROLE_KEY_3=your-key
```

**Your Task:**
1. Check if api-toolkit is installed in this project
2. If installed: Read the Supabase service files listed above
3. Summarize the available methods and current capabilities
4. Ask the user what they want to accomplish with Supabase
5. Use the existing toolkit to help them - DO NOT rewrite it!
