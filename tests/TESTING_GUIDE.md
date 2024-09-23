# API Toolkit Testing Guide

## 🧪 Overview

This testing framework ensures all API services in the toolkit maintain high quality and consistent behavior. Every service must pass a standard set of tests plus service-specific validations.

## 📋 Standard Test Suite

Every service is automatically tested for:

### 1. **Initialization** ✅
- Service can be instantiated
- Required attributes present (base_url, session, rate_limiter)
- No import errors

### 2. **Authentication** 🔐
- API keys properly loaded from environment
- Headers configured correctly
- Auth methods implemented

### 3. **Connection** 🌐
- Can connect to the service
- Test endpoint responds
- Handles auth failures gracefully

### 4. **Rate Limiting** ⏱️
- Rate limiter configured
- Respects service limits
- Prevents API throttling

### 5. **Error Handling** ⚠️
- Raises appropriate errors
- Handles 404s, 401s, 500s
- Provides useful error messages

### 6. **Discovery Methods** 🔍
- Has explore/discover/quick_start methods
- Methods return useful information
- Help users understand the service

### 7. **Response Format** 📦
- Returns expected data types
- Consistent response structure
- Handles empty responses

### 8. **Token Efficiency** 💎
- Service uses < 2000 tokens (excellent)
- Warns if > 5000 tokens
- Fails if excessive token usage

### 9. **Documentation** 📚
- Class has docstring
- Methods are documented
- > 80% documentation coverage

### 10. **Examples** 📝
- examples.py file exists
- Examples are runnable
- Covers common use cases

## 🚀 Running Tests

### Test Single Service
```bash
# Test a specific service
python tests/test_smartlead.py
python tests/test_metabase.py
```

### Test All Services
```bash
# Run all tests
python tests/run_all_tests.py

# Save results
python tests/run_all_tests.py --save

# Generate markdown report
python tests/run_all_tests.py --markdown

# Test specific services only
python tests/run_all_tests.py smartlead metabase
```

### Output Examples
```
🧪 Testing Smartlead Service
============================================================

Running: Initialization... ✅ PASS
Running: Authentication... ✅ PASS
Running: Connection... ⚠️  WARN: Connection works (auth required)
Running: Rate Limiting... ✅ PASS
Running: Error Handling... ✅ PASS
Running: Discovery Methods... ✅ PASS
Running: Response Format... ⏭️  SKIP: Override in service-specific tests
Running: Token Efficiency... ✅ PASS
Running: Documentation... ✅ PASS
Running: Examples... ✅ PASS

📊 Test Summary for Smartlead
============================================================
Total:   10
Passed:  8 ✅
Failed:  0 ❌
Skipped: 2 ⏭️

🎉 All tests passed!
```

## 📝 Creating Tests for New Services

### 1. Create Test File
Create `tests/test_yourservice.py`:

```python
#!/usr/bin/env python3
"""
Test Suite for YourService API
"""

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
            'test_endpoint': 'status',  # endpoint for connection test
            'test_params': {}
        }

    # Add service-specific tests
    def test_custom_feature(self) -> Dict[str, Any]:
        """Test service-specific functionality"""
        test_name = "custom_feature"

        try:
            # Your test logic
            if self.api and hasattr(self.api, 'special_method'):
                return self._pass(test_name, "Special feature works")
            else:
                return self._fail(test_name, "Missing special method")
        except Exception as e:
            return self._fail(test_name, f"Test failed: {e}")

if __name__ == "__main__":
    test = YourServiceTest(YourServiceAPI, 'YourService')
    results = test.run_all_tests()
    test.save_results()
```

### 2. Test Configuration

The `get_test_config()` method should return:

| Field | Description | Example |
|-------|-------------|---------|
| `api_key_env` | Environment variable name | `'SMARTLEAD_API_KEY'` |
| `requires_auth` | If service needs authentication | `True` |
| `rate_limit` | Requests per second | `10` |
| `test_endpoint` | Endpoint for connection test | `'status'` |
| `test_params` | Parameters for test endpoint | `{'limit': 1}` |

### 3. Service-Specific Tests

Add tests for your service's unique features:

```python
def test_special_operation(self) -> Dict[str, Any]:
    """Test something specific to this service"""
    test_name = "special_operation"

    # Test implementation
    # Use self._pass(), self._fail(), self._skip(), self._warn()
    return self._pass(test_name, "Operation works correctly")
```

## 🎯 Best Practices

### 1. **Always Test Without Credentials**
Tests should handle missing API keys gracefully:
```python
if not os.getenv('API_KEY'):
    return self._skip(test_name, "API key not configured")
```

### 2. **Test Method Existence**
Check if methods exist before calling:
```python
if hasattr(self.api, 'method_name'):
    # Test the method
else:
    return self._fail(test_name, "Method not found")
```

### 3. **Handle Rate Limits**
Respect rate limits in tests:
```python
time.sleep(0.1)  # Small delay between test requests
```

### 4. **Provide Clear Messages**
Help users understand failures:
```python
return self._fail(test_name,
    f"Expected 'list' but got '{type(result).__name__}'")
```

### 5. **Test Real Scenarios**
Include tests that mirror actual usage:
```python
def test_typical_workflow(self):
    """Test a common user workflow"""
    # Create resource
    # Update resource
    # Query resource
    # Delete resource
```

## 🔍 Test Results

### Status Types

| Status | Icon | Meaning | Counts As |
|--------|------|---------|-----------|
| `PASS` | ✅ | Test passed | Success |
| `FAIL` | ❌ | Test failed | Failure |
| `SKIP` | ⏭️ | Test skipped (not applicable) | Neither |
| `WARN` | ⚠️ | Test passed with warnings | Success |

### Report Formats

#### JSON Report
Contains detailed test results:
```json
{
  "timestamp": "2025-01-01T12:00:00",
  "services": {
    "smartlead": {
      "tests": {
        "initialization": {
          "status": "PASS",
          "message": "Service initialized successfully"
        }
      }
    }
  }
}
```

#### Markdown Report
Human-readable summary:
```markdown
# API Toolkit Test Report

## Summary
- Services Tested: 3
- Services Passed: 3 ✅
- Tests Passed: 28 ✅
- Tests Failed: 0 ❌
```

## 🏆 Quality Standards

Services should aim for:

| Metric | Excellent | Good | Needs Work |
|--------|-----------|------|------------|
| **Test Pass Rate** | 100% | > 90% | < 90% |
| **Documentation** | > 80% | > 60% | < 60% |
| **Token Usage** | < 2000 | < 5000 | > 5000 |
| **Examples** | Comprehensive | Basic | None |
| **Error Messages** | Detailed | Basic | Generic |

## 🔧 Continuous Testing

### Pre-Commit Hook
Add to `.git/hooks/pre-commit`:
```bash
#!/bin/bash
python tests/run_all_tests.py
if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi
```

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
    - name: Run tests
      run: python tests/run_all_tests.py --save --markdown
    - name: Upload results
      uses: actions/upload-artifact@v2
      with:
        name: test-results
        path: tests/test_report_*.md
```

## 📊 Monitoring Service Health

Regular testing helps identify:

1. **API Changes** - When services update their endpoints
2. **Auth Issues** - Expired or invalid credentials
3. **Rate Limit Changes** - Updated service limits
4. **Breaking Changes** - Incompatible API updates
5. **Performance Issues** - Slow responses or timeouts

## 🆘 Troubleshooting

### Common Issues

#### "Module not found"
```bash
# Ensure you're in the right directory
cd /path/to/api-toolkit
python tests/test_smartlead.py
```

#### "API key not set"
```bash
# Set environment variable
export SMARTLEAD_API_KEY=your_key_here
# Or add to .env file
```

#### "Connection failed"
- Check internet connection
- Verify API endpoint is correct
- Check if service is operational

#### "Rate limit exceeded"
- Reduce test frequency
- Add delays between tests
- Check service rate limits

## 📈 Future Improvements

Planned enhancements:

1. **Performance Benchmarks** - Measure response times
2. **Load Testing** - Test under high volume
3. **Integration Tests** - Test service interactions
4. **Mock Mode** - Test without real API calls
5. **Coverage Reports** - Track test coverage
6. **Automated Fixes** - Self-healing for common issues

---

Remember: **Good tests make good services!** 🎯