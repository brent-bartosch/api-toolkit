# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**API Toolkit** is a lightweight, token-efficient alternative to MCP servers for API integrations. It provides a consistent interface for multiple API services (Supabase, Metabase, Smartlead, Render, BrightData, etc.) with ~500-1000 tokens per service versus 90,000+ for MCP servers.

Key design principle: **Load only what you need, when you need it.**

## Architecture

### Plugin-Based Service System

The toolkit uses a plugin architecture where each service:
1. Inherits from `core/base_api.py::BaseAPI`
2. Implements its own `services/{name}/api.py`
3. Provides helper utilities in `services/{name}/query_helpers.py`
4. Includes working examples in `services/{name}/examples.py`

**BaseAPI provides:**
- Automatic retry logic with exponential backoff
- Rate limiting (configurable per service)
- Error handling with custom `APIError` exceptions
- Session management
- Usage pattern tracking for documentation

### Environment Configuration Priority

The `core/config.py` module loads `.env` files with this priority:
1. **Project root** (`./env`) - Where user works (highest priority)
2. **Toolkit directory** (`api-toolkit/.env`) - Fallback for standalone usage
3. **Home directory** (`~/.api-toolkit.env`) - Global fallback

**Critical:** Services look in project root first, not the toolkit subdirectory. This allows one `.env` per project.

### Service Discovery

The `toolkit.py` CLI dynamically discovers and loads services:
- Scans `services/` directory for subdirectories with `api.py`
- Lazy loads services only when accessed
- Caches loaded instances for reuse
- Supports project-specific configurations (e.g., Supabase has 3 projects: smoothed, blingsting, scraping)

## Development Commands

### Testing
```bash
# Test a specific service
python tests/test_smartlead.py
python tests/test_metabase.py

# Test all services with markdown report
python tests/run_all_tests.py --markdown

# Test specific services only
python tests/run_all_tests.py smartlead supabase
```

All tests inherit from `tests/base_test.py::ServiceTestBase` which provides 10 standard tests (initialization, auth, connection, rate limiting, error handling, discovery, response format, token efficiency, documentation, examples).

### Running Services via CLI
```bash
# List available services
python toolkit.py list

# Test service connection
python toolkit.py supabase test smoothed
python toolkit.py smartlead test

# Query data
python toolkit.py supabase query smoothed leads

# Get documentation (quick, full, or reference)
python toolkit.py supabase docs quick
python toolkit.py context7 quick_start

# Check environment variables
python toolkit.py supabase check
```

### Installation in Projects
```bash
# Install toolkit in another project
./install.sh

# Options:
# 1 = symlink (recommended, auto-updates)
# 2 = copy (standalone)
# 3 = python package (system-wide)

# Check if already installed in a project
./check-installation.sh

# Initialize project configuration
./init-project.sh  # Creates .api-toolkit-config.md
```

### Environment Testing
```bash
# Debug which .env file is being loaded
python test-env-loading.py

# Shows:
# - Which .env path was loaded
# - Status of all service credentials
# - Helpful troubleshooting info
```

## Adding a New Service

Follow this pattern (uses the template in `services/_template/`):

1. **Copy template:**
   ```bash
   cp -r services/_template services/yourservice
   ```

2. **Implement `api.py`:**
   - Inherit from `BaseAPI`
   - Override `_setup_auth()` to configure authentication headers
   - Add discovery methods: `quick_start()`, `explore()`, or `discover()`
   - Keep token usage under 2000 (see `core/documentation.py`)

3. **Add query helpers** in `query_helpers.py`:
   - QueryBuilder class for complex queries
   - CommonQueries for frequent patterns
   - Keep helpers focused on actual usage patterns

4. **Create examples** in `examples.py`:
   - Show common workflows
   - Make examples runnable (`if __name__ == "__main__"`)
   - Cover basic, intermediate, and advanced usage

5. **Write tests** in `tests/test_yourservice.py`:
   - Inherit from `ServiceTestBase`
   - Override `get_test_config()` with service details
   - Add service-specific tests as needed
   - Aim for 100% pass rate

6. **Add to config** in `core/config.py`:
   ```python
   SERVICES = {
       'yourservice': {
           'env_vars': ['YOURSERVICE_API_KEY'],
           'token_cost': 500  # Estimated token usage
       }
   }
   ```

7. **Document** in `services/yourservice/README.md`:
   - Focus on YOUR use cases, not complete API coverage
   - Keep documentation under 1000 tokens
   - Include filter syntax, common queries, troubleshooting

## Key Patterns

### Discovery-First Approach

All Supabase queries should start with discovery to avoid "table/column doesn't exist" errors:

```python
# Always explore before querying
api = SupabaseAPI('project1')
api.quick_start()  # Shows tables, columns, filters in 5 seconds

# Or programmatically
info = api.discover()  # Returns dict with table info
schema = api.get_schema('table_name')  # Returns column definitions

# Then query safely
results = api.query('table_name', limit=10)
```

### QueryBuilder for Complex Queries

Use `QueryBuilder` instead of manual filter syntax:

```python
from api_toolkit.services.supabase.query_helpers import QueryBuilder

query = (QueryBuilder('leads')
         .select('email', 'score', 'status')
         .where('score', '>=', 80)
         .where('status', '=', 'new')
         .order('score', desc=True)
         .limit(20))

results = query.execute(api)
```

### Response Format Convention

**Important:** Services return data directly, not wrapped in `{'data': [...]}`:

```python
# API returns LIST directly
users = api.query('users')  # users is a list
for user in users:          # NOT users['data']
    print(user['email'])
```

### Error Handling

All services raise `APIError` from `core/base_api.py`:

```python
from api_toolkit.core.base_api import APIError

try:
    api = SupabaseAPI('project1')
    results = api.query('table')
except APIError as e:
    print(f"API Error: {e.message}")
    print(f"Status: {e.status_code}")
    print(f"Response: {e.response}")
```

### Rate Limiting

Rate limiting is automatic via `BaseAPI.rate_limiter`:

```python
# Configured per service in __init__
super().__init__(
    api_key=api_key,
    base_url=base_url,
    requests_per_second=10,  # Adjust per service limits
    max_retries=3
)
```

### Project-Specific Configuration

Each project using the toolkit should have `.api-toolkit-config.md`:

```bash
# Create configuration
./init-project.sh

# This creates a markdown file that:
# - Declares which services are active (✅) vs not configured (⚪)
# - Documents project-specific query patterns
# - Tracks progress across conversations
# - Persists across Claude Code conversation restarts
```

See `PROJECT_CONFIG_GUIDE.md` for details.

## Service-Specific Notes

### Supabase (services/supabase/)
- Three configured projects: 'project1' (lead gen), 'project2' (CRM), 'project3' (web scraping)
- Always use discovery methods before querying
- `raw_query()` method for complex SQL (auto-limits to 1000 if no LIMIT clause)
- Filter syntax documented in `FILTER_SYNTAX.md`
- **API Key Changes (2025+)**: Supabase introduced new key formats:
  - `sb_secret_...` replaces `service_role` JWT keys
  - `sb_publishable_...` replaces `anon` JWT keys
  - Both formats work during transition (legacy removed late 2026)
  - See: https://github.com/orgs/supabase/discussions/29260

### Metabase (services/metabase/)
- Supports both API key and session auth
- Can run raw SQL and MBQL queries
- Exports to CSV, JSON, XLSX formats
- Dashboard creation and management

### Smartlead (services/smartlead/)
- Campaign management for cold email
- Webhook handling via `webhooks.py`
- Real-time event processing
- Analytics and reporting

### Render (services/render/)
- Cloud deployment management
- Service, database, and cron job control
- Environment variable management
- Deploy triggering and monitoring

### BrightData (services/brightdata/)
- Web scraping with Project 3 Browser
- Web Unlocker for anti-bot bypass
- SERP API for search results
- Proxy management

### Context7 (services/context7/)
- Real-time documentation fetching
- Library and framework docs
- Contextual examples for AI coding
- Up-to-date API references

## Testing Standards

Services must pass 10 standard tests from `ServiceTestBase`:

1. **Initialization** - Service instantiates without errors
2. **Authentication** - API keys loaded and headers configured
3. **Connection** - Can connect to service endpoint
4. **Rate Limiting** - Rate limiter configured properly
5. **Error Handling** - Raises appropriate errors
6. **Discovery Methods** - Has explore/discover/quick_start
7. **Response Format** - Returns expected data types
8. **Token Efficiency** - Uses < 2000 tokens (warns at > 5000)
9. **Documentation** - > 80% docstring coverage
10. **Examples** - examples.py exists and is runnable

See `tests/TESTING_GUIDE.md` for comprehensive testing documentation.

## Token Optimization

The toolkit is designed to minimize token usage:

- **Lazy loading:** Services loaded only when accessed
- **Progressive documentation:** Quick reference (500 tokens) vs full docs (2000 tokens)
- **Focused scope:** Document YOUR patterns, not entire APIs
- **Smart defaults:** Common operations have simple interfaces

Compare: MCP servers load 90,000 tokens per conversation. This toolkit loads ~500-1000 per service only when needed.

## Common Troubleshooting

### "Table/column doesn't exist" (Supabase)
→ Always run `api.explore()` or `api.get_schema('table')` first

### "Connection failed"
→ Check environment with `python test-env-loading.py`
→ Ensure `.env` is in project root, not toolkit subdirectory

### "JWT expired" / "Invalid API key"
→ Run `python toolkit.py [service] check` to verify credentials
→ Check if `.env` file has correct variable names (see service README)

### "Wrong .env loaded"
→ Environment loads from: (1) project root, (2) toolkit dir, (3) home dir
→ Put `.env` in project root for project-specific configs

### Empty results from query
→ Start with small limit: `api.query('table', limit=5)`
→ Remove filters one by one to isolate issue
→ Check actual data with `api.explore('table')`

### Service not found
→ Run `python toolkit.py list` to see available services
→ Check if `services/{name}/api.py` exists
→ Verify API class name ends with "API"

## MCP Servers (Three Approaches)

The toolkit provides **three MCP server implementations**, each optimized for different scenarios:

### 1. Direct Tools MCP (~300 tokens) - Simple Queries

**Best for**: Small queries (<100 rows), simple operations

```bash
# Install: pip install -r mcp-server/requirements.txt
# Configure in ~/.config/claude/mcp.json (see mcp-server/INSTALLATION.md)
```

**7 Supabase tools:**
- `query_supabase` - Query tables with filters
- `supabase_discover` - List tables or get schema
- `supabase_raw_query` - Execute raw SQL
- `supabase_insert` - Insert records
- `supabase_update` - Update records
- `supabase_rpc` - Call PostgreSQL functions
- `supabase_invoke_function` - Call Deno Edge Functions

**See:** `mcp-server/README.md`

---

### 2. Code Execution MCP (~2,000 tokens) - **RECOMMENDED for Large Datasets**

**Best for**: Large datasets (>100 rows), complex analysis, multi-step operations

Following **Anthropic's pattern**: Execute Python in sandbox, process data before returning (99% token savings!).

```bash
# Install: pip install -r mcp-server-code-exec/requirements.txt
# Configure in ~/.config/claude/mcp.json (see mcp-server-code-exec/INSTALLATION.md)
```

**6 tools:**
- `execute_python` - Run Python code in secure sandbox
- `discover_services` - List available services (progressive disclosure)
- `get_service_info` - Get service details (3 detail levels)
- `get_quick_start` - Minimal working example
- `search_tools` - Find tools by keyword
- `get_code_examples` - Get specific examples

**See:** `mcp-server-code-exec/README.md` | `CODE_EXECUTION_MCP_SUMMARY.md`

---

## Slash Commands (For Documentation)
| Command | Purpose | Tokens |
|---------|---------|--------|
| `/api-toolkit` | Check installation, get overview | ~800 |
| `/supabase` | Database operations (3 projects) | ~1000 |
| `/smartlead` | Email campaigns, webhooks | ~900 |
| `/metabase` | Analytics, BI, SQL queries | ~850 |
| `/render` | Cloud deployments | ~800 |
| `/brightdata` | Web scraping, proxies | ~850 |

## References
- **MCP server summary**: `MCP_SERVER_SUMMARY.md` ⭐ NEW - What was built and why
- **MCP server guide**: `mcp-server/README.md` ⭐ NEW - Complete usage guide
- **MCP installation**: `mcp-server/INSTALLATION.md` ⭐ NEW - Step-by-step setup
- **MCP design**: `mcp-server/design.md` ⭐ NEW - Architecture & token optimization
- **Slash commands guide**: `SLASH_COMMANDS.md` - Documentation loading
- **Command definitions**: `.claude/commands/*.md` - Service-specific commands
- Full documentation: `README.md`
- Quick reference card: `QUICK_REFERENCE.md`
- Setup guide: `SETUP_GUIDE.md`
- Testing guide: `tests/TESTING_GUIDE.md`
- Project configuration: `PROJECT_CONFIG_GUIDE.md`
- Environment troubleshooting: `ENV_TROUBLESHOOTING.md`
- Filter syntax (Supabase): `services/supabase/FILTER_SYNTAX.md`
- Changelog: `CHANGELOG.md`
