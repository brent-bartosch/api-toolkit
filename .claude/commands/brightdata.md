---
description: Load BrightData API toolkit context and check installation
---

# BrightData API Toolkit Context

**CRITICAL INSTRUCTIONS:**

1. **CHECK INSTALLATION FIRST**:
   ```bash
   ls -la api-toolkit/
   ```

2. **USE EXISTING CODE** - Don't recreate scraping tools

3. **REVIEW THE IMPLEMENTATION**:

**Core BrightData Files to Review:**
- `api-toolkit/services/brightdata/api.py` - Main BrightDataAPI class
- `api-toolkit/services/brightdata/web_unlocker.py` - Web Unlocker tool
- `api-toolkit/services/brightdata/examples.py` - Working examples

**Key Features:**

- **Project 3 Browser** - Full browser automation for scraping
- **Web Unlocker** - Anti-bot bypass for protected sites
- **SERP API** - Search engine results
- **Proxy Management** - Residential/datacenter proxies

**Key Methods:**

- `BrightDataAPI()` - Initialize (uses BRIGHTDATA_API_KEY)
- `.scraping_browser()` - Access scraping browser
- `.web_unlocker()` - Access web unlocker
- `.serp_api()` - Access SERP API
- `.list_datasets()` - List available datasets
- `.get_dataset(dataset_id)` - Get dataset contents

**Common Workflow:**
```python
from api_toolkit.services.brightdata.api import BrightDataAPI

api = BrightDataAPI()

# Use Web Unlocker
from api_toolkit.services.brightdata.web_unlocker import WebUnlocker

unlocker = WebUnlocker()
response = unlocker.get('https://example.com')
print(response.text)

# Project 3 Browser
browser = api.scraping_browser()
result = browser.navigate('https://example.com')

# SERP API
serp = api.serp_api()
results = serp.search('keyword', engine='google', country='us')
```

**Environment Requirements:**
```bash
BRIGHTDATA_API_KEY=your-api-key-here
BRIGHTDATA_CUSTOMER_ID=your-customer-id
```

**Your Task:**
1. Check installation
2. Read BrightData service files
3. Summarize scraping capabilities
4. Use existing toolkit
