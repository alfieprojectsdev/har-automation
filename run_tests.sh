#!/bin/bash
#
# Test Runner Script for HAR Automation
#
# This script helps run the end-to-end test suite with common options.
#
# Usage:
#   ./run_tests.sh              # Run all tests
#   ./run_tests.sh --install    # Install dependencies first
#   ./run_tests.sh --coverage   # Run with coverage report
#   ./run_tests.sh --quick      # Run quick subset of tests
#   ./run_tests.sh --help       # Show help

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

show_help() {
    cat << EOF
HAR Automation Test Runner

Usage: ./run_tests.sh [OPTIONS]

Options:
    --install       Install/update test dependencies first
    --coverage      Run tests with coverage report
    --quick         Run quick subset of critical tests
    --parallel      Run tests in parallel (requires pytest-xdist)
    --verbose       Run with extra verbose output
    --debug         Run with Python debugger on failures
    --help          Show this help message

Examples:
    ./run_tests.sh                    # Run all tests
    ./run_tests.sh --install          # Install deps and run tests
    ./run_tests.sh --coverage         # Run with coverage
    ./run_tests.sh --quick --verbose  # Quick tests with verbose output

Test Categories:
    You can also run specific test categories using pytest -k:

    pytest test_e2e.py -k "earthquake"    # Earthquake tests only
    pytest test_e2e.py -k "volcano"       # Volcano tests only
    pytest test_e2e.py -k "validation"    # Validation tests only
    pytest test_e2e.py -k "csrf"          # CSRF security tests only

EOF
}

install_dependencies() {
    print_header "Installing Test Dependencies"

    # Check for virtual environment
    if [ ! -d ".venv" ]; then
        print_error "Virtual environment not found. Creating one..."
        python3 -m venv .venv
    fi

    # Activate virtual environment
    source .venv/bin/activate

    # Install dependencies
    print_info "Installing pytest and dependencies..."
    pip install -q pytest>=7.4.0 pytest-cov>=4.1.0 requests>=2.31.0

    print_success "Dependencies installed successfully"
}

check_dependencies() {
    # Check if pytest is available
    if ! .venv/bin/python3 -c "import pytest" 2>/dev/null; then
        print_error "pytest not found. Installing dependencies..."
        install_dependencies
    fi
}

run_all_tests() {
    print_header "Running All End-to-End Tests"

    .venv/bin/python3 -m pytest test_e2e.py -v --tb=short "$@"

    if [ $? -eq 0 ]; then
        print_success "All tests passed!"
    else
        print_error "Some tests failed. Check output above."
        exit 1
    fi
}

run_with_coverage() {
    print_header "Running Tests with Coverage Report"

    .venv/bin/python3 -m pytest test_e2e.py -v --tb=short \
        --cov=app --cov=src \
        --cov-report=term-missing \
        --cov-report=html

    if [ $? -eq 0 ]; then
        print_success "All tests passed!"
        print_info "Coverage report generated in htmlcov/index.html"
        print_info "Open with: firefox htmlcov/index.html"
    else
        print_error "Some tests failed. Check output above."
        exit 1
    fi
}

run_quick_tests() {
    print_header "Running Quick Test Subset"

    # Run only critical tests
    .venv/bin/python3 -m pytest test_e2e.py -v --tb=short \
        -k "test_server_health or test_earthquake_har or test_volcano_har or test_csrf_protection_missing"

    if [ $? -eq 0 ]; then
        print_success "Quick tests passed!"
    else
        print_error "Some tests failed. Check output above."
        exit 1
    fi
}

run_parallel() {
    print_header "Running Tests in Parallel"

    # Check if pytest-xdist is installed
    if ! .venv/bin/python3 -c "import xdist" 2>/dev/null; then
        print_info "Installing pytest-xdist for parallel execution..."
        .venv/bin/pip install -q pytest-xdist
    fi

    .venv/bin/python3 -m pytest test_e2e.py -v --tb=short -n auto "$@"

    if [ $? -eq 0 ]; then
        print_success "All tests passed!"
    else
        print_error "Some tests failed. Check output above."
        exit 1
    fi
}

# Main script logic
main() {
    local install=false
    local coverage=false
    local quick=false
    local parallel=false
    local extra_args=()

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --install)
                install=true
                shift
                ;;
            --coverage)
                coverage=true
                shift
                ;;
            --quick)
                quick=true
                shift
                ;;
            --parallel)
                parallel=true
                shift
                ;;
            --verbose)
                extra_args+=("-vv")
                shift
                ;;
            --debug)
                extra_args+=("--pdb")
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # Print banner
    print_header "HAR Automation Test Suite"

    # Install dependencies if requested
    if [ "$install" = true ]; then
        install_dependencies
    else
        check_dependencies
    fi

    # Run appropriate test mode
    if [ "$quick" = true ]; then
        run_quick_tests "${extra_args[@]}"
    elif [ "$coverage" = true ]; then
        run_with_coverage "${extra_args[@]}"
    elif [ "$parallel" = true ]; then
        run_parallel "${extra_args[@]}"
    else
        run_all_tests "${extra_args[@]}"
    fi

    print_header "Test Suite Complete"
}

# Run main function
main "$@"
