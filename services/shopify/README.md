# Shopify API Service

Token Cost: ~600 tokens

E-commerce operations for Shopify stores via REST Admin API (2024-01).

## Quick Start

```python
from api_toolkit.services.shopify.api import ShopifyAPI

api = ShopifyAPI()
api.quick_start()  # Shows store info, counts, examples

# List products
products = api.list_products(status='active', limit=50)

# Get recent orders
orders = api.list_orders(status='open', limit=20)

# Search customers
customers = api.search_customers('john@example.com')
```

## Authentication

Set these environment variables in `.env`:

```bash
SHOPIFY_STORE_DOMAIN=mystore.myshopify.com
SHOPIFY_ACCESS_TOKEN=shpat_xxxxxxxxxxxxx
```

## Available Operations

### Products
| Method | Description |
|--------|-------------|
| `list_products(limit, status, vendor, ...)` | List with filters |
| `get_product(product_id)` | Get single product |
| `create_product(data)` | Create product |
| `update_product(product_id, data)` | Update product |
| `delete_product(product_id)` | Delete product |
| `count_products(status, vendor)` | Get count |

### Orders
| Method | Description |
|--------|-------------|
| `list_orders(limit, status, financial_status, ...)` | List with filters |
| `get_order(order_id)` | Get single order |
| `cancel_order(order_id, reason)` | Cancel order |
| `close_order(order_id)` | Close order |
| `count_orders(status)` | Get count |

### Customers
| Method | Description |
|--------|-------------|
| `list_customers(limit)` | List customers |
| `get_customer(customer_id)` | Get single customer |
| `search_customers(query)` | Search by email/name |
| `get_customer_orders(customer_id)` | Get customer's orders |
| `count_customers()` | Get count |

### Shop
| Method | Description |
|--------|-------------|
| `get_shop()` | Get store info |
| `test_connection()` | Verify connection |

## Filter Reference

### Product Filters
- `status`: active, draft, archived
- `vendor`: Filter by vendor name
- `product_type`: Filter by type
- `collection_id`: Filter by collection
- `created_at_min/max`: Date range (ISO 8601)

### Order Filters
- `status`: open, closed, cancelled, any
- `financial_status`: authorized, pending, paid, partially_paid, refunded, voided
- `fulfillment_status`: shipped, partial, unshipped, any, unfulfilled
- `created_at_min/max`: Date range (ISO 8601)

### Customer Filters
- `created_at_min/max`: Date range
- `updated_at_min`: Updated since date

## Query Builder

```python
from api_toolkit.services.shopify.query_helpers import ShopifyQueryBuilder

# Build complex queries fluently
query = (ShopifyQueryBuilder('products')
         .status('active')
         .vendor('Nike')
         .created_after('2024-01-01')
         .limit(50))
products = query.execute(api)

# Orders query
query = (ShopifyQueryBuilder('orders')
         .status('open')
         .financial_status('paid')
         .fulfillment_status('unfulfilled'))
orders = query.execute(api)
```

## Common Patterns

```python
from api_toolkit.services.shopify.query_helpers import CommonQueries, ProductPatterns, OrderPatterns

# Get recent orders
params = CommonQueries.recent_orders(days=7)
orders = api.list_orders(**params)

# Get unfulfilled orders
params = CommonQueries.unfulfilled_orders()
orders = api.list_orders(**params)

# Check low inventory
low_stock = ProductPatterns.low_inventory(api, threshold=10)

# Calculate revenue
revenue = OrderPatterns.calculate_revenue(api, days=30)
print(f"Revenue: ${revenue['total_revenue']}")
```

## CLI Usage

```bash
# Test connection
python services/shopify/api.py test

# Quick overview
python services/shopify/api.py quick_start

# Discover resources
python services/shopify/api.py discover

# List products/orders/customers
python services/shopify/api.py products 10
python services/shopify/api.py orders 10
python services/shopify/api.py customers 10

# Run examples
python services/shopify/examples.py products
python services/shopify/examples.py orders
python services/shopify/examples.py all
```

## Rate Limits

Shopify uses a leaky bucket algorithm:
- Bucket size: 40 requests
- Leak rate: 2 requests/second

The API automatically rate-limits to 2 requests/second to stay within limits.

## Troubleshooting

### 401 Unauthorized
- Check `SHOPIFY_ACCESS_TOKEN` is valid
- Ensure the token has the required scopes (read_products, read_orders, etc.)

### 404 Not Found
- Check `SHOPIFY_STORE_DOMAIN` is correct
- Verify the resource ID exists

### 429 Too Many Requests
- The API handles rate limiting automatically
- If you see this, wait a moment and retry

### Empty Results
- Check your filter values are correct
- Try `status='any'` for orders to include all statuses
- Use `discover()` to see available data
