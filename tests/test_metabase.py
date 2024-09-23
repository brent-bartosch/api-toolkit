#!/usr/bin/env python3
"""
Test Suite for Metabase API Service
"""

import os
import sys
from typing import Dict, Any

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.base_test import ServiceTestBase
from services.metabase.api import MetabaseAPI

class MetabaseTest(ServiceTestBase):
    """Metabase-specific test implementation"""

    def get_test_config(self) -> Dict[str, Any]:
        return {
            'api_key_env': 'METABASE_API_KEY',
            'requires_auth': True,
            'rate_limit': 10,
            'test_endpoint': 'database',
            'test_params': {}
        }

    # ============= METABASE-SPECIFIC TESTS =============

    def test_database_operations(self) -> Dict[str, Any]:
        """Test database-related operations"""
        test_name = "database_operations"

        try:
            if not self.api:
                return self._skip(test_name, "API not initialized")

            # Check database methods exist
            required_methods = [
                'list_databases',
                'get_database',
                'get_database_metadata'
            ]

            missing = []
            for method in required_methods:
                if not hasattr(self.api, method):
                    missing.append(method)

            if missing:
                return self._fail(test_name, f"Missing methods: {', '.join(missing)}")

            # Try to list databases
            try:
                databases = self.api.list_databases()
                if isinstance(databases, (list, dict)):
                    return self._pass(test_name, "Database operations working")
            except Exception as e:
                if '401' in str(e) or 'unauthorized' in str(e).lower():
                    return self._warn(test_name, "Database operations require auth")
                raise

            return self._pass(test_name, "All database methods available")

        except Exception as e:
            return self._fail(test_name, f"Database operations test failed: {e}")

    def test_card_operations(self) -> Dict[str, Any]:
        """Test card/question operations"""
        test_name = "card_operations"

        try:
            if not self.api:
                return self._skip(test_name, "API not initialized")

            # Check card methods exist
            required_methods = [
                'list_cards',
                'get_card',
                'create_card',
                'update_card',
                'delete_card',
                'query_card'
            ]

            missing = []
            for method in required_methods:
                if not hasattr(self.api, method):
                    missing.append(method)

            if missing:
                return self._fail(test_name, f"Missing methods: {', '.join(missing)}")

            return self._pass(test_name, "All card methods available")

        except Exception as e:
            return self._fail(test_name, f"Card operations test failed: {e}")

    def test_dashboard_operations(self) -> Dict[str, Any]:
        """Test dashboard operations"""
        test_name = "dashboard_operations"

        try:
            if not self.api:
                return self._skip(test_name, "API not initialized")

            # Check dashboard methods exist
            required_methods = [
                'list_dashboards',
                'get_dashboard',
                'create_dashboard',
                'add_card_to_dashboard'
            ]

            missing = []
            for method in required_methods:
                if not hasattr(self.api, method):
                    missing.append(method)

            if missing:
                return self._fail(test_name, f"Missing methods: {', '.join(missing)}")

            return self._pass(test_name, "All dashboard methods available")

        except Exception as e:
            return self._fail(test_name, f"Dashboard operations test failed: {e}")

    def test_export_capabilities(self) -> Dict[str, Any]:
        """Test data export functionality"""
        test_name = "export_capabilities"

        try:
            if not self.api:
                return self._skip(test_name, "API not initialized")

            # Check export method
            if hasattr(self.api, 'export_card'):
                return self._pass(test_name, "Export capabilities available")
            else:
                return self._fail(test_name, "Export method not found")

        except Exception as e:
            return self._fail(test_name, f"Export test failed: {e}")

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests including Metabase-specific ones"""
        # Run base tests first
        results = super().run_all_tests()

        # Add Metabase-specific tests
        print("\n📊 Running Metabase-specific tests...")

        specific_tests = [
            ('Database Operations', self.test_database_operations),
            ('Card Operations', self.test_card_operations),
            ('Dashboard Operations', self.test_dashboard_operations),
            ('Export Capabilities', self.test_export_capabilities),
        ]

        for test_name, test_method in specific_tests:
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

        return self.results


if __name__ == "__main__":
    test = MetabaseTest(MetabaseAPI, 'Metabase')
    results = test.run_all_tests()
    test.save_results()