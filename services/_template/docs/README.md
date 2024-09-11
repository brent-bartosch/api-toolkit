# [SERVICE_NAME] API

## Quick Reference (~500 tokens)

### Capabilities
- [Main capability 1]
- [Main capability 2]
- [Main capability 3]

### Common Patterns
```python
# Initialize client
from services.[service].api import [ServiceName]API
api = [ServiceName]API()

# Example 1: [Common use case]
result = api.[method]([params])

# Example 2: [Another common use case]
data = api.[method]([params])
```

### Authentication
- **Method**: [Bearer token / API key / OAuth]
- **Environment Variable**: `[SERVICE]_API_KEY`
- **Header Format**: `Authorization: Bearer {api_key}`

### Rate Limits
- **Requests per second**: [X]
- **Daily limit**: [Y]
- **Burst limit**: [Z]

### When to Use
✅ Use for:
- [Scenario 1]
- [Scenario 2]
- [Scenario 3]

❌ Don't use for:
- [Anti-pattern 1]
- [Anti-pattern 2]

### Your Specific Configuration
- [Any project-specific IDs, lists, etc.]
- [Your common workflows]

### Error Codes
- `400`: Bad request - check parameters
- `401`: Unauthorized - check API key
- `429`: Rate limited - slow down requests
- `500`: Server error - retry with backoff

### Most Used Methods
1. `list_[resources]()` - Get all [resources]
2. `get_[resource](id)` - Get specific [resource]
3. `create_[resource](data)` - Create new [resource]
4. `update_[resource](id, data)` - Update [resource]
5. `delete_[resource](id)` - Delete [resource]

### Links
- Full API Docs: [URL]
- Dashboard: [URL]
- Status Page: [URL]