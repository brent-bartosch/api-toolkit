"""
Query Helpers for BrightData API
Simplifies web scraping and data collection operations
"""

from typing import Dict, List, Optional, Any, Union
import time
import hashlib
from datetime import datetime, timedelta
from urllib.parse import urlparse, urljoin

class ScrapeBuilder:
    """Build complex scraping configurations"""
    
    def __init__(self, url: str):
        self.url = url
        self.config = {
            'url': url,
            'render_js': False,
            'actions': [],
            'wait_conditions': [],
            'extract': []
        }
    
    def wait_for_selector(self, selector: str, timeout: int = 10000) -> 'ScrapeBuilder':
        """Wait for a CSS selector to appear"""
        self.config['wait_for'] = selector
        self.config['wait_timeout'] = timeout
        return self
    
    def click(self, selector: str) -> 'ScrapeBuilder':
        """Click on an element"""
        self.config['actions'].append({
            'type': 'click',
            'selector': selector
        })
        return self
    
    def type_text(self, selector: str, text: str) -> 'ScrapeBuilder':
        """Type text into an input field"""
        self.config['actions'].append({
            'type': 'type',
            'selector': selector,
            'text': text
        })
        return self
    
    def scroll_to(self, selector: str) -> 'ScrapeBuilder':
        """Scroll to an element"""
        self.config['actions'].append({
            'type': 'scroll',
            'selector': selector
        })
        return self
    
    def wait(self, milliseconds: int) -> 'ScrapeBuilder':
        """Wait for specified milliseconds"""
        self.config['actions'].append({
            'type': 'wait',
            'milliseconds': milliseconds
        })
        return self
    
    def screenshot(self, full_page: bool = False) -> 'ScrapeBuilder':
        """Take a screenshot"""
        self.config['actions'].append({
            'type': 'screenshot',
            'fullPage': full_page
        })
        self.config['screenshot'] = True
        return self
    
    def extract_text(self, selector: str, name: str) -> 'ScrapeBuilder':
        """Extract text from elements"""
        self.config['extract'].append({
            'selector': selector,
            'name': name,
            'type': 'text'
        })
        return self
    
    def extract_attribute(self, selector: str, attribute: str, name: str) -> 'ScrapeBuilder':
        """Extract attribute from elements"""
        self.config['extract'].append({
            'selector': selector,
            'attribute': attribute,
            'name': name,
            'type': 'attribute'
        })
        return self
    
    def with_proxy(self, country: Optional[str] = None, 
                   proxy_type: str = 'residential') -> 'ScrapeBuilder':
        """Use specific proxy settings"""
        self.config['proxy'] = {
            'type': proxy_type,
            'country': country
        }
        return self
    
    def build(self) -> Dict:
        """Build the scraping configuration"""
        return self.config


class BatchScraper:
    """Handle batch scraping operations"""
    
    def __init__(self, api):
        self.api = api
        self.results = []
        self.failed = []
    
    def scrape_urls(self, urls: List[str], 
                    delay: float = 1.0,
                    max_retries: int = 3) -> Dict[str, List]:
        """
        Scrape multiple URLs with rate limiting and retries.
        
        Args:
            urls: List of URLs to scrape
            delay: Delay between requests in seconds
            max_retries: Maximum retry attempts for failed requests
        
        Returns:
            Dict with 'success' and 'failed' lists
        """
        results = {'success': [], 'failed': []}
        
        for i, url in enumerate(urls):
            if i > 0:
                time.sleep(delay)
            
            retries = 0
            success = False
            
            while retries < max_retries and not success:
                try:
                    result = self.api.scrape_page(url, render_js=True)
                    
                    if result['success']:
                        results['success'].append({
                            'url': url,
                            'html': result['html'],
                            'timestamp': datetime.now().isoformat()
                        })
                        success = True
                    else:
                        retries += 1
                        if retries < max_retries:
                            time.sleep(delay * 2)  # Longer delay on retry
                except Exception as e:
                    retries += 1
                    if retries >= max_retries:
                        results['failed'].append({
                            'url': url,
                            'error': str(e),
                            'attempts': retries
                        })
            
            if not success:
                results['failed'].append({
                    'url': url,
                    'error': 'Max retries exceeded',
                    'attempts': max_retries
                })
        
        return results
    
    def parallel_scrape(self, urls: List[str], workers: int = 5) -> Dict[str, List]:
        """
        Scrape URLs in parallel (simulated with sequential + batching).
        
        Args:
            urls: List of URLs to scrape
            workers: Number of parallel workers (for future async implementation)
        
        Returns:
            Dict with results
        """
        # For now, just batch the URLs
        batch_size = max(1, len(urls) // workers)
        results = {'success': [], 'failed': []}
        
        for i in range(0, len(urls), batch_size):
            batch = urls[i:i + batch_size]
            batch_results = self.scrape_urls(batch, delay=0.5)
            
            results['success'].extend(batch_results['success'])
            results['failed'].extend(batch_results['failed'])
        
        return results


class DataExtractor:
    """Extract structured data from scraped content"""
    
    def __init__(self):
        self.patterns = {}
    
    def extract_emails(self, html: str) -> List[str]:
        """Extract email addresses from HTML"""
        import re
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, html)
        return list(set(emails))  # Remove duplicates
    
    def extract_phone_numbers(self, html: str) -> List[str]:
        """Extract phone numbers from HTML"""
        import re
        # Simple pattern for US phone numbers
        phone_pattern = r'(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        phones = re.findall(phone_pattern, html)
        return list(set(phones))
    
    def extract_prices(self, html: str, currency: str = '$') -> List[float]:
        """Extract prices from HTML"""
        import re
        # Pattern for prices like $19.99, $1,234.56
        price_pattern = rf'\{currency}\s*([0-9,]+\.?\d*)'
        matches = re.findall(price_pattern, html)
        
        prices = []
        for match in matches:
            try:
                price = float(match.replace(',', ''))
                prices.append(price)
            except ValueError:
                continue
        
        return prices
    
    def extract_social_links(self, html: str) -> Dict[str, List[str]]:
        """Extract social media links"""
        import re
        
        social_patterns = {
            'facebook': r'(?:https?://)?(?:www\.)?facebook\.com/[^\s"\'<>]+',
            'twitter': r'(?:https?://)?(?:www\.)?(?:twitter|x)\.com/[^\s"\'<>]+',
            'instagram': r'(?:https?://)?(?:www\.)?instagram\.com/[^\s"\'<>]+',
            'linkedin': r'(?:https?://)?(?:www\.)?linkedin\.com/[^\s"\'<>]+',
            'youtube': r'(?:https?://)?(?:www\.)?youtube\.com/[^\s"\'<>]+',
        }
        
        results = {}
        for platform, pattern in social_patterns.items():
            links = re.findall(pattern, html)
            if links:
                results[platform] = list(set(links))
        
        return results
    
    def extract_structured_data(self, html: str) -> Dict[str, Any]:
        """Extract JSON-LD structured data"""
        import re
        import json
        
        # Find JSON-LD scripts
        pattern = r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
        matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
        
        structured_data = []
        for match in matches:
            try:
                data = json.loads(match)
                structured_data.append(data)
            except json.JSONDecodeError:
                continue
        
        return {
            'found': len(structured_data) > 0,
            'data': structured_data
        }


class ProxyRotator:
    """Manage proxy rotation for requests"""
    
    def __init__(self, api):
        self.api = api
        self.countries = ['US', 'GB', 'DE', 'FR', 'CA', 'AU']
        self.current_index = 0
    
    def get_next_country(self) -> str:
        """Get next country in rotation"""
        country = self.countries[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.countries)
        return country
    
    def scrape_with_rotation(self, url: str, 
                            attempts: int = 3) -> Optional[Dict]:
        """
        Scrape with automatic country rotation on failure.
        
        Args:
            url: URL to scrape
            attempts: Number of countries to try
        
        Returns:
            Successful result or None
        """
        for i in range(min(attempts, len(self.countries))):
            country = self.get_next_country()
            
            try:
                result = self.api.proxy_request(url, country=country)
                if result['success']:
                    result['proxy_country'] = country
                    return result
            except Exception as e:
                print(f"Failed with {country}: {e}")
                continue
        
        return None
    
    def test_proxies(self) -> Dict[str, bool]:
        """Test proxy availability for different countries"""
        test_url = 'https://httpbin.org/ip'
        results = {}
        
        for country in self.countries:
            try:
                response = self.api.proxy_request(test_url, country=country)
                results[country] = response.get('success', False)
            except:
                results[country] = False
        
        return results


class SearchAggregator:
    """Aggregate search results from multiple engines"""
    
    def __init__(self, api):
        self.api = api
        self.engines = ['google', 'bing', 'duckduckgo']
    
    def multi_engine_search(self, query: str, 
                           num_results: int = 10) -> Dict[str, Any]:
        """
        Search across multiple engines and aggregate results.
        
        Args:
            query: Search query
            num_results: Results per engine
        
        Returns:
            Aggregated search results
        """
        all_results = {}
        unique_urls = set()
        aggregated = []
        
        for engine in self.engines:
            try:
                results = self.api.search(query, engine=engine, num_results=num_results)
                all_results[engine] = results
                
                # Track unique URLs
                for result in results:
                    url = result.get('url')
                    if url and url not in unique_urls:
                        unique_urls.add(url)
                        result['engines'] = [engine]
                        aggregated.append(result)
                    elif url:
                        # URL already seen, add engine to list
                        for agg in aggregated:
                            if agg['url'] == url:
                                agg['engines'].append(engine)
                                break
            except Exception as e:
                all_results[engine] = {'error': str(e)}
        
        # Sort by number of engines (more engines = more relevant)
        aggregated.sort(key=lambda x: len(x.get('engines', [])), reverse=True)
        
        return {
            'query': query,
            'total_unique': len(unique_urls),
            'by_engine': all_results,
            'aggregated': aggregated[:num_results]
        }
    
    def trending_searches(self, topics: List[str]) -> Dict[str, List]:
        """
        Get trending searches for topics.
        
        Args:
            topics: List of topics to check
        
        Returns:
            Trending searches by topic
        """
        trends = {}
        
        for topic in topics:
            # Search for "trending" + topic
            query = f"trending {topic} {datetime.now().year}"
            results = self.api.search(query, num_results=5)
            
            trends[topic] = [
                {
                    'title': r['title'],
                    'url': r['url']
                }
                for r in results
            ]
        
        return trends


class CacheManager:
    """Manage caching for scraped content"""
    
    def __init__(self, cache_dir: str = '/tmp/brightdata_cache'):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def _get_cache_key(self, url: str) -> str:
        """Generate cache key for URL"""
        return hashlib.md5(url.encode()).hexdigest()
    
    def get(self, url: str, max_age: int = 3600) -> Optional[Dict]:
        """
        Get cached content if not expired.
        
        Args:
            url: URL to check
            max_age: Maximum age in seconds
        
        Returns:
            Cached data or None
        """
        cache_key = self._get_cache_key(url)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            import json
            
            # Check age
            file_age = time.time() - cache_file.stat().st_mtime
            if file_age < max_age:
                with open(cache_file, 'r') as f:
                    return json.load(f)
        
        return None
    
    def set(self, url: str, data: Dict) -> None:
        """Cache scraped content"""
        import json
        
        cache_key = self._get_cache_key(url)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        data['cached_at'] = datetime.now().isoformat()
        data['url'] = url
        
        with open(cache_file, 'w') as f:
            json.dump(data, f)
    
    def clear_expired(self, max_age: int = 86400) -> int:
        """Clear expired cache entries"""
        import json
        
        cleared = 0
        current_time = time.time()
        
        for cache_file in self.cache_dir.glob('*.json'):
            file_age = current_time - cache_file.stat().st_mtime
            if file_age > max_age:
                cache_file.unlink()
                cleared += 1
        
        return cleared