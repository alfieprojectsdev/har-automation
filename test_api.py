#!/usr/bin/env python3
"""
Test script for HAR generation API endpoint.

This script:
1. Starts the Flask development server in the background
2. Waits for server to be ready
3. Sends a POST request to /api/generate with sample OHAS summary table data
4. Prints the response (success or error)
5. Cleans up by stopping the server

Usage:
    python test_api.py
"""

import subprocess
import time
import requests
import sys
import signal
import os
import re
import html
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """Print formatted header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}\n")


def print_success(text):
    """Print success message"""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_error(text):
    """Print error message"""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_info(text):
    """Print info message"""
    print(f"{Colors.OKBLUE}ℹ {text}{Colors.ENDC}")


def start_flask_server():
    """
    Start Flask development server in the background.

    Returns:
        subprocess.Popen: The server process
    """
    print_info("Starting Flask development server...")

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

    return process


def wait_for_server(url, timeout=30, interval=0.5):
    """
    Wait for server to be ready.

    Args:
        url: Base URL to check
        timeout: Maximum seconds to wait
        interval: Seconds between checks

    Returns:
        bool: True if server is ready, False if timeout
    """
    print_info(f"Waiting for server at {url} (timeout: {timeout}s)...")

    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=1)
            if response.status_code in [200, 404]:  # Server is responding
                print_success(f"Server is ready!")
                return True
        except requests.exceptions.ConnectionError:
            # Server not ready yet
            pass
        except requests.exceptions.Timeout:
            # Server not ready yet
            pass

        time.sleep(interval)

    return False


def test_api_endpoint(base_url):
    """
    Test the /api/generate endpoint with sample data.

    Args:
        base_url: Base URL of the API server

    Returns:
        bool: True if test passed, False otherwise
    """
    print_header("Testing /api/generate endpoint")

    # Sample OHAS summary table data (tab-separated format)
    # This is what users would copy from the OHAS platform
    sample_table = """Assessment	Category	Feature Type	Location	Active Fault	Liquefaction
24918	Earthquake	Polygon	120.989669,14.537869	Safe; Approximately 7.1 km west of Valley Fault System	High Potential"""

    print_info("Sample input data:")
    print(f"{Colors.BOLD}{sample_table}{Colors.ENDC}\n")

    # Create a session to maintain cookies
    session = requests.Session()

    # Fetch CSRF token from index page
    print_info("Fetching CSRF token...")
    try:
        index_response = session.get(f"{base_url}/", timeout=10)
        if index_response.status_code != 200:
            print_error(f"Failed to fetch index page: {index_response.status_code}")
            return False


    except requests.exceptions.RequestException as e:
        print_error(f"Failed to fetch index page: {str(e)}")
        return False

    # Extract CSRF token from HTML (Flask-WTF embeds it in the page)
    csrf_token = None
    match = re.search(r'const\s+csrfToken\s*=\s*"([^"]+)"', index_response.text)
    if match:
        csrf_token = match.group(1)
        # Decode if it's HTML-encoded
        csrf_token = html.unescape(csrf_token)

    if not csrf_token:
        print_error("Could not retrieve CSRF token from HTML")
        return False

    # Verify session cookie is present (required for CSRF validation)
    if 'session' not in session.cookies:
        print_error("Session cookie not set by server")
        return False

    print_success(f"CSRF token obtained: {csrf_token[:16]}...")

    # Prepare request
    api_url = f"{base_url}/api/generate"
    payload = {
        "summary_table": sample_table
    }

    # Include CSRF token in headers
    headers = {
        "Content-Type": "application/json",
        "X-CSRFToken": csrf_token
    }

    print_info(f"Sending POST request to {api_url}...")

    try:
        response = session.post(
            api_url,
            json=payload,
            headers=headers,
            timeout=10
        )

        print_info(f"Response status code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            if data.get('success'):
                print_success("API request successful!\n")

                # Display generated HARs
                hars = data.get('hars', [])
                print_info(f"Generated {len(hars)} HAR(s):\n")

                for i, har in enumerate(hars, 1):
                    print(f"{Colors.BOLD}HAR {i}:{Colors.ENDC}")
                    print(f"  Assessment ID: {har['assessment_id']}")
                    print(f"  Category: {har['category']}")
                    print(f"\n{Colors.BOLD}HAR Text:{Colors.ENDC}")
                    print("-" * 60)
                    print(har['har_text'])
                    print("-" * 60)
                    print()

                return True
            else:
                print_error(f"API returned success=False")
                print(f"Response: {data}")
                return False
        else:
            print_error(f"API request failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"\nError details:")
                print(f"  Message: {error_data.get('error', 'Unknown error')}")
                if 'traceback' in error_data:
                    print(f"\nTraceback:")
                    print(error_data['traceback'])
            except:
                print(f"Response text: {response.text}")
            return False

    except requests.exceptions.Timeout:
        print_error("Request timed out")
        return False
    except requests.exceptions.RequestException as e:
        print_error(f"Request failed: {str(e)}")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def stop_server(process):
    """
    Stop the Flask server process.

    Args:
        process: The server process to stop
    """
    print_info("Stopping Flask server...")

    try:
        # Kill the entire process group
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)

        # Wait for process to terminate
        try:
            process.wait(timeout=5)
            print_success("Server stopped successfully")
        except subprocess.TimeoutExpired:
            # Force kill if it doesn't stop
            print_info("Force killing server...")
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            process.wait()
            print_success("Server killed")

    except ProcessLookupError:
        # Process already terminated
        print_success("Server already stopped")
    except Exception as e:
        print_error(f"Error stopping server: {str(e)}")


def main():
    """Main test script"""
    print_header("HAR Generation API Test Script")

    base_url = "http://localhost:5000"
    server_process = None
    test_passed = False

    try:
        # 1. Start server
        server_process = start_flask_server()

        # 2. Wait for server to be ready
        if not wait_for_server(base_url, timeout=30):
            print_error("Server failed to start within timeout period")
            sys.exit(1)

        # 3. Test API endpoint
        test_passed = test_api_endpoint(base_url)

        # 4. Print summary
        print_header("Test Summary")
        if test_passed:
            print_success("All tests passed!")
            return 0
        else:
            print_error("Test failed!")
            return 1

    except KeyboardInterrupt:
        print_info("\n\nTest interrupted by user")
        return 1

    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        # 5. Always clean up server process
        if server_process:
            stop_server(server_process)


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
