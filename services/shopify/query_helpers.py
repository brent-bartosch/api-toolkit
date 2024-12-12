#!/usr/bin/env python3
"""
Shopify Query Helpers
Provides common query patterns and builders for Shopify operations.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta


class ShopifyQueryBuilder:
    """Helper class to build Shopify queries more intuitively"""

    def __init__(self, resource: str):
        """
        Initialize builder for a resource type.

        Args:
            resource: 'products', 'orders', or 'customers'
        """
        self.resource = resource
        self.params = {}
        self._limit = 50

    def status(self, value: str):
        """Filter by status (products: active/draft/archived, orders: open/closed/cancelled/any)"""
        self.params['status'] = value
        return self

    def vendor(self, value: str):
        """Filter products by vendor name"""
        self.params['vendor'] = value
        return self

    def product_type(self, value: str):
        """Filter products by type"""
        self.params['product_type'] = value
        return self

    def collection_id(self, value: int):
        """Filter products by collection ID"""
        self.params['collection_id'] = value
        return self

    def financial_status(self, value: str):
        """Filter orders by payment status (authorized, pending, paid, refunded, etc.)"""
        self.params['financial_status'] = value
        return self

    def fulfillment_status(self, value: str):
        """Filter orders by fulfillment status (shipped, partial, unshipped, any)"""
        self.params['fulfillment_status'] = value
        return self

    def created_after(self, date: str):
        """Filter by minimum creation date (ISO 8601 or YYYY-MM-DD)"""
        self.params['created_at_min'] = date
        return self

    def created_before(self, date: str):
        """Filter by maximum creation date (ISO 8601 or YYYY-MM-DD)"""
        self.params['created_at_max'] = date
        return self

    def updated_after(self, date: str):
        """Filter by minimum update date (ISO 8601 or YYYY-MM-DD)"""
        self.params['updated_at_min'] = date
        return self

    def fields(self, *field_names):
        """Select specific fields to return"""
        self.params['fields'] = ','.join(field_names)
        return self

    def since_id(self, value: int):
        """Return records after this ID (for pagination)"""
        self.params['since_id'] = value
        return self

    def limit(self, count: int):
        """Limit results (max 250)"""
        self._limit = min(count, 250)
        return self

    def build(self) -> Dict:
        """Build the query parameters"""
        result = {'limit': self._limit}
        result.update(self.params)
        return result

    def execute(self, api):
        """Execute the query with the given API instance"""
        params = self.build()
        limit = params.pop('limit', 50)

        if self.resource == 'products':
            return api.list_products(limit=limit, **params)
        elif self.resource == 'orders':
            return api.list_orders(limit=limit, **params)
        elif self.resource == 'customers':
            return api.list_customers(limit=limit, **params)
        else:
            raise ValueError(f"Unknown resource: {self.resource}")


class CommonQueries:
    """Pre-built query patterns for common Shopify operations"""

    @staticmethod
    def active_products(limit: int = 50) -> Dict:
        """Get all active products"""
        return {'status': 'active', 'limit': limit}

    @staticmethod
    def draft_products(limit: int = 50) -> Dict:
        """Get draft (unpublished) products"""
        return {'status': 'draft', 'limit': limit}

    @staticmethod
    def products_by_vendor(vendor: str, limit: int = 50) -> Dict:
        """Get products by vendor"""
        return {'vendor': vendor, 'status': 'active', 'limit': limit}

    @staticmethod
    def recent_orders(days: int = 7, status: str = 'any') -> Dict:
        """Get orders from the last N days"""
        date_threshold = (datetime.now() - timedelta(days=days)).isoformat()
        return {
            'status': status,
            'created_at_min': date_threshold,
            'limit': 250
        }

    @staticmethod
    def unfulfilled_orders(limit: int = 50) -> Dict:
        """Get open orders that haven't been fulfilled"""
        return {
            'status': 'open',
            'fulfillment_status': 'unfulfilled',
            'limit': limit
        }

    @staticmethod
    def pending_payment_orders(limit: int = 50) -> Dict:
        """Get orders with pending payment"""
        return {
            'status': 'open',
            'financial_status': 'pending',
            'limit': limit
        }

    @staticmethod
    def paid_unfulfilled_orders(limit: int = 50) -> Dict:
        """Get paid orders waiting to be shipped"""
        return {
            'status': 'open',
            'financial_status': 'paid',
            'fulfillment_status': 'unfulfilled',
            'limit': limit
        }

    @staticmethod
    def refunded_orders(days: int = 30) -> Dict:
        """Get refunded orders from last N days"""
        date_threshold = (datetime.now() - timedelta(days=days)).isoformat()
        return {
            'financial_status': 'refunded',
            'created_at_min': date_threshold,
            'limit': 250
        }

    @staticmethod
    def recent_customers(days: int = 30, limit: int = 50) -> Dict:
        """Get customers created in last N days"""
        date_threshold = (datetime.now() - timedelta(days=days)).isoformat()
        return {
            'created_at_min': date_threshold,
            'limit': limit
        }


class ProductPatterns:
    """Patterns for product-specific operations"""

    @staticmethod
    def low_inventory(api, threshold: int = 10) -> List[Dict]:
        """
        Find products with low inventory.

        Note: Requires fetching all products and checking variants.
        """
        products = api.list_products(status='active', limit=250)
        low_stock = []

        for product in products:
            for variant in product.get('variants', []):
                qty = variant.get('inventory_quantity', 0)
                if qty is not None and qty < threshold:
                    low_stock.append({
                        'product_id': product['id'],
                        'product_title': product['title'],
                        'variant_id': variant['id'],
                        'variant_title': variant.get('title', 'Default'),
                        'sku': variant.get('sku'),
                        'inventory_quantity': qty
                    })

        return low_stock

    @staticmethod
    def out_of_stock(api) -> List[Dict]:
        """Find products that are out of stock"""
        return ProductPatterns.low_inventory(api, threshold=1)


class OrderPatterns:
    """Patterns for order-specific operations"""

    @staticmethod
    def high_value_orders(api, min_amount: float = 500, status: str = 'any') -> List[Dict]:
        """Get orders above a certain value"""
        orders = api.list_orders(status=status, limit=250)
        return [o for o in orders if float(o.get('total_price', 0)) >= min_amount]

    @staticmethod
    def orders_by_date_range(api, start_date: str, end_date: str, status: str = 'any') -> List[Dict]:
        """Get orders within a date range"""
        return api.list_orders(
            status=status,
            created_at_min=start_date,
            created_at_max=end_date,
            limit=250
        )

    @staticmethod
    def calculate_revenue(api, days: int = 30) -> Dict:
        """Calculate revenue metrics for last N days"""
        date_threshold = (datetime.now() - timedelta(days=days)).isoformat()
        orders = api.list_orders(
            status='any',
            financial_status='paid',
            created_at_min=date_threshold,
            limit=250
        )

        total_revenue = sum(float(o.get('total_price', 0)) for o in orders)
        order_count = len(orders)
        avg_order_value = total_revenue / order_count if order_count > 0 else 0

        return {
            'period_days': days,
            'total_revenue': round(total_revenue, 2),
            'order_count': order_count,
            'average_order_value': round(avg_order_value, 2)
        }


# ============= USAGE EXAMPLES =============

def example_usage():
    """Examples of using query helpers"""
    from services.shopify.api import ShopifyAPI

    api = ShopifyAPI()

    # Using QueryBuilder
    query = (ShopifyQueryBuilder('products')
             .status('active')
             .vendor('Nike')
             .created_after('2024-01-01')
             .limit(20))
    products = query.execute(api)

    # Using CommonQueries
    params = CommonQueries.recent_orders(days=7)
    orders = api.list_orders(**params)

    # Using ProductPatterns
    low_stock = ProductPatterns.low_inventory(api, threshold=5)

    # Using OrderPatterns
    revenue = OrderPatterns.calculate_revenue(api, days=30)

    return products, orders, low_stock, revenue


if __name__ == "__main__":
    # Demo the query builder
    print("Query Builder Examples:")
    print("=" * 50)

    # Example 1: Active products
    q1 = ShopifyQueryBuilder('products').status('active').limit(10)
    print(f"Active products: {q1.build()}")

    # Example 2: Recent unfulfilled orders
    q2 = (ShopifyQueryBuilder('orders')
          .status('open')
          .fulfillment_status('unfulfilled')
          .financial_status('paid'))
    print(f"Unfulfilled orders: {q2.build()}")

    # Example 3: Products by vendor
    q3 = ShopifyQueryBuilder('products').vendor('Nike').fields('id', 'title', 'price')
    print(f"Nike products: {q3.build()}")

    print("\nCommon Query Patterns:")
    print("=" * 50)

    print(f"Active products: {CommonQueries.active_products()}")
    print(f"Recent orders: {CommonQueries.recent_orders(days=7)}")
    print(f"Unfulfilled orders: {CommonQueries.unfulfilled_orders()}")
    print(f"Pending payment: {CommonQueries.pending_payment_orders()}")
