#!/usr/bin/env python3
"""
[SERVICE_NAME] API Client
Token Cost: ~[XXX] tokens when loaded

REPLACE THIS TEMPLATE WITH YOUR SERVICE IMPLEMENTATION
"""

import os
from typing import Optional, Dict, Any, List
from core.base_api import BaseAPI

class [ServiceName]API(BaseAPI):
    """
    [SERVICE_NAME] API wrapper for common operations.
    
    CAPABILITIES:
    - [List main capabilities]
    
    COMMON PATTERNS:
    ```python
    api = [ServiceName]API()
    # Add your common usage examples here
    ```
    
    AUTHENTICATION:
    - [Describe auth method]
    
    RATE LIMITS:
    - [Document rate limits]
    """
    
    def __init__(self, api_key: Optional[str] = None):
        # Get API key from environment if not provided
        api_key = api_key or os.getenv('[SERVICE]_API_KEY')
        base_url = "https://api.[service].com"  # Update with actual base URL
        
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            requests_per_second=10  # Adjust based on service limits
        )
    
    def _setup_auth(self):
        """Setup authentication headers"""
        if self.api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_key}',  # Or API key format
                'Content-Type': 'application/json'
            })
    
    # ============= CORE METHODS =============
    
    def list_[resources](self, **filters) -> List[Dict]:
        """
        List [resources] with optional filters.
        
        Args:
            filters: Optional filters for the query
        
        Returns:
            List of [resources]
        
        Example:
            api.list_[resources](status='active', limit=10)
        """
        return self._make_request('GET', '[resources]', params=filters)
    
    def get_[resource](self, resource_id: str) -> Dict:
        """
        Get a specific [resource] by ID.
        
        Args:
            resource_id: The [resource] ID
        
        Returns:
            [Resource] details
        """
        return self._make_request('GET', f'[resources]/{resource_id}')
    
    def create_[resource](self, data: Dict) -> Dict:
        """
        Create a new [resource].
        
        Args:
            data: [Resource] data
        
        Returns:
            Created [resource] details
        """
        return self._make_request('POST', '[resources]', data=data)
    
    def update_[resource](self, resource_id: str, data: Dict) -> Dict:
        """
        Update an existing [resource].
        
        Args:
            resource_id: The [resource] ID
            data: Updated data
        
        Returns:
            Updated [resource] details
        """
        return self._make_request('PATCH', f'[resources]/{resource_id}', data=data)
    
    def delete_[resource](self, resource_id: str) -> bool:
        """
        Delete a [resource].
        
        Args:
            resource_id: The [resource] ID
        
        Returns:
            True if successful
        """
        self._make_request('DELETE', f'[resources]/{resource_id}')
        return True
    
    # ============= SERVICE-SPECIFIC METHODS =============
    
    # Add methods specific to this service
    
    def test_connection(self) -> bool:
        """Test if API connection is working"""
        try:
            # Implement a simple test call
            # self._make_request('GET', 'status')
            return True
        except:
            return False


# ============= CLI INTERFACE =============

if __name__ == "__main__":
    import sys
    import json
    
    api = [ServiceName]API()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python api.py test                     # Test connection")
        print("  python api.py list [resource_type]     # List resources")
        print("  python api.py get [resource_type] [id] # Get specific resource")
        sys.exit(1)
    
    command = sys.argv[1]
    
    try:
        if command == "test":
            if api.test_connection():
                print("✓ Connection successful")
            else:
                print("✗ Connection failed")
        
        elif command == "list" and len(sys.argv) > 2:
            resource_type = sys.argv[2]
            # Implement list command
            print(f"Listing {resource_type}...")
        
        elif command == "get" and len(sys.argv) > 3:
            resource_type = sys.argv[2]
            resource_id = sys.argv[3]
            # Implement get command
            print(f"Getting {resource_type} {resource_id}...")
        
        else:
            print(f"Unknown command: {command}")
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)