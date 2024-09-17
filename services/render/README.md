# Render Service Documentation

## 🚀 Quick Start

```python
from api_toolkit.services.render.api import RenderAPI

api = RenderAPI()
api.quick_start()  # Shows all services and databases in 5 seconds!
```

## ✨ Key Features

- **Zero-friction discovery** - `discover()` method always works
- **Service management** - Deploy, suspend, resume services
- **Environment variables** - Bulk update, copy between services
- **Health analysis** - Success rates, inactive service detection
- **Cost estimation** - Estimate monthly costs

## 🔍 Discovery Pattern

Always start with discovery to see what's deployed:

```python
# Discover everything
info = api.discover()
print(info['services_summary'])  # Service types and counts
print(info['databases_summary']) # Database types and counts

# Discover specific resources
services = api.discover('services')
databases = api.discover('databases')

# Discover specific service details
details = api.discover('srv-xxx')
print(details['env_vars'])       # Environment variables
print(details['recent_deploys']) # Recent deployments
```

## 📝 Common Operations

### List and Deploy Services

```python
# List all services
services = api.list_services()
for service in services:
    print(f"{service['name']} ({service['type']}) - {service['id']}")

# Deploy a service
deploy = api.deploy_service('srv-xxx')
print(f"Deploy triggered: {deploy['id']}")

# Get deployment status
deploy_status = api.get_deploy('srv-xxx', deploy['id'])
print(f"Status: {deploy_status['status']}")
```

### Manage Environment Variables

```python
from api_toolkit.services.render.query_helpers import EnvVarManager

env_manager = EnvVarManager(api)

# Bulk update environment variables
env_manager.bulk_update('srv-xxx', {
    'NODE_ENV': 'production',
    'DEBUG': 'false',
    'API_KEY': 'secret-key'
})

# Copy env vars between services
env_manager.copy_env_vars(
    from_service='srv-source',
    to_service='srv-target',
    exclude=['DATABASE_URL']  # Don't copy database URLs
)

# Find all services with a specific env var
services_with_db = env_manager.find_services_with_var('DATABASE_URL')
```

### Analyze Service Health

```python
from api_toolkit.services.render.query_helpers import ServiceAnalyzer

analyzer = ServiceAnalyzer(api)

# Check service health
health = analyzer.health_check('srv-xxx')
print(f"Success rate: {health['success_rate']}")
print(f"Deploy statuses: {health['deploy_statuses']}")

# Find inactive services
inactive = analyzer.find_inactive_services(days=30)
for service in inactive:
    print(f"{service['service_name']}: {service['days_inactive']} days")
```

### Deployment Management

```python
from api_toolkit.services.render.query_helpers import DeploymentManager

manager = DeploymentManager(api)

# Deploy multiple services at once
results = manager.deploy_all(['srv-1', 'srv-2', 'srv-3'])
print(f"Successful: {len(results['success'])}")
print(f"Failed: {len(results['failed'])}")

# Get recent deployment failures
failures = manager.get_recent_failures('srv-xxx', days=7)
for failure in failures:
    print(f"{failure['created_at']}: {failure['error']}")
```

### Cost Estimation

```python
from api_toolkit.services.render.query_helpers import CostEstimator

estimator = CostEstimator(api)

# Estimate monthly costs
costs = estimator.estimate_monthly_cost()
print(f"Total monthly: ${costs['total_monthly']}")
print(f"Breakdown: {costs['breakdown']}")
```

## 🛠️ Query Helpers

The `query_helpers.py` module provides these utility classes:

- **ServiceFilter** - Filter services by type, status, failures
- **DeploymentManager** - Deploy multiple services, find failures, rollback
- **EnvVarManager** - Bulk update, copy, find services with specific vars
- **ServiceAnalyzer** - Health checks, find inactive services
- **CostEstimator** - Estimate monthly costs

## 📋 Available Methods

### Core API Methods

| Method | Description | Returns |
|--------|-------------|---------|
| `discover(resource)` | Discover platform resources | Dict with resource info |
| `quick_start()` | Show everything in 5 seconds | None (prints info) |
| `list_services()` | List all services | List[Dict] |
| `get_service(id)` | Get service details | Dict |
| `deploy_service(id)` | Trigger deployment | Dict |
| `suspend_service(id)` | Suspend a service | Dict |
| `resume_service(id)` | Resume a service | Dict |
| `list_deploys(id)` | List deployments | List[Dict] |
| `get_env_vars(id)` | Get env variables | List[Dict] |
| `update_env_vars(id, vars)` | Update env variables | List[Dict] |
| `get_logs(id)` | Get service logs | List[str] |

## 🔧 Examples

Run the examples to see all features:

```bash
# Basic usage
python services/render/examples.py basic

# Discovery examples
python services/render/examples.py discover

# Deployment examples
python services/render/examples.py deploy

# Environment variables
python services/render/examples.py env

# Health analysis
python services/render/examples.py health

# Cost estimation
python services/render/examples.py cost

# Advanced patterns
python services/render/examples.py advanced
```

## ⚙️ Configuration

Set your Render API key in `.env`:

```bash
RENDER_API_KEY=rnd_your_api_key_here
```

Get your API key from: https://dashboard.render.com/u/settings

## 🚨 Error Handling

The API provides enhanced error messages:

```python
try:
    api.deploy_service('invalid-id')
except Exception as e:
    print(f"Error: {e}")
    # Will show helpful context about what went wrong
```

## 📊 Response Format

All methods return data directly as lists or dicts:

```python
services = api.list_services()  # Returns List[Dict]
for service in services:         # NOT services['data']
    print(service['name'])

service = api.get_service('srv-xxx')  # Returns Dict
print(service['name'])                # NOT service['data']['name']
```

## 🎯 Best Practices

1. **Always start with discovery**: `api.discover()` or `api.quick_start()`
2. **Check service health before deploying**: Use `ServiceAnalyzer`
3. **Bulk operations for efficiency**: Use `DeploymentManager.deploy_all()`
4. **Copy env vars carefully**: Exclude sensitive service-specific values
5. **Monitor costs**: Regular cost estimation helps avoid surprises
6. **Handle suspensions**: Check `suspended` status before operations

## 🔗 Resources

- [Render API Documentation](https://render.com/docs/api)
- [Render Dashboard](https://dashboard.render.com)
- [API Key Settings](https://dashboard.render.com/u/settings)

---

**Token Cost**: ~600 tokens when loaded (vs 90,000 for MCP servers!)