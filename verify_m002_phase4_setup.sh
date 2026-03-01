#!/bin/bash

# M-002 Phase 4: PostgreSQL Docker Deployment — Pre-Execution Verification Script
# Purpose: Verify all prerequisites before running migration
# Usage: bash verify_m002_phase4_setup.sh

set -e  # Exit on first error

echo "=========================================="
echo "M-002 Phase 4: Setup Verification"
echo "Date: 2026-02-25"
echo "=========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
PASS=0
FAIL=0
WARN=0

# Helper functions
pass() {
    echo -e "${GREEN}✅ PASS${NC}: $1"
    ((PASS++))
}

fail() {
    echo -e "${RED}❌ FAIL${NC}: $1"
    ((FAIL++))
}

warn() {
    echo -e "${YELLOW}⚠️  WARN${NC}: $1"
    ((WARN++))
}

echo "--- System Requirements ---"

# Check Docker
if command -v docker &> /dev/null; then
    docker_version=$(docker --version | grep -oP '\d+\.\d+\.\d+')
    pass "Docker installed: $docker_version"
else
    fail "Docker not found. Install Docker Desktop."
fi

# Check docker-compose
if command -v docker-compose &> /dev/null || docker compose --version &> /dev/null; then
    docker_compose_version=$(docker-compose --version 2>/dev/null || docker compose --version | grep -oP '\d+\.\d+\.\d+')
    pass "docker-compose available: $docker_compose_version"
else
    fail "docker-compose not found"
fi

# Check Python
if command -v python &> /dev/null; then
    python_version=$(python --version | grep -oP '\d+\.\d+\.\d+')
    pass "Python installed: $python_version"
else
    fail "Python not found"
fi

# Check Python version >= 3.8
if python -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
    pass "Python version check (3.8+)"
else
    warn "Python version is < 3.8 (not ideal for Flask)"
fi

echo ""
echo "--- Project Files ---"

# Check key files
[[ -f "docker-compose.yml" ]] && pass "docker-compose.yml exists" || fail "docker-compose.yml missing"
[[ -f "Dockerfile" ]] && pass "Dockerfile exists" || fail "Dockerfile missing"
[[ -f "scripts/migrate_to_postgres.py" ]] && pass "migrate_to_postgres.py exists" || fail "migration script missing"
[[ -f ".env" ]] && pass ".env file exists" || fail ".env file missing"
[[ -f "backend/app.py" ]] && pass "backend/app.py exists" || fail "Flask app missing"
[[ -f "platform.db" ]] && pass "SQLite database exists" || fail "platform.db missing"

echo ""
echo "--- Dependencies ---"

# Check psycopg2
if python -c "import psycopg2" 2>/dev/null; then
    psycopg2_version=$(python -c "import psycopg2; print(psycopg2.__version__)" 2>/dev/null)
    pass "psycopg2-binary installed: $psycopg2_version"
else
    fail "psycopg2-binary not installed. Run: pip install psycopg2-binary"
fi

# Check Flask
if python -c "import flask" 2>/dev/null; then
    flask_version=$(python -c "import flask; print(flask.__version__)" 2>/dev/null)
    pass "Flask installed: $flask_version"
else
    fail "Flask not installed"
fi

# Check SQLAlchemy
if python -c "import sqlalchemy" 2>/dev/null; then
    sqlalchemy_version=$(python -c "import sqlalchemy; print(sqlalchemy.__version__)" 2>/dev/null)
    pass "SQLAlchemy installed: $sqlalchemy_version"
else
    fail "SQLAlchemy not installed"
fi

echo ""
echo "--- Docker Daemon Status ---"

# Check if Docker daemon is running
if docker ps &> /dev/null; then
    pass "Docker daemon is RUNNING"
else
    fail "Docker daemon NOT RUNNING. Start Docker Desktop and retry."
fi

echo ""
echo "--- SQLite Database Validation ---"

# Check if platform.db is readable
if sqlite3 platform.db ".tables" &> /dev/null; then
    tables=$(sqlite3 platform.db ".tables" | wc -w)
    pass "SQLite database readable ($tables tables found)"
else
    fail "Cannot read platform.db. File may be locked or corrupted."
fi

# Check database size
db_size=$(stat -f%z "platform.db" 2>/dev/null || stat --format=%s "platform.db" 2>/dev/null || echo "unknown")
echo "  Database size: $db_size bytes"

echo ""
echo "--- Configuration Files ---"

# Check DATABASE_URL in .env
if grep -q "DATABASE_URL" .env; then
    db_url=$(grep "^DATABASE_URL=" .env | cut -d'=' -f2-)
    pass "DATABASE_URL configured: $db_url"
else
    warn "DATABASE_URL not found in .env (will use migration script default)"
fi

# Check docker-compose.yml PostgreSQL settings
if grep -q "postgres:15-alpine" docker-compose.yml; then
    pass "PostgreSQL 15-alpine configured in docker-compose.yml"
else
    warn "PostgreSQL image may differ from expected (15-alpine)"
fi

echo ""
echo "--- Workspace Status ---"

# Check if we're in the project root
if [[ -f "CLAUDE.md" ]]; then
    pass "Working directory is project root"
else
    fail "Not in project root. cd D:/Project and retry."
fi

# Check git status
if [[ -d ".git" ]]; then
    git_branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
    pass "Git repository detected (branch: $git_branch)"
else
    warn "Not a git repository (optional)"
fi

echo ""
echo "=========================================="
echo "Verification Summary"
echo "=========================================="
echo -e "${GREEN}✅ PASS: $PASS${NC}"
echo -e "${RED}❌ FAIL: $FAIL${NC}"
echo -e "${YELLOW}⚠️  WARN: $WARN${NC}"
echo ""

if [[ $FAIL -eq 0 ]]; then
    echo -e "${GREEN}✅ All prerequisites met. Ready to proceed with migration.${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Start Docker Desktop (if not already running)"
    echo "2. Run: docker-compose up -d db"
    echo "3. Run: python scripts/migrate_to_postgres.py"
    echo "4. Run: docker-compose up -d"
    echo "5. Run: curl http://localhost:8000/health"
    echo ""
    exit 0
else
    echo -e "${RED}❌ Some prerequisites failed. Please fix issues above and retry.${NC}"
    echo ""
    echo "See DEPLOYMENT_CHECKLIST.md Part 1 for detailed instructions."
    exit 1
fi
