# ============================================================
# SoftFactory — Standard Command Interface
# Usage: make <target>
# ============================================================

.PHONY: help install dev test test-unit test-int test-e2e lint format \
        run docker-build docker-up docker-down clean push agents

# Default target
help:
	@echo ""
	@echo "SoftFactory — Available Commands"
	@echo "================================="
	@echo ""
	@echo "  Setup:"
	@echo "    make install      Install all dependencies"
	@echo "    make install-dev  Install with dev dependencies"
	@echo ""
	@echo "  Run:"
	@echo "    make run          Start local server (localhost:8000)"
	@echo "    make docker-up    Start full stack (Docker)"
	@echo "    make docker-down  Stop Docker stack"
	@echo ""
	@echo "  Test:"
	@echo "    make test         Run all tests"
	@echo "    make test-unit    Run unit tests only"
	@echo "    make test-int     Run integration tests only"
	@echo "    make test-e2e     Run E2E tests (requires server)"
	@echo "    make coverage     Run tests with coverage report"
	@echo ""
	@echo "  Code Quality:"
	@echo "    make lint         Run linting (flake8)"
	@echo "    make format       Auto-format code (black)"
	@echo "    make check        lint + format check"
	@echo ""
	@echo "  Agents:"
	@echo "    make agents       List all available sub-agents"
	@echo ""
	@echo "  Git:"
	@echo "    make push         Commit + push current changes"
	@echo "    make clean        Remove cache, bytecode, temp files"
	@echo ""

# ─── Setup ──────────────────────────────────────────────────

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt -r requirements-dev.txt

# ─── Run ────────────────────────────────────────────────────

run:
	python start_platform.py

docker-build:
	docker build -t softfactory:latest .

docker-up:
	docker-compose up -d --build
	@echo "✅ Stack running at http://localhost:8000"

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f api

# ─── Test ───────────────────────────────────────────────────

test:
	pytest tests/ -v --tb=short

test-unit:
	pytest tests/unit/ -v --tb=short

test-int:
	pytest tests/integration/ -v --tb=short

test-e2e:
	pytest tests/e2e/ -v --tb=short

coverage:
	pytest tests/ --cov=backend --cov=agents --cov=core --cov=skills \
	  --cov-report=term-missing --cov-report=html:htmlcov
	@echo "Coverage report: htmlcov/index.html"

# ─── Code Quality ───────────────────────────────────────────

lint:
	flake8 backend/ agents/ core/ skills/ tests/ \
	  --max-line-length=100 --exclude=__pycache__

format:
	black backend/ agents/ core/ skills/ tests/ --line-length=100

check: lint
	black backend/ agents/ core/ skills/ tests/ --check --line-length=100

# ─── Agents ─────────────────────────────────────────────────

agents:
	@echo ""
	@echo "Available Claude Sub-Agents (.claude/agents/)"
	@echo "=============================================="
	@ls .claude/agents/*.md | xargs -I{} basename {} .md | \
	  awk '{printf "  %-30s → Task(subagent_type=...)\n", $$1}'
	@echo ""

# ─── Git ────────────────────────────────────────────────────

push:
	git add -A
	git status --short
	@read -p "Commit message: " msg; \
	  git commit -m "$$msg" && git push softfactory clean-main:main

# ─── Clean ──────────────────────────────────────────────────

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	find . -name "*.pyo" -delete 2>/dev/null || true
	find . -name ".coverage" -delete 2>/dev/null || true
	rm -rf htmlcov/ .pytest_cache/ dist/ build/ 2>/dev/null || true
	@echo "✅ Cleaned"
