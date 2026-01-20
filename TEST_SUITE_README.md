# End-to-End Test Suite for HAR Automation

Comprehensive automated testing for the HAR automation web application.

## Overview

The `test_e2e.py` test suite provides complete end-to-end validation of all HAR automation functionality, including:

- Server startup/shutdown management
- CSRF token handling
- Earthquake HAR generation
- Volcano HAR generation
- Multiple assessment parsing
- Input validation (empty, oversized)
- Error handling (security)
- Concurrent request handling

## Installation

### 1. Install Development Dependencies

```bash
# Activate virtual environment
source .venv/bin/activate

# Install pytest and testing dependencies
pip install pytest>=7.4.0 pytest-cov>=4.1.0 requests>=2.31.0

# Or install all dev dependencies
pip install -r requirements-dev.txt
```

### 2. Verify Installation

```bash
pytest --version
```

## Running Tests

### Run All Tests

```bash
# Run all tests with verbose output
pytest test_e2e.py -v

# Run with detailed output and short traceback
pytest test_e2e.py -v --tb=short
```

### Run Specific Tests

```bash
# Run only earthquake tests
pytest test_e2e.py -v -k test_earthquake

# Run only volcano tests
pytest test_e2e.py -v -k test_volcano

# Run only validation tests
pytest test_e2e.py -v -k validation

# Run only security tests
pytest test_e2e.py -v -k "csrf or traceback"
```

### Run with Coverage

```bash
# Generate coverage report
pytest test_e2e.py -v --cov=app --cov=src --cov-report=html

# View coverage in browser
firefox htmlcov/index.html
```

### Run in Parallel

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel (faster)
pytest test_e2e.py -v -n auto
```

## Test Suite Structure

### Fixtures

- **`test_server`** (module-scoped): Starts Flask server once for all tests
- **`api_session`** (function-scoped): Creates new session with CSRF token for each test

### Test Categories

#### 1. Server Health Tests
- `test_server_health`: Validates health endpoint
- `test_index_page_loads`: Validates UI accessibility

#### 2. HAR Generation Tests
- `test_earthquake_har_generation`: Tests earthquake HAR workflow
- `test_volcano_har_generation`: Tests volcano HAR workflow
- `test_multiple_assessments`: Tests parsing multiple assessments

#### 3. Input Validation Tests
- `test_empty_input_validation`: Empty string rejection
- `test_whitespace_only_input_validation`: Whitespace-only rejection
- `test_oversized_input_validation`: 10KB size limit enforcement

#### 4. Security Tests
- `test_csrf_protection_missing_token`: CSRF token required
- `test_csrf_protection_invalid_token`: CSRF token validated
- `test_error_no_traceback`: No stack traces exposed to clients

#### 5. Edge Case Tests
- `test_missing_json_body`: Malformed request handling
- `test_concurrent_requests`: Concurrent load handling
- `test_special_characters_in_input`: Unicode/special character handling

## Test Data

All test data uses the OHAS summary table format (tab-separated values):

### Earthquake Assessment Example
```
Assessment	Category	Feature Type	Location	Active Fault	Liquefaction
24918	Earthquake	Polygon	120.989669,14.537869	Safe; Approximately 7.1 km west of Valley Fault System	High Potential
```

### Volcano Assessment Example
```
Assessment	Category	...	Lahar	Pyroclastic Flow	...
24778	Volcano	...	Safe	Safe	...
```

## Expected Results

All tests should pass with:
- ✓ Server starts successfully
- ✓ CSRF protection active
- ✓ Input validation working
- ✓ HAR generation successful
- ✓ Error handling secure (no tracebacks)
- ✓ Multiple assessments processed
- ✓ Server stops cleanly

## Troubleshooting

### Port Already in Use

If port 5000 is already in use:

```bash
# Find process using port 5000
lsof -i :5000

# Kill the process
kill -9 <PID>

# Or change port in test_e2e.py:
BASE_URL = "http://localhost:5001"  # Update in run.py too
```

### Server Won't Start

Check logs and dependencies:

```bash
# Test server manually
python run.py

# Check if all dependencies installed
pip list | grep -E 'flask|pytest|requests'
```

### Tests Hang

If tests hang during server shutdown:

```bash
# Force kill Python processes
pkill -9 python

# Run tests with timeout
pytest test_e2e.py -v --timeout=300
```

### CSRF Token Issues

If CSRF tests fail:

1. Verify Flask-WTF is installed: `pip list | grep Flask-WTF`
2. Check `config/config.py` has `WTF_CSRF_ENABLED = True`
3. Verify session cookies are enabled in requests

## Continuous Integration

### GitHub Actions Example

```yaml
name: Test HAR Automation

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements-dev.txt
      - run: pytest test_e2e.py -v --cov=app --cov=src
```

## Test Coverage Goals

- **API Routes**: 100% coverage
- **Input Validation**: 100% coverage
- **Error Handling**: 100% coverage
- **CSRF Protection**: 100% coverage
- **HAR Generation**: 90%+ coverage (core logic)

## Contributing

When adding new features:

1. Write tests first (TDD approach)
2. Ensure all existing tests pass
3. Add new test cases for edge cases
4. Maintain 90%+ test coverage
5. Document new test scenarios

## Test Execution Time

Expected execution times:
- Full suite: ~30-40 seconds (includes server startup/shutdown)
- Individual test: ~1-2 seconds
- Parallel execution: ~15-20 seconds

## Notes

- Tests are **independent** and can run in any order
- Server is started **once** per test session (module scope)
- Each test gets a **fresh session** with new CSRF token
- All tests use **realistic OHAS data** from production examples
- Error messages are **validated** to ensure no information leakage
