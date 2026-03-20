# 🧪 SNS Automation v2.0 — Integration Test Execution Guide

> **Purpose**: ```bash
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 SNS Automation v2.0 — Integration Test Execution Guide 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

> **Quick Start Guide** — How to run the test suite

## Prerequisites
```bash
pip install pytest pytest-cov APScheduler
```

## Quick Commands

### Run All Tests
```bash
pytest tests/integration/ -v
```

### Run with Coverage
```bash
pytest tests/integration/ --cov=backend --cov-report=html
open htmlcov/index.html
```

### Run Specific Test File
```bash
pytest tests/integration/test_auth_oauth.py -v
pytest tests/integration/test_sns_endpoints.py -v
pytest tests/integration/test_review_endpoints.py -v
pytest tests/integration/test_scraper_integration.py -v
```

### Run Specific Test Class
```bash
pytest tests/integration/test_auth_oauth.py::TestOAuthFlow -v
```

### Run Specific Test
```bash
pytest tests/integration/test_auth_oauth.py::TestOAuthFlow::test_google_oauth_url_generation -v
```

## Test Files
- **test_auth_oauth.py** — 22 OAuth & authentication tests
- **test_sns_endpoints.py** — 39 SNS endpoint tests
- **test_review_endpoints.py** — 15 Review platform tests
- **test_scraper_integration.py** — 6 Scraper integration tests

## Expected Output
```
================ 82 passed in ~25 seconds ================
Coverage: ~85% (backend code)
```

## Documentation
- TEAM_I_INTEGRATION_TESTS_SUMMARY.md — Full test guide
- TEAM_I_FINAL_DELIVERY.md — Complete delivery report