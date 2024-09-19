#!/usr/bin/env python3
"""
BrightData Web Unlocker Implementation
Properly handles Cloudflare and other anti-bot protections

This module provides the correct implementation for BrightData's Web Unlocker API
which can bypass Cloudflare, CAPTCHAs, and other anti-scraping measures.
"""

import os
import sys
import json
import time
import requests
from typing import Optional, Dict, Any, List
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

class WebUnlocker:
    """
    BrightData Web Unlocker for bypassing anti-bot protection

    Handles:
    - Cloudflare protection
    - CAPTCHAs
    - JavaScript challenges
    - Rate limiting
    - IP rotation
    """

    def __init__(self, zone: str = 'web_unlocker1'):
        """
        Initialize Web Unlocker with specific zone

        Args:
            zone: BrightData zone name (mcp_unlocker, web_unlocker1, etc.)
        """
        self.customer_id = os.getenv('BRIGHTDATA_CUSTOMER_ID')
        if not self.customer_id:
            raise ValueError("BRIGHTDATA_CUSTOMER_ID environment variable required")

        self.zone = zone

        # Get password/API key from environment
        api_key = os.getenv('BRIGHTDATA_API_KEY')
        self.password = os.getenv('BRIGHTDATA_PASSWORD') or api_key

        if not self.password:
            raise ValueError("BRIGHTDATA_PASSWORD or BRIGHTDATA_API_KEY environment variable required")

        # BrightData proxy URL format
        self.proxy_url = f"http://brd-customer-{self.customer_id}-zone-{self.zone}:{self.password}@brd.superproxy.io:22225"

        # Session for connection pooling
        self.session = requests.Session()
        self.session.proxies = {
            'http': self.proxy_url,
            'https': self.proxy_url
        }

        # Headers to appear more browser-like
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Upgrade-Insecure-Requests': '1'
        }

        print(f"✅ Web Unlocker initialized with zone: {self.zone}")

    def scrape_page(self, url: str,
                   render_js: bool = True,
                   country: Optional[str] = None,
                   timeout: int = 60,
                   retry_count: int = 3) -> Dict[str, Any]:
        """
        Scrape a page using Web Unlocker to bypass protection

        Args:
            url: URL to scrape
            render_js: Whether to render JavaScript (needed for Cloudflare)
            country: Country code for geo-targeting (e.g., 'US')
            timeout: Request timeout in seconds
            retry_count: Number of retries on failure

        Returns:
            Dict with success status, HTML content, and metadata
        """

        # Add Web Unlocker specific headers
        headers = self.headers.copy()

        # BrightData specific headers for control
        if render_js:
            headers['X-Crawler-Render'] = 'true'
            headers['X-Crawler-Wait'] = '5000'  # Wait 5 seconds for JS

        if country:
            headers['X-Country'] = country

        # Retry logic
        for attempt in range(retry_count):
            try:
                print(f"🔄 Attempt {attempt + 1}: Project 3 {url}")

                # Make request through Web Unlocker proxy
                response = self.session.get(
                    url,
                    headers=headers,
                    timeout=timeout,
                    verify=False  # Proxy handles SSL
                )

                # Check if successful
                if response.status_code == 200:
                    print(f"✅ Successfully scraped: {url}")

                    return {
                        'success': True,
                        'url': url,
                        'html': response.text,
                        'status_code': response.status_code,
                        'headers': dict(response.headers),
                        'cookies': response.cookies.get_dict(),
                        'elapsed_ms': response.elapsed.total_seconds() * 1000
                    }
                else:
                    print(f"⚠️ Status {response.status_code} for {url}")

                    # Check if it's a temporary issue
                    if response.status_code in [429, 503]:
                        wait_time = (attempt + 1) * 5
                        print(f"   Waiting {wait_time} seconds before retry...")
                        time.sleep(wait_time)
                        continue

                    return {
                        'success': False,
                        'url': url,
                        'error': f'HTTP {response.status_code}',
                        'html': response.text,
                        'status_code': response.status_code
                    }

            except requests.exceptions.Timeout:
                print(f"⏱️ Timeout on attempt {attempt + 1}")
                if attempt < retry_count - 1:
                    time.sleep(5)
                    continue
                return {
                    'success': False,
                    'url': url,
                    'error': 'Request timeout'
                }

            except Exception as e:
                print(f"❌ Error on attempt {attempt + 1}: {str(e)}")
                if attempt < retry_count - 1:
                    time.sleep(5)
                    continue
                return {
                    'success': False,
                    'url': url,
                    'error': str(e)
                }

        return {
            'success': False,
            'url': url,
            'error': f'Failed after {retry_count} attempts'
        }

    def scrape_with_browser(self, url: str,
                           wait_selector: Optional[str] = None,
                           execute_js: Optional[str] = None,
                           screenshot: bool = False) -> Dict[str, Any]:
        """
        Use Browser API for complex JavaScript rendering

        Args:
            url: URL to scrape
            wait_selector: CSS selector to wait for
            execute_js: JavaScript code to execute
            screenshot: Whether to take a screenshot

        Returns:
            Scraped content and metadata
        """

        # Use scraping_browser1 zone for Browser API
        browser_zone = 'scraping_browser1'
        browser_proxy = f"http://brd-customer-{self.customer_id}-zone-{browser_zone}:{self.password}@brd.superproxy.io:22225"

        headers = self.headers.copy()
        headers['X-Crawler-Render'] = 'true'

        if wait_selector:
            headers['X-Crawler-Wait-Selector'] = wait_selector

        if execute_js:
            headers['X-Crawler-Execute'] = execute_js

        if screenshot:
            headers['X-Crawler-Screenshot'] = 'true'

        session = requests.Session()
        session.proxies = {
            'http': browser_proxy,
            'https': browser_proxy
        }

        try:
            response = session.get(url, headers=headers, timeout=90, verify=False)

            result = {
                'success': response.status_code == 200,
                'url': url,
                'html': response.text,
                'status_code': response.status_code,
                'headers': dict(response.headers)
            }

            # Check for screenshot in headers
            if screenshot and 'X-Crawler-Screenshot-Data' in response.headers:
                result['screenshot'] = response.headers['X-Crawler-Screenshot-Data']

            return result

        except Exception as e:
            return {
                'success': False,
                'url': url,
                'error': str(e)
            }

    def batch_scrape(self, urls: List[str],
                    delay_between: float = 1.0,
                    max_concurrent: int = 5) -> List[Dict[str, Any]]:
        """
        Scrape multiple URLs with rate limiting

        Args:
            urls: List of URLs to scrape
            delay_between: Delay between requests in seconds
            max_concurrent: Maximum concurrent requests

        Returns:
            List of scraping results
        """
        results = []

        for i, url in enumerate(urls):
            print(f"\n📄 Project 3 {i+1}/{len(urls)}: {url}")

            result = self.scrape_page(url)
            results.append(result)

            # Rate limiting
            if i < len(urls) - 1:
                print(f"⏳ Waiting {delay_between} seconds...")
                time.sleep(delay_between)

        # Summary
        successful = sum(1 for r in results if r.get('success'))
        print(f"\n✅ Batch complete: {successful}/{len(results)} successful")

        return results

    def extract_json_ld(self, html: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON-LD structured data from HTML

        Args:
            html: HTML content

        Returns:
            Parsed JSON-LD data or None
        """
        import re

        # Find JSON-LD script tag
        pattern = r'<script\s+type="application/ld\+json"[^>]*>(.*?)</script>'
        matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)

        for match in matches:
            try:
                # Clean and parse JSON
                json_text = match.strip()
                # Handle escaped characters
                json_text = json_text.replace('\\"', '"').replace('\\n', '\n')
                data = json.loads(json_text)

                # Return first valid structured data
                if isinstance(data, dict) and data.get('@type'):
                    return data
                elif isinstance(data, list) and data and data[0].get('@type'):
                    return data[0]

            except json.JSONDecodeError:
                continue

        return None

    def test_connection(self) -> bool:
        """
        Test Web Unlocker connection

        Returns:
            True if connection works, False otherwise
        """
        print("🔌 Testing Web Unlocker connection...")

        # Test with a simple page
        result = self.scrape_page('https://httpbin.org/html', render_js=False, retry_count=1)

        if result.get('success'):
            print("✅ Web Unlocker connection successful!")
            return True
        else:
            print(f"❌ Connection failed: {result.get('error')}")
            return False


# Example usage and testing
if __name__ == '__main__':
    # Test Web Unlocker
    print("🏪 Testing BrightData Web Unlocker for ACE Hardware")
    print("="*50)

    # Try different zones to find one that works
    zones_to_try = ['scraping_browser1', 'mcp_browser', 'web_unlocker1', 'mcp_unlocker']

    for zone in zones_to_try:
        print(f"\n🔧 Trying zone: {zone}")
        unlocker = WebUnlocker(zone)

    # Test connection
    if not unlocker.test_connection():
        print("Failed to connect to Web Unlocker")
        sys.exit(1)

    # Test with ACE Hardware store
    print("\n🏪 Testing ACE Hardware store page...")
    store_url = 'https://www.acehardware.com/store-details/10635'

    result = unlocker.scrape_page(store_url, render_js=True, country='US')

    if result.get('success'):
        print("✅ Successfully scraped ACE Hardware page!")

        html = result.get('html', '')
        print(f"📄 HTML length: {len(html)} characters")

        # Try to extract JSON-LD
        json_ld = unlocker.extract_json_ld(html)

        if json_ld:
            print("✅ Found JSON-LD structured data!")
            print(f"   Store Type: {json_ld.get('@type')}")
            print(f"   Store Name: {json_ld.get('name')}")
            print(f"   Email: {json_ld.get('email')}")
            print(f"   Phone: {json_ld.get('telephone')}")

            # Save for inspection
            with open('ace_test_page.html', 'w') as f:
                f.write(html)
            print("\n📁 Saved HTML to ace_test_page.html for inspection")

            with open('ace_test_jsonld.json', 'w') as f:
                json.dump(json_ld, f, indent=2)
            print("📁 Saved JSON-LD to ace_test_jsonld.json")
        else:
            print("⚠️ No JSON-LD found in page")
            print("   This might mean additional JavaScript execution is needed")
    else:
        print(f"❌ Failed to scrape: {result.get('error')}")

    print("\n" + "="*50)
    print("Test complete!")