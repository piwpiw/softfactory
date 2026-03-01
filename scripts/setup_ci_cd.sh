#!/bin/bash

###############################################################################
# CI/CD Pipeline Setup Script
# This script sets up the complete CI/CD pipeline for SoftFactory
###############################################################################

set -e

COLOR_GREEN='\033[0;32m'
COLOR_BLUE='\033[0;34m'
COLOR_YELLOW='\033[1;33m'
COLOR_RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${COLOR_BLUE}=== SoftFactory CI/CD Pipeline Setup ===${NC}\n"

# Function to print status messages
print_status() {
    echo -e "${COLOR_GREEN}✓${NC} $1"
}

print_section() {
    echo -e "\n${COLOR_BLUE}→ $1${NC}"
}

print_error() {
    echo -e "${COLOR_RED}✗${NC} $1"
}

# Check prerequisites
print_section "Checking prerequisites"

if ! command -v git &> /dev/null; then
    print_error "git is not installed"
    exit 1
fi
print_status "git is installed"

if ! command -v python &> /dev/null; then
    print_error "python is not installed"
    exit 1
fi
print_status "python is installed"

if ! command -v pip &> /dev/null; then
    print_error "pip is not installed"
    exit 1
fi
print_status "pip is installed"

# Install pre-commit
print_section "Setting up pre-commit hooks"

if ! command -v pre-commit &> /dev/null; then
    echo "Installing pre-commit..."
    pip install pre-commit
fi
print_status "pre-commit is installed"

# Install pre-commit hooks
if [ -f ".pre-commit-config.yaml" ]; then
    echo "Installing pre-commit hooks from configuration..."
    pre-commit install --hook-stage commit
    pre-commit install --hook-stage commit-msg
    print_status "Pre-commit hooks installed"
else
    print_error ".pre-commit-config.yaml not found"
fi

# Make hooks executable
print_section "Setting up git hooks"

if [ -f ".husky/pre-commit" ]; then
    chmod +x .husky/pre-commit
    print_status ".husky/pre-commit is executable"
fi

if [ -f ".husky/commit-msg" ]; then
    chmod +x .husky/commit-msg
    print_status ".husky/commit-msg is executable"
fi

# Install Node.js dependencies for commitlint (if package.json exists)
print_section "Setting up commitlint"

if [ -f "package.json" ]; then
    echo "Installing Node.js dependencies for commitlint..."
    npm install --save-dev @commitlint/cli @commitlint/config-conventional husky
    print_status "commitlint dependencies installed"
else
    echo "Skipping Node.js setup (no package.json found)"
fi

# Install Python testing dependencies
print_section "Installing Python dependencies"

if [ -f "requirements.txt" ]; then
    echo "Installing Python testing dependencies..."
    pip install pytest pytest-cov pytest-xdist pytest-timeout pytest-mock
    pip install flake8 black isort mypy bandit
    print_status "Testing dependencies installed"
fi

# Run initial pre-commit checks
print_section "Running initial pre-commit checks"

echo "Running black (code formatter)..."
black --line-length=120 backend tests --quiet || true
print_status "Black formatting complete"

echo "Running isort (import sorter)..."
isort --profile black --line-length 120 backend tests || true
print_status "isort complete"

echo "Running flake8 (linter)..."
flake8 backend tests --max-line-length=120 || true
print_status "flake8 linting complete"

# Generate baseline for secret detection
print_section "Setting up secret detection"

if command -v detect-secrets &> /dev/null; then
    echo "Generating detect-secrets baseline..."
    detect-secrets scan --all-files > .baseline.json 2>/dev/null || true
    print_status "Secret detection baseline generated"
fi

# Create CI/CD status check
print_section "Verifying workflow files"

workflows=(
    ".github/workflows/test.yml"
    ".github/workflows/build.yml"
    ".github/workflows/deploy.yml"
    ".github/workflows/security.yml"
    ".github/workflows/release.yml"
)

for workflow in "${workflows[@]}"; do
    if [ -f "$workflow" ]; then
        print_status "$workflow exists"
    else
        print_error "$workflow not found"
    fi
done

# Summary
print_section "Setup complete"

echo -e """
${COLOR_GREEN}CI/CD Pipeline is now configured!${NC}

${COLOR_BLUE}Next steps:${NC}
1. Commit the new CI/CD configuration files
2. Push to your repository
3. Monitor GitHub Actions workflows

${COLOR_BLUE}Useful commands:${NC}
  - Run all tests:        pytest tests/ -v
  - Run with coverage:    pytest tests/ --cov=backend
  - Format code:          black backend tests
  - Sort imports:         isort backend tests
  - Lint code:            flake8 backend tests
  - Type check:           mypy backend --ignore-missing-imports
  - Security scan:        bandit -r backend

${COLOR_BLUE}Documentation:${NC}
  See docs/CI-CD-PIPELINE.md for full details

${COLOR_YELLOW}Remember:${NC}
  - Commit messages must follow conventional commits format
  - All tests must pass before pushing
  - Coverage must be above 80%
"""
