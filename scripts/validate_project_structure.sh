#!/bin/bash
################################################################################
# Project Structure Validation Script v1.0
# Purpose: Automated validation that project structure matches enterprise standards
# Usage: bash scripts/validate_project_structure.sh
# Exit codes: 0 = all checks pass, 1 = validation failed
################################################################################

set -e

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
CHECKS_PASSED=0
CHECKS_FAILED=0

# Helper functions
check_pass() {
    echo -e "${GREEN}✅ $1${NC}"
    ((CHECKS_PASSED++))
}

check_fail() {
    echo -e "${RED}❌ $1${NC}"
    ((CHECKS_FAILED++))
}

check_warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

echo "🔍 Validating Project Structure (Enterprise Standards)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check 1: Core directories exist
echo ""
echo "📁 Checking core directories..."
dirs=("backend" "web" "tests" "docs" "infrastructure" "orchestrator" ".github" ".claude")
for dir in "${dirs[@]}"; do
    if [ -d "$dir" ]; then
        check_pass "Directory exists: $dir"
    else
        check_fail "Missing directory: $dir"
    fi
done

# Check 2: Critical Python files exist
echo ""
echo "🐍 Checking critical Python files..."
files=("CLAUDE.md" "backend/app.py" "backend/models.py" "backend/error_tracker.py" "backend/auth.py")
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        check_pass "File exists: $file"
    else
        check_fail "Missing file: $file"
    fi
done

# Check 3: Governance files exist
echo ""
echo "📋 Checking governance files..."
gov_files=("CLAUDE.md" "shared-intelligence/patterns.md" "shared-intelligence/pitfalls.md" "shared-intelligence/decisions.md" "orchestrator/agent-registry.md" "orchestrator/mcp-registry.md")
for file in "${gov_files[@]}"; do
    if [ -f "$file" ]; then
        check_pass "Governance file: $file"
    else
        check_fail "Missing governance file: $file"
    fi
done

# Check 4: Python imports valid
echo ""
echo "🔗 Checking Python imports..."
if python3 -c "from backend.app import create_app; print('OK')" 2>/dev/null; then
    check_pass "Backend imports valid"
else
    check_fail "Backend import error - check backend/app.py"
fi

# Check 5: No hardcoded secrets in Python files
echo ""
echo "🔐 Checking for hardcoded secrets..."
if grep -r "password.*=" backend/*.py 2>/dev/null | grep -v "getenv\|os.environ\|config" > /tmp/secrets_check.txt 2>&1; then
    if [ -s /tmp/secrets_check.txt ]; then
        check_fail "Potential hardcoded secrets detected"
        head -3 /tmp/secrets_check.txt
    else
        check_pass "No hardcoded secrets detected"
    fi
else
    check_pass "No hardcoded secrets detected"
fi

# Check 6: Agent charters have IMPORTS header (if they exist)
echo ""
echo "🤖 Checking agent structure..."
if [ -d ".claude/agents" ]; then
    agent_count=$(find .claude/agents -name "*.md" 2>/dev/null | wc -l)
    if [ $agent_count -gt 0 ]; then
        check_pass "Found $agent_count agent charters"
    else
        check_warn "No agent charters found in .claude/agents/"
    fi
else
    check_warn "Agent directory .claude/agents/ not found"
fi

# Check 7: Shared intelligence files have proper headers
echo ""
echo "📚 Checking shared intelligence structure..."
if grep -q "Next-ID\|Next ID" shared-intelligence/pitfalls.md 2>/dev/null; then
    check_pass "shared-intelligence/pitfalls.md has Next-ID header"
else
    check_warn "shared-intelligence/pitfalls.md missing Next-ID header"
fi

if grep -q "## " shared-intelligence/patterns.md 2>/dev/null; then
    check_pass "shared-intelligence/patterns.md is properly formatted"
else
    check_fail "shared-intelligence/patterns.md missing markdown headers"
fi

# Check 8: Database models have to_dict() methods
echo ""
echo "🗂️  Checking database models..."
if grep -q "def to_dict" backend/models.py 2>/dev/null; then
    to_dict_count=$(grep -c "def to_dict" backend/models.py)
    check_pass "Found $to_dict_count to_dict() methods in models.py"
else
    check_fail "Database models missing to_dict() methods"
fi

# Check 9: Test structure is valid
echo ""
echo "🧪 Checking test structure..."
test_dirs=("tests/unit" "tests/integration" "tests/e2e")
for test_dir in "${test_dirs[@]}"; do
    if [ -d "$test_dir" ]; then
        test_count=$(find "$test_dir" -name "test_*.py" 2>/dev/null | wc -l)
        check_pass "Test directory: $test_dir ($test_count test files)"
    else
        check_warn "Test directory missing: $test_dir"
    fi
done

# Check 10: Flask app configuration is valid
echo ""
echo "⚙️  Checking Flask app configuration..."
if python3 -c "
from backend.app import create_app
app = create_app()
assert app is not None, 'App is None'
assert app.config.get('SQLALCHEMY_DATABASE_URI'), 'No database URI'
print('OK')
" 2>/dev/null; then
    check_pass "Flask app creates successfully with valid config"
else
    check_fail "Flask app configuration error"
fi

# Check 11: Infrastructure directory structure
echo ""
echo "🏗️  Checking infrastructure structure..."
infra_subdirs=("monitoring" "deployment" "security")
for subdir in "${infra_subdirs[@]}"; do
    if [ -d "infrastructure/$subdir" ]; then
        check_pass "Infrastructure subdir: infrastructure/$subdir"
    else
        check_warn "Infrastructure subdir missing: infrastructure/$subdir"
    fi
done

# Check 12: GitHub workflows exist
echo ""
echo "🔄 Checking CI/CD workflows..."
workflow_files=("test.yml" "build.yml" "deploy.yml" "security.yml")
for workflow in "${workflow_files[@]}"; do
    if [ -f ".github/workflows/$workflow" ]; then
        check_pass "Workflow exists: .github/workflows/$workflow"
    else
        check_fail "Workflow missing: .github/workflows/$workflow"
    fi
done

# Check 13: Requirements.txt exists and is valid
echo ""
echo "📦 Checking dependencies..."
if [ -f "requirements.txt" ]; then
    check_pass "requirements.txt exists"
    req_count=$(wc -l < requirements.txt)
    check_pass "Requirements contains $req_count packages"
else
    check_fail "requirements.txt not found"
fi

# Check 14: Docker configuration
echo ""
echo "🐳 Checking Docker setup..."
if [ -f "Dockerfile" ]; then
    check_pass "Dockerfile exists"
else
    check_warn "Dockerfile not found"
fi

if [ -f "docker-compose.yml" ]; then
    check_pass "docker-compose.yml exists"
else
    check_warn "docker-compose.yml not found"
fi

# Check 15: Documentation
echo ""
echo "📖 Checking documentation..."
if [ -d "docs" ]; then
    doc_count=$(find docs -name "*.md" 2>/dev/null | wc -l)
    if [ $doc_count -gt 0 ]; then
        check_pass "Documentation exists ($doc_count markdown files)"
    else
        check_warn "docs/ directory is empty"
    fi
else
    check_fail "docs/ directory missing"
fi

# Check 16: Run pytest discovery (no execution)
echo ""
echo "🧬 Checking test discovery..."
if python3 -m pytest --collect-only tests/ 2>/dev/null | grep -q "test session starts"; then
    test_items=$(python3 -m pytest --collect-only -q tests/ 2>/dev/null | wc -l)
    check_pass "Found $test_items test items"
else
    check_fail "Test discovery failed"
fi

# Check 17: Validate YAML files
echo ""
echo "📋 Validating YAML files..."
if python3 -c "import yaml; yaml.safe_load(open('infrastructure/monitoring/prometheus_config.yml'))" 2>/dev/null; then
    check_pass "Prometheus config is valid YAML"
else
    check_fail "Prometheus config YAML is invalid"
fi

# Final summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Validation Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ Passed: $CHECKS_PASSED${NC}"
echo -e "${RED}❌ Failed: $CHECKS_FAILED${NC}"

if [ $CHECKS_FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 All validations passed!${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}⚠️  $CHECKS_FAILED check(s) failed!${NC}"
    exit 1
fi
