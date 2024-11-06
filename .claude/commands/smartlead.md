---
description: Load Smartlead API toolkit context and check installation
---

# Smartlead API Toolkit Context

**CRITICAL INSTRUCTIONS:**

1. **CHECK INSTALLATION FIRST** - The API toolkit may already be installed:
   ```bash
   ls -la api-toolkit/ || ls -la .toolkit-installed
   ```
   - ✅ If you see output: **TOOLKIT IS ALREADY INSTALLED!** Use it, don't recreate it.
   - ❌ If "No such file": Not installed yet, offer to install it.

2. **USE EXISTING CODE** - Don't recreate what already exists:
   - DO NOT write new Smartlead API wrappers
   - DO NOT create new webhook handlers
   - ALWAYS use the existing SmartleadAPI class

3. **REVIEW THE IMPLEMENTATION** - Read these files:

**Core Smartlead Files to Review:**
- `api-toolkit/services/smartlead/api.py` - Main SmartleadAPI class
- `api-toolkit/services/smartlead/webhooks.py` - Webhook event handlers
- `api-toolkit/services/smartlead/examples.py` - Working examples
- `api-toolkit/QUICK_REFERENCE.md` - Filter for Smartlead sections

**Key Methods to Know:**

After reviewing, you should understand:
- `SmartleadAPI()` - Initialize (uses SMARTLEAD_API_KEY from .env)
- `.create_campaign(name, client_id, settings)` - Create email campaign
- `.add_leads_to_campaign(campaign_id, leads)` - Add leads to campaign
- `.get_campaign_analytics(campaign_id)` - Get campaign stats
- `.register_webhook(url, events)` - Register webhook for events
- Webhook handling via `SmartleadWebhookHandler`

**Common Workflow:**
```python
from api_toolkit.services.smartlead.api import SmartleadAPI

# Create campaign
api = SmartleadAPI()
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
```

**Webhook Handling:**
```python
from api_toolkit.services.smartlead.webhooks import SmartleadWebhookHandler

handler = SmartleadWebhookHandler()
result = handler.handle_event(webhook_payload)
```

**Environment Requirements:**
```bash
SMARTLEAD_API_KEY=your-api-key-here
SMARTLEAD_WEBHOOK_SECRET=your-webhook-secret  # Optional
```

**Your Task:**
1. Check if api-toolkit is installed
2. If installed: Read the Smartlead service files listed above
3. Summarize available methods and capabilities
4. Ask what they want to accomplish with Smartlead
5. Use existing toolkit - DO NOT rewrite!
