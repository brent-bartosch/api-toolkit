#!/usr/bin/env python3
"""
Shopify API Client
Token Cost: ~600 tokens

E-commerce operations for Shopify stores via REST Admin API.
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Load environment variables with priority: project root > toolkit dir > home dir
env_locations = [
    Path.cwd() / '.env',
    Path(__file__).parent.parent.parent / '.env',
    Path.home() / '.api-toolkit.env'
]
for env_path in env_locations:
    if env_path.exists():
        load_dotenv(env_path, override=True)
        break

from core.base_api import BaseAPI, APIError


class ShopifyAPI(BaseAPI):
    """
    Shopify REST Admin API wrapper for e-commerce operations.

    CAPABILITIES:
    - Products: List, get, create, update, delete
    - Orders: List, get, cancel, close
    - Customers: List, get, search, order history
    - Shop: Store information

    API Version: 2024-01
    Rate Limits: 2 requests/second (bucket: 40 requests)

    COMMON PATTERNS:
    ```python
    api = ShopifyAPI()
    api.quick_start()  # See store info, products, orders

    # List products
    products = api.list_products(status='active', limit=50)

    # Get recent orders
    orders = api.list_orders(status='open', limit=20)

    # Search customers
    customer = api.search_customers('john@example.com')
    ```

    AUTHENTICATION:
    - SHOPIFY_STORE_DOMAIN: Your store domain (e.g., mystore.myshopify.com)
    - SHOPIFY_ACCESS_TOKEN: Admin API access token (shpat_xxx)
    """

    API_VERSION = '2024-01'

    def __init__(self, store_domain: Optional[str] = None,
                 access_token: Optional[str] = None):
        """
        Initialize Shopify client.

        Args:
            store_domain: Your Shopify store domain (e.g., mystore.myshopify.com)
            access_token: Shopify Admin API access token

        Examples:
            api = ShopifyAPI()  # Uses environment variables
            api = ShopifyAPI('mystore.myshopify.com', 'shpat_xxx')
        """
        self.store_domain = store_domain or os.getenv('SHOPIFY_STORE_DOMAIN')
        self.access_token = access_token or os.getenv('SHOPIFY_ACCESS_TOKEN')

        if not self.store_domain:
            raise APIError("Missing SHOPIFY_STORE_DOMAIN in environment")
        if not self.access_token:
            raise APIError("Missing SHOPIFY_ACCESS_TOKEN in environment")

        # Ensure store domain is in correct format
        if not self.store_domain.endswith('.myshopify.com'):
            self.store_domain = f"{self.store_domain}.myshopify.com"

        base_url = f"https://{self.store_domain}/admin/api/{self.API_VERSION}"

        super().__init__(
            api_key=self.access_token,
            base_url=base_url,
            requests_per_second=2  # Shopify rate limit
        )

    def _setup_auth(self):
        """Setup Shopify authentication headers"""
        self.session.headers.update({
            'X-Shopify-Access-Token': self.api_key,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })

    def _build_endpoint(self, resource: str) -> str:
        """Build API endpoint with .json suffix"""
        return f"{resource}.json"

    def _unwrap_response(self, response: Dict, key: str) -> Any:
        """Unwrap Shopify's response format (e.g., {'products': [...]} -> [...])"""
        return response.get(key, response)

    # ============= SHOP OPERATIONS =============

    def get_shop(self) -> Dict:
        """
        Get store information.

        Returns:
            Dict with shop details (name, email, currency, etc.)
        """
        response = self._make_request('GET', self._build_endpoint('shop'))
        return self._unwrap_response(response, 'shop')

    def test_connection(self) -> bool:
        """Test if API connection is working"""
        try:
            self.get_shop()
            return True
        except:
            return False

    # ============= PRODUCT OPERATIONS =============

    def list_products(self, limit: int = 50, status: Optional[str] = None,
                      vendor: Optional[str] = None, product_type: Optional[str] = None,
                      collection_id: Optional[int] = None, created_at_min: Optional[str] = None,
                      created_at_max: Optional[str] = None, fields: Optional[str] = None,
                      since_id: Optional[int] = None) -> List[Dict]:
        """
        List products with optional filters.

        Args:
            limit: Max products to return (max 250)
            status: Filter by status (active, draft, archived)
            vendor: Filter by vendor name
            product_type: Filter by product type
            collection_id: Filter by collection ID
            created_at_min: Minimum creation date (ISO 8601)
            created_at_max: Maximum creation date (ISO 8601)
            fields: Comma-separated fields to return
            since_id: Return products after this ID (pagination)

        Returns:
            List of product dicts
        """
        params = {'limit': min(limit, 250)}

        if status:
            params['status'] = status
        if vendor:
            params['vendor'] = vendor
        if product_type:
            params['product_type'] = product_type
        if collection_id:
            params['collection_id'] = collection_id
        if created_at_min:
            params['created_at_min'] = created_at_min
        if created_at_max:
            params['created_at_max'] = created_at_max
        if fields:
            params['fields'] = fields
        if since_id:
            params['since_id'] = since_id

        response = self._make_request('GET', self._build_endpoint('products'), params=params)
        return self._unwrap_response(response, 'products')

    def get_product(self, product_id: int, fields: Optional[str] = None) -> Dict:
        """
        Get a single product by ID.

        Args:
            product_id: Shopify product ID
            fields: Comma-separated fields to return

        Returns:
            Product dict with variants, images, etc.
        """
        params = {}
        if fields:
            params['fields'] = fields

        response = self._make_request('GET', self._build_endpoint(f'products/{product_id}'), params=params)
        return self._unwrap_response(response, 'product')

    def create_product(self, data: Dict) -> Dict:
        """
        Create a new product.

        Args:
            data: Product data (title, body_html, vendor, product_type, variants, etc.)

        Returns:
            Created product dict
        """
        response = self._make_request('POST', self._build_endpoint('products'), data={'product': data})
        return self._unwrap_response(response, 'product')

    def update_product(self, product_id: int, data: Dict) -> Dict:
        """
        Update a product.

        Args:
            product_id: Shopify product ID
            data: Fields to update

        Returns:
            Updated product dict
        """
        response = self._make_request('PUT', self._build_endpoint(f'products/{product_id}'), data={'product': data})
        return self._unwrap_response(response, 'product')

    def delete_product(self, product_id: int) -> bool:
        """
        Delete a product.

        Args:
            product_id: Shopify product ID

        Returns:
            True if successful
        """
        self._make_request('DELETE', self._build_endpoint(f'products/{product_id}'))
        return True

    def count_products(self, status: Optional[str] = None, vendor: Optional[str] = None,
                       product_type: Optional[str] = None) -> int:
        """Get count of products with optional filters."""
        params = {}
        if status:
            params['status'] = status
        if vendor:
            params['vendor'] = vendor
        if product_type:
            params['product_type'] = product_type

        response = self._make_request('GET', self._build_endpoint('products/count'), params=params)
        return response.get('count', 0)

    # ============= ORDER OPERATIONS =============

    def list_orders(self, limit: int = 50, status: Optional[str] = None,
                    financial_status: Optional[str] = None, fulfillment_status: Optional[str] = None,
                    created_at_min: Optional[str] = None, created_at_max: Optional[str] = None,
                    fields: Optional[str] = None, since_id: Optional[int] = None) -> List[Dict]:
        """
        List orders with optional filters.

        Args:
            limit: Max orders to return (max 250)
            status: Order status (open, closed, cancelled, any)
            financial_status: Payment status (authorized, pending, paid, refunded, etc.)
            fulfillment_status: Fulfillment status (shipped, partial, unshipped, any, unfulfilled)
            created_at_min: Minimum creation date (ISO 8601)
            created_at_max: Maximum creation date (ISO 8601)
            fields: Comma-separated fields to return
            since_id: Return orders after this ID (pagination)

        Returns:
            List of order dicts
        """
        params = {'limit': min(limit, 250)}

        if status:
            params['status'] = status
        if financial_status:
            params['financial_status'] = financial_status
        if fulfillment_status:
            params['fulfillment_status'] = fulfillment_status
        if created_at_min:
            params['created_at_min'] = created_at_min
        if created_at_max:
            params['created_at_max'] = created_at_max
        if fields:
            params['fields'] = fields
        if since_id:
            params['since_id'] = since_id

        response = self._make_request('GET', self._build_endpoint('orders'), params=params)
        return self._unwrap_response(response, 'orders')

    def get_order(self, order_id: int, fields: Optional[str] = None) -> Dict:
        """
        Get a single order by ID.

        Args:
            order_id: Shopify order ID
            fields: Comma-separated fields to return

        Returns:
            Order dict with line items, customer, etc.
        """
        params = {}
        if fields:
            params['fields'] = fields

        response = self._make_request('GET', self._build_endpoint(f'orders/{order_id}'), params=params)
        return self._unwrap_response(response, 'order')

    def cancel_order(self, order_id: int, reason: Optional[str] = None,
                     email: bool = True, restock: bool = False) -> Dict:
        """
        Cancel an order.

        Args:
            order_id: Shopify order ID
            reason: Cancellation reason (customer, fraud, inventory, declined, other)
            email: Send notification email to customer
            restock: Restock inventory

        Returns:
            Cancelled order dict
        """
        data = {}
        if reason:
            data['reason'] = reason
        data['email'] = email
        data['restock'] = restock

        response = self._make_request('POST', self._build_endpoint(f'orders/{order_id}/cancel'), data=data)
        return self._unwrap_response(response, 'order')

    def close_order(self, order_id: int) -> Dict:
        """
        Close an order.

        Args:
            order_id: Shopify order ID

        Returns:
            Closed order dict
        """
        response = self._make_request('POST', self._build_endpoint(f'orders/{order_id}/close'))
        return self._unwrap_response(response, 'order')

    def count_orders(self, status: Optional[str] = None, financial_status: Optional[str] = None,
                     fulfillment_status: Optional[str] = None) -> int:
        """Get count of orders with optional filters."""
        params = {}
        if status:
            params['status'] = status
        if financial_status:
            params['financial_status'] = financial_status
        if fulfillment_status:
            params['fulfillment_status'] = fulfillment_status

        response = self._make_request('GET', self._build_endpoint('orders/count'), params=params)
        return response.get('count', 0)

    # ============= CUSTOMER OPERATIONS =============

    def list_customers(self, limit: int = 50, created_at_min: Optional[str] = None,
                       created_at_max: Optional[str] = None, updated_at_min: Optional[str] = None,
                       fields: Optional[str] = None, since_id: Optional[int] = None) -> List[Dict]:
        """
        List customers with optional filters.

        Args:
            limit: Max customers to return (max 250)
            created_at_min: Minimum creation date (ISO 8601)
            created_at_max: Maximum creation date (ISO 8601)
            updated_at_min: Minimum update date (ISO 8601)
            fields: Comma-separated fields to return
            since_id: Return customers after this ID (pagination)

        Returns:
            List of customer dicts
        """
        params = {'limit': min(limit, 250)}

        if created_at_min:
            params['created_at_min'] = created_at_min
        if created_at_max:
            params['created_at_max'] = created_at_max
        if updated_at_min:
            params['updated_at_min'] = updated_at_min
        if fields:
            params['fields'] = fields
        if since_id:
            params['since_id'] = since_id

        response = self._make_request('GET', self._build_endpoint('customers'), params=params)
        return self._unwrap_response(response, 'customers')

    def get_customer(self, customer_id: int, fields: Optional[str] = None) -> Dict:
        """
        Get a single customer by ID.

        Args:
            customer_id: Shopify customer ID
            fields: Comma-separated fields to return

        Returns:
            Customer dict
        """
        params = {}
        if fields:
            params['fields'] = fields

        response = self._make_request('GET', self._build_endpoint(f'customers/{customer_id}'), params=params)
        return self._unwrap_response(response, 'customer')

    def search_customers(self, query: str) -> List[Dict]:
        """
        Search customers by email, name, or other fields.

        Args:
            query: Search query (email, name, etc.)

        Returns:
            List of matching customers
        """
        params = {'query': query}
        response = self._make_request('GET', self._build_endpoint('customers/search'), params=params)
        return self._unwrap_response(response, 'customers')

    def get_customer_orders(self, customer_id: int, limit: int = 50) -> List[Dict]:
        """
        Get orders for a specific customer.

        Args:
            customer_id: Shopify customer ID
            limit: Max orders to return

        Returns:
            List of order dicts
        """
        params = {'limit': min(limit, 250)}
        response = self._make_request('GET', self._build_endpoint(f'customers/{customer_id}/orders'), params=params)
        return self._unwrap_response(response, 'orders')

    def count_customers(self) -> int:
        """Get total count of customers."""
        response = self._make_request('GET', self._build_endpoint('customers/count'))
        return response.get('count', 0)

    # ============= DISCOVERY METHODS =============

    def discover(self, resource: Optional[str] = None) -> Dict[str, Any]:
        """
        Discover available resources and their structure.

        Args:
            resource: Optional specific resource to discover ('products', 'orders', 'customers')

        Returns:
            Dict with discovery results
        """
        result = {
            'success': False,
            'store': self.store_domain,
            'api_version': self.API_VERSION
        }

        try:
            if resource:
                # Discover specific resource
                if resource == 'products':
                    sample = self.list_products(limit=1)
                    count = self.count_products()
                    result['resource'] = 'products'
                    result['count'] = count
                    result['sample'] = sample[0] if sample else None
                    result['fields'] = list(sample[0].keys()) if sample else []
                elif resource == 'orders':
                    sample = self.list_orders(limit=1, status='any')
                    count = self.count_orders(status='any')
                    result['resource'] = 'orders'
                    result['count'] = count
                    result['sample'] = sample[0] if sample else None
                    result['fields'] = list(sample[0].keys()) if sample else []
                elif resource == 'customers':
                    sample = self.list_customers(limit=1)
                    count = self.count_customers()
                    result['resource'] = 'customers'
                    result['count'] = count
                    result['sample'] = sample[0] if sample else None
                    result['fields'] = list(sample[0].keys()) if sample else []
                else:
                    result['error'] = f"Unknown resource: {resource}"
                    return result

                result['success'] = True
            else:
                # Discover all resources
                shop = self.get_shop()
                result['shop'] = {
                    'name': shop.get('name'),
                    'email': shop.get('email'),
                    'currency': shop.get('currency'),
                    'domain': shop.get('domain')
                }

                result['resources'] = {
                    'products': self.count_products(),
                    'orders': self.count_orders(status='any'),
                    'customers': self.count_customers()
                }

                result['available_filters'] = {
                    'products': ['status', 'vendor', 'product_type', 'collection_id', 'created_at_min/max'],
                    'orders': ['status', 'financial_status', 'fulfillment_status', 'created_at_min/max'],
                    'customers': ['created_at_min/max', 'updated_at_min']
                }

                result['success'] = True

        except Exception as e:
            result['error'] = str(e)
            result['hint'] = "Check SHOPIFY_STORE_DOMAIN and SHOPIFY_ACCESS_TOKEN"

        return result

    def explore(self, resource: Optional[str] = None) -> None:
        """Interactive exploration of store data (prints results)."""
        info = self.discover(resource)

        if not info.get('success'):
            print(f"Error: {info.get('error', 'Unknown error')}")
            print(f"Hint: {info.get('hint', '')}")
            return

        if resource:
            print(f"\nResource: {info['resource']}")
            print(f"Total count: {info['count']}")
            if info.get('fields'):
                print(f"Fields: {', '.join(info['fields'][:10])}")
                if len(info['fields']) > 10:
                    print(f"  ... and {len(info['fields']) - 10} more")
        else:
            print(f"\nStore: {info['shop']['name']}")
            print(f"Domain: {info['shop']['domain']}")
            print(f"Currency: {info['shop']['currency']}")
            print(f"\nResources:")
            for resource, count in info['resources'].items():
                print(f"  - {resource}: {count}")

    def quick_start(self) -> None:
        """
        Show everything you need to get started in 5 seconds.

        Example:
            api = ShopifyAPI()
            api.quick_start()
        """
        print(f"\n{'='*60}")
        print(f"SHOPIFY QUICK START")
        print(f"{'='*60}\n")

        # Test connection
        if not self.test_connection():
            print("Connection failed! Check your credentials.")
            print("  SHOPIFY_STORE_DOMAIN: Set?", bool(os.getenv('SHOPIFY_STORE_DOMAIN')))
            print("  SHOPIFY_ACCESS_TOKEN: Set?", bool(os.getenv('SHOPIFY_ACCESS_TOKEN')))
            return

        # Get shop info
        shop = self.get_shop()
        print(f"Connected to: {shop.get('name')}")
        print(f"Store: {self.store_domain}")
        print(f"Currency: {shop.get('currency')}\n")

        # Show counts
        print("Resources:")
        print(f"  Products: {self.count_products()}")
        print(f"  Orders: {self.count_orders(status='any')}")
        print(f"  Customers: {self.count_customers()}\n")

        # Show sample product
        products = self.list_products(limit=3)
        if products:
            print("Sample products:")
            for p in products[:3]:
                print(f"  - {p.get('title')} (${p.get('variants', [{}])[0].get('price', 'N/A')})")
            print()

        # Show filter options
        print("Product filters:")
        print("  status: active, draft, archived")
        print("  vendor: Filter by vendor name")
        print("  product_type: Filter by type\n")

        print("Order filters:")
        print("  status: open, closed, cancelled, any")
        print("  financial_status: paid, pending, refunded, etc.")
        print("  fulfillment_status: shipped, unshipped, partial\n")

        # Example queries
        print("Example queries:")
        print("  products = api.list_products(status='active', limit=50)")
        print("  orders = api.list_orders(status='open', financial_status='paid')")
        print("  customer = api.search_customers('john@example.com')")
        print(f"\n{'='*60}\n")


# ============= CLI INTERFACE =============

if __name__ == "__main__":
    import json

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python api.py test              # Test connection")
        print("  python api.py quick_start       # Show overview")
        print("  python api.py discover          # Discover resources")
        print("  python api.py products [limit]  # List products")
        print("  python api.py orders [limit]    # List orders")
        print("  python api.py customers [limit] # List customers")
        sys.exit(1)

    command = sys.argv[1]

    try:
        api = ShopifyAPI()

        if command == "test":
            if api.test_connection():
                shop = api.get_shop()
                print(f"Connected to: {shop.get('name')}")
                print(f"Store: {api.store_domain}")
            else:
                print("Connection failed!")

        elif command == "quick_start":
            api.quick_start()

        elif command == "discover":
            resource = sys.argv[2] if len(sys.argv) > 2 else None
            api.explore(resource)

        elif command == "products":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5
            products = api.list_products(limit=limit)
            print(json.dumps(products, indent=2, default=str))

        elif command == "orders":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5
            orders = api.list_orders(limit=limit, status='any')
            print(json.dumps(orders, indent=2, default=str))

        elif command == "customers":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5
            customers = api.list_customers(limit=limit)
            print(json.dumps(customers, indent=2, default=str))

        else:
            print(f"Unknown command: {command}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
