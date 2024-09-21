# 📚 Documentation Integration Framework

## Overview

The API Toolkit now features a comprehensive documentation integration framework that makes it "as robust as possible" with automatic OpenAPI/Swagger support, live documentation fetching, schema validation, and intelligent auto-discovery capabilities.

## 🎯 Key Features

### 1. **OpenAPI/Swagger Integration**
- Automatic loading and parsing of OpenAPI 3.0 and Swagger 2.0 specifications
- Endpoint extraction with full parameter and response documentation
- Schema extraction for request/response validation
- Automatic caching with 24-hour expiration

### 2. **Schema Validation**
- JSON Schema-based validation for all API requests and responses
- Automatic validation in BaseAPI when enabled
- Schema generation from actual API responses
- Validation error reporting with detailed messages

### 3. **Live Documentation Fetching**
- Real-time documentation fetching from API websites
- Automatic extraction of methods and code examples
- Documentation synchronization with multiple sources
- Intelligent caching to minimize API calls

### 4. **Auto-Discovery**
- Automatic endpoint discovery by probing common patterns
- Learning from actual API usage patterns
- Pattern recording for documentation generation
- Automatic OpenAPI spec discovery

### 5. **Context7 Integration**
- Real-time documentation fetching for any library
- Contextual documentation based on your code
- Automatic caching of Context7 responses
- Seamless integration with existing services

### 6. **Documentation Management**
- Token-aware documentation compression
- Multiple detail levels (quick/standard/full)
- Automatic documentation updates
- Centralized documentation storage

## 🚀 Quick Start

### Basic Usage

```python
from core.documentation import DocumentationManager

# Initialize for a service
doc_manager = DocumentationManager('metabase')

# Load OpenAPI spec
spec = doc_manager.load_openapi_spec('https://api.example.com/openapi.json')

# Extract endpoints
endpoints = doc_manager.extract_endpoints()

# Validate responses
doc_manager.validate_response('/users', 'GET', response_data)

# Learn from usage
doc_manager.learn_from_usage('/users', 'GET', params, response)
```

### With BaseAPI Integration

```python
from services.myservice.api import MyServiceAPI

# Enable validation
api = MyServiceAPI(validate_responses=True)

# All requests/responses are now validated automatically
users = api.query('users')  # Validated against schema
```

### Auto-Discovery

```python
# Discover API endpoints
discovered = doc_manager.discover_endpoints(
    'https://api.example.com',
    api_key='your-key'
)

# Automatic spec discovery
for endpoint in discovered:
    if 'openapi' in endpoint['endpoint']:
        spec = doc_manager.load_openapi_spec(endpoint['url'])
```

## 📁 File Structure

```
api-toolkit/
├── core/
│   ├── documentation.py        # Main DocumentationManager class
│   └── base_api.py            # Updated with validation support
├── tools/
│   └── update_specs.py        # Automatic spec updater script
├── tests/
│   └── test_documentation.py  # Comprehensive test suite
└── services/
    └── [service]/
        └── docs/              # Service-specific docs
            ├── openapi.json   # Cached OpenAPI spec
            ├── schemas/       # JSON schemas
            ├── synced_docs.json
            └── patterns.json  # Learned patterns
```

## 🔧 Configuration

### Enable Validation in Services

```python
class MyServiceAPI(BaseAPI):
    def __init__(self, api_key=None):
        super().__init__(
            api_key=api_key,
            base_url="https://api.example.com",
            validate_responses=True,  # Enable validation
            service_name="myservice"
        )
```

### Update All Specifications

```bash
# Update all service specs
python tools/update_specs.py

# Update specific services
python tools/update_specs.py metabase smartlead

# Force update even if recent
python tools/update_specs.py --force

# Validate after update
python tools/update_specs.py --validate
```

## 📊 Schema Validation

### Automatic Schema Generation

```python
# Generate schema from response
response = api.query('users')
schema = doc_manager.generate_schema_from_response(response)

# Save schema for future validation
schemas_dir = Path('services/myservice/docs/schemas')
with open(schemas_dir / 'users.json', 'w') as f:
    json.dump(schema, f, indent=2)
```

### Manual Validation

```python
# Validate request
try:
    doc_manager.validate_request('/users', 'POST', request_data)
except ValidationError as e:
    print(f"Invalid request: {e}")

# Validate response
try:
    doc_manager.validate_response('/users', 'GET', response_data)
except ValidationError as e:
    print(f"Invalid response: {e}")
```

## 🔄 Live Documentation Sync

### Fetch from URLs

```python
# Fetch documentation from website
content = doc_manager.fetch_live_docs('https://docs.api.com')

# Sync with multiple sources
urls = [
    'https://docs.api.com/getting-started',
    'https://docs.api.com/reference',
    'https://docs.api.com/examples'
]
synced = doc_manager.sync_with_live_docs(urls)
```

### Context7 Real-Time Docs

```python
# Get contextual documentation
docs = doc_manager.fetch_context7_docs(
    "How to implement pagination in Next.js",
    libraries=['nextjs', 'react']
)
```

## 📈 Pattern Learning

The framework automatically learns from your API usage:

```python
# Patterns are recorded automatically
api.query('users', filters={'status': 'active'})

# Later, retrieve learned patterns
patterns = doc_manager.get_patterns()
for pattern in patterns:
    print(f"Endpoint: {pattern['endpoint']}")
    print(f"Method: {pattern['method']}")
    print(f"Params: {pattern['params']}")
```

## 🧪 Testing

Run comprehensive documentation tests:

```bash
# Run all documentation tests
python tests/test_documentation.py

# Test results include:
# - OpenAPI spec loading
# - Endpoint extraction
# - Schema validation
# - Request/response validation
# - Live docs fetching
# - Auto-discovery
# - Pattern learning
# - Context7 integration
# - Documentation compression
```

## 📉 Token Optimization

### Documentation Compression

```python
# Get documentation at different detail levels
quick = doc_manager.get_context('quick')      # ~500 tokens
standard = doc_manager.get_context('standard') # ~1000 tokens
full = doc_manager.get_context('full')        # ~2000 tokens

# Compress existing documentation
compressed = doc_manager.compress_documentation(
    long_docs,
    target_tokens=1000
)
```

### Token Estimation

```python
# Estimate token usage
text = "Your documentation text here"
tokens = doc_manager.estimate_tokens(text)
print(f"Estimated tokens: {tokens}")
```

## 🔮 Future Enhancements

### Planned Features
1. **GraphQL Support** - Add GraphQL schema validation
2. **Mock Server** - Generate mock server from OpenAPI spec
3. **Documentation Generation** - Auto-generate markdown docs
4. **API Versioning** - Track API version changes
5. **Breaking Change Detection** - Alert on API changes
6. **Performance Profiling** - Track response times
7. **SDK Generation** - Generate Python SDK from spec

### Contributing

To add documentation support for a new service:

1. Create OpenAPI spec loader in service directory
2. Add service to `SPEC_SOURCES` in `tools/update_specs.py`
3. Configure validation in service API class
4. Run tests to ensure everything works

## 📚 Benefits

### For Development
- **Type Safety**: Automatic validation catches errors early
- **Auto-Complete**: IDEs can use schemas for better suggestions
- **Documentation**: Always up-to-date with actual API

### For Maintenance
- **Breaking Changes**: Detect API changes immediately
- **Pattern Analysis**: Understand actual API usage
- **Test Coverage**: Validate all API interactions

### For Performance
- **Token Efficiency**: Compress docs to minimum size
- **Caching**: Reduce API calls with intelligent caching
- **Lazy Loading**: Load only needed documentation

## 🎯 Best Practices

1. **Always Enable Validation** in production services
2. **Update Specs Weekly** using the update script
3. **Record Patterns** for common operations
4. **Cache Aggressively** to minimize API calls
5. **Compress Documentation** for LLM contexts
6. **Test Thoroughly** using the test suite

---

The Documentation Integration Framework transforms the API Toolkit into a self-documenting, self-validating, and self-discovering system that ensures reliability, consistency, and efficiency across all API integrations.