#!/usr/bin/env python3
"""
Progressive tool discovery system for code execution MCP.
Follows Anthropic's pattern: load tool docs on-demand, not upfront.
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add parent to path
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))


class ToolDiscovery:
    """
    Progressive tool discovery system.

    Instead of loading all tool definitions (150k tokens),
    let Claude discover tools on-demand (~2k tokens).
    """

    def __init__(self):
        self.toolkit_root = Path(__file__).parent.parent.parent
        self.services_dir = self.toolkit_root / 'services'

    def list_services(self) -> List[Dict[str, Any]]:
        """
        List available services (minimal metadata only).

        Returns lightweight service list without full documentation.
        """
        services = []

        for service_dir in self.services_dir.iterdir():
            if not service_dir.is_dir() or service_dir.name.startswith('_'):
                continue

            api_file = service_dir / 'api.py'
            if not api_file.exists():
                continue

            services.append({
                'name': service_dir.name,
                'path': str(service_dir),
                'has_examples': (service_dir / 'examples.py').exists(),
                'has_docs': (service_dir / 'README.md').exists(),
                'has_helpers': (service_dir / 'query_helpers.py').exists()
            })

        return services

    def get_service_overview(self, service_name: str,
                            detail_level: str = 'basic') -> Dict[str, Any]:
        """
        Get service overview with configurable detail.

        Args:
            service_name: Service to get info for
            detail_level: 'basic', 'standard', or 'full'

        Returns:
            Service metadata and documentation at requested detail level
        """
        service_dir = self.services_dir / service_name
        if not service_dir.exists():
            return {'error': f"Service '{service_name}' not found"}

        overview = {
            'name': service_name,
            'available': True
        }

        # Basic: Just what's available
        if detail_level == 'basic':
            overview['files'] = [
                f.name for f in service_dir.iterdir()
                if f.is_file() and f.suffix in ['.py', '.md']
            ]
            return overview

        # Standard: Include class info
        if detail_level in ['standard', 'full']:
            api_file = service_dir / 'api.py'
            if api_file.exists():
                overview['api_class'] = self._extract_class_info(api_file)

            readme = service_dir / 'README.md'
            if readme.exists() and detail_level == 'full':
                overview['readme'] = readme.read_text()[:2000]  # First 2KB

        return overview

    def get_code_examples(self, service_name: str,
                         example_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get code examples for a service.

        Args:
            service_name: Service name
            example_type: Optional specific example type to get

        Returns:
            Code examples for the service
        """
        service_dir = self.services_dir / service_name
        examples_file = service_dir / 'examples.py'

        if not examples_file.exists():
            return {'error': f"No examples for '{service_name}'"}

        content = examples_file.read_text()

        # Extract example functions
        examples = self._extract_examples(content)

        if example_type:
            examples = [e for e in examples if example_type.lower() in e['name'].lower()]

        return {
            'service': service_name,
            'examples': examples,
            'total': len(examples)
        }

    def search_tools(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search for tools by keyword.

        Args:
            query: Search query
            max_results: Maximum results to return

        Returns:
            Matching tools with brief descriptions
        """
        results = []
        query_lower = query.lower()

        for service_dir in self.services_dir.iterdir():
            if not service_dir.is_dir() or service_dir.name.startswith('_'):
                continue

            # Check service name
            if query_lower in service_dir.name.lower():
                results.append({
                    'service': service_dir.name,
                    'match_type': 'name',
                    'relevance': 10
                })
                continue

            # Check README
            readme = service_dir / 'README.md'
            if readme.exists():
                content = readme.read_text().lower()
                if query_lower in content:
                    results.append({
                        'service': service_dir.name,
                        'match_type': 'documentation',
                        'relevance': 5
                    })

        # Sort by relevance
        results.sort(key=lambda x: x['relevance'], reverse=True)
        return results[:max_results]

    def get_quick_start(self, service_name: str) -> str:
        """
        Get quick start code snippet for a service.

        Returns minimal working example to get started quickly.
        """
        quick_starts = {
            'supabase': '''# Supabase Quick Start
api = SupabaseAPI('project1')  # or 'project2' or 'project3'

# Discover what's available
info = api.discover()
print(f"Tables: {info.get('tables', [])}")

# Query data
leads = api.query('leads', limit=10)
print(f"Found {len(leads)} leads")

# Process data here (in sandbox - no tokens used!)
high_scores = [l for l in leads if l.get('score', 0) > 80]
print(f"High scoring leads: {len(high_scores)}")
''',
            'smartlead': '''# Smartlead Quick Start
from services.smartlead.api import SmartleadAPI
api = SmartleadAPI()

# List campaigns
campaigns = api.list_campaigns()
print(f"Found {len(campaigns)} campaigns")

# Get analytics
if campaigns:
    stats = api.get_campaign_analytics(campaigns[0]['id'])
    print(f"Reply rate: {stats.get('reply_rate', 0)}%")
''',
            'metabase': '''# Metabase Quick Start
from services.metabase.api import MetabaseAPI
api = MetabaseAPI()

# Run SQL query
results = api.run_query(
    "SELECT * FROM sales LIMIT 10",
    database_id=1
)
print(f"Found {len(results)} rows")
'''
        }

        return quick_starts.get(
            service_name,
            f"# {service_name.title()} - check examples.py for usage"
        )

    def _extract_class_info(self, api_file: Path) -> Dict[str, Any]:
        """Extract basic class info from api.py file"""
        content = api_file.read_text()

        # Find class definition
        class_name = None
        methods = []

        for line in content.split('\n'):
            if line.strip().startswith('class ') and 'API' in line:
                class_name = line.split('class ')[1].split('(')[0].strip()
            elif class_name and line.strip().startswith('def ') and not line.strip().startswith('def _'):
                method = line.split('def ')[1].split('(')[0].strip()
                methods.append(method)

        return {
            'class_name': class_name,
            'methods': methods[:20],  # Limit to 20 methods
            'total_methods': len(methods)
        }

    def _extract_examples(self, content: str) -> List[Dict[str, str]]:
        """Extract example functions from examples.py"""
        examples = []
        current_func = None
        current_code = []

        for line in content.split('\n'):
            if line.startswith('def example_') or line.startswith('def test_'):
                if current_func:
                    examples.append({
                        'name': current_func,
                        'code': '\n'.join(current_code)
                    })
                current_func = line.split('def ')[1].split('(')[0]
                current_code = [line]
            elif current_func:
                current_code.append(line)
                # Stop at next function or end
                if line and not line.startswith(' ') and not line.startswith('\t'):
                    if line.startswith('def ') or line.startswith('if __name__'):
                        examples.append({
                            'name': current_func,
                            'code': '\n'.join(current_code[:-1])
                        })
                        current_func = None
                        current_code = []

        return examples


if __name__ == "__main__":
    # Test discovery system
    discovery = ToolDiscovery()

    print("Testing Tool Discovery System...")
    print("=" * 60)

    # Test 1: List services
    print("\n1. Available services:")
    services = discovery.list_services()
    for svc in services:
        print(f"  - {svc['name']}")
        print(f"    Examples: {svc['has_examples']}, Docs: {svc['has_docs']}")

    # Test 2: Get service overview
    print("\n2. Supabase overview (basic):")
    overview = discovery.get_service_overview('supabase', 'basic')
    print(f"  Files: {overview.get('files', [])[:5]}")

    print("\n3. Supabase overview (standard):")
    overview = discovery.get_service_overview('supabase', 'standard')
    if 'api_class' in overview:
        print(f"  Class: {overview['api_class'].get('class_name')}")
        print(f"  Methods: {overview['api_class'].get('methods', [])[:5]}")

    # Test 3: Quick start
    print("\n4. Quick start code:")
    quick_start = discovery.get_quick_start('supabase')
    print(quick_start[:200] + "...")

    # Test 4: Search
    print("\n5. Search for 'query':")
    results = discovery.search_tools('query')
    for r in results[:3]:
        print(f"  - {r['service']} ({r['match_type']})")

    print("\n" + "=" * 60)
    print("Discovery system tests complete!")
