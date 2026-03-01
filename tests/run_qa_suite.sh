#!/bin/bash
#
# QA Test Suite Execution Script
# Purpose: Run comprehensive test suite with coverage reporting
# Usage: ./run_qa_suite.sh [option]
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Configuration
COVERAGE_THRESHOLD=80
PERFORMANCE_TIMEOUT=300

# Functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"

    # Check Python
    if ! command -v python &> /dev/null; then
        print_error "Python not installed"
        exit 1
    fi
    print_success "Python installed: $(python --version)"

    # Check pytest
    if ! python -m pytest --version &> /dev/null; then
        print_error "pytest not installed"
        exit 1
    fi
    print_success "pytest installed"

    # Check requirements
    if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
        print_success "requirements.txt found"
    else
        print_warning "requirements.txt not found"
    fi
}

# Run SNS Monetization tests
run_sns_tests() {
    print_header "Running SNS Monetization Tests"

    pytest "$SCRIPT_DIR/integration/test_sns_monetize.py" \
        -v \
        --tb=short \
        --duration=10 \
        -m "not slow"

    if [ $? -eq 0 ]; then
        print_success "SNS Monetization tests PASSED"
    else
        print_error "SNS Monetization tests FAILED"
        return 1
    fi
}

# Run Review Scraper tests
run_review_tests() {
    print_header "Running Review Scraper Tests"

    pytest "$SCRIPT_DIR/integration/test_review_scrapers_integration.py" \
        -v \
        --tb=short \
        --duration=10 \
        -m "not slow"

    if [ $? -eq 0 ]; then
        print_success "Review Scraper tests PASSED"
    else
        print_error "Review Scraper tests FAILED"
        return 1
    fi
}

# Run E2E Journey tests
run_e2e_tests() {
    print_header "Running E2E Journey Tests"

    pytest "$SCRIPT_DIR/e2e/test_user_journeys_extended.py" \
        -v \
        --tb=long \
        --duration=10

    if [ $? -eq 0 ]; then
        print_success "E2E Journey tests PASSED"
    else
        print_error "E2E Journey tests FAILED"
        return 1
    fi
}

# Run all tests with coverage
run_all_with_coverage() {
    print_header "Running All Tests with Coverage Report"

    pytest "$SCRIPT_DIR/" \
        --cov="$PROJECT_ROOT/backend" \
        --cov-report=html \
        --cov-report=term \
        --cov-fail-under=$COVERAGE_THRESHOLD \
        -v \
        --tb=short

    if [ $? -eq 0 ]; then
        print_success "All tests PASSED with coverage ≥ $COVERAGE_THRESHOLD%"
        print_success "Coverage report generated: htmlcov/index.html"
    else
        print_error "Tests FAILED or coverage below threshold"
        return 1
    fi
}

# Run performance tests
run_performance_tests() {
    print_header "Running Performance Tests"

    pytest "$SCRIPT_DIR/" \
        -k "performance" \
        -v \
        --tb=short \
        --timeout=$PERFORMANCE_TIMEOUT

    if [ $? -eq 0 ]; then
        print_success "Performance tests PASSED"
    else
        print_error "Performance tests FAILED"
        return 1
    fi
}

# Run security tests
run_security_tests() {
    print_header "Running Security Tests"

    pytest "$SCRIPT_DIR/" \
        -k "security" \
        -v \
        --tb=short

    if [ $? -eq 0 ]; then
        print_success "Security tests PASSED"
    else
        print_error "Security tests FAILED"
        return 1
    fi
}

# Run specific test
run_specific_test() {
    local test_path=$1

    if [ ! -f "$test_path" ]; then
        print_error "Test file not found: $test_path"
        return 1
    fi

    print_header "Running Test: $test_path"

    pytest "$test_path" -v --tb=long

    if [ $? -eq 0 ]; then
        print_success "Test PASSED"
    else
        print_error "Test FAILED"
        return 1
    fi
}

# Generate test report
generate_report() {
    print_header "Generating Test Report"

    local report_file="$SCRIPT_DIR/test_report_$(date +%Y%m%d_%H%M%S).txt"

    {
        echo "=== SoftFactory QA Test Suite Report ==="
        echo "Generated: $(date)"
        echo ""
        echo "Test Files:"
        echo "- test_sns_monetize.py"
        echo "- test_review_scrapers_integration.py"
        echo "- test_user_journeys_extended.py"
        echo ""
        echo "Coverage Targets:"
        echo "- Link-in-Bio: 92%"
        echo "- Review Scraping: 90%"
        echo "- E2E Journeys: 97%"
        echo "- Overall: 90%"
        echo ""
        echo "Test Summary:"
        pytest "$SCRIPT_DIR/" --collect-only -q 2>/dev/null || echo "Error collecting tests"
        echo ""
    } | tee "$report_file"

    print_success "Report generated: $report_file"
}

# Main menu
show_menu() {
    echo ""
    print_header "SoftFactory QA Test Suite"
    echo ""
    echo "Options:"
    echo "  1. Run all tests with coverage"
    echo "  2. Run SNS Monetization tests"
    echo "  3. Run Review Scraper tests"
    echo "  4. Run E2E Journey tests"
    echo "  5. Run performance tests"
    echo "  6. Run security tests"
    echo "  7. Quick test (fast validation)"
    echo "  8. Generate report"
    echo "  9. Run with detailed output"
    echo "  0. Exit"
    echo ""
}

# Parse command line arguments
case "${1:-}" in
    "1" | "all")
        check_prerequisites
        run_all_with_coverage
        ;;
    "2" | "sns")
        check_prerequisites
        run_sns_tests
        ;;
    "3" | "review")
        check_prerequisites
        run_review_tests
        ;;
    "4" | "e2e")
        check_prerequisites
        run_e2e_tests
        ;;
    "5" | "performance")
        check_prerequisites
        run_performance_tests
        ;;
    "6" | "security")
        check_prerequisites
        run_security_tests
        ;;
    "7" | "quick")
        check_prerequisites
        print_header "Running Quick Test Suite"
        pytest "$SCRIPT_DIR/integration/" -q -x
        ;;
    "8" | "report")
        generate_report
        ;;
    "9" | "verbose")
        check_prerequisites
        print_header "Running All Tests (Verbose)"
        pytest "$SCRIPT_DIR/" -vv --tb=long
        ;;
    "0" | "exit")
        echo "Exiting..."
        exit 0
        ;;
    *)
        # Interactive mode
        check_prerequisites
        show_menu
        read -p "Select option: " choice
        case "$choice" in
            1) run_all_with_coverage ;;
            2) run_sns_tests ;;
            3) run_review_tests ;;
            4) run_e2e_tests ;;
            5) run_performance_tests ;;
            6) run_security_tests ;;
            7) pytest "$SCRIPT_DIR/integration/" -q -x ;;
            8) generate_report ;;
            9) pytest "$SCRIPT_DIR/" -vv --tb=long ;;
            0) exit 0 ;;
            *) print_error "Invalid option"; exit 1 ;;
        esac
        ;;
esac

# Summary
print_header "Test Suite Execution Summary"
print_success "Test execution completed"
echo ""
echo "Generated artifacts:"
echo "  - htmlcov/index.html (coverage report)"
echo "  - test_report_*.txt (detailed report)"
echo ""
echo "Next steps:"
echo "  1. Review coverage report"
echo "  2. Check for failing tests"
echo "  3. Update tests based on API changes"
echo "  4. Run in CI/CD pipeline"
echo ""
