#!/usr/bin/env python3
"""
BrightData API Examples
Practical examples for web scraping and data collection
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.brightdata.api import BrightDataAPI
from services.brightdata.query_helpers import (
    ScrapeBuilder,
    BatchScraper,
    DataExtractor,
    ProxyRotator,
    SearchAggregator,
    CacheManager
)

def basic_usage():
    """Basic BrightData API usage"""
    print("\n=== Basic BrightData Usage ===\n")
    
    api = BrightDataAPI()
    
    # Quick start shows everything
    api.quick_start()
    
    # Basic page scrape
    print("\n📄 Project 3 example.com:")
    result = api.scrape_page('https://example.com')
    
    if result['success']:
        print(f"  ✅ Success!")
        print(f"  HTML length: {len(result['html'])} characters")
        print(f"  Status code: {result['status_code']}")
    else:
        print(f"  ❌ Failed: {result.get('error')}")


def discovery_examples():
    """Discovery pattern examples"""
    print("\n=== Discovery Examples ===\n")
    
    api = BrightDataAPI()
    
    # Discover everything
    print("🔍 Platform Overview:")
    overview = api.discover()
    
    if overview['success']:
        print(f"  Configuration:")
        for key, value in overview.get('configured', {}).items():
            print(f"    - {key}: {value}")
        
        print(f"\n  Products:")
        for product, desc in overview.get('products_summary', {}).items():
            print(f"    - {product}: {desc}")
    
    # Discover zones
    print("\n🌍 Zones Discovery:")
    zones = api.discover('zones')
    
    if zones.get('zones'):
        for zone in zones['zones']:
            print(f"  - {zone.get('name')} ({zone.get('type')})")
    
    # Discover products
    print("\n🛠️ Products Discovery:")
    products = api.discover('products')
    
    if products.get('products'):
        for product in products['products']:
            configured = "✓ Configured" if product.get('configured') else ""
            print(f"  - {product['name']}: {product['description']} {configured}")


def scraping_examples():
    """Web scraping examples"""
    print("\n=== Project 3 Examples ===\n")
    
    api = BrightDataAPI()
    
    # Simple scrape
    print("📄 Simple page scrape:")
    result = api.scrape_page('https://httpbin.org/html')
    
    if result['success']:
        print(f"  ✅ Scraped successfully")
        print(f"  HTML preview: {result['html'][:200]}...")
    
    # JavaScript-rendered page
    print("\n🌐 JavaScript page scrape:")
    js_result = api.scrape_browser(
        'https://example.com',
        wait_for='body',
        timeout=15
    )
    
    if js_result['success']:
        print(f"  ✅ Scraped with browser")
        print(f"  HTML length: {len(js_result.get('html', ''))}")
        if js_result.get('cookies'):
            print(f"  Cookies collected: {len(js_result['cookies'])}")
    
    # Using ScrapeBuilder for complex scenarios
    print("\n🔧 Complex scrape with ScrapeBuilder:")
    
    builder = (ScrapeBuilder('https://example.com')
        .wait_for_selector('#content', timeout=5000)
        .click('#load-more')
        .wait(2000)
        .scroll_to('#footer')
        .screenshot(full_page=True)
        .extract_text('h1', 'title')
        .extract_attribute('meta[name="description"]', 'content', 'description')
        .with_proxy(country='US')
        .build())
    
    print(f"  Configuration built:")
    print(f"    - URL: {builder['url']}")
    print(f"    - Actions: {len(builder['actions'])} actions")
    print(f"    - Extractions: {len(builder['extract'])} fields")
    print(f"    - Screenshot: {builder.get('screenshot', False)}")


def batch_scraping():
    """Batch scraping examples"""
    print("\n=== Batch Project 3 ===\n")
    
    api = BrightDataAPI()
    batch_scraper = BatchScraper(api)
    
    # List of URLs to scrape
    urls = [
        'https://httpbin.org/html',
        'https://httpbin.org/status/200',
        'https://httpbin.org/delay/1'
    ]
    
    print(f"📦 Batch scraping {len(urls)} URLs:")
    results = batch_scraper.scrape_urls(urls, delay=0.5, max_retries=2)
    
    print(f"  ✅ Successful: {len(results['success'])}")
    print(f"  ❌ Failed: {len(results['failed'])}")
    
    for success in results['success']:
        print(f"    - {success['url']}: {len(success['html'])} chars")
    
    for failed in results['failed']:
        print(f"    - {failed['url']}: {failed['error']}")


def data_extraction():
    """Data extraction from scraped content"""
    print("\n=== Data Extraction ===\n")
    
    api = BrightDataAPI()
    extractor = DataExtractor()
    
    # Sample HTML with various data
    sample_html = """
    <html>
        <body>
            <h1>Contact Us</h1>
            <p>Email: contact@example.com or sales@example.com</p>
            <p>Phone: (555) 123-4567 or +1-555-987-6543</p>
            <p>Price: $29.99, Sale: $19.99</p>
            <a href="https://facebook.com/example">Facebook</a>
            <a href="https://twitter.com/example">Twitter</a>
            <script type="application/ld+json">
            {"@type": "Organization", "name": "Example Corp"}
            </script>
        </body>
    </html>
    """
    
    print("📊 Extracting data from HTML:")
    
    # Extract emails
    emails = extractor.extract_emails(sample_html)
    print(f"  📧 Emails found: {emails}")
    
    # Extract phone numbers
    phones = extractor.extract_phone_numbers(sample_html)
    print(f"  📞 Phones found: {phones}")
    
    # Extract prices
    prices = extractor.extract_prices(sample_html)
    print(f"  💰 Prices found: ${prices}")
    
    # Extract social links
    social = extractor.extract_social_links(sample_html)
    print(f"  🔗 Social links:")
    for platform, links in social.items():
        print(f"     - {platform}: {links[0] if links else 'None'}")
    
    # Extract structured data
    structured = extractor.extract_structured_data(sample_html)
    if structured['found']:
        print(f"  📋 Structured data found: {len(structured['data'])} items")


def search_examples():
    """Search engine scraping examples"""
    print("\n=== Search Examples ===\n")
    
    api = BrightDataAPI()
    aggregator = SearchAggregator(api)
    
    # Basic search
    print("🔍 Search for 'web scraping':")
    results = api.search('web scraping', num_results=5)
    
    for i, result in enumerate(results, 1):
        print(f"  {i}. {result['title']}")
        print(f"     {result['url']}")
    
    # Multi-engine search (commented out to avoid multiple API calls)
    print("\n🔍 Multi-engine search example:")
    print("  # Uncomment to run:")
    print("  # results = aggregator.multi_engine_search('python tutorial', num_results=5)")
    print("  # print(f'Total unique results: {results[\"total_unique\"]}')")
    print("  # for r in results['aggregated'][:3]:")
    print("  #     print(f'{r[\"title\"]} (found on {len(r[\"engines\"])} engines)')")


def proxy_examples():
    """Proxy rotation examples"""
    print("\n=== Proxy Examples ===\n")
    
    api = BrightDataAPI()
    rotator = ProxyRotator(api)
    
    # Test proxy availability
    print("🌐 Testing proxy countries:")
    proxy_status = rotator.test_proxies()
    
    for country, available in proxy_status.items():
        status = "✅" if available else "❌"
        print(f"  {status} {country}")
    
    # Scrape with rotation
    print("\n🔄 Project 3 with country rotation:")
    result = rotator.scrape_with_rotation('https://httpbin.org/ip')
    
    if result:
        print(f"  ✅ Success with {result.get('proxy_country', 'unknown')} proxy")
    else:
        print(f"  ❌ All proxies failed")


def caching_examples():
    """Caching examples for efficiency"""
    print("\n=== Caching Examples ===\n")
    
    api = BrightDataAPI()
    cache = CacheManager()
    
    url = 'https://httpbin.org/uuid'
    
    # First request - not cached
    print("📦 First request (not cached):")
    cached = cache.get(url)
    
    if not cached:
        print("  Cache miss - scraping...")
        result = api.scrape_page(url)
        if result['success']:
            cache.set(url, result)
            print("  ✅ Scraped and cached")
    else:
        print("  ✅ Cache hit!")
        result = cached
    
    # Second request - should be cached
    print("\n📦 Second request (should be cached):")
    cached = cache.get(url, max_age=60)
    
    if cached:
        print("  ✅ Cache hit! No API call needed")
        print(f"  Cached at: {cached.get('cached_at')}")
    else:
        print("  Cache miss or expired")
    
    # Clear old cache
    print("\n🗑️ Clearing expired cache:")
    cleared = cache.clear_expired(max_age=1)
    print(f"  Cleared {cleared} expired entries")


def advanced_patterns():
    """Advanced usage patterns"""
    print("\n=== Advanced Patterns ===\n")
    
    api = BrightDataAPI()
    
    # Cost estimation
    print("💰 Cost Estimation:")
    
    products = ['web_unlocker', 'scraping_browser', 'residential', 'serp']
    requests = 1000
    
    for product in products:
        cost = api.estimate_cost(requests, product)
        print(f"  {product}: ${cost:.2f} for {requests} requests")
    
    # Usage stats (if available)
    print("\n📊 Usage Statistics:")
    stats = api.get_usage_stats()
    
    if stats['success']:
        print(f"  Stats: {stats.get('stats', 'No data available')}")
    else:
        print(f"  Could not retrieve stats: {stats.get('error')}")
    
    # E-commerce data collection
    print("\n🛍️ E-commerce Data Collection:")
    
    # Example ASINs (Amazon product IDs)
    asins = ['B08N5WRWNW', 'B07VYZJDVM']
    
    print(f"  Collecting data for {len(asins)} products:")
    products = api.collect_amazon_products(asins)
    
    for product in products:
        if product.get('scraped'):
            print(f"    ✅ {product['asin']}: {product['html_length']} chars")
        else:
            print(f"    ❌ {product['asin']}: {product.get('error')}")
    
    # Social media collection
    print("\n📱 Social Media Collection:")
    
    social_urls = [
        'https://twitter.com/elonmusk/status/123456789',
        'https://www.instagram.com/p/ABC123/'
    ]
    
    print(f"  Collecting {len(social_urls)} social posts:")
    posts = api.collect_social_posts(social_urls)
    
    for post in posts:
        status = "✅" if post['success'] else "❌"
        print(f"    {status} {post['platform']}: {post['url']}")


def marketplace_dataset_examples():
    """Marketplace dataset filtering examples"""
    print("\n=== Marketplace Dataset Examples ===\n")

    api = BrightDataAPI()

    # Import chain lists
    from services.brightdata.chain_lists import get_exclusion_list

    # 1. List available datasets
    print("📊 Available Datasets:")
    datasets = api.get_dataset_list()
    if datasets['success']:
        for dataset in datasets.get('datasets', [])[:5]:
            print(f"  - {dataset.get('name')}: {dataset.get('id')}")

    # 2. Get Google Maps dataset metadata
    print("\n🗺️ Google Maps Dataset Schema:")
    metadata = api.get_dataset_metadata('gd_lw8kc4s7r2')
    if metadata['success']:
        fields = metadata.get('metadata', {}).get('fields', [])
        print(f"  Available fields: {', '.join(fields[:10])}")

    # 3. Filter beauty and gun stores (excluding chains)
    print("\n🔍 Filtering Beauty & Gun Stores (Independent Only):")

    filters = {
        'country': 'United States',
        'category': {'$regex': 'beauty|gun|firearm|salon|cosmetic'},
        'name': {'$nin': get_exclusion_list('all')},
        'review_count': {'$lt': 500}  # Chains typically have more reviews
    }

    # Get sample data first
    sample_result = api.filter_marketplace_dataset(
        dataset_id='gd_lw8kc4s7r2',
        filters=filters,
        limit=10,
        sample=True
    )

    if sample_result['success']:
        print(f"  ✅ Found {sample_result['count']} matching locations")
        print(f"  📍 Sample results:")
        for location in sample_result.get('data', [])[:5]:
            name = location.get('name', 'Unknown')
            category = location.get('category', 'Unknown')
            city = location.get('city', 'Unknown')
            print(f"    - {name} ({category}) in {city}")

    # 4. Create full dataset snapshot
    print("\n💾 Creating Full Dataset Snapshot:")

    full_result = api.filter_marketplace_dataset(
        dataset_id='gd_lw8kc4s7r2',
        filters=filters,
        sample=False  # This creates a snapshot for download
    )

    if full_result['success']:
        snapshot_id = full_result.get('snapshot_id')
        print(f"  ✅ Snapshot created: {snapshot_id}")
        print(f"  📊 Status: {full_result.get('status')}")
        print(f"  💡 Use api.get_snapshot_status('{snapshot_id}') to check progress")


def smart_filtering_example():
    """Advanced filtering with business logic"""
    print("\n=== Smart Filtering Example ===\n")

    from services.brightdata.chain_lists import BEAUTY_CHAINS, GUN_CHAINS

    api = BrightDataAPI()

    # Multi-stage filtering approach
    print("🎯 Multi-Stage Filtering Strategy:\n")

    # Stage 1: Basic filtering
    print("Stage 1: Apply basic filters")
    basic_filters = {
        'country': 'United States',
        'state': {'$in': ['Texas', 'California', 'Florida', 'New York']},
        'category': {'$regex': 'beauty|salon|cosmetic|gun|firearm|sporting'}
    }

    # Stage 2: Exclude known chains
    print("Stage 2: Exclude known chains")
    basic_filters['name'] = {
        '$nin': BEAUTY_CHAINS + GUN_CHAINS,
        '$not': {'$regex': '(#\\d+|store \\d+|location \\d+)'}  # Store numbers
    }

    # Stage 3: Business indicators
    print("Stage 3: Filter by business indicators")
    basic_filters.update({
        'review_count': {'$gte': 10, '$lte': 500},  # Active but not massive chains
        'rating': {'$gte': 3.5},  # Quality businesses
        'price_range': {'$in': ['$', '$$', '$$$']},  # Not luxury/exclusive
        'permanently_closed': False
    })

    # Test the filters
    result = api.filter_marketplace_dataset(
        dataset_id='gd_lw8kc4s7r2',
        filters=basic_filters,
        limit=100,
        sample=True
    )

    if result['success']:
        print(f"\n✅ Filtering Results:")
        print(f"  Total matches: {result.get('count', 0)}")

        # Analyze the sample
        data = result.get('data', [])
        categories = {}
        states = {}

        for item in data:
            cat = item.get('category', 'Unknown')
            state = item.get('state', 'Unknown')
            categories[cat] = categories.get(cat, 0) + 1
            states[state] = states.get(state, 0) + 1

        print(f"\n  Category Distribution:")
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"    - {cat}: {count}")

        print(f"\n  State Distribution:")
        for state, count in sorted(states.items(), key=lambda x: x[1], reverse=True):
            print(f"    - {state}: {count}")


def main():
    """Run all examples"""
    import sys

    if len(sys.argv) > 1:
        example = sys.argv[1]

        examples = {
            'basic': basic_usage,
            'discover': discovery_examples,
            'scrape': scraping_examples,
            'batch': batch_scraping,
            'extract': data_extraction,
            'search': search_examples,
            'proxy': proxy_examples,
            'cache': caching_examples,
            'advanced': advanced_patterns,
            'marketplace': marketplace_dataset_examples,
            'smart_filter': smart_filtering_example
        }
        
        if example in examples:
            examples[example]()
        else:
            print(f"Unknown example: {example}")
            print(f"Available: {', '.join(examples.keys())}")
    else:
        # Run basic example by default
        print("BrightData API Examples")
        print("=" * 50)
        print("\nUsage: python examples.py [example]")
        print("Examples: basic, discover, scrape, batch, extract, search, proxy, cache, advanced, marketplace, smart_filter")
        print("\nRunning basic example...\n")
        
        basic_usage()
        
        print("\n" + "=" * 50)
        print("Run other examples:")
        print("  python examples.py discover")
        print("  python examples.py scrape")
        print("  python examples.py extract")


if __name__ == "__main__":
    main()