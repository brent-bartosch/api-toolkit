# API Toolkit - Detailed Integration Guide

## 🔍 CLAUDE DISCOVERY PATTERN

When Claude starts in a new project, it should follow this pattern:

### Step 1: Check if Toolkit Exists
```bash
# First, check if toolkit is already installed
ls -la api-toolkit 2>/dev/null || echo "Not installed"

# If not installed, check if main toolkit exists
ls -la /path/to/api-toolkit 2>/dev/null || echo "Main toolkit missing"
```

### Step 2: Install if Needed
```bash
# Run installer (choose option 1 for symlink)
echo "1" | /path/to/api-toolkit/install.sh
```

### Step 3: Verify Environment
```bash
# Check if .env exists
ls -la .env api-toolkit/.env 2>/dev/null

# Test Supabase connections
python api-toolkit/toolkit.py supabase test
```

### Step 4: Explore Available Data
```bash
# See what services are available
python api-toolkit/toolkit.py list

# Explore Supabase tables
python api-toolkit/services/supabase/api.py explore smoothed
python api-toolkit/services/supabase/api.py explore blingsting
python api-toolkit/services/supabase/api.py explore scraping
```

## 📊 SUPABASE QUERY TROUBLESHOOTING

### Problem: "I don't know what tables exist"

**Solution 1: Explore the Database**
```python
from api_toolkit.services.supabase.api import SupabaseAPI

# List all tables
api = SupabaseAPI('project1')
api.explore()  # Shows all tables with row counts

# Get specific table info
api.explore('leads')  # Shows columns, types, sample data
```

**Solution 2: Use Table Documentation**
```python
from api_toolkit.services.supabase.table_docs import list_project_tables, get_table_info

# See documented tables
tables = list_project_tables('project1')
print(f"Known tables: {tables}")

# Get table details
info = get_table_info('project1', 'leads')
print(info['key_columns'])
print(info['sample_queries'])
```

### Problem: "Column doesn't exist" errors

**Solution: Always Check Schema First**
```python
# Before querying, check what columns exist
api = SupabaseAPI('project1')
schema = api.get_schema('leads')

print("Available columns:")
for col in schema:
    print(f"  {col['column']}: {col['type']}")

# Now query with confidence
results = api.query('leads', 
    select='id,email,score',  # We know these exist
    filters={'score': 'gte.80'}
)
```

### Problem: "How do I filter data?"

**Solution: Use Query Builder**
```python
from api_toolkit.services.supabase.query_helpers import QueryBuilder

# Intuitive syntax - no filter formatting needed
query = (QueryBuilder('users')
         .where('age', '>=', 18)        # Converts to 'gte.18'
         .where('status', '=', 'active') # Converts to 'eq.active'
         .contains('email', 'gmail')     # Converts to 'ilike.%gmail%'
         .order('created_at', desc=True)
         .limit(10))

results = query.execute(api)
```

**Filter Reference Table:**
```python
# OPERATOR CONVERSIONS
# Python operator -> Supabase filter
filters = {
    'age': 'gte.18',         # age >= 18
    'status': 'eq.active',   # status = 'active'
    'email': 'neq.test@example.com',  # email != 'test@example.com'
    'price': 'lt.100',       # price < 100
    'score': 'lte.50',       # score <= 50
    'name': 'like.John%',    # name LIKE 'John%'
    'bio': 'ilike.%engineer%',  # bio ILIKE '%engineer%' (case-insensitive)
    'deleted_at': 'is.null', # deleted_at IS NULL
    'status': 'in.(active,pending)',  # status IN ('active', 'pending')
}
```

### Problem: "Query returns too much data"

**Solution: Always Use Limits and Pagination**
```python
# ALWAYS start with a small limit
sample = api.query('large_table', limit=5)

# Check total count before full query
count = api.count('large_table')
print(f"Total records: {count}")

# Use pagination for large datasets
from api_toolkit.services.supabase.query_helpers import CommonQueries

page = 1
per_page = 100
while True:
    params = CommonQueries.paginated('large_table', page=page, per_page=per_page)
    batch = api.query('large_table', **params)
    
    if not batch:
        break
    
    # Process batch
    process_records(batch)
    page += 1
```

## 🎯 PROJECT-SPECIFIC PATTERNS

### For Project1 (Lead Gen) Project

```python
from api_toolkit.services.supabase.api import SupabaseAPI
from api_toolkit.services.supabase.query_helpers import QueryBuilder

api = SupabaseAPI('project1')

# Common Pattern 1: Find high-quality leads
hot_leads = (QueryBuilder('leads')
             .where('score', '>=', 85)
             .where('status', '=', 'new')
             .where('contacted', '=', False)
             .order('score', desc=True)
             .limit(20)
             .execute(api))

# Common Pattern 2: Recent scraping results
from datetime import datetime, timedelta
yesterday = (datetime.now() - timedelta(days=1)).isoformat()

recent_scrapes = api.query('scraping_results',
    filters={
        'scraped_at': f'gte.{yesterday}',
        'status': 'eq.success'
    },
    order='-scraped_at',
    limit=50
)

# Common Pattern 3: Brands by industry
fashion_brands = api.query('brands',
    filters={'industry': 'eq.fashion', 'status': 'eq.active'},
    select='id,name,domain,last_scraped'
)
```

### For Project2 (CRM) Project

```python
api = SupabaseAPI('project2')

# Common Pattern 1: Customer lifetime value
high_value_customers = api.query('customers',
    filters={'lifetime_value': 'gte.5000'},
    select='id,email,name,lifetime_value,last_order_date',
    order='-lifetime_value'
)

# Common Pattern 2: Recent orders
recent_orders = api.query('orders',
    filters={'status': 'in.(pending,processing)'},
    select='id,customer_id,total,status,created_at',
    order='-created_at',
    limit=25
)

# Common Pattern 3: Low inventory alert
low_stock = api.query('products',
    filters={'inventory': 'lte.10', 'active': 'eq.true'},
    select='sku,name,inventory,reorder_point'
)
```

### For Project 3 Project

```python
api = SupabaseAPI('project3')

# Common Pattern 1: Priority scraping targets
priority_guides = api.query('scrape_guide',
    filters={'priority': 'gte.8', 'active': 'eq.true'},
    select='id,url,selector,priority,category_display_name',
    order='-priority'
)

# Common Pattern 2: Failed scrapes for retry
failed_jobs = api.query('scrape_results',
    filters={'status': 'eq.failed', 'retry_count': 'lt.3'},
    select='id,guide_id,url,error_message,retry_count',
    limit=20
)

# Common Pattern 3: Project 3 performance metrics
from datetime import datetime, timedelta
last_hour = (datetime.now() - timedelta(hours=1)).isoformat()

recent_performance = api.query('scrape_results',
    filters={'extracted_at': f'gte.{last_hour}'},
    select='status,COUNT(*)',
    group_by='status'
)
```

## 🛠 COMPLETE WORKFLOW EXAMPLES

### Example 1: New Project Setup
```bash
# 1. Navigate to project
cd ~/Development/my-new-project

# 2. Install toolkit
echo "1" | /path/to/api-toolkit/install.sh

# 3. Verify installation
ls -la api-toolkit/
python api-toolkit/toolkit.py list

# 4. Test Supabase connection
python api-toolkit/toolkit.py supabase test

# 5. Explore available data
python -c "
from api_toolkit.services.supabase.api import SupabaseAPI
api = SupabaseAPI('project1')
api.explore()
"
```

### Example 2: Data Analysis Workflow
```python
# analyze_leads.py
import sys
sys.path.insert(0, 'api-toolkit')

from services.supabase.api import SupabaseAPI
from services.supabase.query_helpers import QueryBuilder
from datetime import datetime, timedelta

def analyze_lead_quality():
    api = SupabaseAPI('project1')
    
    # First, explore the table
    print("Checking leads table structure...")
    schema = api.get_schema('leads')
    print(f"Columns: {[col['column'] for col in schema]}")
    
    # Count total leads
    total = api.count('leads')
    print(f"Total leads: {total}")
    
    # Get high-quality leads
    query = (QueryBuilder('leads')
             .where('score', '>=', 80)
             .where('status', '=', 'new')
             .order('score', desc=True)
             .limit(100))
    
    high_quality = query.execute(api)
    print(f"High-quality leads: {len(high_quality)}")
    
    # Analyze by source
    for lead in high_quality[:5]:
        print(f"  - {lead.get('email', 'N/A')}: Score {lead.get('score', 0)}")
    
    return high_quality

if __name__ == "__main__":
    analyze_lead_quality()
```

### Example 3: Data Sync Workflow
```python
# sync_data.py
from api_toolkit.services.supabase.api import SupabaseAPI

def sync_customer_data():
    # Source: CRM
    crm = SupabaseAPI('project2')
    
    # Target: Lead Gen
    leads = SupabaseAPI('project1')
    
    # Get active customers
    active_customers = crm.query('customers',
        filters={'status': 'eq.active'},
        select='email,name,company'
    )
    
    # Convert to leads format
    new_leads = []
    for customer in active_customers:
        new_leads.append({
            'email': customer['email'],
            'name': customer.get('name', ''),
            'company': customer.get('company', ''),
            'source': 'crm_sync',
            'score': 70,  # Default score for CRM imports
            'status': 'qualified'
        })
    
    # Upsert to prevent duplicates
    if new_leads:
        result = leads.insert('leads', new_leads, on_conflict='email')
        print(f"Synced {len(result)} customers to leads")
    
    return result
```

## 🔧 ENVIRONMENT TROUBLESHOOTING

### Check Environment Variables
```python
# check_env.py
import os
from pathlib import Path
from dotenv import load_dotenv

# Try loading from different locations
locations = [
    '.env',
    'api-toolkit/.env',
    '/path/to/api-toolkit/.env'
]

for loc in locations:
    if Path(loc).exists():
        load_dotenv(loc)
        print(f"Loaded .env from: {loc}")
        break

# Check what's configured
projects = {
    'project1': ('SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY'),
    'project2': ('SUPABASE_URL_2', 'SUPABASE_SERVICE_ROLE_KEY_2'),
    'project3': ('SUPABASE_URL_3', 'SUPABASE_SERVICE_ROLE_KEY_3'),
}

for project, (url_key, api_key) in projects.items():
    url = os.getenv(url_key, 'NOT SET')
    key = os.getenv(api_key, 'NOT SET')
    
    print(f"\n{project}:")
    print(f"  URL: {'✓ Configured' if url != 'NOT SET' else '✗ Missing'}")
    print(f"  Key: {'✓ Configured' if key != 'NOT SET' else '✗ Missing'}")
```

### Test All Connections
```python
# test_all.py
from api_toolkit.services.supabase.api import SupabaseAPI

projects = ['project1', 'project2', 'project3']

for project in projects:
    try:
        api = SupabaseAPI(project)
        if api.test_connection():
            tables = api.get_tables()
            print(f"✓ {project}: Connected ({len(tables)} tables)")
        else:
            print(f"✗ {project}: Connection failed")
    except Exception as e:
        print(f"✗ {project}: Error - {e}")
```

## 📝 QUICK REFERENCE CARD

### Essential Commands
```bash
# Installation
/path/to/api-toolkit/install.sh

# List services
python api-toolkit/toolkit.py list

# Test connection
python api-toolkit/toolkit.py supabase test

# Explore database
python api-toolkit/toolkit.py supabase explore [project]

# Get table schema
python api-toolkit/services/supabase/api.py schema [project] [table]

# Run examples
python api-toolkit/services/supabase/examples.py explore
```

### Essential Imports
```python
# Basic API
from api_toolkit.services.supabase.api import SupabaseAPI

# Query builder
from api_toolkit.services.supabase.query_helpers import QueryBuilder, CommonQueries

# Table documentation
from api_toolkit.services.supabase.table_docs import get_table_info, list_project_tables

# Initialize
api = SupabaseAPI('project1')  # or 'project2' or 'project3'
```

### Filter Quick Reference
```python
# Comparison
'eq'    # equals: {'status': 'eq.active'}
'neq'   # not equals: {'status': 'neq.deleted'}
'gt'    # greater than: {'age': 'gt.18'}
'gte'   # greater or equal: {'score': 'gte.80'}
'lt'    # less than: {'price': 'lt.100'}
'lte'   # less or equal: {'stock': 'lte.10'}

# Pattern matching
'like'  # case-sensitive: {'email': 'like.%@gmail.com'}
'ilike' # case-insensitive: {'name': 'ilike.%john%'}

# Special
'is'    # null/bool check: {'deleted': 'is.null'}
'in'    # in list: {'status': 'in.(active,pending)'}
```

## 🚨 COMMON PITFALLS & SOLUTIONS

### Pitfall 1: Forgetting to Check Schema
```python
# ❌ BAD - Assuming columns exist
api.query('users', filters={'full_name': 'eq.John'})  # Error if full_name doesn't exist

# ✅ GOOD - Check first
schema = api.get_schema('users')
columns = [col['column'] for col in schema]
if 'full_name' in columns:
    api.query('users', filters={'full_name': 'eq.John'})
elif 'name' in columns:
    api.query('users', filters={'name': 'eq.John'})
```

### Pitfall 2: Not Handling Empty Results
```python
# ❌ BAD - Assuming results exist
user = api.query('users', filters={'email': 'eq.test@example.com'})[0]

# ✅ GOOD - Check for empty
results = api.query('users', filters={'email': 'eq.test@example.com'})
if results:
    user = results[0]
else:
    user = None
```

### Pitfall 3: Querying Without Limits
```python
# ❌ BAD - Could return thousands of rows
all_users = api.query('users')

# ✅ GOOD - Always use limits for exploration
sample = api.query('users', limit=10)
total = api.count('users')
print(f"Showing {len(sample)} of {total} users")
```

### Pitfall 4: Wrong Project Name
```python
# ❌ BAD - Using old aliases
api = SupabaseAPI('main')  # Works but not clear

# ✅ GOOD - Use descriptive names
api = SupabaseAPI('project1')    # Clear what project this is
```

## 💡 PRO TIPS

1. **Always explore first**: `api.explore()` before writing queries
2. **Use QueryBuilder**: Cleaner syntax, fewer errors
3. **Check table_docs.py**: Has common patterns for each project
4. **Test with limits**: Start with `limit=5` then increase
5. **Count before fetch**: Use `api.count()` to check data size
6. **Use examples.py**: Copy working patterns from there
7. **Check schema changes**: Tables might have new columns
8. **Use proper error handling**: Wrap queries in try-catch
9. **Log your queries**: Keep track of what works
10. **Update documentation**: Add your patterns to table_docs.py

---

**Remember**: The toolkit saves ~89,400 tokens per conversation. Use it wisely!