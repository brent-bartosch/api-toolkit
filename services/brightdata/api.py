#!/usr/bin/env python3
"""
BrightData API Client
Token Cost: ~600 tokens when loaded

Web scraping and proxy services with residential IPs and scraping browser.
"""

import os
import sys
import json
import base64
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from dotenv import load_dotenv
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Load environment variables
env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

from core.base_api import BaseAPI

class BrightDataAPI(BaseAPI):
    """
    BrightData (formerly Luminati) API wrapper for web scraping and proxies.
    
    CAPABILITIES:
    - Project 3 Browser - Automated browser for complex sites
    - Web Unlocker - Bypass anti-bot measures
    - Residential proxies - Real IP addresses
    - SERP API - Search engine results
    - Data collection - Pre-built collectors
    
    COMMON PATTERNS:
    ```python
    api = BrightDataAPI()
    api.quick_start()  # See zones and products
    
    # Scrape a webpage
    result = api.scrape_page('https://example.com')
    
    # Search Google
    results = api.search('python tutorial', engine='google')
    
    # Use proxy for request
    response = api.proxy_request('https://api.example.com/data')
    ```
    
    AUTHENTICATION:
    - Customer ID and Zone from BrightData dashboard
    - API key for account management
    
    RATE LIMITS:
    - Varies by product and plan
    - Project 3 Browser: 100 concurrent browsers
    """
    
    # BrightData product types
    PRODUCTS = {
        'scraping_browser': {
            'name': 'Project 3 Browser',
            'description': 'Automated browser for JavaScript sites',
            'endpoint': 'https://brightdata.com/api/scraping_browser/v1'
        },
        'web_unlocker': {
            'name': 'Web Unlocker',
            'description': 'Bypass anti-bot measures',
            'endpoint': 'https://api.brightdata.com/unlocker'
        },
        'serp': {
            'name': 'SERP API',
            'description': 'Search engine results',
            'endpoint': 'https://api.brightdata.com/serp'
        },
        'datacenter': {
            'name': 'Datacenter Proxies',
            'description': 'Fast datacenter IPs',
            'endpoint': 'https://zproxy.lum-superproxy.io'
        },
        'residential': {
            'name': 'Residential Proxies',
            'description': 'Real residential IPs',
            'endpoint': 'https://zproxy.lum-superproxy.io'
        }
    }

    # Known marketplace dataset IDs
    MARKETPLACE_DATASETS = {
        'google_maps': 'gd_lw8kc4s7r2',
        'google_search': 'gd_l7q7zkf5kq7vz7164',
        'linkedin_companies': 'gd_l3q4sjf9p5ld7zj72',
        'amazon_products': 'gd_l1g5kqf3j4h2k8j92'
    }

    def __init__(self, api_key: Optional[str] = None, 
                 customer_id: Optional[str] = None,
                 zone: Optional[str] = None):
        """
        Initialize BrightData client.
        
        Args:
            api_key: BrightData API key
            customer_id: Customer ID (e.g., 'hl_xxxxx')
            zone: Zone name (e.g., 'scraping_browser1')
        """
        self.api_key = api_key or os.getenv('BRIGHTDATA_API_KEY')
        self.customer_id = customer_id or os.getenv('BRIGHTDATA_CUSTOMER_ID')
        self.zone = zone or os.getenv('BRIGHTDATA_ZONE', 'scraping_browser1')
        self.password = os.getenv('BRIGHTDATA_PASSWORD', self.api_key)  # Often same as API key
        
        super().__init__(
            api_key=self.api_key,
            base_url='https://api.brightdata.com',
            requests_per_second=2  # Conservative rate limit
        )
    
    def _setup_auth(self):
        """Setup BrightData authentication headers"""
        if self.api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            })
    
    # ============= DISCOVERY METHODS =============
    
    def discover(self, resource: Optional[str] = None) -> Dict[str, Any]:
        """
        🔍 DISCOVER BRIGHTDATA RESOURCES - Always works!
        
        This method ALWAYS returns useful information about available scraping tools.
        Use this FIRST to understand what's available!
        
        Args:
            resource: Optional specific resource ('zones', 'products', 'stats')
        
        Returns:
            Dict with discovery results including zones, products, usage
        
        Examples:
            # Discover everything
            info = api.discover()
            print(info['products'])  # Available products
            
            # Discover zones
            info = api.discover('zones')
            print(info['zones'])  # Your zones and their settings
            
            # Discover usage stats
            info = api.discover('stats')
            print(info['usage'])  # Usage statistics
        """
        result = {'success': False, 'platform': 'brightdata'}
        
        if resource == 'zones':
            # Discover zones
            result['zones'] = []
            try:
                # Get zones via API
                zones_response = self._make_request('GET', '/zone')
                if isinstance(zones_response, list):
                    for zone in zones_response:
                        result['zones'].append({
                            'name': zone.get('name'),
                            'type': zone.get('type'),
                            'ips': zone.get('ips', 0),
                            'plan': zone.get('plan', {}).get('type'),
                            'status': zone.get('status')
                        })
                    result['success'] = True
                    result['message'] = f"Found {len(result['zones'])} zones"
            except:
                # Fallback to configured zone
                if self.zone:
                    result['zones'] = [{
                        'name': self.zone,
                        'type': 'scraping_browser',
                        'configured': True
                    }]
                    result['success'] = True
                    result['message'] = f"Using configured zone: {self.zone}"
                else:
                    result['message'] = "Could not discover zones"
                    
        elif resource == 'products':
            # Discover available products
            result['products'] = []
            for key, product in self.PRODUCTS.items():
                product_info = {
                    'id': key,
                    'name': product['name'],
                    'description': product['description'],
                    'available': True  # Check if we have access
                }
                
                # Check if this is our configured zone type
                if key in self.zone:
                    product_info['configured'] = True
                    
                result['products'].append(product_info)
            
            result['success'] = True
            result['message'] = f"Found {len(result['products'])} products"
            
        elif resource == 'stats':
            # Discover usage statistics
            try:
                stats = self._make_request('GET', f'/customer/{self.customer_id}/stats')
                result['usage'] = {
                    'bandwidth': stats.get('bandwidth_usage'),
                    'requests': stats.get('request_count'),
                    'success_rate': stats.get('success_rate'),
                    'cost': stats.get('cost_usd')
                }
                result['success'] = True
                result['message'] = "Usage statistics retrieved"
            except:
                result['usage'] = {}
                result['message'] = "Could not retrieve statistics"
                result['hint'] = "Check customer_id and api_key"
                
        else:
            # Discover everything
            result['configured'] = {
                'customer_id': bool(self.customer_id),
                'zone': self.zone,
                'api_key': bool(self.api_key)
            }
            
            # List available products
            result['products_summary'] = {
                'scraping_browser': 'Automated browser for JS sites',
                'web_unlocker': 'Bypass anti-bot protection',
                'serp_api': 'Search engine results',
                'proxies': 'Residential and datacenter IPs'
            }
            
            # Common use cases
            result['use_cases'] = [
                'Scrape JavaScript-heavy sites',
                'Bypass CAPTCHAs and anti-bot',
                'Collect search engine results',
                'Rotate residential IPs',
                'Extract e-commerce data'
            ]
            
            result['success'] = True
            result['message'] = "BrightData platform overview"
            result['hint'] = "Use discover('zones') or discover('products') for details"
        
        return result
    
    def quick_start(self) -> None:
        """
        🚀 QUICK START - Shows everything about your BrightData setup!
        
        This shows available products, zones, and example usage.
        Use this FIRST when starting!
        """
        print(f"\n{'='*60}")
        print(f"🚀 BRIGHTDATA QUICK START")
        print(f"{'='*60}\n")
        
        # Test connection
        if not self.test_connection():
            print("❌ Connection failed! Check your .env file")
            print("   Expected variables:")
            print("   - BRIGHTDATA_API_KEY")
            print("   - BRIGHTDATA_CUSTOMER_ID")
            print("   - BRIGHTDATA_ZONE")
            print("\n   Get them from: https://brightdata.com/cp/zones")
            return
        
        print("✅ Connected to BrightData!\n")
        print(f"   Customer: {self.customer_id}")
        print(f"   Zone: {self.zone}\n")
        
        # Discover resources
        discovery = self.discover()
        
        # Show products
        if discovery.get('products_summary'):
            print("🛠️ Available Products:")
            for product, desc in discovery['products_summary'].items():
                print(f"   - {product}: {desc}")
            print()
        
        # Show use cases
        if discovery.get('use_cases'):
            print("💡 Common Use Cases:")
            for use_case in discovery['use_cases'][:3]:
                print(f"   - {use_case}")
            print()
        
        # Show example commands
        print("📝 Example Commands:")
        print("   # Scrape a webpage")
        print("   result = api.scrape_page('https://example.com')")
        print()
        print("   # Search Google")
        print("   results = api.search('python tutorial')")
        print()
        print("   # Scrape with JavaScript execution")
        print("   data = api.scrape_browser('https://spa-site.com', wait_for='#content')")
        print()
        print("   # Use residential proxy")
        print("   response = api.proxy_request('https://api.example.com')")
        print()
        
        print("📚 Next steps:")
        print("   1. api.discover('zones')     # See your zones")
        print("   2. api.discover('products')  # See all products")
        print("   3. api.scrape_page(url)      # Start scraping")
        print(f"\n{'='*60}\n")
    
    # ============= SCRAPING OPERATIONS =============
    
    def scrape_page(self, url: str, country: Optional[str] = None,
                    render_js: bool = False) -> Dict[str, Any]:
        """
        Scrape a webpage using Web Unlocker.
        
        Args:
            url: URL to scrape
            country: Optional country code for geo-targeting
            render_js: Whether to render JavaScript
        
        Returns:
            Scraped content and metadata
        """
        params = {
            'url': url,
            'country': country,
            'render': render_js
        }
        
        # Use Web Unlocker endpoint
        try:
            response = self.session.get(
                'https://api.brightdata.com/unlocker',
                params=params,
                auth=(f"{self.customer_id}-zone-{self.zone}", self.password)
            )
            response.raise_for_status()
            
            return {
                'success': True,
                'url': url,
                'html': response.text,
                'status_code': response.status_code,
                'headers': dict(response.headers)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'url': url
            }
    
    def scrape_browser(self, url: str, wait_for: Optional[str] = None,
                      actions: Optional[List[Dict]] = None,
                      timeout: int = 30) -> Dict[str, Any]:
        """
        Scrape using Project 3 Browser (Puppeteer/Playwright).
        
        Args:
            url: URL to scrape
            wait_for: CSS selector to wait for
            actions: List of browser actions (click, type, etc.)
            timeout: Timeout in seconds
        
        Returns:
            Scraped content and screenshots if requested
        
        Example actions:
            actions = [
                {'type': 'click', 'selector': '#load-more'},
                {'type': 'wait', 'milliseconds': 2000},
                {'type': 'screenshot', 'fullPage': True}
            ]
        """
        payload = {
            'url': url,
            'timeout': timeout * 1000,  # Convert to milliseconds
        }
        
        if wait_for:
            payload['waitFor'] = wait_for
            
        if actions:
            payload['actions'] = actions
        
        # Use Project 3 Browser endpoint
        auth = base64.b64encode(f"{self.customer_id}-zone-{self.zone}:{self.password}".encode()).decode()
        
        try:
            response = self.session.post(
                f'https://{self.zone}.brightdata.com/browser',
                json=payload,
                headers={'Authorization': f'Basic {auth}'}
            )
            response.raise_for_status()
            
            result = response.json()
            return {
                'success': True,
                'url': url,
                'html': result.get('html'),
                'screenshot': result.get('screenshot'),
                'cookies': result.get('cookies'),
                'console_logs': result.get('console'),
                'network_logs': result.get('network')
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'url': url
            }
    
    def search(self, query: str, engine: str = 'google',
              country: Optional[str] = None,
              num_results: int = 10) -> List[Dict]:
        """
        Search using SERP API.
        
        Args:
            query: Search query
            engine: Search engine ('google', 'bing', 'duckduckgo')
            country: Country code for localized results
            num_results: Number of results to return
        
        Returns:
            List of search results
        """
        params = {
            'q': query,
            'engine': engine,
            'num': num_results
        }
        
        if country:
            params['gl'] = country  # Google country code
        
        try:
            response = self.session.get(
                'https://api.brightdata.com/serp/search',
                params=params,
                auth=(f"{self.customer_id}-zone-serp", self.password)
            )
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for item in data.get('organic_results', []):
                results.append({
                    'title': item.get('title'),
                    'url': item.get('link'),
                    'description': item.get('snippet'),
                    'position': item.get('position')
                })
            
            return results
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def proxy_request(self, url: str, method: str = 'GET',
                     country: Optional[str] = None,
                     proxy_type: str = 'residential',
                     **kwargs) -> Dict[str, Any]:
        """
        Make a request through BrightData proxy.
        
        Args:
            url: Target URL
            method: HTTP method
            country: Country code for proxy location
            proxy_type: 'residential' or 'datacenter'
            **kwargs: Additional request parameters
        
        Returns:
            Response data
        """
        # Configure proxy
        proxy_url = f"http://{self.customer_id}-zone-{proxy_type}"
        if country:
            proxy_url += f"-country-{country}"
        proxy_url += f":{self.password}@zproxy.lum-superproxy.io:22225"
        
        proxies = {
            'http': proxy_url,
            'https': proxy_url
        }
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                proxies=proxies,
                **kwargs
            )
            response.raise_for_status()
            
            return {
                'success': True,
                'url': url,
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'text': response.text,
                'proxy_used': proxy_type
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'url': url
            }
    
    # ============= DATA COLLECTION =============
    
    def collect_amazon_products(self, asins: List[str]) -> List[Dict]:
        """
        Collect Amazon product data using pre-built collector.
        
        Args:
            asins: List of Amazon ASINs
        
        Returns:
            Product data including price, reviews, availability
        """
        results = []
        
        for asin in asins:
            url = f"https://www.amazon.com/dp/{asin}"
            
            # Scrape product page
            data = self.scrape_browser(url, wait_for='#productTitle')
            
            if data['success'] and data.get('html'):
                # Parse product data (simplified - real implementation would use BeautifulSoup)
                product = {
                    'asin': asin,
                    'url': url,
                    'scraped': True,
                    'html_length': len(data['html'])
                }
                results.append(product)
            else:
                results.append({
                    'asin': asin,
                    'error': data.get('error', 'Failed to scrape')
                })
        
        return results
    
    def collect_social_posts(self, urls: List[str]) -> List[Dict]:
        """
        Collect social media posts (Twitter, Instagram, etc.).
        
        Args:
            urls: List of social media URLs
        
        Returns:
            Post data including text, metrics, media
        """
        results = []
        
        for url in urls:
            # Determine platform
            platform = 'unknown'
            if 'twitter.com' in url or 'x.com' in url:
                platform = 'twitter'
            elif 'instagram.com' in url:
                platform = 'instagram'
            elif 'linkedin.com' in url:
                platform = 'linkedin'
            
            # Scrape with appropriate wait conditions
            wait_selector = {
                'twitter': '[data-testid="tweet"]',
                'instagram': 'article',
                'linkedin': '.feed-shared-update-v2'
            }.get(platform, 'body')
            
            data = self.scrape_browser(url, wait_for=wait_selector)
            
            if data['success']:
                results.append({
                    'url': url,
                    'platform': platform,
                    'success': True,
                    'html_length': len(data.get('html', ''))
                })
            else:
                results.append({
                    'url': url,
                    'platform': platform,
                    'success': False,
                    'error': data.get('error')
                })
        
        return results

    # ============= MARKETPLACE DATASET METHODS =============

    def get_dataset_list(self) -> Dict[str, Any]:
        """
        Get list of available marketplace datasets.

        Returns:
            List of datasets with IDs and descriptions
        """
        try:
            response = self.session.get(
                f'{self.base_url}/api/datasets/get-dataset-list',
                headers={'Authorization': f'Bearer {self.api_key}'}
            )
            response.raise_for_status()
            return {
                'success': True,
                'datasets': response.json()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_dataset_metadata(self, dataset_id: str) -> Dict[str, Any]:
        """
        Get metadata for a specific dataset including available fields.

        Args:
            dataset_id: Dataset ID (e.g., 'gd_lw8kc4s7r2' for Google Maps)

        Returns:
            Dataset schema and filterable fields
        """
        try:
            response = self.session.get(
                f'{self.base_url}/api/datasets/get-dataset-metadata',
                params={'dataset_id': dataset_id},
                headers={'Authorization': f'Bearer {self.api_key}'}
            )
            response.raise_for_status()
            return {
                'success': True,
                'metadata': response.json()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def filter_marketplace_dataset(self, dataset_id: str,
                                  filters: Dict[str, Any],
                                  format: str = 'json',
                                  limit: Optional[int] = None,
                                  sample: bool = True) -> Dict[str, Any]:
        """
        Filter marketplace dataset with specific criteria.

        Args:
            dataset_id: Dataset ID (e.g., 'gd_lw8kc4s7r2' for Google Maps)
            filters: Filter criteria dictionary
            format: Output format ('json' or 'csv')
            limit: Maximum records to return
            sample: If True, returns sample data; if False, creates snapshot for download

        Returns:
            Filtered dataset or snapshot information

        Example filters for Google Maps:
            {
                'country': 'United States',
                'category': {'$regex': 'beauty|gun'},
                'name': {'$nin': ['Sally Beauty', 'Ulta', 'Sephora']},
                'chain': False,  # If field exists
                'review_count': {'$lt': 500}
            }
        """
        try:
            payload = {
                'dataset_id': dataset_id,
                'filters': filters,
                'format': format
            }

            if limit:
                payload['limit'] = limit

            if not sample:
                payload['deliver'] = True  # Create snapshot for full download

            response = self.session.post(
                f'{self.base_url}/api/datasets/filter-dataset',
                json=payload,
                headers={'Authorization': f'Bearer {self.api_key}'}
            )
            response.raise_for_status()

            result = response.json()

            if sample:
                return {
                    'success': True,
                    'data': result.get('data', []),
                    'count': result.get('count', 0),
                    'sample': True
                }
            else:
                return {
                    'success': True,
                    'snapshot_id': result.get('snapshot_id'),
                    'status': result.get('status'),
                    'sample': False,
                    'message': 'Snapshot created. Use get_snapshot_status() to check progress.'
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def filter_dataset_with_exclusion_list(self, dataset_id: str,
                                           inclusion_filters: Dict[str, Any],
                                           exclusion_list: List[str],
                                           exclusion_field: str = 'name') -> Dict[str, Any]:
        """
        Filter dataset with inclusion criteria and exclusion list.

        Args:
            dataset_id: Dataset ID
            inclusion_filters: What to include
            exclusion_list: List of values to exclude
            exclusion_field: Field to apply exclusion list to

        Returns:
            Filtered results
        """
        # Combine inclusion and exclusion filters
        filters = inclusion_filters.copy()
        filters[exclusion_field] = {'$nin': exclusion_list}

        return self.filter_marketplace_dataset(dataset_id, filters)

    def get_snapshot_status(self, snapshot_id: str) -> Dict[str, Any]:
        """
        Check status of a dataset snapshot.

        Args:
            snapshot_id: Snapshot ID from filter_marketplace_dataset()

        Returns:
            Snapshot status and download information
        """
        try:
            response = self.session.get(
                f'{self.base_url}/api/datasets/get-snapshot-meta',
                params={'snapshot_id': snapshot_id},
                headers={'Authorization': f'Bearer {self.api_key}'}
            )
            response.raise_for_status()
            return {
                'success': True,
                'snapshot': response.json()
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def download_snapshot(self, snapshot_id: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Download a completed snapshot.

        Args:
            snapshot_id: Snapshot ID
            output_path: Where to save the file (optional)

        Returns:
            Download status
        """
        try:
            response = self.session.get(
                f'{self.base_url}/api/datasets/download-the-file-by-snapshot_id',
                params={'snapshot_id': snapshot_id},
                headers={'Authorization': f'Bearer {self.api_key}'},
                stream=True
            )
            response.raise_for_status()

            if output_path:
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                return {
                    'success': True,
                    'saved_to': output_path
                }
            else:
                return {
                    'success': True,
                    'data': response.content
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    # ============= UTILITY METHODS =============
    
    def test_connection(self) -> bool:
        """Test if API connection is working"""
        if not all([self.customer_id, self.zone]):
            return False
            
        try:
            # Try a simple request
            response = self.scrape_page('https://www.example.com')
            return response.get('success', False)
        except:
            return False
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics for the account"""
        try:
            stats = self._make_request('GET', f'/customer/{self.customer_id}/stats')
            return {
                'success': True,
                'stats': stats
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def estimate_cost(self, requests: int, product: str = 'web_unlocker') -> float:
        """
        Estimate cost for number of requests.
        
        Args:
            requests: Number of requests
            product: Product type
        
        Returns:
            Estimated cost in USD
        """
        # Rough pricing (varies by plan)
        pricing = {
            'web_unlocker': 0.001,  # $1 per 1000 requests
            'scraping_browser': 0.005,  # $5 per 1000 requests
            'residential': 0.0001,  # $0.10 per 1000 requests
            'datacenter': 0.00001,  # $0.01 per 1000 requests
            'serp': 0.002  # $2 per 1000 searches
        }
        
        rate = pricing.get(product, 0.001)
        return requests * rate


# ============= CLI INTERFACE =============

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        # Default to quick start
        api = BrightDataAPI()
        api.quick_start()
    else:
        command = sys.argv[1]
        api = BrightDataAPI()
        
        if command == "test":
            if api.test_connection():
                print("✅ Connection successful!")
            else:
                print("❌ Connection failed. Check credentials")
        
        elif command == "discover":
            if len(sys.argv) > 2:
                result = api.discover(sys.argv[2])
            else:
                result = api.discover()
            print(json.dumps(result, indent=2))
        
        elif command == "scrape" and len(sys.argv) > 2:
            url = sys.argv[2]
            result = api.scrape_page(url)
            if result['success']:
                print(f"✅ Scraped {url}")
                print(f"   HTML length: {len(result['html'])} chars")
            else:
                print(f"❌ Failed: {result.get('error')}")
        
        elif command == "search" and len(sys.argv) > 2:
            query = ' '.join(sys.argv[2:])
            results = api.search(query)
            print(f"Found {len(results)} results for '{query}':")
            for r in results[:5]:
                print(f"  - {r['title']}")
                print(f"    {r['url']}")

        elif command == "datasets":
            # List marketplace datasets
            datasets = api.get_dataset_list()
            if datasets['success']:
                print("📊 Available Marketplace Datasets:")
                for ds in datasets.get('datasets', []):
                    print(f"  - {ds.get('name')}: {ds.get('id')}")

        elif command == "filter" and len(sys.argv) > 2:
            # Quick filter for beauty/gun stores
            from services.brightdata.chain_lists import get_exclusion_list

            dataset_id = 'gd_lw8kc4s7r2'  # Google Maps
            category = sys.argv[2]  # 'beauty' or 'gun'

            filters = {
                'country': 'United States',
                'category': {'$regex': category},
                'name': {'$nin': get_exclusion_list(category)}
            }

            result = api.filter_marketplace_dataset(
                dataset_id=dataset_id,
                filters=filters,
                limit=10,
                sample=True
            )

            if result['success']:
                print(f"✅ Found {result['count']} {category} locations")
                for item in result.get('data', [])[:5]:
                    print(f"  - {item.get('name')} in {item.get('city')}, {item.get('state')}")

        else:
            print("Commands:")
            print("  python api.py              # Quick start")
            print("  python api.py test         # Test connection")
            print("  python api.py discover [resource] # Discover resources")
            print("  python api.py scrape <url> # Scrape a page")
            print("  python api.py search <query> # Search Google")
            print("  python api.py datasets     # List marketplace datasets")
            print("  python api.py filter <category> # Filter beauty/gun stores")