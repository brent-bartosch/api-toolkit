#!/usr/bin/env python3
"""
Test Suite for Smartlead API Service
"""

import os
import sys
from typing import Dict, Any

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.base_test import ServiceTestBase
from services.smartlead.api import SmartleadAPI

class SmartleadTest(ServiceTestBase):
    """Smartlead-specific test implementation"""

    def get_test_config(self) -> Dict[str, Any]:
        return {
            'api_key_env': 'SMARTLEAD_API_KEY',
            'requires_auth': True,
            'rate_limit': 5,  # 10 requests per 2 seconds = 5/sec
            'test_endpoint': 'campaigns/list',
            'test_params': {'limit': 1}
        }

    # ============= SMARTLEAD-SPECIFIC TESTS =============

    def test_campaign_operations(self) -> Dict[str, Any]:
        """Test campaign-related operations"""
        test_name = "campaign_operations"

        try:
            if not self.api:
                return self._skip(test_name, "API not initialized")

            # Check campaign methods exist
            required_methods = [
                'create_campaign',
                'get_campaign',
                'list_campaigns',
                'update_campaign_settings',
                'pause_campaign',
                'resume_campaign'
            ]

            missing = []
            for method in required_methods:
                if not hasattr(self.api, method):
                    missing.append(method)

            if missing:
                return self._fail(test_name, f"Missing methods: {', '.join(missing)}")

            return self._pass(test_name, "All campaign methods available")

        except Exception as e:
            return self._fail(test_name, f"Campaign operations test failed: {e}")

    def test_lead_operations(self) -> Dict[str, Any]:
        """Test lead-related operations"""
        test_name = "lead_operations"

        try:
            if not self.api:
                return self._skip(test_name, "API not initialized")

            # Check lead methods exist
            required_methods = [
                'add_leads_to_campaign',
                'get_lead',
                'get_lead_status',
                'update_lead_category',
                'block_lead',
                'unblock_lead'
            ]

            missing = []
            for method in required_methods:
                if not hasattr(self.api, method):
                    missing.append(method)

            if missing:
                return self._fail(test_name, f"Missing methods: {', '.join(missing)}")

            return self._pass(test_name, "All lead methods available")

        except Exception as e:
            return self._fail(test_name, f"Lead operations test failed: {e}")

    def test_webhook_support(self) -> Dict[str, Any]:
        """Test webhook functionality"""
        test_name = "webhook_support"

        try:
            if not self.api:
                return self._skip(test_name, "API not initialized")

            # Check webhook methods
            if hasattr(self.api, 'register_webhook') and \
               hasattr(self.api, 'list_webhooks') and \
               hasattr(self.api, 'delete_webhook'):
                return self._pass(test_name, "Webhook support available")
            else:
                return self._warn(test_name, "Incomplete webhook support")

        except Exception as e:
            return self._fail(test_name, f"Webhook test failed: {e}")

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests including Smartlead-specific ones"""
        # Run base tests first
        results = super().run_all_tests()

        # Add Smartlead-specific tests
        print("\n📧 Running Smartlead-specific tests...")

        specific_tests = [
            ('Campaign Operations', self.test_campaign_operations),
            ('Lead Operations', self.test_lead_operations),
            ('Webhook Support', self.test_webhook_support),
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
    test = SmartleadTest(SmartleadAPI, 'Smartlead')
    results = test.run_all_tests()
    test.save_results()