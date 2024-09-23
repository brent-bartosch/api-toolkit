#!/usr/bin/env python3
"""
Test Suite for Shopify API Service
"""

import os
import sys
from typing import Dict, Any

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.base_test import ServiceTestBase
from services.shopify.api import ShopifyAPI


class ShopifyTest(ServiceTestBase):
    """Shopify-specific test implementation"""

    def get_test_config(self) -> Dict[str, Any]:
        return {
            'api_key_env': 'SHOPIFY_ACCESS_TOKEN',
            'requires_auth': True,
            'rate_limit': 2,  # Shopify rate limit
            'test_endpoint': f'admin/api/{ShopifyAPI.API_VERSION}/shop.json',
            'test_params': {}
        }

    # ============= SHOPIFY-SPECIFIC TESTS =============

    def test_product_operations(self) -> Dict[str, Any]:
        """Test product-related operations"""
        test_name = "product_operations"

        try:
            if not self.api:
                return self._skip(test_name, "API not initialized")

            # Check product methods exist
            required_methods = [
                'list_products',
                'get_product',
                'create_product',
                'update_product',
                'delete_product',
                'count_products'
            ]

            missing = []
            for method in required_methods:
                if not hasattr(self.api, method):
                    missing.append(method)

            if missing:
                return self._fail(test_name, f"Missing methods: {', '.join(missing)}")

            return self._pass(test_name, "All product methods available")

        except Exception as e:
            return self._fail(test_name, f"Product operations test failed: {e}")

    def test_order_operations(self) -> Dict[str, Any]:
        """Test order-related operations"""
        test_name = "order_operations"

        try:
            if not self.api:
                return self._skip(test_name, "API not initialized")

            # Check order methods exist
            required_methods = [
                'list_orders',
                'get_order',
                'cancel_order',
                'close_order',
                'count_orders'
            ]

            missing = []
            for method in required_methods:
                if not hasattr(self.api, method):
                    missing.append(method)

            if missing:
                return self._fail(test_name, f"Missing methods: {', '.join(missing)}")

            return self._pass(test_name, "All order methods available")

        except Exception as e:
            return self._fail(test_name, f"Order operations test failed: {e}")

    def test_customer_operations(self) -> Dict[str, Any]:
        """Test customer-related operations"""
        test_name = "customer_operations"

        try:
            if not self.api:
                return self._skip(test_name, "API not initialized")

            # Check customer methods exist
            required_methods = [
                'list_customers',
                'get_customer',
                'search_customers',
                'get_customer_orders',
                'count_customers'
            ]

            missing = []
            for method in required_methods:
                if not hasattr(self.api, method):
                    missing.append(method)

            if missing:
                return self._fail(test_name, f"Missing methods: {', '.join(missing)}")

            return self._pass(test_name, "All customer methods available")

        except Exception as e:
            return self._fail(test_name, f"Customer operations test failed: {e}")

    def test_shop_operations(self) -> Dict[str, Any]:
        """Test shop-related operations"""
        test_name = "shop_operations"

        try:
            if not self.api:
                return self._skip(test_name, "API not initialized")

            # Check shop methods exist
            required_methods = [
                'get_shop',
                'test_connection'
            ]

            missing = []
            for method in required_methods:
                if not hasattr(self.api, method):
                    missing.append(method)

            if missing:
                return self._fail(test_name, f"Missing methods: {', '.join(missing)}")

            return self._pass(test_name, "All shop methods available")

        except Exception as e:
            return self._fail(test_name, f"Shop operations test failed: {e}")

    def test_query_builder(self) -> Dict[str, Any]:
        """Test query builder functionality"""
        test_name = "query_builder"

        try:
            from services.shopify.query_helpers import ShopifyQueryBuilder, CommonQueries

            # Test building a product query
            query = (ShopifyQueryBuilder('products')
                     .status('active')
                     .vendor('Test')
                     .limit(10))
            params = query.build()

            # Verify params structure
            assert 'status' in params, "Missing status in params"
            assert 'vendor' in params, "Missing vendor in params"
            assert params['limit'] == 10, "Limit not set correctly"

            # Test CommonQueries
            recent_params = CommonQueries.recent_orders(days=7)
            assert 'created_at_min' in recent_params, "Missing date filter"

            return self._pass(test_name, "Query builder works correctly")

        except ImportError:
            return self._fail(test_name, "Could not import query_helpers")
        except AssertionError as e:
            return self._fail(test_name, str(e))
        except Exception as e:
            return self._fail(test_name, f"Query builder test failed: {e}")

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests including Shopify-specific ones"""
        # Run base tests first
        results = super().run_all_tests()

        # Add Shopify-specific tests
        print("\n🛒 Running Shopify-specific tests...")

        specific_tests = [
            ('Product Operations', self.test_product_operations),
            ('Order Operations', self.test_order_operations),
            ('Customer Operations', self.test_customer_operations),
            ('Shop Operations', self.test_shop_operations),
            ('Query Builder', self.test_query_builder),
        ]

        for test_name, test_method in specific_tests:
            print(f"Running: {test_name}...", end=" ")
            result = test_method()

            # Print result
            status = result['status']
            if status == 'PASS':
                print(f"PASS")
            elif status == 'FAIL':
                print(f"FAIL: {result['message']}")
            elif status == 'SKIP':
                print(f"SKIP: {result['message']}")
            elif status == 'WARN':
                print(f"WARN: {result['message']}")

        return self.results


if __name__ == "__main__":
    test = ShopifyTest(ShopifyAPI, 'Shopify')
    results = test.run_all_tests()
    test.save_results()
