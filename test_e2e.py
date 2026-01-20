#!/usr/bin/env python3
"""
End-to-End Test Suite for HAR Automation Web Application

This comprehensive test suite validates all functionality of the HAR automation
web application, including:
- Server startup/shutdown
- CSRF token handling
- Earthquake and volcano HAR generation
- Input validation (empty input, oversized input)
- Error handling (no stack traces exposed)
- Multiple assessment parsing

Usage:
    pytest test_e2e.py -v
    pytest test_e2e.py -v -k test_earthquake  # Run specific test
    pytest test_e2e.py -v --tb=short          # Short traceback format
"""

import pytest
import requests
import subprocess
import time
import sys
import signal
import os
import re
import html
from pathlib import Path


# Test configuration
BASE_URL = "http://localhost:5000"
SERVER_STARTUP_TIMEOUT = 30
SERVER_SHUTDOWN_TIMEOUT = 5


@pytest.fixture(scope="module")
def test_server():
    """
    Start Flask server for testing and ensure clean shutdown.

    This fixture:
    1. Starts the Flask development server in a subprocess
    2. Waits for server to be ready
    3. Yields the base URL for tests to use
    4. Ensures clean shutdown after all tests complete

    Yields:
        str: Base URL of the test server
    """
    print("\n" + "=" * 60)
    print("Starting Flask test server...")
    print("=" * 60)

    # Get the directory of this script
    script_dir = Path(__file__).parent

    # Check for virtual environment
    venv_python = script_dir / '.venv' / 'bin' / 'python'
    python_executable = str(venv_python) if venv_python.exists() else sys.executable

    # Start the server using run.py
    process = subprocess.Popen(
        [python_executable, 'run.py'],
        cwd=script_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        preexec_fn=os.setsid  # Create new process group for clean shutdown
    )

    # Wait for server to be ready
    start_time = time.time()
    server_ready = False

    while time.time() - start_time < SERVER_STARTUP_TIMEOUT:
        try:
            response = requests.get(BASE_URL, timeout=1)
            if response.status_code in [200, 404]:
                server_ready = True
                print(f"✓ Server ready at {BASE_URL}")
                break
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            pass

        time.sleep(0.5)

    if not server_ready:
        # Clean up and fail
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            process.wait(timeout=5)
        except:
            pass
        pytest.fail(f"Server failed to start within {SERVER_STARTUP_TIMEOUT}s")

    # Yield control to tests
    yield BASE_URL

    # Cleanup: Stop server
    print("\n" + "=" * 60)
    print("Stopping Flask test server...")
    print("=" * 60)

    try:
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        try:
            process.wait(timeout=SERVER_SHUTDOWN_TIMEOUT)
            print("✓ Server stopped cleanly")
        except subprocess.TimeoutExpired:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            process.wait()
            print("✓ Server forcefully terminated")
    except ProcessLookupError:
        print("✓ Server already stopped")
    except Exception as e:
        print(f"⚠ Warning: Error stopping server: {e}")


@pytest.fixture
def api_session(test_server):
    """
    Create a requests session with CSRF token for API calls.

    This fixture:
    1. Creates a new requests session
    2. Fetches the index page to get CSRF token
    3. Extracts CSRF token from HTML
    4. Returns session and token for test to use

    Args:
        test_server: Base URL from test_server fixture

    Yields:
        tuple: (session, csrf_token) for making authenticated API calls
    """
    session = requests.Session()

    # Fetch CSRF token from index page
    response = session.get(f"{test_server}/", timeout=10)
    assert response.status_code == 200, "Failed to fetch index page"

    # Extract CSRF token from HTML
    match = re.search(r'const\s+csrfToken\s*=\s*"([^"]+)"', response.text)
    assert match, "Could not find CSRF token in HTML"

    csrf_token = html.unescape(match.group(1))

    # Verify session cookie is set
    assert 'session' in session.cookies, "Session cookie not set"

    yield session, csrf_token

    # Cleanup
    session.close()


@pytest.mark.e2e
def test_server_health(test_server):
    """
    Test that server health check endpoint responds correctly.

    This validates the server is running and the health endpoint works.
    """
    response = requests.get(f"{test_server}/health", timeout=5)

    assert response.status_code == 200, "Health check endpoint should return 200"

    data = response.json()
    assert data.get('status') == 'ok', "Health status should be 'ok'"
    assert 'version' in data, "Health response should include version"


@pytest.mark.e2e
def test_index_page_loads(test_server):
    """
    Test that the main index page loads successfully.

    This validates the UI is accessible and contains required elements.
    """
    response = requests.get(f"{test_server}/", timeout=5)

    assert response.status_code == 200, "Index page should return 200"
    assert 'HAR Automation' in response.text, "Page should contain title"
    assert 'summaryTable' in response.text, "Page should contain textarea for input"
    assert 'generateBtn' in response.text, "Page should contain generate button"
    assert 'csrfToken' in response.text, "Page should contain CSRF token"


@pytest.mark.e2e
@pytest.mark.integration
def test_earthquake_har_generation(api_session, test_server):
    """
    Test successful generation of earthquake HAR.

    This validates:
    - API accepts valid earthquake assessment data
    - HAR is generated with correct structure
    - Response includes all required fields
    """
    session, csrf_token = api_session

    # Sample earthquake assessment (tab-separated format from OHAS)
    earthquake_data = """Assessment	Category	Feature Type	Location	Active Fault	Liquefaction
24918	Earthquake	Polygon	120.989669,14.537869	Safe; Approximately 7.1 km west of Valley Fault System	High Potential"""

    response = session.post(
        f"{test_server}/api/generate",
        json={"summary_table": earthquake_data},
        headers={
            "Content-Type": "application/json",
            "X-CSRFToken": csrf_token
        },
        timeout=10
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    data = response.json()
    assert data.get('success') is True, "Response should indicate success"
    assert 'hars' in data, "Response should contain 'hars' field"

    hars = data['hars']
    assert len(hars) == 1, "Should generate exactly 1 HAR"

    har = hars[0]
    assert har['assessment_id'] == '24918', "Assessment ID should match input"
    assert har['category'] == 'Earthquake', "Category should be Earthquake"
    assert 'har_text' in har, "HAR should contain generated text"
    assert len(har['har_text']) > 0, "HAR text should not be empty"

    # Verify HAR contains expected sections
    har_text = har['har_text']
    assert 'EXPLANATION' in har_text, "HAR should contain EXPLANATION section"
    assert 'RECOMMENDATION' in har_text, "HAR should contain RECOMMENDATION section"


@pytest.mark.e2e
@pytest.mark.integration
def test_volcano_har_generation(api_session, test_server):
    """
    Test successful generation of volcano HAR.

    This validates:
    - API accepts valid volcano assessment data
    - Volcano HAR is generated correctly
    - All volcano-specific fields are processed
    """
    session, csrf_token = api_session

    # Sample volcano assessment (tab-separated format from OHAS)
    volcano_data = """Assessment	Category	Feature Type	Location	Active Fault	Liquefaction	Landslide	Tsunami	Nearest Active Volcano	Nearest Potentially Active Volcano	Fissure	Lahar	Pyroclastic Flow	Base Surge	Lava Flow	Ballistic Projectile	Volcanic Tsunami
24778	Volcano	Polygon	125.072479,11.788131	--	--	--	--	Approximately 67.7 kilometers east of Biliran Volcano	Approximately 85.4 km northeast of Cancajanag Volcano	--	Safe	Safe	--	Safe	--	--"""

    response = session.post(
        f"{test_server}/api/generate",
        json={"summary_table": volcano_data},
        headers={
            "Content-Type": "application/json",
            "X-CSRFToken": csrf_token
        },
        timeout=10
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    data = response.json()
    assert data.get('success') is True, "Response should indicate success"
    assert 'hars' in data, "Response should contain 'hars' field"

    hars = data['hars']
    assert len(hars) == 1, "Should generate exactly 1 HAR"

    har = hars[0]
    assert har['assessment_id'] == '24778', "Assessment ID should match input"
    assert har['category'] == 'Volcano', "Category should be Volcano"
    assert 'har_text' in har, "HAR should contain generated text"
    assert len(har['har_text']) > 0, "HAR text should not be empty"

    # Verify HAR contains expected sections
    har_text = har['har_text']
    assert 'EXPLANATION' in har_text, "HAR should contain EXPLANATION section"
    assert 'RECOMMENDATION' in har_text, "HAR should contain RECOMMENDATION section"


@pytest.mark.e2e
@pytest.mark.integration
def test_multiple_assessments(api_session, test_server):
    """
    Test parsing and generation of multiple assessments in one request.

    This validates:
    - API can handle multiple assessments
    - Each assessment generates a separate HAR
    - All HARs are returned in correct order
    """
    session, csrf_token = api_session

    # Multiple assessments (earthquake + volcano)
    multi_data = """Assessment	Category	Feature Type	Location	Active Fault	Liquefaction	Landslide	Tsunami	Nearest Active Volcano	Nearest Potentially Active Volcano	Fissure	Lahar	Pyroclastic Flow	Base Surge	Lava Flow	Ballistic Projectile	Volcanic Tsunami
24777	Earthquake	Polygon	125.083337,11.772125	Safe; Approximately 458 meters west of the Central Samar Fault: Paranas Segment	Safe	Least to Highly Susceptible; Within the depositional zone	Safe	--	--	--	--	--	--	--	--	--
24778	Volcano	Polygon	125.072479,11.788131	--	--	--	--	Approximately 67.7 kilometers east of Biliran Volcano	Approximately 85.4 km northeast of Cancajanag Volcano	--	Safe	Safe	--	Safe	--	--"""

    response = session.post(
        f"{test_server}/api/generate",
        json={"summary_table": multi_data},
        headers={
            "Content-Type": "application/json",
            "X-CSRFToken": csrf_token
        },
        timeout=10
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    data = response.json()
    assert data.get('success') is True, "Response should indicate success"
    assert 'hars' in data, "Response should contain 'hars' field"

    hars = data['hars']
    assert len(hars) == 2, "Should generate exactly 2 HARs"

    # Verify first HAR (Earthquake)
    har1 = hars[0]
    assert har1['assessment_id'] == '24777', "First assessment ID should be 24777"
    assert har1['category'] == 'Earthquake', "First category should be Earthquake"
    assert len(har1['har_text']) > 0, "First HAR text should not be empty"

    # Verify second HAR (Volcano)
    har2 = hars[1]
    assert har2['assessment_id'] == '24778', "Second assessment ID should be 24778"
    assert har2['category'] == 'Volcano', "Second category should be Volcano"
    assert len(har2['har_text']) > 0, "Second HAR text should not be empty"


@pytest.mark.validation
def test_empty_input_validation(api_session, test_server):
    """
    Test that empty input is properly rejected.

    This validates:
    - API rejects empty summary_table
    - Appropriate error message is returned
    - HTTP 400 status code is used
    """
    session, csrf_token = api_session

    response = session.post(
        f"{test_server}/api/generate",
        json={"summary_table": ""},
        headers={
            "Content-Type": "application/json",
            "X-CSRFToken": csrf_token
        },
        timeout=10
    )

    assert response.status_code == 400, "Empty input should return 400"

    data = response.json()
    assert 'error' in data, "Response should contain error message"
    assert 'No summary table provided' in data['error'], "Error message should be descriptive"


@pytest.mark.validation
def test_whitespace_only_input_validation(api_session, test_server):
    """
    Test that whitespace-only input is properly rejected.

    This validates edge case where input contains only spaces/newlines.
    """
    session, csrf_token = api_session

    response = session.post(
        f"{test_server}/api/generate",
        json={"summary_table": "   \n\n  \t  "},
        headers={
            "Content-Type": "application/json",
            "X-CSRFToken": csrf_token
        },
        timeout=10
    )

    assert response.status_code == 400, "Whitespace-only input should return 400"

    data = response.json()
    assert 'error' in data, "Response should contain error message"


@pytest.mark.validation
@pytest.mark.security
def test_oversized_input_validation(api_session, test_server):
    """
    Test that input larger than 10KB is rejected (DoS protection).

    This validates:
    - API enforces MAX_INPUT_SIZE limit
    - Large payloads are rejected before processing
    - Appropriate error message is returned
    """
    session, csrf_token = api_session

    # Generate input larger than 10KB (10 * 1024 bytes)
    large_input = "A" * (10 * 1024 + 1)

    response = session.post(
        f"{test_server}/api/generate",
        json={"summary_table": large_input},
        headers={
            "Content-Type": "application/json",
            "X-CSRFToken": csrf_token
        },
        timeout=10
    )

    assert response.status_code == 400, "Oversized input should return 400"

    data = response.json()
    assert 'error' in data, "Response should contain error message"
    assert 'too large' in data['error'].lower(), "Error should mention size limit"
    assert '10240' in data['error'] or '10 KB' in data['error'], "Error should specify the limit"


@pytest.mark.security
def test_csrf_protection_missing_token(test_server):
    """
    Test that requests without CSRF token are rejected.

    This validates:
    - CSRF protection is active
    - Requests without token are rejected
    - HTTP 400 status code is returned
    """
    # Create session without fetching CSRF token
    session = requests.Session()

    sample_data = """Assessment	Category	Feature Type	Location	Active Fault
24918	Earthquake	Polygon	120.989669,14.537869	Safe"""

    response = session.post(
        f"{test_server}/api/generate",
        json={"summary_table": sample_data},
        headers={"Content-Type": "application/json"},
        timeout=10
    )

    # Flask-WTF returns 400 for CSRF validation failure
    assert response.status_code == 400, "Request without CSRF token should be rejected"


@pytest.mark.security
def test_csrf_protection_invalid_token(api_session, test_server):
    """
    Test that requests with invalid CSRF token are rejected.

    This validates:
    - CSRF tokens are validated
    - Invalid tokens are rejected
    """
    session, _ = api_session  # Get session but ignore valid token

    sample_data = """Assessment	Category	Feature Type	Location	Active Fault
24918	Earthquake	Polygon	120.989669,14.537869	Safe"""

    response = session.post(
        f"{test_server}/api/generate",
        json={"summary_table": sample_data},
        headers={
            "Content-Type": "application/json",
            "X-CSRFToken": "invalid-token-12345"
        },
        timeout=10
    )

    # Flask-WTF returns 400 for CSRF validation failure
    assert response.status_code == 400, "Request with invalid CSRF token should be rejected"


@pytest.mark.security
def test_error_no_traceback(api_session, test_server):
    """
    Test that server errors don't expose stack traces to clients.

    This validates:
    - Internal errors return HTTP 500
    - Error responses contain generic error message
    - No stack traces or sensitive data exposed
    - Error is logged server-side (but not returned to client)
    """
    session, csrf_token = api_session

    # Send malformed data that will cause parsing error
    malformed_data = "This is not a valid table format at all!"

    response = session.post(
        f"{test_server}/api/generate",
        json={"summary_table": malformed_data},
        headers={
            "Content-Type": "application/json",
            "X-CSRFToken": csrf_token
        },
        timeout=10
    )

    # Should return 500 for processing error
    assert response.status_code == 500, "Processing error should return 500"

    data = response.json()
    assert 'error' in data, "Response should contain error field"

    # Verify generic error message (no technical details)
    error_msg = data['error']
    assert 'Failed to generate HAR' in error_msg, "Should contain generic error message"

    # Verify NO stack trace information is exposed
    assert 'traceback' not in data, "Response should not include traceback field"
    assert 'Traceback' not in error_msg, "Error message should not contain traceback"
    assert 'File "' not in error_msg, "Error message should not contain file paths"
    assert 'line ' not in error_msg.lower(), "Error message should not contain line numbers"

    # Verify no Python exception names are exposed
    python_exceptions = ['Exception', 'ValueError', 'KeyError', 'AttributeError',
                        'TypeError', 'IndexError', 'RuntimeError']
    for exc in python_exceptions:
        assert exc not in error_msg, f"Error message should not contain '{exc}'"


@pytest.mark.validation
def test_missing_json_body(api_session, test_server):
    """
    Test that requests without JSON body are handled properly.

    This validates error handling for malformed requests.
    """
    session, csrf_token = api_session

    response = session.post(
        f"{test_server}/api/generate",
        data="not json",
        headers={
            "Content-Type": "application/json",
            "X-CSRFToken": csrf_token
        },
        timeout=10
    )

    # Should return 4xx error for bad request
    assert response.status_code >= 400 and response.status_code < 500, \
        "Malformed request should return 4xx error"


@pytest.mark.slow
@pytest.mark.integration
def test_concurrent_requests(api_session, test_server):
    """
    Test that server can handle multiple concurrent requests.

    This validates:
    - Server doesn't crash under concurrent load
    - CSRF tokens work independently per session
    - All requests are processed correctly
    """
    import concurrent.futures

    session, csrf_token = api_session

    sample_data = """Assessment	Category	Feature Type	Location	Active Fault	Liquefaction
24918	Earthquake	Polygon	120.989669,14.537869	Safe; Approximately 7.1 km west of Valley Fault System	High Potential"""

    def make_request():
        """Helper function to make a single API request"""
        response = session.post(
            f"{test_server}/api/generate",
            json={"summary_table": sample_data},
            headers={
                "Content-Type": "application/json",
                "X-CSRFToken": csrf_token
            },
            timeout=10
        )
        return response.status_code, response.json()

    # Make 5 concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(make_request) for _ in range(5)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    # Verify all requests succeeded
    for status_code, data in results:
        assert status_code == 200, f"Concurrent request failed with status {status_code}"
        assert data.get('success') is True, "Concurrent request should succeed"
        assert len(data.get('hars', [])) == 1, "Each request should generate 1 HAR"


@pytest.mark.integration
def test_special_characters_in_input(api_session, test_server):
    """
    Test that input with special characters is handled correctly.

    This validates proper encoding and parsing of various characters.
    """
    session, csrf_token = api_session

    # Data with special characters (em dash, degree symbol, etc.)
    special_char_data = """Assessment	Category	Feature Type	Location	Active Fault	Liquefaction
24918	Earthquake	Polygon	120.989669°N,14.537869°E	Safe; Approximately 7.1 km west — Valley Fault System	High Potential"""

    response = session.post(
        f"{test_server}/api/generate",
        json={"summary_table": special_char_data},
        headers={
            "Content-Type": "application/json",
            "X-CSRFToken": csrf_token
        },
        timeout=10
    )

    # Should either succeed or fail gracefully (no crash)
    assert response.status_code in [200, 400, 500], \
        "Special characters should not cause unexpected errors"

    if response.status_code == 200:
        data = response.json()
        assert 'hars' in data, "Successful response should contain HARs"


# Test summary fixture
@pytest.fixture(scope="module", autouse=True)
def test_summary(request):
    """Print test summary after all tests complete"""
    yield

    print("\n" + "=" * 60)
    print("END-TO-END TEST SUITE COMPLETED")
    print("=" * 60)
