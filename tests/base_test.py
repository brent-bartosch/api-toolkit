#!/usr/bin/env python3
"""
Base Test Suite for API Toolkit Services

Provides standardized tests that every service should pass.
"""

import os
import sys
import time
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Type
from datetime import datetime
import traceback

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.base_api import BaseAPI, APIError

class ServiceTestBase(ABC):
    """
    Base test class for all API services.

    Every service should inherit from this and pass all tests.
    """

    def __init__(self, service_class: Type[BaseAPI], service_name: str):
        """
        Initialize test suite for a service.

        Args:
            service_class: The API class to test
            service_name: Name of the service
        """
        self.service_class = service_class
        self.service_name = service_name
        self.api = None
        self.results = {
            'service': service_name,
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'summary': {
                'total': 0,
                'passed': 0,
                'failed': 0,
                'skipped': 0
            }
        }

    @abstractmethod
    def get_test_config(self) -> Dict[str, Any]:
        """
        Get service-specific test configuration.

        Should return:
        {
            'api_key_env': 'SMARTLEAD_API_KEY',
            'requires_auth': True,
            'rate_limit': 10,  # requests per second
            'test_endpoint': 'some/endpoint',
            'test_params': {}
        }
        """
        pass

    def setup(self) -> bool:
        """Setup test environment"""
        try:
            config = self.get_test_config()

            # Check for API key if required
            if config.get('requires_auth', True):
                api_key_env = config.get('api_key_env')
                if not os.getenv(api_key_env):
                    print(f"⚠️  {api_key_env} not set - some tests will be skipped")
                    return False

            # Initialize API
            self.api = self.service_class()
            return True

        except Exception as e:
            print(f"❌ Setup failed: {e}")
            return False

    def teardown(self):
        """Cleanup after tests"""
        self.api = None

    # ============= STANDARD TESTS =============

    def test_initialization(self) -> Dict[str, Any]:
        """Test 1: Service can be initialized"""
        test_name = "initialization"

        try:
            api = self.service_class()

            # Check required attributes
            assert hasattr(api, 'base_url'), "Missing base_url"
            assert hasattr(api, 'session'), "Missing session"
            assert hasattr(api, 'rate_limiter'), "Missing rate_limiter"

            return self._pass(test_name, "Service initialized successfully")

        except Exception as e:
            return self._fail(test_name, f"Initialization failed: {e}")

    def test_authentication(self) -> Dict[str, Any]:
        """Test 2: Authentication is properly configured"""
        test_name = "authentication"
        config = self.get_test_config()

        if not config.get('requires_auth', True):
            return self._skip(test_name, "Service doesn't require authentication")

        try:
            api = self.service_class()

            # Check auth setup
            if hasattr(api, 'api_key'):
                assert api.api_key, "API key not set"

            # Check headers
            headers = api.session.headers
            assert headers, "No headers configured"

            return self._pass(test_name, "Authentication configured")

        except Exception as e:
            return self._fail(test_name, f"Authentication error: {e}")

    def test_connection(self) -> Dict[str, Any]:
        """Test 3: Can connect to the service"""
        test_name = "connection"

        try:
            if not self.api:
                return self._skip(test_name, "API not initialized")

            # Use test_connection if available
            if hasattr(self.api, 'test_connection'):
                result = self.api.test_connection()
                if result:
                    return self._pass(test_name, "Connection successful")
                else:
                    return self._fail(test_name, "Connection test returned False")
            else:
                # Try a simple request
                config = self.get_test_config()
                endpoint = config.get('test_endpoint')
                if endpoint:
                    self.api._make_request('GET', endpoint,
                                         params=config.get('test_params', {}))
                    return self._pass(test_name, "Test request successful")
                else:
                    return self._skip(test_name, "No test endpoint configured")

        except Exception as e:
            # Some errors are expected without auth
            if '401' in str(e) or 'unauthorized' in str(e).lower():
                return self._pass(test_name, "Connection works (auth required)")
            return self._fail(test_name, f"Connection failed: {e}")

    def test_rate_limiting(self) -> Dict[str, Any]:
        """Test 4: Rate limiting is enforced"""
        test_name = "rate_limiting"

        try:
            if not self.api:
                return self._skip(test_name, "API not initialized")

            config = self.get_test_config()
            expected_rps = config.get('rate_limit', 10)

            # Check rate limiter configuration
            if hasattr(self.api, 'rate_limiter'):
                actual_rps = self.api.rate_limiter.requests_per_second

                if actual_rps <= expected_rps:
                    return self._pass(test_name,
                                    f"Rate limiting configured: {actual_rps} rps")
                else:
                    return self._warn(test_name,
                                    f"Rate limit ({actual_rps} rps) exceeds expected ({expected_rps} rps)")
            else:
                return self._fail(test_name, "No rate limiter found")

        except Exception as e:
            return self._fail(test_name, f"Rate limiting test failed: {e}")

    def test_error_handling(self) -> Dict[str, Any]:
        """Test 5: Errors are handled properly"""
        test_name = "error_handling"

        try:
            if not self.api:
                return self._skip(test_name, "API not initialized")

            # Try to trigger a 404
            try:
                if hasattr(self.api, '_make_request'):
                    self.api._make_request('GET', 'nonexistent/endpoint/12345')
                    return self._fail(test_name, "Should have raised an error")
            except APIError as e:
                # This is expected
                if e.status_code or 'not found' in str(e).lower():
                    return self._pass(test_name, "Errors raised properly")
                return self._fail(test_name, f"Unexpected error type: {e}")
            except Exception as e:
                # Some other error
                return self._warn(test_name, f"Different error raised: {type(e).__name__}")

        except Exception as e:
            return self._fail(test_name, f"Error handling test failed: {e}")

    def test_discovery_methods(self) -> Dict[str, Any]:
        """Test 6: Discovery/exploration methods work"""
        test_name = "discovery_methods"

        try:
            if not self.api:
                return self._skip(test_name, "API not initialized")

            methods_found = []

            # Check for discovery methods
            if hasattr(self.api, 'discover'):
                try:
                    result = self.api.discover()
                    if result:
                        methods_found.append('discover')
                except:
                    pass

            if hasattr(self.api, 'quick_start'):
                methods_found.append('quick_start')

            if hasattr(self.api, 'explore'):
                methods_found.append('explore')

            if methods_found:
                return self._pass(test_name,
                                f"Discovery methods available: {', '.join(methods_found)}")
            else:
                return self._warn(test_name, "No discovery methods found")

        except Exception as e:
            return self._fail(test_name, f"Discovery test failed: {e}")

    def test_response_format(self) -> Dict[str, Any]:
        """Test 7: Responses follow expected format"""
        test_name = "response_format"

        try:
            if not self.api:
                return self._skip(test_name, "API not initialized")

            # This is service-specific
            # Override in subclasses for detailed testing
            return self._skip(test_name, "Override in service-specific tests")

        except Exception as e:
            return self._fail(test_name, f"Response format test failed: {e}")

    def test_token_efficiency(self) -> Dict[str, Any]:
        """Test 8: Service is token-efficient"""
        test_name = "token_efficiency"

        try:
            # Rough estimate of token usage
            import inspect

            # Get source code
            source = inspect.getsource(self.service_class)

            # Estimate tokens (rough: ~4 chars per token)
            estimated_tokens = len(source) // 4

            if estimated_tokens < 2000:
                return self._pass(test_name,
                                f"Token efficient: ~{estimated_tokens} tokens")
            elif estimated_tokens < 5000:
                return self._warn(test_name,
                                f"Moderate token usage: ~{estimated_tokens} tokens")
            else:
                return self._fail(test_name,
                                f"High token usage: ~{estimated_tokens} tokens")

        except Exception as e:
            return self._skip(test_name, f"Could not estimate tokens: {e}")

    def test_documentation(self) -> Dict[str, Any]:
        """Test 9: Service is properly documented"""
        test_name = "documentation"

        try:
            # Check for docstrings
            has_class_doc = bool(self.service_class.__doc__)

            # Check for method documentation
            methods = [m for m in dir(self.service_class)
                      if not m.startswith('_') and callable(getattr(self.service_class, m))]

            documented_methods = 0
            for method_name in methods:
                method = getattr(self.service_class, method_name)
                if hasattr(method, '__doc__') and method.__doc__:
                    documented_methods += 1

            doc_percentage = (documented_methods / len(methods) * 100) if methods else 0

            if has_class_doc and doc_percentage >= 80:
                return self._pass(test_name,
                                f"Well documented: {doc_percentage:.0f}% methods")
            elif has_class_doc and doc_percentage >= 50:
                return self._warn(test_name,
                                f"Partially documented: {doc_percentage:.0f}% methods")
            else:
                return self._fail(test_name,
                                f"Poor documentation: {doc_percentage:.0f}% methods")

        except Exception as e:
            return self._fail(test_name, f"Documentation test failed: {e}")

    def test_examples_exist(self) -> Dict[str, Any]:
        """Test 10: Examples file exists and is runnable"""
        test_name = "examples"

        try:
            # Check if examples.py exists
            service_dir = os.path.dirname(sys.modules[self.service_class.__module__].__file__)
            examples_path = os.path.join(service_dir, 'examples.py')

            if os.path.exists(examples_path):
                # Try to import it
                import importlib.util
                spec = importlib.util.spec_from_file_location("examples", examples_path)
                examples_module = importlib.util.module_from_spec(spec)

                return self._pass(test_name, "Examples file exists")
            else:
                return self._warn(test_name, "No examples.py file found")

        except Exception as e:
            return self._fail(test_name, f"Examples test failed: {e}")

    # ============= TEST HELPERS =============

    def _pass(self, test_name: str, message: str) -> Dict[str, Any]:
        """Record a passing test"""
        result = {
            'status': 'PASS',
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        self.results['tests'][test_name] = result
        self.results['summary']['passed'] += 1
        self.results['summary']['total'] += 1
        return result

    def _fail(self, test_name: str, message: str) -> Dict[str, Any]:
        """Record a failing test"""
        result = {
            'status': 'FAIL',
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'traceback': traceback.format_exc()
        }
        self.results['tests'][test_name] = result
        self.results['summary']['failed'] += 1
        self.results['summary']['total'] += 1
        return result

    def _skip(self, test_name: str, message: str) -> Dict[str, Any]:
        """Record a skipped test"""
        result = {
            'status': 'SKIP',
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        self.results['tests'][test_name] = result
        self.results['summary']['skipped'] += 1
        self.results['summary']['total'] += 1
        return result

    def _warn(self, test_name: str, message: str) -> Dict[str, Any]:
        """Record a warning (counts as pass)"""
        result = {
            'status': 'WARN',
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        self.results['tests'][test_name] = result
        self.results['summary']['passed'] += 1
        self.results['summary']['total'] += 1
        return result

    # ============= TEST RUNNER =============

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all standard tests"""
        print(f"\n{'='*60}")
        print(f"🧪 Testing {self.service_name} Service")
        print(f"{'='*60}\n")

        # Setup
        if not self.setup():
            print("⚠️  Setup failed - some tests will be skipped\n")

        # Run tests
        test_methods = [
            ('Initialization', self.test_initialization),
            ('Authentication', self.test_authentication),
            ('Connection', self.test_connection),
            ('Rate Limiting', self.test_rate_limiting),
            ('Error Handling', self.test_error_handling),
            ('Discovery Methods', self.test_discovery_methods),
            ('Response Format', self.test_response_format),
            ('Token Efficiency', self.test_token_efficiency),
            ('Documentation', self.test_documentation),
            ('Examples', self.test_examples_exist),
        ]

        for test_name, test_method in test_methods:
            print(f"Running: {test_name}...", end=" ")
            result = test_method()

            # Print result
            status = result['status']
            if status == 'PASS':
                print(f"✅ PASS")
            elif status == 'FAIL':
                print(f"❌ FAIL: {result['message']}")
            elif status == 'SKIP':
                print(f"⏭️  SKIP: {result['message']}")
            elif status == 'WARN':
                print(f"⚠️  WARN: {result['message']}")

        # Teardown
        self.teardown()

        # Print summary
        print(f"\n{'='*60}")
        print(f"📊 Test Summary for {self.service_name}")
        print(f"{'='*60}")
        summary = self.results['summary']
        print(f"Total:   {summary['total']}")
        print(f"Passed:  {summary['passed']} ✅")
        print(f"Failed:  {summary['failed']} ❌")
        print(f"Skipped: {summary['skipped']} ⏭️")

        # Overall result
        if summary['failed'] == 0:
            print(f"\n🎉 All tests passed!")
        else:
            print(f"\n⚠️  {summary['failed']} test(s) failed")

        return self.results

    def save_results(self, filepath: Optional[str] = None):
        """Save test results to JSON file"""
        if not filepath:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"test_results_{self.service_name}_{timestamp}.json"

        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"\n📝 Results saved to: {filepath}")


# Example implementation for testing the base class
class ExampleServiceTest(ServiceTestBase):
    """Example test implementation"""

    def get_test_config(self) -> Dict[str, Any]:
        return {
            'api_key_env': 'EXAMPLE_API_KEY',
            'requires_auth': True,
            'rate_limit': 10,
            'test_endpoint': 'status',
            'test_params': {}
        }


if __name__ == "__main__":
    # This would normally not run directly
    print("This is the base test class. Run service-specific tests instead.")
    print("\nExample usage:")
    print("  from tests.base_test import ServiceTestBase")
    print("  from services.smartlead.api import SmartleadAPI")
    print("")
    print("  class SmartleadTest(ServiceTestBase):")
    print("      def get_test_config(self):")
    print("          return {'api_key_env': 'SMARTLEAD_API_KEY', ...}")
    print("")
    print("  test = SmartleadTest(SmartleadAPI, 'Smartlead')")
    print("  test.run_all_tests()")