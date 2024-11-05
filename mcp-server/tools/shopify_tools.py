#!/usr/bin/env python3
"""
Shopify MCP Tools - Lightweight tool definitions for Shopify Admin API
Read-only access to products and orders
"""

import sys
import os
import requests
from pathlib import Path
from typing import Optional, Dict, List, Any

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

# Load environment variables using toolkit's config (same priority as other services)
from dotenv import load_dotenv

# Load with priority: project root > toolkit dir > home dir
env_locations = [
    Path.cwd() / '.env',
    parent_dir / '.env',
    Path.home() / '.api-toolkit.env'
]
for env_path in env_locations:
    if env_path.exists():
        load_dotenv(env_path, override=True)
        break


class ShopifyAPI:
    """Minimal Shopify API wrapper for MCP tools"""

    def __init__(self):
        self.store_domain = os.getenv('SHOPIFY_STORE_DOMAIN')
        self.access_token = os.getenv('SHOPIFY_ACCESS_TOKEN')

        if not self.store_domain or not self.access_token:
            raise ValueError("Missing SHOPIFY_STORE_DOMAIN or SHOPIFY_ACCESS_TOKEN in environment")

        # Ensure store domain is in correct format
        if not self.store_domain.endswith('.myshopify.com'):
            self.store_domain = f"{self.store_domain}.myshopify.com"

        self.base_url = f"https://{self.store_domain}/admin/api/2024-01"
        self.headers = {
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json"
        }

    def _request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make GET request to Shopify API"""
        url = f"{self.base_url}/{endpoint}.json"
        response = requests.get(url, headers=self.headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json()


def get_shopify_products(status: str = None, vendor: str = None,
                         product_type: str = None, limit: int = 50) -> Dict:
    """
    Get products from Shopify store.

    Args:
        status: Filter by status (active, draft, archived)
        vendor: Filter by vendor name
        product_type: Filter by product type
        limit: Max products to return (default 50, max 250)

    Returns:
        {success: bool, data: list, error: str, metadata: dict}
    """
    try:
        api = ShopifyAPI()

        # Build query parameters
        params = {'limit': min(limit, 250)}
        if status:
            params['status'] = status
        if vendor:
            params['vendor'] = vendor
        if product_type:
            params['product_type'] = product_type

        result = api._request('products', params)
        products = result.get('products', [])

        return {
            "success": True,
            "data": products,
            "error": None,
            "metadata": {
                "count": len(products),
                "store": api.store_domain,
                "filters": {k: v for k, v in params.items() if k != 'limit'}
            }
        }

    except Exception as e:
        return {
            "success": False,
            "data": None,
            "error": str(e),
            "suggestion": "Check SHOPIFY_STORE_DOMAIN and SHOPIFY_ACCESS_TOKEN are set correctly"
        }


def get_shopify_product(product_id: int, fields: str = None) -> Dict:
    """
    Get a single product by ID.

    Args:
        product_id: Shopify product ID
        fields: Comma-separated fields to return (optional)

    Returns:
        {success: bool, data: dict, error: str, metadata: dict}
    """
    try:
        api = ShopifyAPI()

        params = {}
        if fields:
            params['fields'] = fields

        result = api._request(f'products/{product_id}', params)
        product = result.get('product', {})

        return {
            "success": True,
            "data": product,
            "error": None,
            "metadata": {
                "product_id": product_id,
                "store": api.store_domain
            }
        }

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return {
                "success": False,
                "data": None,
                "error": f"Product {product_id} not found",
                "suggestion": "Use get_shopify_products() to list available products"
            }
        return {
            "success": False,
            "data": None,
            "error": str(e),
            "suggestion": "Check product_id is valid"
        }

    except Exception as e:
        return {
            "success": False,
            "data": None,
            "error": str(e),
            "suggestion": "Check SHOPIFY credentials"
        }


def get_shopify_orders(status: str = None, financial_status: str = None,
                       fulfillment_status: str = None, created_at_min: str = None,
                       created_at_max: str = None, limit: int = 50) -> Dict:
    """
    Get orders from Shopify store.

    Args:
        status: Order status (open, closed, cancelled, any)
        financial_status: Payment status (authorized, pending, paid, etc.)
        fulfillment_status: Fulfillment status (shipped, partial, unshipped, any)
        created_at_min: Minimum creation date (ISO 8601 format)
        created_at_max: Maximum creation date (ISO 8601 format)
        limit: Max orders to return (default 50, max 250)

    Returns:
        {success: bool, data: list, error: str, metadata: dict}
    """
    try:
        api = ShopifyAPI()

        # Build query parameters
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

        result = api._request('orders', params)
        orders = result.get('orders', [])

        return {
            "success": True,
            "data": orders,
            "error": None,
            "metadata": {
                "count": len(orders),
                "store": api.store_domain,
                "filters": {k: v for k, v in params.items() if k != 'limit'}
            }
        }

    except Exception as e:
        return {
            "success": False,
            "data": None,
            "error": str(e),
            "suggestion": "Check SHOPIFY_STORE_DOMAIN and SHOPIFY_ACCESS_TOKEN are set correctly"
        }


def get_shopify_order(order_id: int, fields: str = None) -> Dict:
    """
    Get a single order by ID.

    Args:
        order_id: Shopify order ID
        fields: Comma-separated fields to return (optional)

    Returns:
        {success: bool, data: dict, error: str, metadata: dict}
    """
    try:
        api = ShopifyAPI()

        params = {}
        if fields:
            params['fields'] = fields

        result = api._request(f'orders/{order_id}', params)
        order = result.get('order', {})

        return {
            "success": True,
            "data": order,
            "error": None,
            "metadata": {
                "order_id": order_id,
                "store": api.store_domain
            }
        }

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return {
                "success": False,
                "data": None,
                "error": f"Order {order_id} not found",
                "suggestion": "Use get_shopify_orders() to list available orders"
            }
        return {
            "success": False,
            "data": None,
            "error": str(e),
            "suggestion": "Check order_id is valid"
        }

    except Exception as e:
        return {
            "success": False,
            "data": None,
            "error": str(e),
            "suggestion": "Check SHOPIFY credentials"
        }


def shopify_discover() -> Dict:
    """
    Discover available Shopify resources and connection status.

    Returns:
        {success: bool, data: dict, error: str}
    """
    try:
        api = ShopifyAPI()

        # Test connection by getting a single product
        test = api._request('products', {'limit': 1})

        # Get shop info
        shop_info = api._request('shop')
        shop = shop_info.get('shop', {})

        return {
            "success": True,
            "data": {
                "store": api.store_domain,
                "shop_name": shop.get('name'),
                "email": shop.get('email'),
                "currency": shop.get('currency'),
                "available_resources": [
                    "products",
                    "orders",
                    "customers",
                    "inventory"
                ],
                "available_tools": [
                    "get_shopify_products",
                    "get_shopify_product",
                    "get_shopify_orders",
                    "get_shopify_order"
                ],
                "product_filters": [
                    "status (active, draft, archived)",
                    "vendor",
                    "product_type"
                ],
                "order_filters": [
                    "status (open, closed, cancelled, any)",
                    "financial_status (authorized, pending, paid, etc.)",
                    "fulfillment_status (shipped, partial, unshipped, any)",
                    "created_at_min (ISO 8601)",
                    "created_at_max (ISO 8601)"
                ]
            },
            "error": None,
            "metadata": {
                "connected": True,
                "api_version": "2024-01"
            }
        }

    except Exception as e:
        return {
            "success": False,
            "data": None,
            "error": str(e),
            "suggestion": "Check SHOPIFY_STORE_DOMAIN and SHOPIFY_ACCESS_TOKEN in .env file"
        }


# Tool registry for MCP
SHOPIFY_TOOLS = [
    {
        "name": "get_shopify_products",
        "description": "Get products from Shopify store with optional filters",
        "function": get_shopify_products
    },
    {
        "name": "get_shopify_product",
        "description": "Get a single product by ID",
        "function": get_shopify_product
    },
    {
        "name": "get_shopify_orders",
        "description": "Get orders from Shopify store with optional filters",
        "function": get_shopify_orders
    },
    {
        "name": "get_shopify_order",
        "description": "Get a single order by ID",
        "function": get_shopify_order
    },
    {
        "name": "shopify_discover",
        "description": "Discover available Shopify resources and test connection",
        "function": shopify_discover
    }
]


if __name__ == "__main__":
    # Test the tools
    print("Testing Shopify tools...")

    # Test discover
    print("\n1. Testing shopify_discover...")
    result = shopify_discover()
    print(f"Success: {result['success']}")
    if result['success']:
        print(f"Store: {result['data']['store']}")
        print(f"Shop Name: {result['data']['shop_name']}")
        print(f"Available tools: {len(result['data']['available_tools'])}")
    else:
        print(f"Error: {result['error']}")

    # Test get products
    print("\n2. Testing get_shopify_products...")
    result = get_shopify_products(limit=5)
    print(f"Success: {result['success']}")
    if result['success']:
        print(f"Products returned: {result['metadata']['count']}")
        if result['data']:
            print(f"First product: {result['data'][0].get('title', 'N/A')}")
    else:
        print(f"Error: {result['error']}")

    # Test get orders
    print("\n3. Testing get_shopify_orders...")
    result = get_shopify_orders(limit=5, status='any')
    print(f"Success: {result['success']}")
    if result['success']:
        print(f"Orders returned: {result['metadata']['count']}")
        if result['data']:
            print(f"First order: #{result['data'][0].get('order_number', 'N/A')}")
    else:
        print(f"Error: {result['error']}")
