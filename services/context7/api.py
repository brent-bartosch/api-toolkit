"""
Context7 API Client - Real-time documentation fetcher for AI coding

Context7 provides up-to-date code documentation directly from source repositories,
eliminating outdated or hallucinated code examples.

Token cost: ~500 tokens
"""

import os
import json
import requests
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode

class Context7API:
    """
    Context7 API client for fetching real-time documentation.

    Usage:
        from api_toolkit.services.context7.api import Context7API

        # Initialize with API key from environment
        api = Context7API()

        # Or provide API key directly
        api = Context7API(api_key='your-key-here')

        # Fetch documentation for a library
        docs = api.get_docs('react', 'hooks')

        # Search for specific documentation
        results = api.search('nextjs middleware JWT')
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize Context7 API client.

        Args:
            api_key: Optional API key. If not provided, uses CONTEXT7_API_KEY from environment
            base_url: Optional base URL. If not provided, uses CONTEXT7_URL from environment or default
        """
        self.api_key = api_key or os.getenv('CONTEXT7_API_KEY')
        self.base_url = base_url or os.getenv('CONTEXT7_URL', 'https://mcp.context7.com')

        if not self.api_key:
            print("Warning: No Context7 API key found. Rate limits may apply.")

        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

        if self.api_key:
            self.headers['CONTEXT7_API_KEY'] = self.api_key

    def quick_start(self):
        """Show quick start guide and test connection."""
        print("=" * 60)
        print("Context7 API - Real-time Documentation Fetcher")
        print("=" * 60)
        print("\n✅ Initialized successfully!")

        if self.api_key:
            print(f"API Key: {'*' * 10}{self.api_key[-4:]}")
        else:
            print("⚠️  No API key configured (rate limits may apply)")

        print(f"Base URL: {self.base_url}")

        print("\n📚 Available Methods:")
        print("  - get_docs(library, topic)    # Fetch specific docs")
        print("  - search(query)               # Search documentation")
        print("  - get_examples(library)       # Get code examples")
        print("  - list_libraries()            # Show available libraries")

        print("\n🚀 Quick Examples:")
        print("  api.get_docs('react', 'hooks')")
        print("  api.search('nextjs middleware JWT')")
        print("  api.get_examples('tailwindcss')")

        print("\n💡 Usage Pattern:")
        print("  1. Search for documentation")
        print("  2. Get specific docs for your library/framework")
        print("  3. Use examples in your code generation")

        # Test connection
        print("\n🔍 Testing connection...")
        if self.test_connection():
            print("✅ Connection successful!")
        else:
            print("❌ Connection failed. Check your API key and network.")

        return True

    def test_connection(self) -> bool:
        """Test the Context7 API connection."""
        try:
            # Simple ping endpoint (adjust based on actual API)
            response = requests.get(
                f"{self.base_url}/health",
                headers=self.headers,
                timeout=5
            )
            return response.status_code == 200
        except:
            return False

    def get_docs(self, library: str, topic: Optional[str] = None, version: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch documentation for a specific library and topic.

        Args:
            library: The library name (e.g., 'react', 'nextjs', 'tailwindcss')
            topic: Optional specific topic within the library (e.g., 'hooks', 'middleware')
            version: Optional version specification (e.g., 'latest', '13.4.0')

        Returns:
            Documentation content and metadata

        Example:
            docs = api.get_docs('react', 'hooks', 'latest')
            print(docs['content'])
        """
        endpoint = f"{self.base_url}/api/docs/{library}"

        params = {}
        if topic:
            params['topic'] = topic
        if version:
            params['version'] = version

        if params:
            endpoint += f"?{urlencode(params)}"

        try:
            response = requests.get(endpoint, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                'error': str(e),
                'library': library,
                'topic': topic,
                'status': 'failed'
            }

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for documentation across all available libraries.

        Args:
            query: Search query (e.g., 'JWT authentication middleware')
            limit: Maximum number of results to return

        Returns:
            List of relevant documentation snippets

        Example:
            results = api.search('nextjs middleware JWT')
            for result in results:
                print(f"{result['library']}: {result['title']}")
        """
        endpoint = f"{self.base_url}/api/search"

        payload = {
            'query': query,
            'limit': limit
        }

        try:
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json().get('results', [])
        except requests.exceptions.RequestException as e:
            print(f"Search error: {e}")
            return []

    def get_examples(self, library: str, pattern: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get code examples for a specific library.

        Args:
            library: The library name
            pattern: Optional pattern to filter examples (e.g., 'authentication', 'forms')

        Returns:
            List of code examples with descriptions

        Example:
            examples = api.get_examples('react', 'forms')
            for ex in examples:
                print(f"Example: {ex['title']}")
                print(ex['code'])
        """
        endpoint = f"{self.base_url}/api/examples/{library}"

        if pattern:
            endpoint += f"?pattern={pattern}"

        try:
            response = requests.get(endpoint, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json().get('examples', [])
        except requests.exceptions.RequestException as e:
            print(f"Error fetching examples: {e}")
            return []

    def list_libraries(self) -> List[str]:
        """
        List all available libraries with documentation.

        Returns:
            List of library names

        Example:
            libraries = api.list_libraries()
            print(f"Available libraries: {', '.join(libraries)}")
        """
        endpoint = f"{self.base_url}/api/libraries"

        try:
            response = requests.get(endpoint, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json().get('libraries', [])
        except requests.exceptions.RequestException as e:
            print(f"Error listing libraries: {e}")
            return []

    def get_context(self, prompt: str, libraries: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get contextual documentation based on a prompt.
        This is the main method for AI-assisted coding.

        Args:
            prompt: The coding task or question
            libraries: Optional list of preferred libraries to search

        Returns:
            Contextual documentation and examples

        Example:
            context = api.get_context(
                "Create a Next.js middleware that checks for JWT in cookies",
                libraries=['nextjs', 'jose']
            )
            print(context['documentation'])
            print(context['examples'])
        """
        endpoint = f"{self.base_url}/api/context"

        payload = {
            'prompt': prompt
        }

        if libraries:
            payload['libraries'] = libraries

        try:
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=payload,
                timeout=45
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                'error': str(e),
                'prompt': prompt,
                'status': 'failed'
            }

    def fetch_url_docs(self, url: str) -> Dict[str, Any]:
        """
        Fetch documentation from a specific URL.

        Args:
            url: URL to documentation page

        Returns:
            Parsed documentation content

        Example:
            docs = api.fetch_url_docs('https://docs.example.com/api/authentication')
        """
        endpoint = f"{self.base_url}/api/fetch"

        payload = {
            'url': url
        }

        try:
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                'error': str(e),
                'url': url,
                'status': 'failed'
            }


# CLI interface for testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python api.py [command] [args...]")
        print("Commands:")
        print("  quick_start          - Show quick start guide")
        print("  test                 - Test connection")
        print("  search <query>       - Search documentation")
        print("  docs <library>       - Get library documentation")
        print("  examples <library>   - Get code examples")
        print("  libraries            - List available libraries")
        sys.exit(1)

    api = Context7API()
    command = sys.argv[1]

    if command == "quick_start":
        api.quick_start()

    elif command == "test":
        if api.test_connection():
            print("✅ Connection successful!")
        else:
            print("❌ Connection failed!")

    elif command == "search" and len(sys.argv) > 2:
        query = " ".join(sys.argv[2:])
        results = api.search(query)
        for result in results:
            print(f"\n{result.get('library', 'Unknown')}: {result.get('title', 'No title')}")
            print(f"  {result.get('description', 'No description')}")

    elif command == "docs" and len(sys.argv) > 2:
        library = sys.argv[2]
        topic = sys.argv[3] if len(sys.argv) > 3 else None
        docs = api.get_docs(library, topic)
        print(json.dumps(docs, indent=2))

    elif command == "examples" and len(sys.argv) > 2:
        library = sys.argv[2]
        examples = api.get_examples(library)
        for ex in examples:
            print(f"\n{ex.get('title', 'Example')}:")
            print(ex.get('code', 'No code'))

    elif command == "libraries":
        libs = api.list_libraries()
        print("Available libraries:")
        for lib in libs:
            print(f"  - {lib}")

    else:
        print(f"Unknown command: {command}")