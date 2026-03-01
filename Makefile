# SoftFactory Unified Interface
# Version: 1.0
# Purpose: Standardize execution commands across Dev, Demo, and Ops
# See MULTI_AGENT_CROSSCHECK_REPORT_2026-02-26.md for details

.PHONY: help run-dev run-demo run-docker stop-docker test lint sync-docs clean verify

help:
	@echo "SoftFactory Management Commands"
	@echo "  make run-dev      - Run development server (run.py)"
	@echo "  make run-demo     - Run platform in demo mode (Port 9000)"
	@echo "  make run-docker   - Run full stack using Docker Compose"
	@echo "  make stop-docker  - Stop Docker services"
	@echo "  make test         - Run all tests"
	@echo "  make lint         - Run code style checks"
	@echo "  make sync-docs    - Synchronize documentation and API specs (Orchestrator)"
	@echo "  make verify       - Verify implementation status (Configs & Assets)"
	@echo "  make clean        - Remove temporary files"

run-dev:
	@echo "Starting development server on http://localhost:8000"
	python run.py

run-demo:
	@echo "Starting Demo Platform (Port 9000)..."
	python start_platform.py

run-docker:
	@echo "Starting Docker Stack..."
	docker-compose up -d

stop-docker:
	@echo "Stopping Docker services..."
	docker-compose down

test:
	@echo "Running Tests..."
	pytest

lint:
	@echo "Running Linter..."
	flake8 .

sync-docs:
	@echo "Harmonizing project state... (Running Orchestrator)"
	python orchestrator.py

verify:
	@echo "Verifying Implementation..."
	python scripts/verify_implementation.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete