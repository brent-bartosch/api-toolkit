# API Toolkit - Lightweight Alternative to MCP Servers

## 🔴 IMPORTANT: Check Installation Status First!

**BEFORE doing anything, check if the toolkit is already installed:**

```bash
# Quick check (recommended)
bash /path/to/api-toolkit/check-installation.sh

# Or manual check
ls -la api-toolkit/

# If you see the directory, IT'S ALREADY INSTALLED!
# Skip to the "Usage Examples" section below.
# DO NOT run install.sh again!
```

**If not installed yet:**
```bash
/path/to/api-toolkit/install.sh
```

---

## 🚀 Quick Start (For Any User/LLM)

> **New to the toolkit?** See [SETUP_GUIDE.md](SETUP_GUIDE.md) for a complete 5-minute walkthrough.

**Step 1: Install in your project**
```bash
cd /path/to/your/project
/path/to/api-toolkit/install.sh
# Choose option 1 (symlink recommended)
```

**Step 2: Create .env file in project root**
```bash
# Copy template to YOUR project directory (not api-toolkit/)
cp api-toolkit/.env.example .env

# Add your API keys
nano .env
```

**Step 3: Test it works**
```bash
# Check which .env was loaded and credential status
python api-toolkit/test-env-loading.py

# Try a query
python -c "from api_toolkit.services.supabase.api import SupabaseAPI; SupabaseAPI('project1').quick_start()"
```

**Done!** Now use it in your code:
```python
from api_toolkit.services.supabase.api import SupabaseAPI
api = SupabaseAPI('project1')
leads = api.query('leads', limit=10)
```

**Troubleshooting?** See [ENV_TROUBLESHOOTING.md](ENV_TROUBLESHOOTING.md)

---

## 🚀 180x More Efficient Than MCP

**MCP Servers**: 90,000 tokens loaded into every conversation
**API Toolkit**: 500-1000 tokens loaded only when needed

## ⚡ NEW: Zero-Friction Experience

```python
# Start with ANY project in 5 seconds!
from api_toolkit.services.supabase.api import SupabaseAPI

api = SupabaseAPI('project1')
api.quick_start()  # Shows tables, columns, filters, EVERYTHING!

# Bulletproof discovery - always works
info = api.discover()          # All tables
info = api.discover('users')   # Table details with columns & samples

# Raw SQL for complex queries
results = api.raw_query("SELECT * FROM users WHERE age > 18")

# API returns LIST directly, not {'data': [...]}
users = api.query('users')     # users is a list, NOT dict!
```

## Why This Exists

MCP servers are convenient but destroy your context budget. This toolkit provides the same functionality with:
- **Minimal token usage** - Load only what you need
- **Your patterns built-in** - Customized for your workflows
- **Progressive loading** - Quick reference or full details
- **Learn from usage** - Automatically documents successful patterns

---

## 🤖 For Claude Code: 3-Step Startup

**Every new conversation, run these commands FIRST:**

```bash
# Step 1: Check installation (2 seconds)
ls -la api-toolkit/
# ✅ See files? Already installed! Continue to step 2.
# ❌ "No such file"? Run: /path/to/api-toolkit/install.sh

# Step 2: Read project config (3 seconds)
cat .api-toolkit-config.md
# Look for services marked: ✅ Active
# ONLY use those services (ignore ⚪ Not Configured)

# Step 3: Quick health check (5 seconds)
python -c "from api_toolkit.services.supabase.api import SupabaseAPI; SupabaseAPI('project1').quick_start()"
```

**Critical:** API returns **LIST directly**, not `{'data': [...]}` format!
```python
users = api.query('users')  # users is a list
for user in users:          # NOT users['data']
    print(user['email'])
```

---

## Quick Start

### 🔍 Detailed Startup Sequence

```bash
# 1. Check if toolkit is installed in current project
ls -la api-toolkit 2>/dev/null || echo "Not installed - run: /path/to/api-toolkit/install.sh"

# 2. Check project configuration (which services are active)
cat .api-toolkit-config.md 2>/dev/null || echo "No project config - create one: /path/to/api-toolkit/init-project.sh"

# 3. Test connections for active services
python api-toolkit/toolkit.py supabase test

# 4. Explore what's available
python api-toolkit/services/supabase/api.py explore smoothed

# 5. Check schema before querying
python api-toolkit/services/supabase/api.py schema smoothed leads

# 6. Query with confidence
python api-toolkit/toolkit.py supabase query smoothed leads
```

### 📋 Project Configuration

Each project should have a `.api-toolkit-config.md` file declaring which services are active:

```bash
# Create project configuration
/path/to/api-toolkit/init-project.sh

# This creates .api-toolkit-config.md with:
# - Which services are active for THIS project
# - Project-specific patterns and queries
# - Progress tracking across conversations
# - Integration documentation

# See full guide: PROJECT_CONFIG_GUIDE.md
```

### 📊 Database Discovery Pattern (USE THIS FIRST!)

```python
# ALWAYS start with exploration to avoid errors
from api_toolkit.services.supabase.api import SupabaseAPI

# Step 1: Connect and explore
api = SupabaseAPI('project1')  # or 'project2' or 'project3'
api.explore()  # Shows all tables

# Step 2: Check schema before querying
schema = api.get_schema('table_name')
for col in schema:
    print(f"{col['column']}: {col['type']}")

# Step 3: Use QueryBuilder for clean queries
from api_toolkit.services.supabase.query_helpers import QueryBuilder

query = (QueryBuilder('table_name')
         .select('column1', 'column2')  # Only columns that exist!
         .where('status', '=', 'active')
         .limit(10))

results = query.execute(api)
```

## Available Services

| Service | Token Cost | Status | Description | Key Tables/Features |
|---------|------------|--------|-------------|--------------------|
| **supabase** | ~600 | ✅ Ready | Database operations | 3 Projects with full schema discovery |
| ↳ smoothed | - | ✅ Ready | Lead Generation | brands, leads, scraping_results |
| ↳ blingsting | - | ✅ Ready | CRM System | customers, orders, products |
| ↳ scraping | - | ✅ Ready | Web Project 3 | scrape_guide, scrape_results, scrape_queue |
| **context7** | ~500 | ✅ Ready | Real-time docs fetcher | Up-to-date API docs, code examples, library discovery |
| **metabase** | ~600 | ✅ Ready | Analytics & BI | Queries, cards, dashboards, exports |
| **smartlead** | ~600 | ✅ Ready | Cold email automation | Campaigns, leads, sequences, webhooks |
| **render** | ~600 | ✅ Ready | Cloud deployments | Services, databases, deploys, env vars |
| **brightdata** | ~500 | ✅ Ready | Web scraping & proxies | Project 3 Browser, Web Unlocker, SERP API |
| klaviyo | ~500 | 🔧 Pending | Email marketing | - |
| shopify | ~600 | 🔧 Pending | E-commerce | - |

## Installation

1. Navigate to the toolkit directory:
```bash
cd /path/to/api-toolkit
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. **Configure your API keys** - Create `.env` in your project root:

```bash
# In YOUR project directory (not in api-toolkit/):
cd /path/to/your/project

# Copy the template
cp api-toolkit/.env.example .env

# Edit with your actual API keys
nano .env  # or vim, code, etc.
```

**Where to put .env:**
```
your-project/
├── .env                    ← Create here (recommended)
├── api-toolkit/           ← Symlink or copy
└── main.py
```

4. **Test your configuration:**
```bash
# Shows which .env is loaded and credential status
python api-toolkit/test-env-loading.py

# Test specific service
python api-toolkit/toolkit.py supabase test
```

**Alternative:** Use system environment variables in `~/.zshrc` or `~/.bashrc`:
```bash
export SUPABASE_URL="your-url"
export SUPABASE_SERVICE_ROLE_KEY="your-key"
# ... etc
```

## Usage Examples

### 🎯 Supabase Query Patterns (COPY THESE!)

```python
from api_toolkit.services.supabase.api import SupabaseAPI
from api_toolkit.services.supabase.query_helpers import QueryBuilder

# PATTERN 1: Always explore first
api = SupabaseAPI('project1')
api.explore()  # See what tables exist
api.explore('leads')  # See columns and sample data

# PATTERN 2: Use QueryBuilder for complex queries
query = (QueryBuilder('leads')
         .where('score', '>=', 80)
         .where('status', '=', 'new')
         .contains('email', 'gmail')
         .order('score', desc=True)
         .limit(20))

hot_leads = query.execute(api)

# PATTERN 3: Check schema before querying
schema = api.get_schema('brands')
columns = [col['column'] for col in schema]
if 'industry' in columns:
    brands = api.query('brands', filters={'industry': 'eq.fashion'})

# PATTERN 4: Use documented patterns
from api_toolkit.services.supabase.table_docs import get_table_info

info = get_table_info('project1', 'leads')
print(info['sample_queries'])  # Copy working queries!

# PATTERN 5: Handle errors gracefully
try:
    data = api.query('users', limit=10)
except Exception as e:
    print(f"Query failed: {e}")
    # Check schema or use api.explore()
```

### 📋 Filter Operations Reference

```python
# COMPLETE FILTER SYNTAX GUIDE
filters = {
    # Comparison
    'age': 'eq.25',           # age = 25
    'status': 'neq.deleted',  # status != 'deleted'
    'score': 'gt.80',         # score > 80
    'score': 'gte.80',        # score >= 80
    'price': 'lt.100',        # price < 100
    'stock': 'lte.10',        # stock <= 10
    
    # Pattern matching
    'email': 'like.%@gmail.com',     # ends with @gmail.com
    'name': 'ilike.%john%',          # contains 'john' (case-insensitive)
    
    # Special checks
    'deleted_at': 'is.null',         # IS NULL
    'active': 'is.true',             # IS TRUE
    'verified': 'is.false',          # IS FALSE
    
    # In array
    'status': 'in.(active,pending)', # IN ('active', 'pending')
    
    # Not in array
    'role': 'not.in.(admin,super)',  # NOT IN ('admin', 'super')
}
```

### Metabase Analytics
```python
from api_toolkit.services.metabase.api import MetabaseAPI

# Using API key (recommended)
api = MetabaseAPI(api_key='mb_your_api_key')

# Or session auth
api = MetabaseAPI()
api.login('user@example.com', 'password')

# Run SQL queries
results = api.run_query('SELECT * FROM sales', database_id=1)

# Query saved cards
data = api.query_card(123)

# Export data
csv = api.export_card(123, format='csv')

# Create dashboards
dashboard = api.create_dashboard('KPI Dashboard')
api.add_card_to_dashboard(dashboard['id'], card_id=123)
```

### Context7 Documentation Fetching
```python
from api_toolkit.services.context7.api import Context7API

api = Context7API()  # Uses CONTEXT7_API_KEY from .env
api.quick_start()    # Shows available features

# Search for documentation
results = api.search("react hooks useState")
for result in results[:3]:
    print(f"{result['title']} - {result['library']}")

# Get contextual docs for AI coding
context = api.get_context(
    "Create a Next.js middleware that checks for JWT in cookies",
    libraries=['nextjs', 'jose']
)

# Fetch specific library docs
docs = api.get_docs('react', 'hooks')
examples = api.get_examples('nextjs', 'middleware')

# List available libraries
libraries = api.list_libraries()
```

### Smartlead Cold Email
```python
from api_toolkit.services.smartlead.api import SmartleadAPI

api = SmartleadAPI()  # Uses SMARTLEAD_API_KEY from .env

# Create campaign
campaign = api.create_campaign('Q1 Outreach', client_id=1)

# Add leads
leads = [
    {'email': 'prospect@company.com', 'first_name': 'John', 'company_name': 'Company Inc'}
]
api.add_leads_to_campaign(campaign['id'], leads)

# Check analytics
stats = api.get_campaign_analytics(campaign['id'])
print(f"Reply rate: {stats['reply_rate']}%")

# Setup webhooks
from api_toolkit.services.smartlead.webhooks import SmartleadWebhookHandler
handler = SmartleadWebhookHandler()
# Process incoming webhook events
```

### CLI Usage
```bash
# List services
python toolkit.py list

# Test connection
python toolkit.py supabase test smoothed
python toolkit.py context7 test

# Query table
python toolkit.py supabase query scraping scrape_guide

# Get documentation
python toolkit.py supabase docs full
python toolkit.py context7 quick_start

# Search documentation
python toolkit.py context7 search "react hooks"

# Check environment
python toolkit.py supabase check
python toolkit.py context7 check
```

## Adding New Services

1. Copy the template:
```bash
cp -r services/_template services/your-service
```

2. Follow the integration guide:
```bash
cat services/_template/INTEGRATION_GUIDE.md
```

3. Keep documentation focused (~1000 tokens):
- Your common patterns
- Methods you actually use
- Your specific configurations

## Token Usage Comparison

### Before (MCP Servers)
```
Context usage: 108k/200k tokens (54%)
- MCP tools: 90.3k tokens (45.1%) 😱
- Free space: 92.3k (46.1%)
```

### After (API Toolkit)
```
Context usage: 20k/200k tokens (10%)
- API toolkit: 0.6k tokens (0.3%) ✨
- Free space: 180k (90%)
```

## Directory Structure

```
api-toolkit/
├── core/                    # Framework
│   ├── base_api.py         # Base class with retry, auth, errors
│   ├── config.py           # Environment and configuration
│   └── documentation.py    # Doc loading and compression
├── services/
│   ├── _template/          # Template for new services
│   ├── supabase/           # ✅ Implemented
│   ├── context7/           # ✅ Implemented - Real-time docs
│   ├── metabase/           # ✅ Implemented
│   ├── smartlead/          # ✅ Implemented
│   ├── render/             # ✅ Implemented
│   ├── brightdata/         # ✅ Implemented
│   ├── klaviyo/            # 🔧 Pending
│   └── shopify/            # 🔧 Pending
├── tools/                  # Documentation extraction
└── toolkit.py              # Main CLI interface
```

## 🏆 Best Practices (CLAUDE: FOLLOW THESE!)

### 1. **ALWAYS Explore Before Querying**
```python
# ✅ GOOD - Know what exists
api = SupabaseAPI('project1')
api.explore()  # See tables
schema = api.get_schema('leads')  # See columns
results = api.query('leads', filters={'score': 'gte.80'})

# ❌ BAD - Guessing at structure
api.query('users', filters={'full_name': 'eq.John'})  # Error if column doesn't exist
```

### 2. **Use QueryBuilder for Complex Queries**
```python
# ✅ GOOD - Clean, readable, no filter syntax errors
from api_toolkit.services.supabase.query_helpers import QueryBuilder

query = (QueryBuilder('users')
         .where('age', '>=', 18)
         .contains('email', 'gmail')
         .order('created_at', desc=True)
         .limit(10))

# ❌ BAD - Manual filter formatting
api.query('users', filters={'age': 'gte.18', 'email': 'ilike.%gmail%'})
```

### 3. **Check Table Documentation**
```python
# ✅ GOOD - Use known patterns
from api_toolkit.services.supabase.table_docs import get_table_info

info = get_table_info('project1', 'leads')
example_query = info['sample_queries'][0]  # Use working examples

# ❌ BAD - Writing queries from scratch every time
```

### 4. **Handle Errors Gracefully**
```python
# ✅ GOOD - Prepared for issues
try:
    api = SupabaseAPI('project1')
    if not api.test_connection():
        print("Connection issue - check .env")
        return
    
    data = api.query('leads', limit=10)
except Exception as e:
    print(f"Error: {e}")
    api.explore()  # Show what's available

# ❌ BAD - No error handling
data = api.query('leads')  # Crashes if anything goes wrong
```

### 5. **Use Proper Project Names**
```python
# ✅ GOOD - Clear and descriptive
api = SupabaseAPI('project1')    # Lead generation
api = SupabaseAPI('project2')  # CRM data
api = SupabaseAPI('project3')    # Web scraping

# ❌ BAD - Old aliases
api = SupabaseAPI('main')        # What is main?
api = SupabaseAPI('project2')    # Not descriptive
```

## 🔧 Troubleshooting Guide

### Problem: "Table/Column doesn't exist"
```python
# SOLUTION: Always check what actually exists
api = SupabaseAPI('project1')

# List all tables
api.explore()

# Check specific table schema
schema = api.get_schema('table_name')
for col in schema:
    print(f"{col['column']}: {col['type']}")

# Get sample data to see structure
sample = api.query('table_name', limit=3)
if sample:
    print(sample[0].keys())  # Shows all column names
```

### Problem: "Connection failed"
```bash
# SOLUTION: Check environment step by step

# 1. Check if .env exists
ls -la .env api-toolkit/.env

# 2. Test specific project
python -c "
from api_toolkit.services.supabase.api import SupabaseAPI
api = SupabaseAPI('project1')
print('Connected!' if api.test_connection() else 'Failed!')
"

# 3. Check all projects
python api-toolkit/services/supabase/api.py test smoothed
python api-toolkit/services/supabase/api.py test blingsting
python api-toolkit/services/supabase/api.py test scraping
```

### Problem: "How do I write this query?"
```python
# SOLUTION: Use the examples and helpers

# 1. Check documented examples
from api_toolkit.services.supabase.table_docs import get_table_info
info = get_table_info('project1', 'leads')
print(info['sample_queries'])

# 2. Use QueryBuilder for complex queries
from api_toolkit.services.supabase.query_helpers import QueryBuilder
query = QueryBuilder('table').where('col', '=', 'value').build()
print(query)  # See the generated parameters

# 3. Reference working examples
python api-toolkit/services/supabase/examples.py smoothed
```

### Problem: "Query returns too much data"
```python
# SOLUTION: Always use limits and pagination

# Check size first
count = api.count('large_table')
print(f"Total records: {count}")

# Get sample
sample = api.query('large_table', limit=10)

# Paginate through results
from api_toolkit.services.supabase.query_helpers import CommonQueries

for page in range(1, 5):  # First 4 pages
    params = CommonQueries.paginated('large_table', page=page, per_page=100)
    batch = api.query('large_table', **params)
    process_batch(batch)
```

## Environment Variables

### 📍 Where to Put Your .env File

**Recommendation:** One `.env` file in your **project root** (not in api-toolkit subdirectory).

```bash
your-project/
├── .env                    # ✅ PUT YOUR API KEYS HERE
├── api-toolkit/           # Symlink to toolkit
├── src/
└── main.py
```

**How it works:** The toolkit uses smart env loading with this priority:
1. **Project root** (`./env`) - Checked first ✅
2. Toolkit directory (`api-toolkit/.env`) - Fallback
3. Home directory (`~/.api-toolkit.env`) - Global fallback

**Debug which .env was loaded:**
```python
from api_toolkit.core.config import Config
print(f"Loaded env from: {Config.get_env_source()}")
```

### Required Environment Variables

Configure these in your project's `.env` file:

### Supabase Projects
```bash
# Project 1: Project1 (Lead Generation)
SUPABASE_URL=https://your-project-1.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-key-here

# Project 2: Project2 (CRM)
SUPABASE_URL_2=https://your-project-2.supabase.co
SUPABASE_SERVICE_ROLE_KEY_2=your-key-here

# Project 3: Project 3 (Web Project 3)
SUPABASE_URL_3=https://your-project-3.supabase.co
SUPABASE_SERVICE_ROLE_KEY_3=your-key-here
```

### Context7 (Real-time Documentation)
```bash
# Get your API key from https://context7.com
CONTEXT7_API_KEY=your-api-key-here
CONTEXT7_URL=https://context7.com/api/v1  # Optional, uses default
```

### Metabase (Analytics)
```bash
METABASE_URL=http://localhost:3000  # Or your Metabase instance URL
METABASE_USERNAME=your-email@example.com
METABASE_PASSWORD=your-password
# Or use API key instead:
METABASE_API_KEY=mb_your_api_key_here
```

### Smartlead (Cold Email)
```bash
SMARTLEAD_API_KEY=your-api-key-here
SMARTLEAD_WEBHOOK_SECRET=your-webhook-secret  # Optional, for webhook validation
```

### Render (Cloud Deployments)
```bash
RENDER_API_KEY=your-api-key-here
```

### BrightData (Web Project 3 & Proxies)
```bash
BRIGHTDATA_API_KEY=your-api-key-here
BRIGHTDATA_CUSTOMER_ID=your-customer-id
```

### Other Services (Pending Implementation)
```bash
# Klaviyo (Email Marketing)
KLAVIYO_API_KEY=pk_your_key_here

# Shopify (E-commerce)
SHOPIFY_ACCESS_TOKEN=your-token-here
SHOPIFY_STORE_URL=your-store.myshopify.com
```

### Quick Setup Check
```bash
# Check which services are configured
python toolkit.py list

# Test individual service connections
python toolkit.py supabase test
python toolkit.py context7 test
python toolkit.py metabase test
python toolkit.py smartlead test
python toolkit.py render test
python toolkit.py brightdata test

# Check environment variables for a service
python toolkit.py supabase check
python toolkit.py context7 check
```

## Contributing

To add a new service:
1. Use the template in `services/_template`
2. Focus on YOUR use cases, not complete coverage
3. Keep documentation under 1000 tokens
4. Test with real workflows

## Future Enhancements

- [ ] Batch operations for all services
- [ ] Async support for parallel calls
- [ ] Auto-generate docs from usage
- [ ] Export patterns as documentation
- [ ] Web UI for configuration

---

**Remember**: Every token saved is more room for actual work. Stop loading 90,000 tokens of MCP overhead!