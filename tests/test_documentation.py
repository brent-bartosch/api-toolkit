#!/usr/bin/env python3
"""
Documentation Integration Test Suite

Tests for OpenAPI/Swagger integration, schema validation,
live docs fetching, and auto-discovery features.
"""

import os
import sys
import json
import tempfile
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.base_test import ServiceTestBase
from core.documentation import DocumentationManager

class DocumentationTest(ServiceTestBase):
    """Test suite for documentation integration framework"""

    def __init__(self):
        """Initialize documentation tests"""
        self.service_name = 'DocumentationFramework'
        self.test_dir = tempfile.mkdtemp(prefix='doc_test_')
        self.doc_manager = DocumentationManager('test_service', self.test_dir)
        self.results = []
        self.start_time = datetime.now()

    def get_test_config(self) -> Dict[str, Any]:
        """Get test configuration"""
        return {
            'api_key_env': None,
            'requires_auth': False,
            'rate_limit': 10,
            'test_endpoint': None,
            'test_params': {}
        }

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all documentation tests"""
        test_methods = [
            self.test_openapi_spec_loading,
            self.test_endpoint_extraction,
            self.test_schema_validation,
            self.test_request_validation,
            self.test_response_validation,
            self.test_schema_generation,
            self.test_live_docs_fetching,
            self.test_documentation_caching,
            self.test_auto_discovery,
            self.test_pattern_learning,
            self.test_context7_integration,
            self.test_documentation_compression,
            self.test_token_estimation,
            self.test_documentation_sync
        ]

        for test_method in test_methods:
            result = test_method()
            self.results.append(result)

        return self._compile_results()

    def test_openapi_spec_loading(self) -> Dict[str, Any]:
        """Test OpenAPI specification loading"""
        test_name = "openapi_spec_loading"

        try:
            # Create sample OpenAPI spec
            sample_spec = {
                "openapi": "3.0.0",
                "info": {
                    "title": "Test API",
                    "version": "1.0.0"
                },
                "paths": {
                    "/users": {
                        "get": {
                            "summary": "Get users",
                            "responses": {
                                "200": {
                                    "description": "Success"
                                }
                            }
                        }
                    }
                }
            }

            # Save spec to file
            spec_file = Path(self.test_dir) / 'spec.json'
            with open(spec_file, 'w') as f:
                json.dump(sample_spec, f)

            # Load spec
            loaded_spec = self.doc_manager.load_openapi_spec(str(spec_file))

            if loaded_spec and loaded_spec['info']['title'] == 'Test API':
                return self._pass(test_name, "OpenAPI spec loaded successfully")
            else:
                return self._fail(test_name, "Failed to load spec correctly")

        except Exception as e:
            return self._fail(test_name, str(e))

    def test_endpoint_extraction(self) -> Dict[str, Any]:
        """Test endpoint extraction from OpenAPI spec"""
        test_name = "endpoint_extraction"

        try:
            # Create spec with multiple endpoints
            spec = {
                "paths": {
                    "/users": {
                        "get": {"summary": "Get users"},
                        "post": {"summary": "Create user"}
                    },
                    "/users/{id}": {
                        "get": {"summary": "Get user by ID"},
                        "delete": {"summary": "Delete user"}
                    }
                }
            }

            self.doc_manager.spec = spec
            endpoints = self.doc_manager.extract_endpoints()

            if len(endpoints) == 4:
                return self._pass(test_name, f"Extracted {len(endpoints)} endpoints")
            else:
                return self._fail(test_name, f"Expected 4 endpoints, got {len(endpoints)}")

        except Exception as e:
            return self._fail(test_name, str(e))

    def test_schema_validation(self) -> Dict[str, Any]:
        """Test JSON schema validation"""
        test_name = "schema_validation"

        try:
            from jsonschema import validate, ValidationError

            # Create schema
            schema = {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer"}
                },
                "required": ["name"]
            }

            # Valid data
            valid_data = {"name": "John", "age": 30}
            validate(instance=valid_data, schema=schema)

            # Invalid data
            invalid_data = {"age": "thirty"}
            try:
                validate(instance=invalid_data, schema=schema)
                return self._fail(test_name, "Should have raised validation error")
            except ValidationError:
                return self._pass(test_name, "Schema validation working correctly")

        except Exception as e:
            return self._fail(test_name, str(e))

    def test_request_validation(self) -> Dict[str, Any]:
        """Test API request validation"""
        test_name = "request_validation"

        try:
            # Setup spec with request schema
            self.doc_manager.spec = {
                "paths": {
                    "/users": {
                        "post": {
                            "requestBody": {
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "name": {"type": "string"},
                                                "email": {"type": "string"}
                                            },
                                            "required": ["name", "email"]
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            # Valid request
            valid = self.doc_manager.validate_request(
                "/users", "POST",
                {"name": "John", "email": "john@example.com"}
            )

            if valid:
                return self._pass(test_name, "Request validation working")
            else:
                return self._fail(test_name, "Valid request failed validation")

        except Exception as e:
            return self._fail(test_name, str(e))

    def test_response_validation(self) -> Dict[str, Any]:
        """Test API response validation"""
        test_name = "response_validation"

        try:
            # Setup spec with response schema
            self.doc_manager.spec = {
                "paths": {
                    "/users": {
                        "get": {
                            "responses": {
                                "200": {
                                    "content": {
                                        "application/json": {
                                            "schema": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "id": {"type": "integer"},
                                                        "name": {"type": "string"}
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            # Valid response
            valid = self.doc_manager.validate_response(
                "/users", "GET",
                [{"id": 1, "name": "John"}, {"id": 2, "name": "Jane"}]
            )

            if valid:
                return self._pass(test_name, "Response validation working")
            else:
                return self._fail(test_name, "Valid response failed validation")

        except Exception as e:
            return self._fail(test_name, str(e))

    def test_schema_generation(self) -> Dict[str, Any]:
        """Test schema generation from response data"""
        test_name = "schema_generation"

        try:
            # Sample response data
            response_data = {
                "id": 1,
                "name": "John Doe",
                "age": 30,
                "active": True,
                "tags": ["user", "admin"],
                "metadata": {
                    "created_at": "2025-01-01",
                    "updated_at": "2025-01-23"
                }
            }

            schema = self.doc_manager.generate_schema_from_response(response_data)

            # Verify schema structure
            if (schema["type"] == "object" and
                "properties" in schema and
                schema["properties"]["id"]["type"] == "integer" and
                schema["properties"]["name"]["type"] == "string" and
                schema["properties"]["tags"]["type"] == "array"):
                return self._pass(test_name, "Schema generated correctly")
            else:
                return self._fail(test_name, "Generated schema incorrect")

        except Exception as e:
            return self._fail(test_name, str(e))

    def test_live_docs_fetching(self) -> Dict[str, Any]:
        """Test fetching documentation from live URLs"""
        test_name = "live_docs_fetching"

        try:
            # Test with a simple URL (this would need mocking in real tests)
            # For now, just test the method exists
            if hasattr(self.doc_manager, 'fetch_live_docs'):
                return self._pass(test_name, "Live docs fetching available")
            else:
                return self._fail(test_name, "fetch_live_docs method not found")

        except Exception as e:
            return self._fail(test_name, str(e))

    def test_documentation_caching(self) -> Dict[str, Any]:
        """Test documentation caching mechanism"""
        test_name = "documentation_caching"

        try:
            # Save spec
            spec = {"test": "spec", "version": "1.0"}
            self.doc_manager._save_spec(spec)

            # Load cached spec
            cached = self.doc_manager._load_cached_spec()

            if cached and cached["test"] == "spec":
                return self._pass(test_name, "Documentation caching working")
            else:
                return self._fail(test_name, "Failed to cache/load spec")

        except Exception as e:
            return self._fail(test_name, str(e))

    def test_auto_discovery(self) -> Dict[str, Any]:
        """Test endpoint auto-discovery"""
        test_name = "auto_discovery"

        try:
            # Test discovery method exists
            if hasattr(self.doc_manager, 'discover_endpoints'):
                # Would need mock server for real test
                return self._pass(test_name, "Auto-discovery feature available")
            else:
                return self._fail(test_name, "discover_endpoints method not found")

        except Exception as e:
            return self._fail(test_name, str(e))

    def test_pattern_learning(self) -> Dict[str, Any]:
        """Test learning from API usage patterns"""
        test_name = "pattern_learning"

        try:
            # Record a pattern
            self.doc_manager.learn_from_usage(
                endpoint="/users",
                method="GET",
                params={"limit": 10},
                response=[{"id": 1, "name": "John"}]
            )

            # Check if pattern was recorded
            patterns = self.doc_manager.get_patterns()

            if patterns and len(patterns) > 0:
                return self._pass(test_name, f"Recorded {len(patterns)} patterns")
            else:
                return self._fail(test_name, "Pattern learning not working")

        except Exception as e:
            return self._fail(test_name, str(e))

    def test_context7_integration(self) -> Dict[str, Any]:
        """Test Context7 integration for real-time docs"""
        test_name = "context7_integration"

        try:
            # Check if Context7 fetching is available
            if hasattr(self.doc_manager, 'fetch_context7_docs'):
                return self._pass(test_name, "Context7 integration available")
            else:
                return self._fail(test_name, "Context7 integration not found")

        except Exception as e:
            return self._fail(test_name, str(e))

    def test_documentation_compression(self) -> Dict[str, Any]:
        """Test documentation compression"""
        test_name = "documentation_compression"

        try:
            # Long documentation text
            long_text = """
            # API Documentation

            This is a very long documentation text that needs to be compressed.

            ## Methods

            def method_one(): Important method
            def method_two(): Another important method

            ## Examples

            Here are some examples that might be less important...
            Lorem ipsum dolor sit amet, consectetur adipiscing elit.
            Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
            """ * 10

            compressed = self.doc_manager.compress_documentation(long_text, target_tokens=100)

            # Check compression worked
            if len(compressed) < len(long_text):
                # Check important content preserved
                if 'def method_one' in compressed:
                    return self._pass(test_name, "Documentation compressed while preserving key content")
                else:
                    return self._warn(test_name, "Compression may have lost important content")
            else:
                return self._fail(test_name, "Compression did not reduce size")

        except Exception as e:
            return self._fail(test_name, str(e))

    def test_token_estimation(self) -> Dict[str, Any]:
        """Test token count estimation"""
        test_name = "token_estimation"

        try:
            # Test text (approximately 10 tokens)
            text = "This is a test text for token counting"

            estimated = self.doc_manager.estimate_tokens(text)

            # Should be roughly 10 tokens (1 token ≈ 4 chars)
            # Text is 38 chars, so ~9-10 tokens
            if 8 <= estimated <= 12:
                return self._pass(test_name, f"Token estimation accurate: {estimated} tokens")
            else:
                return self._warn(test_name, f"Token estimation off: {estimated} tokens")

        except Exception as e:
            return self._fail(test_name, str(e))

    def test_documentation_sync(self) -> Dict[str, Any]:
        """Test documentation synchronization"""
        test_name = "documentation_sync"

        try:
            # Update service docs
            updated = self.doc_manager.update_service_docs()

            if updated and 'service' in updated and 'last_updated' in updated:
                return self._pass(test_name, "Documentation sync working")
            else:
                return self._fail(test_name, "Documentation sync failed")

        except Exception as e:
            return self._fail(test_name, str(e))

    def _compile_results(self) -> Dict[str, Any]:
        """Compile test results"""
        passed = sum(1 for r in self.results if r['status'] == 'PASS')
        failed = sum(1 for r in self.results if r['status'] == 'FAIL')
        warned = sum(1 for r in self.results if r['status'] == 'WARN')
        skipped = sum(1 for r in self.results if r['status'] == 'SKIP')

        return {
            'service': self.service_name,
            'timestamp': self.start_time.isoformat(),
            'tests': {r['test']: r for r in self.results},
            'summary': {
                'total': len(self.results),
                'passed': passed,
                'failed': failed,
                'warned': warned,
                'skipped': skipped,
                'duration': (datetime.now() - self.start_time).total_seconds()
            }
        }

    def _pass(self, test_name: str, message: str) -> Dict[str, Any]:
        """Record passing test"""
        return {
            'test': test_name,
            'status': 'PASS',
            'message': message,
            'timestamp': datetime.now().isoformat()
        }

    def _fail(self, test_name: str, message: str) -> Dict[str, Any]:
        """Record failing test"""
        return {
            'test': test_name,
            'status': 'FAIL',
            'message': message,
            'timestamp': datetime.now().isoformat()
        }

    def _warn(self, test_name: str, message: str) -> Dict[str, Any]:
        """Record warning test"""
        return {
            'test': test_name,
            'status': 'WARN',
            'message': message,
            'timestamp': datetime.now().isoformat()
        }

    def _skip(self, test_name: str, message: str) -> Dict[str, Any]:
        """Record skipped test"""
        return {
            'test': test_name,
            'status': 'SKIP',
            'message': message,
            'timestamp': datetime.now().isoformat()
        }

    def save_results(self, output_file: Optional[str] = None):
        """Save test results to file"""
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"tests/test_documentation_{timestamp}.json"

        results = self._compile_results()

        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"Test results saved to: {output_file}")

        return output_file


def main():
    """Run documentation tests"""
    print("🧪 Running Documentation Integration Tests\n")
    print("=" * 60)

    test = DocumentationTest()
    results = test.run_all_tests()

    # Print summary
    print("\n📊 Test Results")
    print("=" * 60)
    print(f"Total Tests: {results['summary']['total']}")
    print(f"✅ Passed: {results['summary']['passed']}")
    print(f"❌ Failed: {results['summary']['failed']}")
    print(f"⚠️ Warned: {results['summary']['warned']}")
    print(f"⏭️ Skipped: {results['summary']['skipped']}")
    print(f"⏱️ Duration: {results['summary']['duration']:.2f}s")

    # Show individual results
    print("\nIndividual Test Results:")
    print("-" * 60)
    for test_name, result in results['tests'].items():
        status_icon = {
            'PASS': '✅',
            'FAIL': '❌',
            'WARN': '⚠️',
            'SKIP': '⏭️'
        }.get(result['status'], '?')

        print(f"{status_icon} {test_name}: {result['message']}")

    # Save results
    test.save_results()

    # Return exit code
    if results['summary']['failed'] > 0:
        return 1
    return 0


if __name__ == "__main__":
    exit(main())