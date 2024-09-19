# BrightData API Service

Web scraping and proxy services with zero-friction experience.

## 🚀 Quick Start

```python
from services.brightdata.api import BrightDataAPI

# Start with quick overview
api = BrightDataAPI()
api.quick_start()  # Shows everything in 5 seconds!

# Discover what's available
info = api.discover()  # All products and capabilities
info = api.discover('zones')  # Available proxy zones
info = api.discover('products')  # Available products
```

## Core Features

### 🌐 Web Project 3
- **Project 3 Browser**: Full browser automation
- **Web Unlocker**: Bypass anti-bot measures
- **Simple HTTP scraping**: Fast page fetching

### 🔍 Search & SERP
- Google, Bing, DuckDuckGo search results
- Structured search data extraction
- Multi-engine aggregation

### 🌍 Proxy Services
- Residential proxies (195 countries)
- Datacenter proxies (98 countries)  
- ISP proxies
- Mobile proxies

## Usage Examples

### Basic Web Project 3

```python
# Simple page scrape
result = api.scrape_page('https://example.com')

# JavaScript-rendered page
result = api.scrape_browser('https://example.com', wait_for='body')

# With proxy rotation
result = api.proxy_request('https://example.com', country='US')
```

### Search Engine Project 3

```python
# Search Google
results = api.search('python tutorial', num_results=10)

# Search with specific engine
results = api.search('web scraping', engine='bing', num_results=5)
```

### Advanced Project 3 with Builder

```python
from services.brightdata.query_helpers import ScrapeBuilder

config = (ScrapeBuilder('https://example.com')
    .wait_for_selector('#content')
    .click('#load-more')
    .scroll_to('#footer')
    .extract_text('h1', 'title')
    .with_proxy(country='US')
    .build())

result = api.scrape_browser(**config)
```

### Batch Operations

```python
from services.brightdata.query_helpers import BatchScraper

batch = BatchScraper(api)
urls = ['https://example1.com', 'https://example2.com']
results = batch.scrape_urls(urls, delay=1.0)
```

### Data Extraction

```python
from services.brightdata.query_helpers import DataExtractor

extractor = DataExtractor()
html = "<html>...</html>"

emails = extractor.extract_emails(html)
phones = extractor.extract_phone_numbers(html)
prices = extractor.extract_prices(html)
social = extractor.extract_social_links(html)
```

## Available Methods

### Core API Methods
- `discover(resource)` - Discover capabilities
- `quick_start()` - 5-second overview
- `test_connection()` - Verify credentials
- `scrape_page(url)` - Simple HTTP scraping
- `scrape_browser(url)` - Browser automation
- `proxy_request(url)` - Proxy scraping
- `search(query)` - Search engine scraping

### Query Helpers
- `ScrapeBuilder` - Build complex scraping configs
- `BatchScraper` - Handle batch operations
- `DataExtractor` - Extract structured data
- `ProxyRotator` - Manage proxy rotation
- `SearchAggregator` - Multi-engine search
- `CacheManager` - Cache scraped content

## Configuration

Set your API key in `.env`:
```bash
BRIGHTDATA_API_KEY=your-api-key-here
```

Optional settings:
```bash
BRIGHTDATA_CUSTOMER_ID=your-customer-id
BRIGHTDATA_ZONE=your-zone
BRIGHTDATA_PASSWORD=your-password
```

## Token Usage

- Service documentation: ~500 tokens
- Minimal overhead compared to 90,000 tokens from MCP servers
- Load only what you need

## Error Handling

```python
# Always check connection first
if not api.test_connection():
    print("Check your API key in .env")
    return

# Handle scraping errors
try:
    result = api.scrape_page(url)
    if result['success']:
        print(f"Scraped: {len(result['html'])} chars")
    else:
        print(f"Failed: {result.get('error')}")
except Exception as e:
    print(f"Error: {e}")
```

## Best Practices

1. **Start with discovery**: Use `discover()` to see available capabilities
2. **Use builders for complex scraping**: ScrapeBuilder for multi-step operations
3. **Implement rate limiting**: Add delays between requests
4. **Cache when possible**: Use CacheManager to avoid redundant API calls
5. **Handle failures gracefully**: Implement retry logic for critical scrapes

## Marketplace Datasets

Access and filter BrightData's marketplace datasets programmatically.

### Quick Start
```python
from services.brightdata.api import BrightDataAPI
from services.brightdata.chain_lists import get_exclusion_list

api = BrightDataAPI()

# Filter Google Maps for independent beauty/gun stores
filters = {
    'country': 'United States',
    'category': {'$regex': 'beauty|gun'},
    'name': {'$nin': get_exclusion_list('all')},
    'review_count': {'$lt': 500}
}

result = api.filter_marketplace_dataset(
    dataset_id='gd_lw8kc4s7r2',  # Google Maps
    filters=filters,
    limit=100,
    sample=True
)

print(f"Found {result['count']} independent businesses")
```

### Available Datasets
- Google Maps: `gd_lw8kc4s7r2`
- Google Search: `gd_l7q7zkf5kq7vz7164`
- LinkedIn Companies: `gd_l3q4sjf9p5ld7zj72`
- Amazon Products: `gd_l1g5kqf3j4h2k8j92`

### Filter Operators
- `$eq`: Equals
- `$ne`: Not equals
- `$in`: In array
- `$nin`: Not in array
- `$regex`: Regex match
- `$gt`, `$gte`, `$lt`, `$lte`: Comparison
- `$exists`: Field exists

### CLI Commands
```bash
# List marketplace datasets
python services/brightdata/api.py datasets

# Quick filter for beauty stores (excludes chains)
python services/brightdata/api.py filter beauty

# Quick filter for gun stores (excludes chains)
python services/brightdata/api.py filter gun
```

### Examples
```bash
# Run marketplace examples
python services/brightdata/examples.py marketplace

# Run smart filtering example
python services/brightdata/examples.py smart_filter
```

### Cost Considerations
- Sampling is free/cheap - use `sample=True` for testing
- Full dataset downloads incur costs - use specific filters to minimize data
- Check your BrightData account for specific pricing

## Common Patterns

### E-commerce Project 3
```python
# Collect Amazon products
asins = ['B08N5WRWNW', 'B07VYZJDVM']
products = api.collect_amazon_products(asins)
```

### Social Media Collection
```python
# Collect social posts
urls = ['https://twitter.com/...', 'https://instagram.com/...']
posts = api.collect_social_posts(urls)
```

### Cost Estimation
```python
# Estimate costs before scraping
cost = api.estimate_cost(requests=1000, product='web_unlocker')
print(f"Estimated cost: ${cost:.2f}")
```

## Support

For more examples, see:
- `examples.py` - Complete usage examples
- `query_helpers.py` - Helper utilities
- `api.py` - Core API implementation