---
description: Load Metabase API toolkit context and check installation
---

# Metabase API Toolkit Context

**CRITICAL INSTRUCTIONS:**

1. **CHECK INSTALLATION FIRST**:
   ```bash
   ls -la api-toolkit/
   ```
   - ✅ Installed: Use it, don't recreate it
   - ❌ Not found: Offer to install

2. **USE EXISTING CODE** - Don't duplicate:
   - DO NOT write new Metabase API clients
   - DO NOT create new query builders
   - ALWAYS use the existing MetabaseAPI class

3. **REVIEW THE IMPLEMENTATION**:

**Core Metabase Files to Review:**
- `api-toolkit/services/metabase/api.py` - Main MetabaseAPI class
- `api-toolkit/services/metabase/examples.py` - Working examples
- `api-toolkit/QUICK_REFERENCE.md` - Metabase sections

**Key Methods:**

- `MetabaseAPI(api_key)` or `MetabaseAPI()` - Initialize
- `.login(email, password)` - Session auth (if not using API key)
- `.run_query(sql, database_id, parameters)` - Run SQL queries
- `.query_card(card_id)` - Query saved questions/cards
- `.export_card(card_id, format)` - Export to CSV/JSON/XLSX
- `.create_dashboard(name)` - Create dashboard
- `.add_card_to_dashboard(dashboard_id, card_id)` - Add cards

**Common Workflow:**
```python
from api_toolkit.services.metabase.api import MetabaseAPI

# Using API key (recommended)
api = MetabaseAPI(api_key='mb_your_api_key')

# Or session auth
api = MetabaseAPI()
api.login('user@example.com', 'password')

# Run SQL query
results = api.run_query(
    'SELECT * FROM sales WHERE date > ?',
    database_id=1,
    parameters=[{"type": "date", "value": "2024-01-01"}]
)

# Query saved card
data = api.query_card(123)

# Export to CSV
csv_data = api.export_card(123, format='csv')

# Create dashboard
dashboard = api.create_dashboard('Monthly KPIs')
```

**Environment Requirements:**
```bash
METABASE_URL=http://localhost:3000  # Or your instance URL
METABASE_API_KEY=mb_your_api_key_here

# Or for session auth:
METABASE_USERNAME=your-email@example.com
METABASE_PASSWORD=your-password
```

**Your Task:**
1. Check installation status
2. If installed: Read the Metabase service files
3. Summarize available methods
4. Ask what they want to accomplish
5. Use existing toolkit - DO NOT rewrite!
