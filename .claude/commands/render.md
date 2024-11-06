---
description: Load Render API toolkit context and check installation
---

# Render API Toolkit Context

**CRITICAL INSTRUCTIONS:**

1. **CHECK INSTALLATION FIRST**:
   ```bash
   ls -la api-toolkit/
   ```

2. **USE EXISTING CODE** - Don't recreate Render integrations

3. **REVIEW THE IMPLEMENTATION**:

**Core Render Files to Review:**
- `api-toolkit/services/render/api.py` - Main RenderAPI class
- `api-toolkit/services/render/query_helpers.py` - Helpers for filtering
- `api-toolkit/services/render/examples.py` - Working examples

**Key Methods:**

- `RenderAPI()` - Initialize (uses RENDER_API_KEY)
- `.list_services()` - List all services
- `.get_service(service_id)` - Get service details
- `.trigger_deploy(service_id)` - Trigger manual deploy
- `.list_deploys(service_id)` - Get deploy history
- `.get_env_vars(service_id)` - Get environment variables
- `.update_env_var(service_id, key, value)` - Update env var
- `.list_databases()` - List databases
- `.get_database(database_id)` - Get database details

**Common Workflow:**
```python
from api_toolkit.services.render.api import RenderAPI

api = RenderAPI()

# List services
services = api.list_services()
for service in services:
    print(f"{service['name']}: {service['type']}")

# Trigger deploy
api.trigger_deploy('srv-abc123')

# Update environment variable
api.update_env_var('srv-abc123', 'API_KEY', 'new-value')

# Check deploy status
deploys = api.list_deploys('srv-abc123', limit=5)
latest = deploys[0]
print(f"Status: {latest['status']}")
```

**Environment Requirements:**
```bash
RENDER_API_KEY=your-render-api-key-here
```

**Your Task:**
1. Check installation
2. Read Render service files
3. Summarize capabilities
4. Use existing toolkit
