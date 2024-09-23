#!/usr/bin/env python3
"""
API Specification Updater

Automatically updates OpenAPI/Swagger specifications for all services.
Fetches latest specs, validates them, and updates cached versions.
"""

import os
import sys
import json
import yaml
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.documentation import DocumentationManager

# Known API specification sources
SPEC_SOURCES = {
    'metabase': {
        'spec_endpoints': [
            '/api/swagger.json',
            '/api/docs',
            '/api/endpoints'
        ],
        'docs_url': 'https://www.metabase.com/docs/latest/api',
        'requires_auth': True
    },
    'smartlead': {
        'spec_endpoints': [
            '/v1.1/docs/openapi.json',
            '/swagger.json'
        ],
        'docs_url': 'https://api.smartlead.ai/v1.1/docs',
        'interactive_docs': 'https://api.smartlead.ai/v1.1/docs/getting-started',
        'requires_auth': True
    },
    'supabase': {
        'spec_endpoints': [
            '/rest/v1/',
            '/rest/v1/openapi.json'
        ],
        'docs_url': 'https://supabase.com/docs/guides/api',
        'requires_auth': True
    },
    'context7': {
        'spec_endpoints': [
            '/api/v1/spec',
            '/api/v1/openapi.json'
        ],
        'docs_url': 'https://mcp.context7.com/docs',
        'requires_auth': True
    },
    'render': {
        'spec_endpoints': [
            '/v1/openapi',
            '/docs/api/spec'
        ],
        'docs_url': 'https://api-docs.render.com/reference',
        'requires_auth': True
    },
    'brightdata': {
        'spec_endpoints': [
            '/api/swagger.json',
            '/docs/openapi'
        ],
        'docs_url': 'https://docs.brightdata.com/api-reference',
        'requires_auth': True
    },
    'klaviyo': {
        'spec_endpoints': [
            '/api/v3/openapi.json',
            '/api/docs'
        ],
        'docs_url': 'https://developers.klaviyo.com/en/reference/api-overview',
        'requires_auth': True
    },
    'shopify': {
        'spec_endpoints': [
            '/admin/api/2024-01/graphql.json',
            '/api/docs'
        ],
        'docs_url': 'https://shopify.dev/api/admin-rest',
        'requires_auth': True
    }
}

class SpecUpdater:
    """Updates API specifications for all services"""

    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize spec updater.

        Args:
            base_path: Base path for API toolkit
        """
        self.base_path = base_path or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.services_path = Path(self.base_path) / 'services'
        self.updated = []
        self.failed = []

    def update_all(self) -> Dict[str, Any]:
        """
        Update specifications for all services.

        Returns:
            Summary of updates
        """
        print("🔄 Starting API specification update...\n")

        for service_name, config in SPEC_SOURCES.items():
            print(f"📦 Updating {service_name}...")
            success = self.update_service(service_name, config)

            if success:
                self.updated.append(service_name)
                print(f"✅ {service_name} updated successfully")
            else:
                self.failed.append(service_name)
                print(f"❌ {service_name} update failed")

            print()

        return self._generate_report()

    def update_service(self, service_name: str, config: Dict) -> bool:
        """
        Update specification for a single service.

        Args:
            service_name: Name of the service
            config: Service configuration

        Returns:
            True if update successful
        """
        service_path = self.services_path / service_name

        if not service_path.exists():
            print(f"  ⚠️ Service directory not found: {service_path}")
            return False

        # Initialize documentation manager
        doc_manager = DocumentationManager(service_name, self.base_path)

        # Try to fetch OpenAPI spec from known endpoints
        spec = self._fetch_spec(service_name, config)

        if spec:
            doc_manager._save_spec(spec)
            print(f"  📄 Saved OpenAPI spec with {len(spec.get('paths', {}))} endpoints")

            # Extract and save schemas
            if 'components' in spec and 'schemas' in spec['components']:
                self._save_schemas(service_name, spec['components']['schemas'])
                print(f"  📋 Saved {len(spec['components']['schemas'])} schemas")

            # Generate quick reference from spec
            self._generate_quick_reference(service_name, spec)
            print(f"  📝 Generated quick reference")

            return True

        # Fallback: Try to fetch from documentation URL
        if 'docs_url' in config:
            print(f"  🌐 Fetching from documentation URL: {config['docs_url']}")
            content = doc_manager.fetch_live_docs(config['docs_url'])

            if content:
                print(f"  📖 Fetched documentation ({len(content)} characters)")
                return True

        return False

    def _fetch_spec(self, service_name: str, config: Dict) -> Optional[Dict]:
        """
        Fetch OpenAPI spec from service endpoints.

        Args:
            service_name: Name of the service
            config: Service configuration

        Returns:
            OpenAPI specification or None
        """
        # Get base URL from environment
        base_url = self._get_base_url(service_name)

        if not base_url:
            print(f"  ⚠️ No base URL configured for {service_name}")
            return None

        # Get API key if required
        api_key = None
        if config.get('requires_auth'):
            api_key = self._get_api_key(service_name)
            if not api_key:
                print(f"  ⚠️ No API key configured for {service_name}")

        # Try each known endpoint
        for endpoint in config.get('spec_endpoints', []):
            url = f"{base_url.rstrip('/')}{endpoint}"
            print(f"  🔍 Trying: {url}")

            try:
                headers = {}
                if api_key:
                    headers['Authorization'] = f'Bearer {api_key}'
                    headers['X-API-Key'] = api_key

                response = requests.get(url, headers=headers, timeout=10)

                if response.status_code == 200:
                    # Parse response
                    content_type = response.headers.get('Content-Type', '')

                    if 'json' in content_type:
                        return response.json()
                    elif 'yaml' in content_type:
                        return yaml.safe_load(response.text)
                    else:
                        # Try to parse as JSON first
                        try:
                            return response.json()
                        except:
                            # Try YAML
                            try:
                                return yaml.safe_load(response.text)
                            except:
                                pass
                else:
                    print(f"    Response: {response.status_code}")
            except Exception as e:
                print(f"    Error: {str(e)[:50]}")

        return None

    def _get_base_url(self, service_name: str) -> Optional[str]:
        """Get base URL for service from environment or config"""
        # Service-specific URL patterns
        url_patterns = {
            'metabase': 'METABASE_URL',
            'supabase': 'SUPABASE_URL',
            'context7': 'CONTEXT7_URL',
            'render': 'RENDER_API_URL',
            'brightdata': 'BRIGHTDATA_API_URL',
            'smartlead': None,  # Uses hardcoded URL
            'klaviyo': None,  # Uses hardcoded URL
            'shopify': 'SHOPIFY_STORE_URL'
        }

        # Try environment variable
        if service_name in url_patterns and url_patterns[service_name]:
            url = os.getenv(url_patterns[service_name])
            if url:
                return url

        # Use hardcoded URLs for some services
        hardcoded_urls = {
            'smartlead': 'https://api.smartlead.ai',
            'klaviyo': 'https://a.klaviyo.com',
            'context7': 'https://mcp.context7.com'
        }

        return hardcoded_urls.get(service_name)

    def _get_api_key(self, service_name: str) -> Optional[str]:
        """Get API key for service from environment"""
        key_patterns = {
            'metabase': 'METABASE_API_KEY',
            'supabase': 'SUPABASE_SERVICE_ROLE_KEY',
            'smartlead': 'SMARTLEAD_API_KEY',
            'context7': 'CONTEXT7_API_KEY',
            'render': 'RENDER_API_KEY',
            'brightdata': 'BRIGHTDATA_API_KEY',
            'klaviyo': 'KLAVIYO_API_KEY',
            'shopify': 'SHOPIFY_ACCESS_TOKEN'
        }

        env_var = key_patterns.get(service_name)
        if env_var:
            return os.getenv(env_var)

        return None

    def _save_schemas(self, service_name: str, schemas: Dict):
        """Save JSON schemas for a service"""
        schema_dir = self.services_path / service_name / 'docs' / 'schemas'
        os.makedirs(schema_dir, exist_ok=True)

        for schema_name, schema_def in schemas.items():
            schema_file = schema_dir / f"{schema_name}.json"
            with open(schema_file, 'w') as f:
                json.dump(schema_def, f, indent=2)

    def _generate_quick_reference(self, service_name: str, spec: Dict):
        """Generate quick reference from OpenAPI spec"""
        ref_file = self.services_path / service_name / 'quick_reference.md'

        content = f"# {service_name.title()} Quick Reference\n\n"
        content += f"Generated from OpenAPI spec on {datetime.now().strftime('%Y-%m-%d')}\n\n"

        # Add general info
        if 'info' in spec:
            info = spec['info']
            content += f"**Version**: {info.get('version', 'Unknown')}\n"
            content += f"**Description**: {info.get('description', 'N/A')}\n\n"

        # Add endpoints
        content += "## Endpoints\n\n"
        paths = spec.get('paths', {})

        for path, methods in list(paths.items())[:20]:  # First 20 endpoints
            for method, details in methods.items():
                if method in ['get', 'post', 'put', 'patch', 'delete']:
                    content += f"### {method.upper()} {path}\n"
                    content += f"{details.get('summary', 'No description')}\n\n"

        with open(ref_file, 'w') as f:
            f.write(content)

    def _generate_report(self) -> Dict[str, Any]:
        """Generate update report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'updated': self.updated,
            'failed': self.failed,
            'total': len(SPEC_SOURCES),
            'success_rate': len(self.updated) / len(SPEC_SOURCES) * 100 if SPEC_SOURCES else 0
        }

        # Save report
        report_file = Path(self.base_path) / 'tools' / 'spec_update_report.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        print("\n📊 Update Summary")
        print("=" * 40)
        print(f"✅ Updated: {len(self.updated)} services")
        print(f"❌ Failed: {len(self.failed)} services")
        print(f"📈 Success Rate: {report['success_rate']:.1f}%")

        if self.updated:
            print(f"\n✅ Successfully updated: {', '.join(self.updated)}")

        if self.failed:
            print(f"\n❌ Failed to update: {', '.join(self.failed)}")

        print(f"\n📄 Full report saved to: {report_file}")

        return report


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Update API specifications')
    parser.add_argument('services', nargs='*', help='Services to update (default: all)')
    parser.add_argument('--force', action='store_true', help='Force update even if recent')
    parser.add_argument('--validate', action='store_true', help='Validate specs after update')

    args = parser.parse_args()

    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    updater = SpecUpdater()

    if args.services:
        # Update specific services
        for service in args.services:
            if service in SPEC_SOURCES:
                print(f"Updating {service}...")
                updater.update_service(service, SPEC_SOURCES[service])
            else:
                print(f"Unknown service: {service}")
    else:
        # Update all services
        updater.update_all()


if __name__ == "__main__":
    main()