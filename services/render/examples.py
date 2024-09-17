#!/usr/bin/env python3
"""
Render API Examples
Practical examples for managing Render deployments
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.render.api import RenderAPI
from services.render.query_helpers import (
    ServiceFilter,
    DeploymentManager,
    EnvVarManager,
    ServiceAnalyzer,
    CostEstimator
)

def basic_usage():
    """Basic Render API usage"""
    print("\n=== Basic Render Usage ===\n")
    
    api = RenderAPI()
    
    # Quick start shows everything
    api.quick_start()
    
    # List all services
    services = api.list_services()
    print(f"\n📱 Found {len(services)} services:")
    for service in services[:5]:  # Show first 5
        print(f"  - {service.get('name')} ({service.get('type')})")
        print(f"    ID: {service.get('id')}")
        print(f"    Status: {'Suspended' if service.get('suspended') else 'Active'}")


def discovery_examples():
    """Discovery pattern examples"""
    print("\n=== Discovery Examples ===\n")
    
    api = RenderAPI()
    
    # Discover all resources
    print("📊 Platform Overview:")
    overview = api.discover()
    print(f"  Services: {overview.get('services_summary', {})}")
    print(f"  Databases: {overview.get('databases_summary', {})}")
    
    # Discover services in detail
    print("\n🌐 Services Discovery:")
    services = api.discover('services')
    if services['success']:
        for svc_type, svcs in services.get('service_types', {}).items():
            print(f"  {svc_type}: {len(svcs)}")
            for svc in svcs[:2]:  # Show first 2 of each type
                print(f"    - {svc['name']} ({svc['status']})")
    
    # Discover databases
    print("\n🗄️ Databases Discovery:")
    dbs = api.discover('databases')
    if dbs['success']:
        print(f"  PostgreSQL: {len(dbs.get('postgres', []))}")
        print(f"  Redis: {len(dbs.get('redis', []))}")


def deployment_examples():
    """Deployment management examples"""
    print("\n=== Deployment Examples ===\n")
    
    api = RenderAPI()
    manager = DeploymentManager(api)
    
    # Get services
    services = api.list_services()
    if not services:
        print("No services found")
        return
    
    service = services[0]
    service_id = service['id']
    
    print(f"📦 Deployment examples for: {service['name']}")
    
    # List recent deploys
    deploys = api.list_deploys(service_id, limit=5)
    print(f"\n🚀 Recent deploys ({len(deploys)}):")
    for deploy in deploys:
        status = deploy.get('status', 'unknown')
        emoji = '✅' if status == 'live' else '❌' if status == 'failed' else '⏳'
        print(f"  {emoji} {deploy.get('id')[:8]}... - {status}")
        print(f"     Commit: {deploy.get('commit', {}).get('message', 'No message')[:50]}")
    
    # Check for failures
    print(f"\n❌ Recent failures:")
    failures = manager.get_recent_failures(service_id, days=30)
    if failures:
        for fail in failures[:3]:
            print(f"  - {fail['created_at']}: {fail.get('error', 'Unknown error')[:60]}")
    else:
        print("  No failures in last 30 days! 🎉")
    
    # Example: Deploy a service (commented out to prevent accidental deploys)
    # print(f"\n🚀 Deploying {service['name']}...")
    # result = api.deploy_service(service_id)
    # print(f"  Deploy triggered: {result.get('id')}")


def environment_examples():
    """Environment variable management"""
    print("\n=== Environment Variable Examples ===\n")
    
    api = RenderAPI()
    env_manager = EnvVarManager(api)
    
    # Get a service
    services = api.list_services()
    if not services:
        print("No services found")
        return
    
    service = services[0]
    service_id = service['id']
    
    print(f"🔐 Environment variables for: {service['name']}")
    
    # Get current env vars
    env_vars = api.get_env_vars(service_id)
    print(f"\n📋 Current variables ({len(env_vars)}):")
    for var in env_vars[:5]:  # Show first 5
        value_preview = var['value'][:20] + '...' if len(var['value']) > 20 else var['value']
        # Mask sensitive values
        if any(sensitive in var['key'].lower() for sensitive in ['key', 'secret', 'token', 'password']):
            value_preview = '***MASKED***'
        print(f"  {var['key']} = {value_preview}")
    
    # Find services with specific env var
    print("\n🔍 Services with DATABASE_URL:")
    services_with_db = env_manager.find_services_with_var('DATABASE_URL')
    for svc in services_with_db:
        print(f"  - {svc['service_name']} ({svc['service_id']})")
    
    # Example: Update env vars (commented out to prevent changes)
    # print("\n📝 Updating environment variables...")
    # new_vars = {
    #     'APP_ENV': 'production',
    #     'DEBUG': 'false'
    # }
    # result = env_manager.bulk_update(service_id, new_vars)
    # print(f"  Updated {len(result)} variables")


def health_analysis():
    """Service health and analysis"""
    print("\n=== Service Health Analysis ===\n")
    
    api = RenderAPI()
    analyzer = ServiceAnalyzer(api)
    
    # Get services
    services = api.list_services()
    if not services:
        print("No services found")
        return
    
    # Analyze first service
    service = services[0]
    service_id = service['id']
    
    print(f"🏥 Health check for: {service['name']}")
    health = analyzer.health_check(service_id)
    
    print(f"  Status: {'❌ Suspended' if health['suspended'] else '✅ Active'}")
    print(f"  Success rate: {health['success_rate']}")
    print(f"  Recent deploys: {health['recent_deploys']}")
    print(f"  Deploy statuses: {health['deploy_statuses']}")
    
    if health['url']:
        print(f"  URL: {health['url']}")
    
    # Find inactive services
    print("\n😴 Inactive services (30+ days):")
    inactive = analyzer.find_inactive_services(days=30)
    
    if inactive:
        for svc in inactive[:5]:
            if isinstance(svc['days_inactive'], int):
                print(f"  - {svc['service_name']}: {svc['days_inactive']} days")
            else:
                print(f"  - {svc['service_name']}: {svc['days_inactive']}")
    else:
        print("  All services are active! 🎉")


def cost_estimation():
    """Estimate Render costs"""
    print("\n=== Cost Estimation ===\n")
    
    api = RenderAPI()
    estimator = CostEstimator(api)
    
    print("💰 Monthly cost estimate:")
    estimate = estimator.estimate_monthly_cost()
    
    print(f"  Total: ${estimate['total_monthly']:.2f}/month")
    
    if estimate['breakdown']:
        print("\n  Breakdown:")
        for item, cost in estimate['breakdown'].items():
            if cost > 0:
                print(f"    {item}: ${cost:.2f}")
    
    print("\n  Note: Estimates based on standard pricing.")
    print("  Actual costs may vary with usage and custom plans.")


def advanced_patterns():
    """Advanced usage patterns"""
    print("\n=== Advanced Patterns ===\n")
    
    api = RenderAPI()
    
    # Filter services
    print("🔍 Filtering services:")
    filter = ServiceFilter()
    web_services = [s for s in api.list_services() 
                   if s.get('type') == 'web_service' and not s.get('suspended')]
    
    print(f"  Active web services: {len(web_services)}")
    
    # Batch operations
    print("\n🔄 Batch operations:")
    manager = DeploymentManager(api)
    
    # Example: Deploy multiple services (commented out)
    # service_ids = [s['id'] for s in web_services[:3]]
    # results = manager.deploy_all(service_ids)
    # print(f"  Deployed: {len(results['success'])}")
    # print(f"  Failed: {len(results['failed'])}")
    
    # Service discovery by ID
    if web_services:
        service_id = web_services[0]['id']
        print(f"\n📋 Detailed discovery for {service_id}:")
        details = api.discover(service_id)
        
        if details['success']:
            print(f"  Service: {details.get('service', {}).get('name')}")
            print(f"  Env vars: {len(details.get('env_vars', []))}")
            print(f"  Recent deploys: {len(details.get('recent_deploys', []))}")


def main():
    """Run all examples"""
    import sys
    
    if len(sys.argv) > 1:
        example = sys.argv[1]
        
        examples = {
            'basic': basic_usage,
            'discover': discovery_examples,
            'deploy': deployment_examples,
            'env': environment_examples,
            'health': health_analysis,
            'cost': cost_estimation,
            'advanced': advanced_patterns
        }
        
        if example in examples:
            examples[example]()
        else:
            print(f"Unknown example: {example}")
            print(f"Available: {', '.join(examples.keys())}")
    else:
        # Run basic example by default
        print("Render API Examples")
        print("=" * 50)
        print("\nUsage: python examples.py [example]")
        print("Examples: basic, discover, deploy, env, health, cost, advanced")
        print("\nRunning basic example...\n")
        
        basic_usage()
        
        print("\n" + "=" * 50)
        print("Run other examples:")
        print("  python examples.py discover")
        print("  python examples.py health")
        print("  python examples.py cost")


if __name__ == "__main__":
    main()