# 🧪 SoftFactory Testing Guide

> **Purpose**: ```bash
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 SoftFactory Testing Guide 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

## Quick Start

### Run All Tests
```bash
pytest tests/ -v
```

### Run with Coverage
```bash
pytest tests/ -v --cov=backend --cov-report=term-missing
```

### Generate HTML Coverage Report
```bash
pytest tests/ --cov=backend --cov-report=html
# Open htmlcov/index.html
```

---

## Test Organization

```
tests/
├── unit/
│   ├── test_edge_cases.py              # Boundary values, edge cases (30+ tests)
│   └── test_models.py                  # Data model tests (4 tests)
├── integration/
│   ├── test_error_paths.py            # HTTP error codes 400/401/403/404/405 (40+ tests)
│   ├── test_api_endpoints.py          # API endpoint tests (12 tests)
│   ├── test_workflows.py              # Multi-step business flows (30+ tests)
│   └── test_services.py               # Service logic tests (40+ tests)
├── e2e/
│   └── test_user_journeys.py          # End-to-end user journeys (7 tests)
└── conftest.py                         # pytest fixtures and configuration
```

---

## Test Execution Modes

### Run Specific Test Files
```bash
# Edge case tests
pytest tests/unit/test_edge_cases.py -v

# Error path tests
pytest tests/integration/test_error_paths.py -v

# Workflow tests
pytest tests/integration/test_workflows.py -v

# Service tests
pytest tests/integration/test_services.py -v
```

### Run Specific Test Class
```bash
pytest tests/unit/test_edge_cases.py::TestUserModelEdgeCases -v
pytest tests/integration/test_error_paths.py::TestAuthenticationErrorPaths -v
pytest tests/integration/test_workflows.py::TestCooCookWorkflow -v
```

### Run Specific Test Method
```bash
pytest tests/unit/test_edge_cases.py::TestUserModelEdgeCases::test_user_with_empty_email -v
pytest tests/integration/test_error_paths.py::TestAuthenticationErrorPaths::test_missing_auth_header -v
```

---

## Coverage Reports

### Terminal Report
```bash
pytest tests/ --cov=backend --cov-report=term-missing
```

Shows:
- Coverage percentage per module
- Missing lines (not covered)
- Coverage summary

### HTML Report
```bash
pytest tests/ --cov=backend --cov-report=html
open htmlcov/index.html
```

Interactive report with:
- Color-coded coverage status
- Line-by-line coverage details
- Branch coverage information
- Coverage trends

### JSON Report
```bash
pytest tests/ --cov=backend --cov-report=json
```

Machine-readable format for CI/CD integration

---

## Test Categories

### Unit Tests: Edge Cases (30+ tests)
Tests boundary conditions and edge cases:

**User Model:**
- Empty email, very long email, duplicate email
- Role defaults, is_active defaults
- Timestamp generation

**Product Model:**
- Zero/negative/very high prices
- NULL annual_price, duplicate slug
- is_active state

**Booking Model:**
- Past dates, zero/long duration
- Price validation, status values

**Campaign Model:**
- Zero max_reviewers, past deadlines
- Status enum values

**Chef Model:**
- Zero/perfect rating, price validation
- NULL bio

**Payment Model:**
- Zero amount, multiple currencies
- Status values

### Integration Tests: Error Paths (40+ tests)
Tests HTTP error scenarios:

**Authentication (401)**
- Missing header, invalid token
- Expired token, malformed header

**Validation (400)**
- Missing required fields
- Invalid field values
- Malformed JSON

**Authorization (403)**
- Admin endpoint without admin role
- Access without subscription
- Inactive user

**Not Found (404)**
- Non-existent endpoint
- Non-existent resource ID

**Method Error (405)**
- GET on POST-only endpoint
- POST on GET-only endpoint

### Integration Tests: Workflows (30+ tests)
Tests complete business processes:

- User registration → login → access dashboard
- Browse chefs → book chef → view bookings
- Browse campaigns → apply to campaign
- Create SNS post → schedule post
- Browse scenarios → deploy automation
- Enroll in bootcamp → track progress
- Payment flow → subscription management

### Integration Tests: Services (40+ tests)
Tests service-specific business logic:

**CooCook Service:**
- Chef data validation
- Rating/price constraints
- Booking logic

**Review Service:**
- Campaign data validation
- Application requirements
- Status tracking

**SNS Auto Service:**
- Post status validation
- Platform/template validation
- Scheduling logic

**AI Automation Service:**
- Scenario validation
- Complexity levels
- Deployment logic

**WebApp Builder Service:**
- Plan validation
- Enrollment tracking
- Progress measurement

**Platform Service:**
- Health checks
- Infrastructure monitoring

---

## Common Test Patterns

### Test Database Setup
```python
@pytest.fixture(scope="function")
def db(app):
    """Test database with rollback."""
    with app.app_context():
        connection = _db.engine.connect()
        transaction = connection.begin()
        yield _db
        transaction.rollback()
        connection.close()
```

### Test Client Setup
```python
def test_example(client, auth_headers):
    res = client.get("/api/endpoint", headers=auth_headers)
    assert res.status_code == 200
```

### Test with Demo Token
```python
def test_with_demo_token(client, auth_headers):
    # auth_headers = {"Authorization": "Bearer demo_token"}
    res = client.get("/api/platform/dashboard", headers=auth_headers)
    assert res.status_code == 200
```

### Test Database Operations
```python
def test_model(db):
    from backend.models import User
    user = User(email="test@example.com", name="Test")
    db.session.add(user)
    db.session.commit()
    assert user.id is not None
```

---

## Debugging Tests

### Run with Verbose Output
```bash
pytest tests/ -vv --tb=long
```

### Run with Print Statements
```bash
pytest tests/ -v -s
```

### Run with Debugger
```bash
pytest tests/ -v --pdb
```

Drops into pdb on failure

### Run Specific Test with Full Output
```bash
pytest tests/path/to/test.py::TestClass::test_method -vv --tb=long -s
```

---

## Performance

### Run Fastest Tests First
```bash
pytest tests/ -v --durations=0
```

Shows execution time per test

### Run Tests in Parallel (pytest-xdist)
```bash
pip install pytest-xdist
pytest tests/ -n auto
```

### Profile Test Execution
```bash
pytest tests/ --profile --profile-svg
```

---

## Continuous Integration

### Pre-commit Hook
```bash
# .git/hooks/pre-commit
#!/bin/bash
pytest tests/ -q --tb=short
```

### CI/CD Pipeline
```bash
# In your CI/CD config (GitHub Actions, GitLab CI, etc.)
- name: Run Tests
  run: pytest tests/ -v --cov=backend --cov-report=json

- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    files: ./coverage.json
```

---

## Test Maintenance

### Update Edge Case Tests
Edit `tests/unit/test_edge_cases.py` to add:
- New boundary conditions
- Additional enum values
- Constraint violations

### Add New Error Path Tests
Edit `tests/integration/test_error_paths.py` to add:
- New HTTP status codes
- New validation rules
- New error scenarios

### Add Workflow Tests
Edit `tests/integration/test_workflows.py` to add:
- New user journeys
- New process flows
- Multi-service interactions

### Add Service Tests
Edit `tests/integration/test_services.py` to add:
- New service features
- Data consistency checks
- Performance assertions

---

## Troubleshooting

### Issue: Tests fail with "UNIQUE constraint failed"
**Solution:** Tests use shared database; add unique identifiers:
```python
import uuid
email = f"test-{uuid.uuid4().hex[:8]}@example.com"
```

### Issue: "Port 8000 already in use"
**Solution:** Close existing server or change port in conftest.py

### Issue: "Module not found"
**Solution:** Run from project root:
```bash
cd /d/Project
pytest tests/ -v
```

### Issue: Coverage report shows 0%
**Solution:** Ensure tests actually exercise the code:
```bash
pytest tests/ --cov=backend --cov-report=term-missing
```

---

## Best Practices

1. **Use Fixtures:** Share setup code with @pytest.fixture
2. **Isolate Tests:** Each test should be independent
3. **Use Descriptive Names:** test_user_with_very_long_email (not test_user_1)
4. **Test One Thing:** Each test validates single behavior
5. **Mock External APIs:** Don't call Stripe, social media APIs in tests
6. **Use Unique Data:** Avoid duplicate email/slug conflicts
7. **Document Edge Cases:** Add comments for non-obvious tests
8. **Keep Tests Fast:** Avoid slow operations (long sleeps, heavy I/O)

---

## Coverage Targets

| Layer | Target | Current | Status |
|-------|--------|---------|--------|
| Unit | 95%+ | 90% | ✅ High |
| Integration | 85%+ | 89% | ✅ High |
| Services | 80%+ | 46% | 🟡 Medium |
| Overall | 85%+ | 45% | 🔴 Low |

**Note:** Coverage percentage will increase as API responses are normalized.

---

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-cov Documentation](https://pytest-cov.readthedocs.io/)
- [unittest.mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/14/faq/sqlalchemy_orm.html#faq-testing-sqlalchemy-orm)

---

*Last Updated: 2026-02-25*