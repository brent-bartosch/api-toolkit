# 🧪 API Toolkit Testing Reference

## Overview

Comprehensive testing framework for all API services in the toolkit, ensuring quality, consistency, and reliability across all integrations.

## 📂 Testing Structure

```
tests/
├── base_test.py              # Base test class with standard tests
├── test_smartlead.py         # Smartlead-specific tests
├── test_metabase.py          # Metabase-specific tests
├── run_all_tests.py          # Test runner and reporter
├── TESTING_GUIDE.md          # Testing best practices
├── TESTING_REFERENCE.md     # This file
└── test_report_*.json/md    # Generated test reports
```

## 🎯 Standard Test Suite

Every service automatically undergoes 10 standard tests:

| Test | Purpose | Pass Criteria |
|------|---------|---------------|
| **1. Initialization** | Service can be instantiated | No import errors, required attributes present |
| **2. Authentication** | API keys properly configured | Headers set, auth methods implemented |
| **3. Connection** | Can connect to service | Test endpoint responds, handles auth failures |
| **4. Rate Limiting** | Respects API limits | Rate limiter configured correctly |
| **5. Error Handling** | Proper error management | Raises appropriate errors with useful messages |
| **6. Discovery Methods** | Has exploration features | explore/discover/quick_start methods available |
| **7. Response Format** | Consistent data structure | Returns expected types, handles empty responses |
| **8. Token Efficiency** | Minimal token usage | < 2000 tokens (excellent), warns if > 5000 |
| **9. Documentation** | Well-documented code | > 80% method documentation coverage |
| **10. Examples** | Usage examples exist | examples.py file present and runnable |

## 🚀 Quick Start

### Run All Tests
```bash
# Basic run
python tests/run_all_tests.py

# With reports
python tests/run_all_tests.py --save --markdown

# Specific services only
python tests/run_all_tests.py smartlead metabase
```

### Test Single Service
```bash
python tests/test_smartlead.py
python tests/test_metabase.py
```

### Generate Reports
```bash
# JSON report
python tests/run_all_tests.py --save --output my_report.json

# Markdown report
python tests/run_all_tests.py --markdown --output my_report.md
```

## 📊 Test Status Indicators

| Status | Icon | Meaning | Counts As |
|--------|------|---------|-----------|
| `PASS` | ✅ | Test passed completely | Success |
| `FAIL` | ❌ | Test failed | Failure |
| `SKIP` | ⏭️ | Test not applicable/no auth | Neither |
| `WARN` | ⚠️ | Test passed with warnings | Success |

## 📝 Creating Tests for New Services

### 1. Create Test File
Create `tests/test_yourservice.py`:

```python
#!/usr/bin/env python3
"""Test Suite for YourService API"""

import os
import sys
from typing import Dict, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.base_test import ServiceTestBase
from services.yourservice.api import YourServiceAPI

class YourServiceTest(ServiceTestBase):
    """YourService-specific test implementation"""

    def get_test_config(self) -> Dict[str, Any]:
        return {
            'api_key_env': 'YOURSERVICE_API_KEY',
            'requires_auth': True,
            'rate_limit': 10,  # requests per second
            'test_endpoint': 'status',
            'test_params': {}
        }

    # Add service-specific tests
    def test_custom_feature(self) -> Dict[str, Any]:
        """Test unique functionality"""
        test_name = "custom_feature"

        try:
            if hasattr(self.api, 'special_method'):
                # Test the method
                result = self.api.special_method()
                return self._pass(test_name, "Feature works")
            else:
                return self._fail(test_name, "Method missing")
        except Exception as e:
            return self._fail(test_name, str(e))

if __name__ == "__main__":
    test = YourServiceTest(YourServiceAPI, 'YourService')
    results = test.run_all_tests()
    test.save_results()
```

### 2. Configuration Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `api_key_env` | Environment variable name | `'SMARTLEAD_API_KEY'` |
| `requires_auth` | Service needs authentication | `True` |
| `rate_limit` | Requests per second | `10` |
| `test_endpoint` | Endpoint for connection test | `'status'` |
| `test_params` | Parameters for test endpoint | `{'limit': 1}` |

## 📈 Test Reports

### JSON Report Structure
```json
{
  "timestamp": "2025-01-23T12:00:00",
  "services": {
    "smartlead": {
      "service": "smartlead",
      "timestamp": "2025-01-23T12:00:00",
      "tests": {
        "initialization": {
          "status": "PASS",
          "message": "Service initialized successfully",
          "timestamp": "2025-01-23T12:00:01"
        }
      },
      "summary": {
        "total": 10,
        "passed": 8,
        "failed": 0,
        "skipped": 2
      }
    }
  },
  "summary": {
    "total_services": 2,
    "services_passed": 2,
    "services_failed": 0,
    "total_tests": 20,
    "tests_passed": 16,
    "tests_failed": 0,
    "tests_skipped": 4
  }
}
```

### Markdown Report Example
```markdown
# API Toolkit Test Report

**Generated**: 2025-01-23T12:00:00

## Summary
- **Services Tested**: 2
- **Services Passed**: 2 ✅
- **Total Tests**: 20
- **Tests Passed**: 16 ✅
- **Tests Skipped**: 4 ⏭️

## Service Details

### Smartlead
**Status**: ✅ PASSED

| Test | Status | Message |
|------|--------|---------|
| initialization | ✅ PASS | Service initialized |
| authentication | ✅ PASS | Auth configured |
| connection | ✅ PASS | Connected |
```

## 🏆 Quality Standards

| Metric | Excellent | Good | Needs Work |
|--------|-----------|------|------------|
| **Test Pass Rate** | 100% | > 90% | < 90% |
| **Documentation Coverage** | > 80% | > 60% | < 60% |
| **Token Usage** | < 2000 | < 5000 | > 5000 |
| **Response Time** | < 1s | < 3s | > 3s |
| **Error Messages** | Detailed | Basic | Generic |

## 🔧 Best Practices

### 1. Handle Missing Credentials
```python
if not os.getenv('API_KEY'):
    return self._skip(test_name, "API key not configured")
```

### 2. Test Method Existence
```python
if hasattr(self.api, 'method_name'):
    # Test the method
else:
    return self._fail(test_name, "Method not found")
```

### 3. Provide Clear Messages
```python
return self._fail(test_name,
    f"Expected list but got {type(result).__name__}")
```

### 4. Test Real Workflows
```python
def test_typical_workflow(self):
    """Test common user scenario"""
    # Create -> Update -> Query -> Delete
```

## 🔍 Troubleshooting

### Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| "Module not found" | Ensure you're in the api-toolkit directory |
| "API key not set" | Add key to .env file or export as environment variable |
| "Connection failed" | Check internet, verify endpoint, check service status |
| "Rate limit exceeded" | Add delays between tests, check service limits |
| "Tests timing out" | Check network, increase timeout values |

### Debug Mode
```bash
# Verbose output
PYTEST_VERBOSE=1 python tests/test_smartlead.py

# Skip certain tests
SKIP_CONNECTION_TESTS=1 python tests/run_all_tests.py
```

## 🚦 CI/CD Integration

### GitHub Actions
```yaml
name: Test API Services
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Setup Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    - name: Install dependencies
      run: pip install -r requirements.txt
    - name: Load secrets
      env:
        SMARTLEAD_API_KEY: ${{ secrets.SMARTLEAD_API_KEY }}
        METABASE_API_KEY: ${{ secrets.METABASE_API_KEY }}
      run: echo "Secrets loaded"
    - name: Run tests
      run: python tests/run_all_tests.py --save --markdown
    - name: Upload results
      uses: actions/upload-artifact@v2
      if: always()
      with:
        name: test-results
        path: tests/test_report_*
```

### Pre-commit Hook
`.git/hooks/pre-commit`:
```bash
#!/bin/bash
python tests/run_all_tests.py
if [ $? -ne 0 ]; then
    echo "❌ Tests failed. Commit aborted."
    exit 1
fi
echo "✅ All tests passed!"
```

## 📊 Test Metrics

### Coverage Goals
- **Minimum**: 80% of methods tested
- **Target**: 95% of methods tested
- **Ideal**: 100% coverage with edge cases

### Performance Benchmarks
- **API Response**: < 2 seconds
- **Test Suite Runtime**: < 30 seconds
- **Memory Usage**: < 100MB

## 🔄 Test Lifecycle

1. **Development**: Run tests locally during development
2. **Pre-commit**: Automatic test run before commits
3. **Pull Request**: CI runs full test suite
4. **Deployment**: Final test run before release
5. **Monitoring**: Regular scheduled test runs

## 📝 Test Documentation

Each test should document:
- **Purpose**: What it's testing
- **Setup**: Required configuration
- **Expected**: What should happen
- **Actual**: What did happen
- **Cleanup**: Any teardown needed

## 🎯 Test Strategy

### Unit Tests (Current)
- Test individual methods
- Mock external dependencies
- Fast execution

### Integration Tests (Future)
- Test service interactions
- Real API calls
- End-to-end workflows

### Load Tests (Future)
- Concurrent requests
- Rate limit validation
- Performance metrics

## 🆘 Getting Help

### Resources
- **Testing Guide**: `tests/TESTING_GUIDE.md`
- **Base Test Class**: `tests/base_test.py`
- **Examples**: `tests/test_*.py`

### Common Commands
```bash
# List available tests
ls tests/test_*.py

# Run with Python path debug
python -c "import sys; print(sys.path)"

# Check environment variables
python -c "import os; print(os.environ.get('SMARTLEAD_API_KEY', 'Not set'))"

# Test single method
python -c "from tests.test_smartlead import SmartleadTest; t = SmartleadTest(...); t.test_connection()"
```

## 📈 Future Enhancements

### Planned Features
1. **Mock Mode** - Test without real API calls
2. **Performance Profiling** - Measure response times
3. **Coverage Reports** - Track test coverage
4. **Parallel Execution** - Run tests concurrently
5. **Visual Reports** - HTML dashboard
6. **Regression Testing** - Track changes over time
7. **Automated Fixes** - Self-healing for common issues

### Contribution Guidelines
1. All new services must include tests
2. Maintain > 80% test coverage
3. Document test failures clearly
4. Add service-specific tests for unique features
5. Update this reference with new patterns

---

**Remember**: Good tests ensure good services! Every test helps maintain quality and reliability across the entire API toolkit. 🎯