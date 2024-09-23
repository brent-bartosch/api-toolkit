#!/usr/bin/env python3
"""
Test Runner for API Toolkit

Runs all service tests and generates a comprehensive report.
"""

import os
import sys
import json
import importlib
from datetime import datetime
from typing import Dict, Any, List
import traceback

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestRunner:
    """Orchestrates running tests for all services"""

    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'services': {},
            'summary': {
                'total_services': 0,
                'services_passed': 0,
                'services_failed': 0,
                'total_tests': 0,
                'tests_passed': 0,
                'tests_failed': 0,
                'tests_skipped': 0
            }
        }

    def discover_tests(self) -> List[Dict[str, Any]]:
        """Discover all test files in the tests directory"""
        tests = []
        test_dir = os.path.dirname(os.path.abspath(__file__))

        for filename in os.listdir(test_dir):
            if filename.startswith('test_') and filename.endswith('.py'):
                service_name = filename[5:-3]  # Remove 'test_' and '.py'

                # Skip if it's a template or base
                if service_name in ['base', 'template', 'example']:
                    continue

                tests.append({
                    'service': service_name,
                    'module': filename[:-3],
                    'file': os.path.join(test_dir, filename)
                })

        return sorted(tests, key=lambda x: x['service'])

    def run_service_test(self, test_info: Dict[str, Any]) -> Dict[str, Any]:
        """Run tests for a single service"""
        service_name = test_info['service']
        module_name = test_info['module']

        print(f"\n{'='*60}")
        print(f"🧪 Testing {service_name.title()} Service")
        print(f"{'='*60}")

        try:
            # Import the test module
            test_module = importlib.import_module(f'tests.{module_name}')

            # Find the test class (should be named like SmartleadTest)
            test_class_name = f"{service_name.title()}Test"
            if hasattr(test_module, test_class_name):
                test_class = getattr(test_module, test_class_name)

                # Get the API class
                api_module = importlib.import_module(f'services.{service_name}.api')
                api_class_name = f"{service_name.title()}API"
                if hasattr(api_module, api_class_name):
                    api_class = getattr(api_module, api_class_name)
                else:
                    # Try alternative naming
                    api_class = getattr(api_module, f"{service_name.upper()}API", None)

                if api_class:
                    # Run the tests
                    test_instance = test_class(api_class, service_name.title())
                    results = test_instance.run_all_tests()
                    return results
                else:
                    return {
                        'service': service_name,
                        'error': f"API class not found: {api_class_name}",
                        'summary': {'total': 0, 'passed': 0, 'failed': 1, 'skipped': 0}
                    }
            else:
                return {
                    'service': service_name,
                    'error': f"Test class not found: {test_class_name}",
                    'summary': {'total': 0, 'passed': 0, 'failed': 1, 'skipped': 0}
                }

        except ImportError as e:
            print(f"❌ Could not import test: {e}")
            return {
                'service': service_name,
                'error': f"Import error: {e}",
                'summary': {'total': 0, 'passed': 0, 'failed': 1, 'skipped': 0}
            }
        except Exception as e:
            print(f"❌ Test failed: {e}")
            traceback.print_exc()
            return {
                'service': service_name,
                'error': f"Test execution error: {e}",
                'summary': {'total': 0, 'passed': 0, 'failed': 1, 'skipped': 0}
            }

    def run_all_tests(self, services: List[str] = None):
        """Run tests for all or specified services"""
        # Discover available tests
        available_tests = self.discover_tests()

        if not available_tests:
            print("❌ No tests found!")
            return

        # Filter by specified services if provided
        if services:
            tests_to_run = [t for t in available_tests
                          if t['service'] in services]
        else:
            tests_to_run = available_tests

        print(f"\n🚀 API Toolkit Test Suite")
        print(f"{'='*60}")
        print(f"Found {len(tests_to_run)} service(s) to test")
        print(f"Services: {', '.join([t['service'] for t in tests_to_run])}")

        # Run tests for each service
        for test_info in tests_to_run:
            service_results = self.run_service_test(test_info)
            self.results['services'][test_info['service']] = service_results

            # Update summary
            self.results['summary']['total_services'] += 1

            if 'summary' in service_results:
                summary = service_results['summary']
                self.results['summary']['total_tests'] += summary.get('total', 0)
                self.results['summary']['tests_passed'] += summary.get('passed', 0)
                self.results['summary']['tests_failed'] += summary.get('failed', 0)
                self.results['summary']['tests_skipped'] += summary.get('skipped', 0)

                if summary.get('failed', 0) == 0:
                    self.results['summary']['services_passed'] += 1
                else:
                    self.results['summary']['services_failed'] += 1

    def print_summary(self):
        """Print overall test summary"""
        print(f"\n{'='*60}")
        print(f"📊 Overall Test Summary")
        print(f"{'='*60}")

        summary = self.results['summary']

        print(f"\nServices:")
        print(f"  Total:  {summary['total_services']}")
        print(f"  Passed: {summary['services_passed']} ✅")
        print(f"  Failed: {summary['services_failed']} ❌")

        print(f"\nTests:")
        print(f"  Total:   {summary['total_tests']}")
        print(f"  Passed:  {summary['tests_passed']} ✅")
        print(f"  Failed:  {summary['tests_failed']} ❌")
        print(f"  Skipped: {summary['tests_skipped']} ⏭️")

        # Success rate
        if summary['total_tests'] > 0:
            success_rate = (summary['tests_passed'] / summary['total_tests']) * 100
            print(f"\nSuccess Rate: {success_rate:.1f}%")

        # Service details
        print(f"\n{'='*60}")
        print(f"Service Details:")
        print(f"{'='*60}")

        for service, results in self.results['services'].items():
            if 'error' in results:
                print(f"\n{service.title()}: ❌ ERROR")
                print(f"  {results['error']}")
            elif 'summary' in results:
                s = results['summary']
                status = "✅" if s.get('failed', 0) == 0 else "❌"
                print(f"\n{service.title()}: {status}")
                print(f"  Tests: {s.get('total', 0)} total, "
                      f"{s.get('passed', 0)} passed, "
                      f"{s.get('failed', 0)} failed, "
                      f"{s.get('skipped', 0)} skipped")

    def save_report(self, filename: str = None):
        """Save test results to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_report_{timestamp}.json"

        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               filename)

        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"\n📝 Report saved to: {filepath}")

    def generate_markdown_report(self) -> str:
        """Generate a markdown report of test results"""
        md = []
        md.append("# API Toolkit Test Report")
        md.append(f"\n**Generated**: {self.results['timestamp']}")

        # Summary
        summary = self.results['summary']
        md.append("\n## Summary")
        md.append(f"- **Services Tested**: {summary['total_services']}")
        md.append(f"- **Services Passed**: {summary['services_passed']} ✅")
        md.append(f"- **Services Failed**: {summary['services_failed']} ❌")
        md.append(f"- **Total Tests**: {summary['total_tests']}")
        md.append(f"- **Tests Passed**: {summary['tests_passed']} ✅")
        md.append(f"- **Tests Failed**: {summary['tests_failed']} ❌")
        md.append(f"- **Tests Skipped**: {summary['tests_skipped']} ⏭️")

        # Service details
        md.append("\n## Service Details")

        for service, results in self.results['services'].items():
            md.append(f"\n### {service.title()}")

            if 'error' in results:
                md.append(f"**Status**: ❌ ERROR")
                md.append(f"\n```\n{results['error']}\n```")
            elif 'tests' in results:
                s = results.get('summary', {})
                status = "✅ PASSED" if s.get('failed', 0) == 0 else "❌ FAILED"
                md.append(f"**Status**: {status}")
                md.append(f"\n**Test Results**:")

                # Create a table of test results
                md.append("\n| Test | Status | Message |")
                md.append("|------|--------|---------|")

                for test_name, test_result in results['tests'].items():
                    status_icon = {
                        'PASS': '✅',
                        'FAIL': '❌',
                        'SKIP': '⏭️',
                        'WARN': '⚠️'
                    }.get(test_result.get('status', 'UNKNOWN'), '❓')

                    message = test_result.get('message', '').replace('|', '\\|')
                    md.append(f"| {test_name} | {status_icon} {test_result.get('status', 'UNKNOWN')} | {message} |")

        return "\n".join(md)

    def save_markdown_report(self, filename: str = None):
        """Save markdown report to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_report_{timestamp}.md"

        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               filename)

        with open(filepath, 'w') as f:
            f.write(self.generate_markdown_report())

        print(f"📄 Markdown report saved to: {filepath}")


def main():
    """Main entry point for test runner"""
    import argparse

    parser = argparse.ArgumentParser(description='Run API Toolkit tests')
    parser.add_argument('services', nargs='*',
                       help='Specific services to test (default: all)')
    parser.add_argument('--save', action='store_true',
                       help='Save test results to file')
    parser.add_argument('--markdown', action='store_true',
                       help='Generate markdown report')
    parser.add_argument('--output', type=str,
                       help='Output filename for report')

    args = parser.parse_args()

    # Create test runner
    runner = TestRunner()

    # Run tests
    runner.run_all_tests(args.services if args.services else None)

    # Print summary
    runner.print_summary()

    # Save results if requested
    if args.save:
        runner.save_report(args.output)

    if args.markdown:
        runner.save_markdown_report(
            args.output.replace('.json', '.md') if args.output else None
        )

    # Exit with appropriate code
    if runner.results['summary']['tests_failed'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()