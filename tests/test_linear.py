#!/usr/bin/env python3
"""
Test Suite for Linear API Service
"""

import os
import sys
from typing import Dict, Any

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.base_test import ServiceTestBase
from services.linear.api import LinearAPI

# Ensure .env is loaded before setup() checks for the API key
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))


class LinearTest(ServiceTestBase):
    """Linear-specific test implementation"""

    def get_test_config(self) -> Dict[str, Any]:
        return {
            'api_key_env': 'LINEAR_API_KEY',
            'requires_auth': True,
            'rate_limit': 10,
            'test_endpoint': None,  # GraphQL: test_connection() handles this
            'test_params': {}
        }

    # ============= LINEAR-SPECIFIC TESTS =============

    def test_issue_operations(self) -> Dict[str, Any]:
        """Verify read methods exist and return expected shapes"""
        test_name = "issue_operations"

        try:
            if not self.api:
                return self._skip(test_name, "API not initialized")

            required_methods = [
                'list_teams', 'list_projects', 'list_issues',
                'get_issue', 'search_issues', 'health_check',
                'get_sprint_status', 'create_issue', 'update_issue',
                'add_comment', 'log_milestone'
            ]
            missing = [m for m in required_methods if not hasattr(self.api, m)]
            if missing:
                return self._fail(test_name, f"Missing methods: {', '.join(missing)}")

            teams = self.api.list_teams()
            assert isinstance(teams, list), "list_teams did not return a list"

            issues = self.api.list_issues(limit=5)
            assert isinstance(issues, list), "list_issues did not return a list"
            if issues:
                sample = issues[0]
                for field in ('identifier', 'title', 'state'):
                    assert field in sample, f"Issue missing field: {field}"

            return self._pass(
                test_name,
                f"All methods available; {len(teams)} team(s), {len(issues)} issue(s) fetched"
            )

        except Exception as e:
            return self._fail(test_name, f"Issue operations test failed: {e}")

    def test_search(self) -> Dict[str, Any]:
        """Search returns a list without erroring"""
        test_name = "search"

        try:
            if not self.api:
                return self._skip(test_name, "API not initialized")

            results = self.api.search_issues("test", limit=3)
            assert isinstance(results, list), "search_issues did not return a list"
            return self._pass(test_name, f"Search returned {len(results)} result(s)")

        except Exception as e:
            return self._fail(test_name, f"Search test failed: {e}")

    def test_health_report(self) -> Dict[str, Any]:
        """Health check produces a summary"""
        test_name = "health_report"

        try:
            if not self.api:
                return self._skip(test_name, "API not initialized")

            report = self.api.health_check()
            assert isinstance(report, dict), "health_check did not return a dict"
            assert 'summary' in report, "health_check missing summary key"
            return self._pass(test_name, str(report['summary'])[:80])

        except Exception as e:
            return self._fail(test_name, f"Health check failed: {e}")

    def test_query_helpers(self) -> Dict[str, Any]:
        """Pre-built GraphQL queries construct valid strings"""
        test_name = "query_helpers"

        try:
            from services.linear import query_helpers as qh

            viewer = qh.viewer_query()
            assert "viewer" in viewer

            search = qh.search_issues_query('my "quoted" term', limit=5)
            assert '\\"' in search, "Quote escaping not applied"
            assert "first: 5" in search

            detail = qh.issue_by_identifier_query("ENG-123")
            assert "issueSearch" in detail
            assert "comments" in detail

            return self._pass(test_name, "Query helpers build correctly")

        except ImportError:
            return self._fail(test_name, "Could not import query_helpers")
        except AssertionError as e:
            return self._fail(test_name, str(e))
        except Exception as e:
            return self._fail(test_name, f"Query helper test failed: {e}")

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests including Linear-specific ones"""
        results = super().run_all_tests()

        # Base teardown() nulls self.api before subclass tests run
        if not self.api:
            self.setup()

        print("\n📋 Running Linear-specific tests...")

        specific_tests = [
            ('Issue Operations', self.test_issue_operations),
            ('Search', self.test_search),
            ('Health Report', self.test_health_report),
            ('Query Helpers', self.test_query_helpers),
        ]

        for test_name, test_method in specific_tests:
            print(f"Running: {test_name}...", end=" ")
            result = test_method()

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
    test = LinearTest(LinearAPI, 'Linear')
    results = test.run_all_tests()
    test.save_results()
