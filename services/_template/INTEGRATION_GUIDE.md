# Adding a New API Service

## Quick Start Checklist

1. [ ] Copy this template directory
2. [ ] Set environment variables
3. [ ] Extract/write documentation
4. [ ] Implement core methods
5. [ ] Add your patterns
6. [ ] Test the integration

## Step 1: Copy Template

```bash
cd /path/to/api-toolkit
cp -r services/_template services/[your-service]
```

## Step 2: Environment Setup

Add to your `~/.zshrc` or `~/.bashrc`:
```bash
export [SERVICE]_API_KEY="your-api-key"
# Add any other required environment variables
```

## Step 3: Documentation Extraction

### Option A: From OpenAPI/Swagger
```bash
# If the service provides OpenAPI spec:
python tools/extract_openapi.py https://api.[service].com/swagger.json \
    > services/[your-service]/docs/api_methods.yaml
```

### Option B: From HTML Documentation
```bash
# Scrape and compress documentation:
python tools/scrape_docs.py https://docs.[service].com/api \
    > services/[your-service]/docs/raw_docs.md

python tools/compress_docs.py services/[your-service]/docs/raw_docs.md \
    > services/[your-service]/docs/README.md
```

### Option C: Manual Documentation
Create `services/[your-service]/docs/README.md` with:
- Top 10-20 methods you actually use
- Authentication method
- Rate limits
- 3-5 real examples from your work

## Step 4: Implement API Client

Edit `services/[your-service]/api.py`:

1. Update class name and imports
2. Set correct base URL
3. Implement authentication in `_setup_auth()`
4. Add your most-used methods
5. Update docstrings with real examples

## Step 5: Add Your Patterns

Create `services/[your-service]/docs/examples.json`:
```json
[
  {
    "name": "Create and send campaign",
    "code": "api.create_campaign(name='Welcome', template_id='abc123')",
    "description": "Your common workflow"
  }
]
```

## Step 6: Test Your Integration

```bash
# Test connection
python services/[your-service]/api.py test

# Test a simple query
python -c "
from services.[your-service].api import [ServiceName]API
api = [ServiceName]API()
print(api.test_connection())
"
```

## Documentation Token Budget

Keep your documentation efficient:
- `README.md`: ~500 tokens (essential reference)
- `api_methods.yaml`: ~300 tokens (method signatures)
- `examples.json`: ~200 tokens (your patterns)
- **Total**: ~1000 tokens per service

## What to Include

### Must Have
- Authentication method
- 5-10 most used endpoints
- Rate limits
- Your specific IDs/configurations
- 3-5 real examples

### Nice to Have
- Error codes and handling
- Pagination patterns
- Webhook setup (if applicable)
- Your common workflows

### Don't Include
- Every possible endpoint
- Detailed parameter descriptions
- Generic examples you'll never use
- Full response schemas

## Common Patterns to Implement

```python
class YourAPI(BaseAPI):
    def __init__(self):
        # Your specific configuration
        self.list_id = "abc123"  # Your actual IDs
        self.template_id = "xyz789"
        super().__init__(...)
    
    def your_common_workflow(self):
        """
        Implement your specific workflow as a method
        Example: sync_leads_to_crm()
        """
        pass
```

## Final Steps

1. Update main README.md to include your service
2. Add to `toolkit.py` service registry
3. Document any special setup requirements
4. Consider creating a specific workflow script

## Tips

- Start with the methods you use most
- Add methods as you need them
- Keep documentation focused on YOUR use cases
- Record successful patterns for future reference
- Don't try to implement everything at once

---

Remember: The goal is ~1000 tokens of focused, useful documentation - not comprehensive coverage of every API feature.