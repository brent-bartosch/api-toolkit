#!/usr/bin/env python3
"""
Render API Client
Token Cost: ~600 tokens when loaded

Cloud platform for deploying web services, static sites, cron jobs, and databases.
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Load environment variables
env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

from core.base_api import BaseAPI

class RenderAPI(BaseAPI):
    """
    Render.com API wrapper for cloud deployments.
    
    CAPABILITIES:
    - List and manage services (web services, static sites, cron jobs)
    - Deploy and monitor applications
    - Manage databases (PostgreSQL, Redis)
    - View logs and metrics
    - Manage environment variables
    
    COMMON PATTERNS:
    ```python
    api = RenderAPI()
    api.quick_start()  # See all services and databases
    
    # List services
    services = api.list_services()
    
    # Get service details
    service = api.get_service('srv-xxx')
    
    # Deploy a service
    api.deploy_service('srv-xxx')
    ```
    
    AUTHENTICATION:
    - API key from dashboard.render.com/u/settings
    
    RATE LIMITS:
    - 100 requests per minute
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Render client.
        
        Args:
            api_key: Optional Render API key (defaults to RENDER_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('RENDER_API_KEY')
        
        super().__init__(
            api_key=self.api_key,
            base_url='https://api.render.com/v1',
            requests_per_second=1.5  # Conservative rate limit
        )
    
    def _setup_auth(self):
        """Setup Render authentication headers"""
        if self.api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_key}',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            })
    
    # ============= DISCOVERY METHODS =============
    
    def discover(self, resource: Optional[str] = None) -> Dict[str, Any]:
        """
        🔍 DISCOVER RENDER RESOURCES - Always works!
        
        This method ALWAYS returns useful information.
        Use this FIRST to see what's deployed!
        
        Args:
            resource: Optional specific resource type ('services', 'databases', 'envs')
                     Or specific service ID to get details
        
        Returns:
            Dict with discovery results including services, databases, deployments
        
        Examples:
            # Discover everything
            info = api.discover()
            print(info['services'])  # List of all services
            
            # Discover specific resource type
            info = api.discover('databases')
            print(info['postgres'])  # PostgreSQL instances
            
            # Discover specific service
            info = api.discover('srv-xxx')
            print(info['env_vars'])  # Environment variables
        """
        result = {'success': False, 'platform': 'render'}
        
        if resource:
            if resource == 'services':
                # Discover services
                try:
                    services = self.list_services(limit=100)
                    result['services'] = services
                    result['service_count'] = len(services)
                    result['service_types'] = {}
                    
                    for svc in services:
                        svc_type = svc.get('type', 'unknown')
                        if svc_type not in result['service_types']:
                            result['service_types'][svc_type] = []
                        result['service_types'][svc_type].append({
                            'name': svc.get('name'),
                            'id': svc.get('id'),
                            'status': svc.get('suspended') and 'suspended' or 'active'
                        })
                    
                    result['success'] = True
                    result['message'] = f"Found {len(services)} services"
                except Exception as e:
                    result['error'] = str(e)
                    result['message'] = "Could not list services"
                    
            elif resource == 'databases':
                # Discover databases
                result['postgres'] = []
                result['redis'] = []
                
                try:
                    # Get PostgreSQL databases
                    pg_dbs = self._make_request('GET', 'postgres')
                    if isinstance(pg_dbs, list):
                        result['postgres'] = [{
                            'name': db.get('name'),
                            'id': db.get('id'),
                            'status': db.get('status'),
                            'plan': db.get('plan', {}).get('name'),
                            'region': db.get('region', {}).get('id')
                        } for db in pg_dbs]
                except:
                    pass
                
                try:
                    # Get Redis instances
                    redis_dbs = self._make_request('GET', 'redis')
                    if isinstance(redis_dbs, list):
                        result['redis'] = [{
                            'name': db.get('name'),
                            'id': db.get('id'),
                            'status': db.get('status'),
                            'plan': db.get('plan', {}).get('name')
                        } for db in redis_dbs]
                except:
                    pass
                
                result['database_count'] = len(result['postgres']) + len(result['redis'])
                result['success'] = result['database_count'] > 0
                result['message'] = f"Found {result['database_count']} databases"
                
            elif resource.startswith('srv-') or resource.startswith('rds-') or resource.startswith('red-'):
                # Discover specific service details
                try:
                    # Determine resource type
                    if resource.startswith('srv-'):
                        details = self.get_service(resource)
                        envs = self.get_env_vars(resource)
                        deploys = self.list_deploys(resource, limit=5)
                        
                        result['service'] = details
                        result['env_vars'] = envs
                        result['recent_deploys'] = deploys
                        result['success'] = True
                        result['message'] = f"Details for service {details.get('name', resource)}"
                        
                    elif resource.startswith('rds-'):
                        details = self._make_request('GET', f'postgres/{resource}')
                        result['database'] = details
                        result['type'] = 'postgres'
                        result['success'] = True
                        
                    elif resource.startswith('red-'):
                        details = self._make_request('GET', f'redis/{resource}')
                        result['database'] = details
                        result['type'] = 'redis'
                        result['success'] = True
                        
                except Exception as e:
                    result['error'] = str(e)
                    result['message'] = f"Could not get details for {resource}"
            else:
                result['message'] = "Unknown resource type. Use 'services', 'databases', or a specific ID"
                
        else:
            # Discover everything
            summary = {'services': {}, 'databases': {}}
            
            # Get services summary
            try:
                services = self.list_services(limit=20)
                for svc in services:
                    svc_type = svc.get('type', 'unknown')
                    if svc_type not in summary['services']:
                        summary['services'][svc_type] = 0
                    summary['services'][svc_type] += 1
                
                result['services_summary'] = summary['services']
                result['recent_services'] = [{
                    'name': s.get('name'),
                    'id': s.get('id'),
                    'type': s.get('type'),
                    'url': s.get('serviceDetails', {}).get('url')
                } for s in services[:5]]
            except:
                pass
            
            # Get databases summary
            try:
                pg_count = len(self._make_request('GET', 'postgres') or [])
                redis_count = len(self._make_request('GET', 'redis') or [])
                
                if pg_count > 0:
                    summary['databases']['postgres'] = pg_count
                if redis_count > 0:
                    summary['databases']['redis'] = redis_count
                
                result['databases_summary'] = summary['databases']
            except:
                pass
            
            result['success'] = bool(summary['services'] or summary['databases'])
            result['message'] = "Render platform overview"
            result['hint'] = "Use discover('services') or discover('databases') for details"
        
        return result
    
    def quick_start(self) -> None:
        """
        🚀 QUICK START - Shows everything deployed on Render!
        
        This shows all your services, databases, and recent deployments.
        Use this FIRST when starting!
        """
        print(f"\n{'='*60}")
        print(f"🚀 RENDER QUICK START")
        print(f"{'='*60}\n")
        
        # Test connection
        if not self.test_connection():
            print("❌ Connection failed! Check your .env file")
            print("   Expected: RENDER_API_KEY")
            print("   Get it from: https://dashboard.render.com/u/settings")
            return
        
        print("✅ Connected to Render API!\n")
        
        # Discover all resources
        discovery = self.discover()
        
        # Show services
        if discovery.get('services_summary'):
            print("🌐 Services Overview:")
            for svc_type, count in discovery['services_summary'].items():
                print(f"   - {svc_type}: {count}")
            print()
            
            if discovery.get('recent_services'):
                print("📱 Recent Services:")
                for svc in discovery['recent_services']:
                    print(f"   - {svc['name']} ({svc['type']})")
                    print(f"     ID: {svc['id']}")
                    if svc.get('url'):
                        print(f"     URL: {svc['url']}")
                print()
        
        # Show databases
        if discovery.get('databases_summary'):
            print("🗄️ Databases:")
            for db_type, count in discovery['databases_summary'].items():
                print(f"   - {db_type}: {count}")
            print()
        
        # Show example commands
        print("💡 Example Commands:")
        print("   # List all services")
        print("   services = api.list_services()")
        print()
        print("   # Get service details")
        print("   service = api.get_service('srv-xxx')")
        print()
        print("   # Deploy a service")
        print("   api.deploy_service('srv-xxx')")
        print()
        print("   # Get logs")
        print("   logs = api.get_logs('srv-xxx')")
        print()
        
        print("📚 Next steps:")
        print("   1. api.discover('services')  # List all services")
        print("   2. api.discover('databases') # List all databases")
        print("   3. api.discover('srv-xxx')   # Get service details")
        print(f"\n{'='*60}\n")
    
    # ============= SERVICE OPERATIONS =============
    
    def list_services(self, limit: int = 100) -> List[Dict]:
        """
        List all services in your Render account.
        
        Returns:
            List of service objects
        """
        try:
            services = self._make_request('GET', 'services', params={'limit': limit})
            return services if isinstance(services, list) else []
        except Exception as e:
            print(f"Error listing services: {e}")
            return []
    
    def get_service(self, service_id: str) -> Dict:
        """Get details for a specific service"""
        return self._make_request('GET', f'services/{service_id}')
    
    def deploy_service(self, service_id: str, clear_cache: bool = False) -> Dict:
        """
        Trigger a new deploy for a service.
        
        Args:
            service_id: The service ID (e.g., 'srv-xxx')
            clear_cache: Clear build cache
        
        Returns:
            Deploy object
        """
        data = {'clearCache': clear_cache}
        return self._make_request('POST', f'services/{service_id}/deploys', data=data)
    
    def suspend_service(self, service_id: str) -> Dict:
        """Suspend a service"""
        return self._make_request('POST', f'services/{service_id}/suspend')
    
    def resume_service(self, service_id: str) -> Dict:
        """Resume a suspended service"""
        return self._make_request('POST', f'services/{service_id}/resume')
    
    # ============= DEPLOY OPERATIONS =============
    
    def list_deploys(self, service_id: str, limit: int = 20) -> List[Dict]:
        """List deploys for a service"""
        try:
            deploys = self._make_request('GET', f'services/{service_id}/deploys', 
                                       params={'limit': limit})
            return deploys if isinstance(deploys, list) else []
        except:
            return []
    
    def get_deploy(self, service_id: str, deploy_id: str) -> Dict:
        """Get details for a specific deploy"""
        return self._make_request('GET', f'services/{service_id}/deploys/{deploy_id}')
    
    # ============= ENVIRONMENT VARIABLES =============
    
    def get_env_vars(self, service_id: str) -> List[Dict]:
        """Get environment variables for a service"""
        try:
            env_vars = self._make_request('GET', f'services/{service_id}/env-vars')
            return env_vars if isinstance(env_vars, list) else []
        except:
            return []
    
    def update_env_vars(self, service_id: str, env_vars: List[Dict]) -> List[Dict]:
        """
        Update environment variables for a service.
        
        Args:
            service_id: The service ID
            env_vars: List of {'key': 'NAME', 'value': 'value'} dicts
        
        Returns:
            Updated environment variables
        """
        return self._make_request('PUT', f'services/{service_id}/env-vars', 
                                 data=env_vars)
    
    # ============= LOGS =============
    
    def get_logs(self, service_id: str, tail: int = 100) -> List[str]:
        """
        Get logs for a service.
        
        Args:
            service_id: The service ID
            tail: Number of lines to return
        
        Returns:
            List of log lines
        """
        try:
            # Note: Render's log endpoint might require different handling
            logs = self._make_request('GET', f'services/{service_id}/logs',
                                     params={'tail': tail})
            if isinstance(logs, list):
                return logs
            elif isinstance(logs, dict) and 'logs' in logs:
                return logs['logs']
            return []
        except Exception as e:
            print(f"Error getting logs: {e}")
            return []
    
    # ============= UTILITY METHODS =============
    
    def test_connection(self) -> bool:
        """Test if API connection is working"""
        try:
            # Try to list services with limit 1
            self._make_request('GET', 'services', params={'limit': 1})
            return True
        except:
            return False
    
    def get_service_url(self, service_id: str) -> Optional[str]:
        """Get the public URL for a service"""
        try:
            service = self.get_service(service_id)
            return service.get('serviceDetails', {}).get('url')
        except:
            return None


# ============= CLI INTERFACE =============

if __name__ == "__main__":
    import json
    
    if len(sys.argv) < 2:
        # Default to quick start
        api = RenderAPI()
        api.quick_start()
    else:
        command = sys.argv[1]
        api = RenderAPI()
        
        if command == "test":
            if api.test_connection():
                print("✅ Connection successful!")
            else:
                print("❌ Connection failed. Check RENDER_API_KEY")
        
        elif command == "services":
            services = api.list_services()
            print(f"Found {len(services)} services:")
            for svc in services:
                print(f"  - {svc.get('name')} ({svc.get('type')}) - {svc.get('id')}")
        
        elif command == "discover":
            if len(sys.argv) > 2:
                result = api.discover(sys.argv[2])
            else:
                result = api.discover()
            print(json.dumps(result, indent=2))
        
        elif command == "deploy" and len(sys.argv) > 2:
            service_id = sys.argv[2]
            result = api.deploy_service(service_id)
            print(f"Deploy triggered: {result.get('id')}")
        
        else:
            print("Commands:")
            print("  python api.py          # Quick start")
            print("  python api.py test     # Test connection")
            print("  python api.py services # List services")
            print("  python api.py discover [resource] # Discover resources")
            print("  python api.py deploy <service-id> # Deploy service")