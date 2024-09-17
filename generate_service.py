#!/usr/bin/env python3
"""
Service Generator for API Toolkit
Creates consistent structure for new service integrations
"""

import os
import sys
from pathlib import Path

def generate_service(service_name: str):
    """Generate a new service with our proven patterns"""
    
    service_path = Path(f"services/{service_name}")
    service_path.mkdir(parents=True, exist_ok=True)
    
    # API file with discover() and quick_start()
    api_content = f'''#!/usr/bin/env python3
"""
{service_name.title()} API Client
Token Cost: ~500-700 tokens when loaded
"""

from typing import Optional, Dict, Any, List
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.base_api import BaseAPI

class {service_name.title()}API(BaseAPI):
    """
    {service_name.title()} API wrapper.
    
    CAPABILITIES:
    - TODO: List main capabilities
    
    COMMON PATTERNS:
    ```python
    api = {service_name.title()}API()
    api.quick_start()  # See everything in 5 seconds
    api.discover()     # Explore available endpoints
    ```
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize {service_name.title()} client"""
        super().__init__(
            api_key=api_key or os.getenv('{service_name.upper()}_API_KEY'),
            base_url=os.getenv('{service_name.upper()}_API_URL', 'https://api.{service_name}.com'),
            requests_per_second=10
        )
    
    def discover(self, resource: Optional[str] = None) -> Dict[str, Any]:
        """
        🔍 DISCOVER API STRUCTURE - Always works!
        
        This method ALWAYS returns useful information.
        Use this FIRST before making any API calls!
        
        Args:
            resource: Optional specific resource to discover
        
        Returns:
            Dict with discovery results
        """
        result = {{'success': False, 'service': '{service_name}'}}
        
        # TODO: Implement discovery logic
        # Should always return something useful
        
        return result
    
    def quick_start(self) -> None:
        """
        🚀 QUICK START - Shows everything you need in 5 seconds!
        
        This eliminates 80% of the friction.
        Use this FIRST when starting!
        """
        print(f"\\n{{'='*60}}")
        print(f"🚀 QUICK START for {service_name.title()}")
        print(f"{{'='*60}}\\n")
        
        # Test connection
        if not self.test_connection():
            print("❌ Connection failed! Check your .env file")
            print(f"   Expected: {service_name.upper()}_API_KEY")
            return
        
        print("✅ Connected successfully!\\n")
        
        # Discover resources
        discovery = self.discover()
        
        # TODO: Show discovered resources
        
        print("\\n📚 Next steps:")
        print("   1. api.discover()       # See all resources")
        print("   2. api.query(...)       # Make API calls")
        print(f"\\n{{'='*60}}\\n")
    
    def test_connection(self) -> bool:
        """Test if API connection is working"""
        try:
            # TODO: Implement connection test
            return True
        except:
            return False

if __name__ == "__main__":
    # CLI interface for testing
    api = {service_name.title()}API()
    api.quick_start()
'''
    
    (service_path / "api.py").write_text(api_content)
    
    # Query helpers
    helpers_content = f'''"""
Query helpers for {service_name.title()}
"""

class QueryBuilder:
    """Build {service_name} queries with clean syntax"""
    
    def __init__(self):
        self.params = {{}}
    
    def build(self) -> dict:
        """Build the query parameters"""
        return self.params
'''
    
    (service_path / "query_helpers.py").write_text(helpers_content)
    
    # Examples
    examples_content = f'''#!/usr/bin/env python3
"""
{service_name.title()} Examples
"""

def basic_example():
    """Basic usage example"""
    from .api import {service_name.title()}API
    
    api = {service_name.title()}API()
    api.quick_start()

if __name__ == "__main__":
    basic_example()
'''
    
    (service_path / "examples.py").write_text(examples_content)
    
    # Documentation
    doc_content = f'''# {service_name.title()} Service Documentation

## Quick Start

```python
from api_toolkit.services.{service_name}.api import {service_name.title()}API

api = {service_name.title()}API()
api.quick_start()  # Shows everything in 5 seconds!
```

## Discovery Pattern

Always start with discovery:

```python
# Discover all resources
info = api.discover()

# Discover specific resource
info = api.discover('resource_name')
```

## Common Patterns

TODO: Add common usage patterns

## Error Handling

TODO: Document common errors and solutions
'''
    
    (service_path / "README.md").write_text(doc_content)
    
    # Init file
    init_content = f'''"""
{service_name.title()} Service
"""

from .api import {service_name.title()}API

__all__ = ['{service_name.title()}API']
'''
    
    (service_path / "__init__.py").write_text(init_content)
    
    print(f"✅ Generated service structure for '{service_name}':")
    print(f"   services/{service_name}/")
    print(f"   ├── api.py (with discover() and quick_start())")
    print(f"   ├── query_helpers.py")
    print(f"   ├── examples.py")
    print(f"   ├── README.md")
    print(f"   └── __init__.py")
    print(f"\n🎯 Next steps:")
    print(f"   1. Update .env with {service_name.upper()}_API_KEY")
    print(f"   2. Implement discover() method")
    print(f"   3. Add service-specific methods")
    print(f"   4. Test with: python services/{service_name}/api.py")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python generate_service.py <service_name>")
        print("Example: python generate_service.py klaviyo")
        sys.exit(1)
    
    service_name = sys.argv[1].lower()
    generate_service(service_name)