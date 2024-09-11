#!/usr/bin/env python3
"""
Documentation Integration Framework

Provides OpenAPI/Swagger support, live documentation fetching,
schema validation, and auto-discovery features.
"""

import os
import json
import yaml
import requests
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
import hashlib
from jsonschema import validate, ValidationError
import re
from pathlib import Path

class DocumentationManager:
    """
    Manages API documentation, schemas, and validation.
    Integrates OpenAPI specs, live docs fetching, and auto-discovery.
    """

    def __init__(self, service_name: str, base_path: Optional[str] = None):
        """
        Initialize documentation manager for a service.

        Args:
            service_name: Name of the service
            base_path: Base path for documentation storage
        """
        self.service_name = service_name
        self.base_path = base_path or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.service_path = Path(self.base_path) / 'services' / service_name
        self.docs_path = self.service_path / 'docs'
        self.cache_duration = timedelta(hours=24)  # Cache docs for 24 hours
        self._cache = {}

        # Create docs directory if it doesn't exist
        os.makedirs(self.docs_path, exist_ok=True)

        # Load cached documentation if available
        self.spec = self._load_cached_spec()
        self.schemas = self._load_schemas()
    
    # ============= OPENAPI/SWAGGER SUPPORT =============

    def load_openapi_spec(self, spec_path: Optional[str] = None) -> Dict:
        """
        Load OpenAPI/Swagger specification.

        Args:
            spec_path: Path to spec file or URL

        Returns:
            OpenAPI specification dict
        """
        if spec_path and spec_path.startswith('http'):
            # Fetch from URL
            response = requests.get(spec_path)
            response.raise_for_status()

            if spec_path.endswith('.yaml') or spec_path.endswith('.yml'):
                spec = yaml.safe_load(response.text)
            else:
                spec = response.json()

            # Cache the spec
            self._save_spec(spec)
            return spec

        elif spec_path:
            # Load from file
            with open(spec_path, 'r') as f:
                if spec_path.endswith('.yaml') or spec_path.endswith('.yml'):
                    return yaml.safe_load(f)
                else:
                    return json.load(f)
        else:
            # Load from default location
            return self._load_cached_spec()
    
    def _save_spec(self, spec: Dict):
        """Save OpenAPI spec to cache"""
        spec_file = self.docs_path / 'openapi.json'
        with open(spec_file, 'w') as f:
            json.dump(spec, f, indent=2)

        # Update timestamp
        timestamp_file = self.docs_path / '.last_updated'
        with open(timestamp_file, 'w') as f:
            f.write(datetime.now().isoformat())

    def _load_cached_spec(self) -> Optional[Dict]:
        """Load cached OpenAPI spec if available and not expired"""
        spec_file = self.docs_path / 'openapi.json'
        timestamp_file = self.docs_path / '.last_updated'

        if not spec_file.exists():
            return None

        # Check if cache is expired
        if timestamp_file.exists():
            with open(timestamp_file, 'r') as f:
                last_updated = datetime.fromisoformat(f.read().strip())
                if datetime.now() - last_updated > self.cache_duration:
                    return None  # Cache expired

        with open(spec_file, 'r') as f:
            return json.load(f)
    
    def extract_endpoints(self, spec: Optional[Dict] = None) -> List[Dict]:
        """
        Extract all endpoints from OpenAPI spec.

        Returns:
            List of endpoint definitions
        """
        spec = spec or self.spec
        if not spec:
            return []

        endpoints = []
        paths = spec.get('paths', {})

        for path, methods in paths.items():
            for method, details in methods.items():
                if method in ['get', 'post', 'put', 'patch', 'delete']:
                    endpoints.append({
                        'path': path,
                        'method': method.upper(),
                        'operation_id': details.get('operationId'),
                        'summary': details.get('summary'),
                        'description': details.get('description'),
                        'parameters': details.get('parameters', []),
                        'request_body': details.get('requestBody'),
                        'responses': details.get('responses', {})
                    })

        return endpoints
    
    def get_patterns(self) -> List[Dict[str, Any]]:
        """Get learned usage patterns from actual usage"""
        patterns_path = self.service_path / "patterns.json"
        if patterns_path.exists():
            with open(patterns_path, 'r') as f:
                return json.load(f)
        
        return []
    
    def get_context(self, level: str = 'quick') -> str:
        """
        Get documentation at specified detail level.
        Levels: 'quick' (~500 tokens), 'standard' (~1000 tokens), 'full' (~2000 tokens)
        """
        if level == 'quick':
            return self.get_quick_reference()
        
        elif level == 'standard':
            quick_ref = self.get_quick_reference()
            methods = self.get_api_methods()
            
            methods_text = "\n\n## API Methods\n"
            for method_name, details in list(methods.items())[:10]:  # Top 10 methods
                methods_text += f"- **{method_name}**: {details.get('description', '')}\n"
            
            return quick_ref + methods_text
        
        elif level == 'full':
            quick_ref = self.get_quick_reference()
            methods = self.get_api_methods()
            examples = self.get_examples()
            
            methods_text = "\n\n## API Methods\n"
            for method_name, details in methods.items():
                methods_text += f"- **{method_name}**: {details.get('description', '')}\n"
                if 'params' in details:
                    methods_text += f"  Params: {', '.join(details['params'])}\n"
            
            examples_text = "\n\n## Examples\n"
            for example in examples[:5]:  # Top 5 examples
                examples_text += f"```python\n{example.get('code', '')}\n```\n"
            
            return quick_ref + methods_text + examples_text
        
        return self.get_quick_reference()
    
    def estimate_tokens(self, text: str) -> int:
        """Rough estimate of token count (1 token ≈ 4 characters)"""
        return len(text) // 4
    
    def compress_documentation(self, source_text: str, target_tokens: int = 1000) -> str:
        """
        Compress documentation to target token count.
        Prioritizes: methods > examples > descriptions
        """
        target_chars = target_tokens * 4
        
        if len(source_text) <= target_chars:
            return source_text
        
        # Extract sections
        lines = source_text.split('\n')
        essential = []
        nice_to_have = []
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['def ', 'class ', 'api', 'endpoint', 'method']):
                essential.append(line)
            else:
                nice_to_have.append(line)
        
        # Build compressed version
        compressed = '\n'.join(essential)
        
        # Add nice-to-have until we hit limit
        for line in nice_to_have:
            if len(compressed) + len(line) < target_chars:
                compressed += '\n' + line
            else:
                break
        
        return compressed
    
    # ============= SCHEMA VALIDATION =============

    def _load_schemas(self) -> Dict[str, Any]:
        """Load JSON schemas for request/response validation"""
        schemas = {}
        schema_dir = self.docs_path / 'schemas'

        if schema_dir.exists():
            for schema_file in schema_dir.glob('*.json'):
                with open(schema_file, 'r') as f:
                    schema_name = schema_file.stem
                    schemas[schema_name] = json.load(f)

        # Also extract schemas from OpenAPI spec if available
        if self.spec and 'components' in self.spec and 'schemas' in self.spec['components']:
            schemas.update(self.spec['components']['schemas'])

        return schemas

    def validate_response(self, endpoint: str, method: str, response_data: Any) -> bool:
        """
        Validate API response against schema.

        Args:
            endpoint: API endpoint path
            method: HTTP method
            response_data: Response data to validate

        Returns:
            True if valid, raises ValidationError if not
        """
        if not self.spec:
            return True  # No spec to validate against

        # Find the endpoint in spec
        paths = self.spec.get('paths', {})
        if endpoint not in paths:
            return True  # Endpoint not in spec, skip validation

        method_spec = paths[endpoint].get(method.lower())
        if not method_spec:
            return True

        # Get response schema
        responses = method_spec.get('responses', {})
        response_schema = None

        # Check for 200 response schema
        if '200' in responses:
            content = responses['200'].get('content', {})
            if 'application/json' in content:
                response_schema = content['application/json'].get('schema')

        if response_schema:
            try:
                validate(instance=response_data, schema=response_schema)
                return True
            except ValidationError as e:
                raise ValidationError(f"Response validation failed: {e.message}")

        return True

    def validate_request(self, endpoint: str, method: str, request_data: Any) -> bool:
        """
        Validate API request against schema.

        Args:
            endpoint: API endpoint path
            method: HTTP method
            request_data: Request data to validate

        Returns:
            True if valid, raises ValidationError if not
        """
        if not self.spec:
            return True

        paths = self.spec.get('paths', {})
        if endpoint not in paths:
            return True

        method_spec = paths[endpoint].get(method.lower())
        if not method_spec:
            return True

        # Get request body schema
        request_body = method_spec.get('requestBody')
        if request_body:
            content = request_body.get('content', {})
            if 'application/json' in content:
                request_schema = content['application/json'].get('schema')
                if request_schema:
                    try:
                        validate(instance=request_data, schema=request_schema)
                        return True
                    except ValidationError as e:
                        raise ValidationError(f"Request validation failed: {e.message}")

        return True

    def generate_schema_from_response(self, response_data: Any) -> Dict:
        """
        Generate JSON schema from response data.
        Useful for creating initial schemas.
        """
        def infer_schema(data):
            if isinstance(data, dict):
                return {
                    "type": "object",
                    "properties": {k: infer_schema(v) for k, v in data.items()}
                }
            elif isinstance(data, list):
                if data:
                    return {
                        "type": "array",
                        "items": infer_schema(data[0])
                    }
                return {"type": "array"}
            elif isinstance(data, str):
                return {"type": "string"}
            elif isinstance(data, bool):
                return {"type": "boolean"}
            elif isinstance(data, int):
                return {"type": "integer"}
            elif isinstance(data, float):
                return {"type": "number"}
            elif data is None:
                return {"type": "null"}
            else:
                return {"type": "string"}  # Default

        return infer_schema(response_data)

    # ============= LIVE DOCUMENTATION FETCHING =============

    def fetch_live_docs(self, docs_url: str, selector: Optional[str] = None) -> str:
        """
        Fetch documentation from live website.

        Args:
            docs_url: URL of documentation
            selector: CSS selector for content extraction

        Returns:
            Extracted documentation text
        """
        try:
            response = requests.get(docs_url, timeout=10)
            response.raise_for_status()

            # Simple text extraction (could be enhanced with BeautifulSoup)
            content = response.text

            # Remove HTML tags (basic)
            content = re.sub(r'<[^>]+>', '', content)

            # Cache the fetched docs
            cache_file = self.docs_path / f"live_docs_{hashlib.md5(docs_url.encode()).hexdigest()}.txt"
            with open(cache_file, 'w') as f:
                f.write(content)

            return content
        except Exception as e:
            print(f"Error fetching live docs: {e}")
            return ""

    def sync_with_live_docs(self, docs_urls: List[str]):
        """
        Synchronize documentation with live sources.

        Args:
            docs_urls: List of documentation URLs to sync
        """
        synced_docs = {}

        for url in docs_urls:
            content = self.fetch_live_docs(url)
            if content:
                # Extract methods and examples from content
                methods = self._extract_methods_from_text(content)
                examples = self._extract_examples_from_text(content)

                synced_docs[url] = {
                    'methods': methods,
                    'examples': examples,
                    'last_synced': datetime.now().isoformat()
                }

        # Save synced docs
        sync_file = self.docs_path / 'synced_docs.json'
        with open(sync_file, 'w') as f:
            json.dump(synced_docs, f, indent=2)

        return synced_docs

    def _extract_methods_from_text(self, text: str) -> List[Dict]:
        """Extract method signatures from documentation text"""
        methods = []

        # Look for common method patterns
        # Pattern: method_name(params) -> return_type
        pattern = r'([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)(?:\s*->\s*[^\n]+)?'

        for match in re.finditer(pattern, text):
            method_name = match.group(1)
            full_sig = match.group(0)
            methods.append({
                'name': method_name,
                'signature': full_sig
            })

        return methods

    def _extract_examples_from_text(self, text: str) -> List[str]:
        """Extract code examples from documentation text"""
        examples = []

        # Look for code blocks (```...```)
        pattern = r'```(?:python)?\n([^`]+)```'

        for match in re.finditer(pattern, text, re.MULTILINE):
            examples.append(match.group(1).strip())

        return examples

    # ============= AUTO-DISCOVERY =============

    def discover_endpoints(self, base_url: str, api_key: Optional[str] = None) -> List[Dict]:
        """
        Auto-discover API endpoints by probing common patterns.

        Args:
            base_url: Base URL of the API
            api_key: API key for authentication

        Returns:
            List of discovered endpoints
        """
        discovered = []

        # Common API endpoint patterns
        common_endpoints = [
            '/api', '/v1', '/v2', '/status', '/health',
            '/info', '/version', '/endpoints', '/spec',
            '/swagger.json', '/openapi.json', '/api-docs'
        ]

        headers = {}
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'
            headers['X-API-Key'] = api_key

        for endpoint in common_endpoints:
            try:
                url = f"{base_url.rstrip('/')}{endpoint}"
                response = requests.get(url, headers=headers, timeout=5)

                if response.status_code == 200:
                    discovered.append({
                        'endpoint': endpoint,
                        'status': response.status_code,
                        'content_type': response.headers.get('Content-Type', ''),
                        'discovered_at': datetime.now().isoformat()
                    })

                    # If it's a spec endpoint, try to load it
                    if 'swagger' in endpoint or 'openapi' in endpoint:
                        try:
                            spec = response.json()
                            self._save_spec(spec)
                            self.spec = spec
                        except:
                            pass
            except:
                continue

        # Save discovered endpoints
        discovery_file = self.docs_path / 'discovered_endpoints.json'
        with open(discovery_file, 'w') as f:
            json.dump(discovered, f, indent=2)

        return discovered

    def learn_from_usage(self, endpoint: str, method: str, params: Dict, response: Any):
        """
        Learn and document patterns from actual API usage.

        Args:
            endpoint: API endpoint used
            method: HTTP method used
            params: Parameters sent
            response: Response received
        """
        patterns_file = self.service_path / 'patterns.json'

        # Load existing patterns
        if patterns_file.exists():
            with open(patterns_file, 'r') as f:
                patterns = json.load(f)
        else:
            patterns = []

        # Add new pattern
        pattern = {
            'endpoint': endpoint,
            'method': method,
            'params': params,
            'response_schema': self.generate_schema_from_response(response),
            'timestamp': datetime.now().isoformat(),
            'success': True
        }

        patterns.append(pattern)

        # Keep only recent patterns (last 100)
        patterns = patterns[-100:]

        # Save patterns
        with open(patterns_file, 'w') as f:
            json.dump(patterns, f, indent=2)

    # ============= CONTEXT7 INTEGRATION =============

    def fetch_context7_docs(self, query: str, libraries: Optional[List[str]] = None) -> Dict:
        """
        Fetch real-time documentation from Context7.

        Args:
            query: Search query or code context
            libraries: List of libraries to search

        Returns:
            Context7 documentation response
        """
        # Check if Context7 service is available
        context7_path = self.base_path / 'services' / 'context7' / 'api.py'

        if context7_path.exists():
            import sys
            sys.path.insert(0, str(self.base_path))

            try:
                from services.context7.api import Context7API

                context7 = Context7API()

                # Get contextual documentation
                if libraries:
                    docs = context7.get_context(query, libraries=libraries)
                else:
                    docs = context7.search(query)

                # Cache Context7 response
                cache_file = self.docs_path / f"context7_{hashlib.md5(query.encode()).hexdigest()}.json"
                with open(cache_file, 'w') as f:
                    json.dump(docs, f, indent=2)

                return docs
            except Exception as e:
                print(f"Error fetching Context7 docs: {e}")
                return {}

        return {}

    # ============= DOCUMENTATION SYNC =============

    def update_service_docs(self):
        """
        Update service documentation from all sources.
        Combines OpenAPI spec, live docs, patterns, and Context7.
        """
        updated_docs = {
            'service': self.service_name,
            'last_updated': datetime.now().isoformat(),
            'sources': {}
        }

        # Update from OpenAPI spec
        if self.spec:
            updated_docs['sources']['openapi'] = {
                'endpoints': self.extract_endpoints(),
                'schemas': self.schemas
            }

        # Update from patterns
        patterns = self.get_patterns()
        if patterns:
            updated_docs['sources']['patterns'] = patterns

        # Update from discovered endpoints
        discovery_file = self.docs_path / 'discovered_endpoints.json'
        if discovery_file.exists():
            with open(discovery_file, 'r') as f:
                updated_docs['sources']['discovered'] = json.load(f)

        # Save updated documentation
        docs_file = self.service_path / 'documentation.json'
        with open(docs_file, 'w') as f:
            json.dump(updated_docs, f, indent=2)

        return updated_docs

    # ============= HELPER METHODS =============

    def get_quick_reference(self) -> str:
        """Get quick reference documentation"""
        ref_file = self.service_path / 'quick_reference.md'
        if ref_file.exists():
            with open(ref_file, 'r') as f:
                return f.read()
        return f"# {self.service_name} Quick Reference\n\nNo quick reference available."

    def get_api_methods(self) -> Dict[str, Any]:
        """Get API methods from documentation"""
        if self.spec:
            methods = {}
            for endpoint in self.extract_endpoints():
                operation_id = endpoint.get('operation_id')
                if operation_id:
                    methods[operation_id] = {
                        'path': endpoint['path'],
                        'method': endpoint['method'],
                        'description': endpoint.get('summary', ''),
                        'params': [p.get('name') for p in endpoint.get('parameters', [])]
                    }
            return methods
        return {}

    def get_examples(self) -> List[Dict[str, str]]:
        """Get code examples from documentation"""
        examples = []
        examples_file = self.service_path / 'examples.py'

        if examples_file.exists():
            with open(examples_file, 'r') as f:
                content = f.read()

                # Extract example functions
                pattern = r'def\s+(example_[^(]+)\([^)]*\):[^#]*?(?=def|$)'

                for match in re.finditer(pattern, content, re.MULTILINE | re.DOTALL):
                    examples.append({
                        'name': match.group(1),
                        'code': match.group(0)
                    })

        return examples

    @staticmethod
    def create_from_url(service_name: str, docs_url: str):
        """
        Create documentation manager from a URL.
        """
        manager = DocumentationManager(service_name)

        # Try to fetch OpenAPI spec from common locations
        for spec_endpoint in ['/openapi.json', '/swagger.json', '/api-docs']:
            try:
                spec_url = f"{docs_url.rstrip('/')}{spec_endpoint}"
                spec = manager.load_openapi_spec(spec_url)
                if spec:
                    print(f"Loaded OpenAPI spec from {spec_url}")
                    break
            except:
                continue

        # Fetch live documentation
        content = manager.fetch_live_docs(docs_url)
        if content:
            print(f"Fetched documentation from {docs_url}")

        return manager

    @staticmethod
    def create_from_openapi(service_name: str, spec_url: str):
        """
        Create documentation manager from OpenAPI/Swagger spec.
        """
        manager = DocumentationManager(service_name)
        spec = manager.load_openapi_spec(spec_url)

        if spec:
            print(f"Loaded OpenAPI spec with {len(manager.extract_endpoints())} endpoints")

        return manager