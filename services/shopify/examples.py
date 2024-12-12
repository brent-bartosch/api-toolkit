#!/usr/bin/env python3
"""
Shopify API Examples
Demonstrates common e-commerce workflows using the Shopify API.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def basic_examples():
    """Basic setup and connection testing"""
    from services.shopify.api import ShopifyAPI

    print("\n" + "=" * 60)
    print("BASIC EXAMPLES")
    print("=" * 60)

    # Initialize API
    api = ShopifyAPI()

    # Test connection
    if api.test_connection():
        print("Connected successfully!")
    else:
        print("Connection failed!")
        return

    # Get shop info
    shop = api.get_shop()
    print(f"\nStore: {shop.get('name')}")
    print(f"Domain: {shop.get('domain')}")
    print(f"Email: {shop.get('email')}")
    print(f"Currency: {shop.get('currency')}")

    # Quick overview
    print(f"\nResource counts:")
    print(f"  Products: {api.count_products()}")
    print(f"  Orders: {api.count_orders(status='any')}")
    print(f"  Customers: {api.count_customers()}")


def product_examples():
    """Product listing and filtering examples"""
    from services.shopify.api import ShopifyAPI
    from services.shopify.query_helpers import ShopifyQueryBuilder, CommonQueries

    print("\n" + "=" * 60)
    print("PRODUCT EXAMPLES")
    print("=" * 60)

    api = ShopifyAPI()

    # List active products
    print("\n1. Active products (first 5):")
    products = api.list_products(status='active', limit=5)
    for p in products:
        price = p.get('variants', [{}])[0].get('price', 'N/A')
        print(f"  - {p.get('title')} - ${price}")

    # Using QueryBuilder
    print("\n2. Using QueryBuilder:")
    query = (ShopifyQueryBuilder('products')
             .status('active')
             .limit(3)
             .fields('id', 'title', 'vendor'))
    products = query.execute(api)
    for p in products:
        print(f"  - {p.get('title')} by {p.get('vendor', 'Unknown')}")

    # Get product count by status
    print("\n3. Product counts by status:")
    print(f"  Active: {api.count_products(status='active')}")
    print(f"  Draft: {api.count_products(status='draft')}")
    print(f"  Archived: {api.count_products(status='archived')}")

    # Get a single product (if any exist)
    if products:
        product_id = products[0]['id']
        print(f"\n4. Single product details (ID: {product_id}):")
        product = api.get_product(product_id)
        print(f"  Title: {product.get('title')}")
        print(f"  Vendor: {product.get('vendor')}")
        print(f"  Tags: {product.get('tags')}")
        print(f"  Variants: {len(product.get('variants', []))}")


def order_examples():
    """Order management examples"""
    from services.shopify.api import ShopifyAPI
    from services.shopify.query_helpers import ShopifyQueryBuilder, CommonQueries, OrderPatterns

    print("\n" + "=" * 60)
    print("ORDER EXAMPLES")
    print("=" * 60)

    api = ShopifyAPI()

    # List recent orders
    print("\n1. Recent orders (first 5):")
    orders = api.list_orders(status='any', limit=5)
    for o in orders:
        print(f"  Order #{o.get('order_number')} - ${o.get('total_price')} - {o.get('financial_status')}")

    # Get unfulfilled orders
    print("\n2. Unfulfilled orders:")
    unfulfilled = api.list_orders(status='open', fulfillment_status='unfulfilled', limit=5)
    if unfulfilled:
        for o in unfulfilled:
            print(f"  Order #{o.get('order_number')} - {o.get('fulfillment_status')}")
    else:
        print("  No unfulfilled orders found")

    # Order counts
    print("\n3. Order counts:")
    print(f"  Total: {api.count_orders(status='any')}")
    print(f"  Open: {api.count_orders(status='open')}")
    print(f"  Closed: {api.count_orders(status='closed')}")

    # Using CommonQueries
    print("\n4. Using CommonQueries - Recent 7 days:")
    params = CommonQueries.recent_orders(days=7)
    recent = api.list_orders(**params)
    print(f"  Found {len(recent)} orders in last 7 days")

    # Calculate revenue (if orders exist)
    if orders:
        print("\n5. Revenue metrics (last 30 days):")
        revenue = OrderPatterns.calculate_revenue(api, days=30)
        print(f"  Total Revenue: ${revenue['total_revenue']}")
        print(f"  Order Count: {revenue['order_count']}")
        print(f"  Avg Order Value: ${revenue['average_order_value']}")


def customer_examples():
    """Customer lookup and history examples"""
    from services.shopify.api import ShopifyAPI

    print("\n" + "=" * 60)
    print("CUSTOMER EXAMPLES")
    print("=" * 60)

    api = ShopifyAPI()

    # List customers
    print("\n1. Recent customers (first 5):")
    customers = api.list_customers(limit=5)
    for c in customers:
        name = f"{c.get('first_name', '')} {c.get('last_name', '')}".strip() or 'Unknown'
        print(f"  - {name} ({c.get('email', 'No email')})")

    # Customer count
    print(f"\n2. Total customers: {api.count_customers()}")

    # Search customers (example)
    if customers and customers[0].get('email'):
        email = customers[0]['email']
        print(f"\n3. Searching for customer: {email}")
        results = api.search_customers(email)
        if results:
            c = results[0]
            print(f"  Found: {c.get('first_name')} {c.get('last_name')}")
            print(f"  Orders count: {c.get('orders_count', 0)}")
            print(f"  Total spent: ${c.get('total_spent', '0.00')}")

    # Get customer orders
    if customers:
        customer_id = customers[0]['id']
        print(f"\n4. Orders for customer ID {customer_id}:")
        orders = api.get_customer_orders(customer_id, limit=3)
        if orders:
            for o in orders:
                print(f"  Order #{o.get('order_number')} - ${o.get('total_price')}")
        else:
            print("  No orders found for this customer")


def inventory_examples():
    """Inventory management examples"""
    from services.shopify.api import ShopifyAPI
    from services.shopify.query_helpers import ProductPatterns

    print("\n" + "=" * 60)
    print("INVENTORY EXAMPLES")
    print("=" * 60)

    api = ShopifyAPI()

    # Check for low inventory items
    print("\n1. Low inventory check (threshold: 10):")
    low_stock = ProductPatterns.low_inventory(api, threshold=10)
    if low_stock:
        print(f"  Found {len(low_stock)} low-stock items:")
        for item in low_stock[:5]:
            print(f"    - {item['product_title']} ({item['variant_title']}): {item['inventory_quantity']} left")
    else:
        print("  No low-stock items found")

    # Out of stock items
    print("\n2. Out of stock items:")
    out_of_stock = ProductPatterns.out_of_stock(api)
    if out_of_stock:
        print(f"  Found {len(out_of_stock)} out-of-stock items")
        for item in out_of_stock[:5]:
            print(f"    - {item['product_title']} ({item['variant_title']})")
    else:
        print("  No out-of-stock items found")


def discovery_examples():
    """Discovery and exploration examples"""
    from services.shopify.api import ShopifyAPI

    print("\n" + "=" * 60)
    print("DISCOVERY EXAMPLES")
    print("=" * 60)

    api = ShopifyAPI()

    # Quick start
    print("\n1. Quick Start:")
    api.quick_start()

    # Discover specific resource
    print("\n2. Discover products resource:")
    info = api.discover('products')
    if info.get('success'):
        print(f"  Count: {info['count']}")
        print(f"  Fields: {', '.join(info['fields'][:8])}...")

    # Explore interactively
    print("\n3. Explore store:")
    api.explore()


def run_all_examples():
    """Run all examples"""
    try:
        basic_examples()
        product_examples()
        order_examples()
        customer_examples()
        inventory_examples()
        # discovery_examples()  # Commented out as it's verbose
    except Exception as e:
        print(f"\nError running examples: {e}")
        print("Make sure SHOPIFY_STORE_DOMAIN and SHOPIFY_ACCESS_TOKEN are set in .env")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "basic":
            basic_examples()
        elif command == "products":
            product_examples()
        elif command == "orders":
            order_examples()
        elif command == "customers":
            customer_examples()
        elif command == "inventory":
            inventory_examples()
        elif command == "discovery":
            discovery_examples()
        elif command == "all":
            run_all_examples()
        else:
            print(f"Unknown command: {command}")
            print("Available: basic, products, orders, customers, inventory, discovery, all")
    else:
        print("Shopify API Examples")
        print("=" * 40)
        print("\nUsage: python examples.py [command]")
        print("\nCommands:")
        print("  basic      - Connection and setup")
        print("  products   - Product operations")
        print("  orders     - Order operations")
        print("  customers  - Customer operations")
        print("  inventory  - Inventory checks")
        print("  discovery  - Discovery methods")
        print("  all        - Run all examples")
        print("\nExample: python examples.py products")
