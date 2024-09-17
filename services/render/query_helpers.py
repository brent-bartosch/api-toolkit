"""
Query Helpers for Render API
Simplifies common Render operations
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

class ServiceFilter:
    """Build filters for listing services"""
    
    def __init__(self):
        self.filters = {}
        self.service_types = ['web_service', 'static_site', 'cron_job', 'private_service', 'background_worker']
    
    def by_type(self, service_type: str) -> 'ServiceFilter':
        """Filter by service type"""
        if service_type in self.service_types:
            self.filters['type'] = service_type
        return self
    
    def active_only(self) -> 'ServiceFilter':
        """Only show active (not suspended) services"""
        self.filters['suspended'] = False
        return self
    
    def with_failures(self) -> 'ServiceFilter':
        """Services with recent deploy failures"""
        self.filters['hasFailures'] = True
        return self
    
    def build(self) -> Dict:
        """Build the filter parameters"""
        return self.filters


class DeploymentManager:
    """Manage deployments for services"""
    
    def __init__(self, api):
        self.api = api
    
    def deploy_all(self, service_ids: List[str], clear_cache: bool = False) -> Dict[str, Any]:
        """
        Deploy multiple services at once.
        
        Args:
            service_ids: List of service IDs to deploy
            clear_cache: Whether to clear build cache
        
        Returns:
            Dict with deployment results
        """
        results = {'success': [], 'failed': []}
        
        for service_id in service_ids:
            try:
                deploy = self.api.deploy_service(service_id, clear_cache)
                results['success'].append({
                    'service_id': service_id,
                    'deploy_id': deploy.get('id')
                })
            except Exception as e:
                results['failed'].append({
                    'service_id': service_id,
                    'error': str(e)
                })
        
        return results
    
    def get_recent_failures(self, service_id: str, days: int = 7) -> List[Dict]:
        """Get failed deployments from the last N days"""
        deploys = self.api.list_deploys(service_id, limit=50)
        
        cutoff_date = datetime.now() - timedelta(days=days)
        failures = []
        
        for deploy in deploys:
            if deploy.get('status') == 'failed':
                created_at = datetime.fromisoformat(deploy.get('createdAt', '').replace('Z', '+00:00'))
                if created_at > cutoff_date:
                    failures.append({
                        'id': deploy.get('id'),
                        'created_at': deploy.get('createdAt'),
                        'commit': deploy.get('commit', {}).get('message'),
                        'error': deploy.get('error')
                    })
        
        return failures
    
    def rollback(self, service_id: str, deploy_id: str) -> Dict:
        """Rollback to a specific deployment"""
        # Render doesn't have direct rollback, but we can redeploy a commit
        deploy = self.api.get_deploy(service_id, deploy_id)
        commit_id = deploy.get('commit', {}).get('id')
        
        if commit_id:
            # Deploy the specific commit
            return self.api.deploy_service(service_id, clear_cache=False)
        else:
            raise ValueError(f"Could not find commit for deploy {deploy_id}")


class EnvVarManager:
    """Manage environment variables across services"""
    
    def __init__(self, api):
        self.api = api
    
    def bulk_update(self, service_id: str, env_dict: Dict[str, str]) -> List[Dict]:
        """
        Update multiple environment variables at once.
        
        Args:
            service_id: Service to update
            env_dict: Dict of key-value pairs
        
        Returns:
            Updated environment variables
        """
        env_vars = [{'key': k, 'value': v} for k, v in env_dict.items()]
        return self.api.update_env_vars(service_id, env_vars)
    
    def copy_env_vars(self, from_service: str, to_service: str, 
                      exclude: List[str] = None) -> List[Dict]:
        """
        Copy environment variables from one service to another.
        
        Args:
            from_service: Source service ID
            to_service: Target service ID
            exclude: List of keys to exclude
        
        Returns:
            Updated environment variables
        """
        exclude = exclude or []
        
        # Get source env vars
        source_vars = self.api.get_env_vars(from_service)
        
        # Filter out excluded keys
        env_vars = [
            {'key': var['key'], 'value': var['value']}
            for var in source_vars
            if var['key'] not in exclude
        ]
        
        # Update target service
        return self.api.update_env_vars(to_service, env_vars)
    
    def find_services_with_var(self, key: str) -> List[Dict]:
        """Find all services that have a specific environment variable"""
        services = self.api.list_services()
        results = []
        
        for service in services:
            try:
                env_vars = self.api.get_env_vars(service['id'])
                for var in env_vars:
                    if var['key'] == key:
                        results.append({
                            'service_id': service['id'],
                            'service_name': service['name'],
                            'value': var['value']
                        })
                        break
            except:
                continue
        
        return results


class ServiceAnalyzer:
    """Analyze service health and performance"""
    
    def __init__(self, api):
        self.api = api
    
    def health_check(self, service_id: str) -> Dict[str, Any]:
        """
        Check the health of a service.
        
        Returns:
            Health status including recent deploys, failures, status
        """
        service = self.api.get_service(service_id)
        deploys = self.api.list_deploys(service_id, limit=10)
        
        # Count recent statuses
        status_counts = {}
        for deploy in deploys:
            status = deploy.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Calculate success rate
        total = len(deploys)
        successful = status_counts.get('live', 0)
        success_rate = (successful / total * 100) if total > 0 else 0
        
        return {
            'service_name': service.get('name'),
            'service_id': service_id,
            'suspended': service.get('suspended', False),
            'url': service.get('serviceDetails', {}).get('url'),
            'recent_deploys': total,
            'success_rate': f"{success_rate:.1f}%",
            'deploy_statuses': status_counts,
            'last_deploy': deploys[0] if deploys else None
        }
    
    def find_inactive_services(self, days: int = 30) -> List[Dict]:
        """Find services that haven't been deployed in N days"""
        services = self.api.list_services()
        cutoff_date = datetime.now() - timedelta(days=days)
        inactive = []
        
        for service in services:
            try:
                deploys = self.api.list_deploys(service['id'], limit=1)
                if deploys:
                    last_deploy = deploys[0]
                    deploy_date = datetime.fromisoformat(
                        last_deploy.get('createdAt', '').replace('Z', '+00:00')
                    )
                    
                    if deploy_date < cutoff_date:
                        inactive.append({
                            'service_id': service['id'],
                            'service_name': service['name'],
                            'last_deploy': last_deploy.get('createdAt'),
                            'days_inactive': (datetime.now() - deploy_date).days
                        })
                else:
                    # No deploys at all
                    inactive.append({
                        'service_id': service['id'],
                        'service_name': service['name'],
                        'last_deploy': None,
                        'days_inactive': 'Never deployed'
                    })
            except:
                continue
        
        return sorted(inactive, key=lambda x: x.get('days_inactive', 0), reverse=True)


class CostEstimator:
    """Estimate costs for Render services"""
    
    # Rough pricing (may be outdated)
    PRICING = {
        'web_service': {
            'free': 0,
            'starter': 7,
            'standard': 25,
            'pro': 85,
            'pro_plus': 175,
            'pro_max': 450,
            'pro_ultra': 850
        },
        'static_site': {
            'free': 0
        },
        'postgres': {
            'free': 0,
            'starter': 7,
            'standard': 20,
            'pro': 95
        },
        'redis': {
            'free': 0,
            'starter': 10,
            'standard': 30,
            'pro': 130
        }
    }
    
    def __init__(self, api):
        self.api = api
    
    def estimate_monthly_cost(self) -> Dict[str, float]:
        """Estimate total monthly cost for all services"""
        total = 0
        breakdown = {}
        
        # Get services
        services = self.api.list_services()
        for service in services:
            if not service.get('suspended'):
                service_type = service.get('type', 'web_service')
                plan = service.get('plan', {}).get('name', 'free')
                
                cost = self.PRICING.get(service_type, {}).get(plan, 0)
                total += cost
                
                key = f"{service_type}_{plan}"
                breakdown[key] = breakdown.get(key, 0) + cost
        
        # Get databases
        discovery = self.api.discover('databases')
        
        for db in discovery.get('postgres', []):
            plan = db.get('plan', 'free')
            cost = self.PRICING.get('postgres', {}).get(plan, 0)
            total += cost
            breakdown[f"postgres_{plan}"] = breakdown.get(f"postgres_{plan}", 0) + cost
        
        for db in discovery.get('redis', []):
            plan = db.get('plan', 'free')
            cost = self.PRICING.get('redis', {}).get(plan, 0)
            total += cost
            breakdown[f"redis_{plan}"] = breakdown.get(f"redis_{plan}", 0) + cost
        
        return {
            'total_monthly': total,
            'breakdown': breakdown
        }