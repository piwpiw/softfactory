# COMMON PROJECT GUIDELINES
> **Platform Standard** | Version 1.0 | 2026-02-25
> **Authority:** Enterprise Governance v3.0 (CLAUDE.md Section 17)

---

## 1. PROJECT DEFINITION STANDARDS

### 1.1 Scope Definition (Mandatory Template)

Every project MUST begin with explicit scope-in/out:

```markdown
## PROJECT SCOPE

**SCOPE IN:**
- Feature/Component A (1-2 sentences)
- Feature/Component B
- Integration with System X

**SCOPE OUT (Explicitly Excluded):**
- Legacy system migration (save for Phase 2)
- Mobile app (Phase 3 future)
- Advanced analytics (MVP uses basic metrics)

**Success Metrics (SMART):**
- [ ] API responds in <200ms (p99)
- [ ] 95%+ uptime (SLA)
- [ ] 100% test coverage on critical paths
- [ ] Zero security vulnerabilities (Critical)
- [ ] Supports 1000 concurrent users
```

**Rule:** Scope-out is as important as scope-in. Prevents scope creep (cost savings: 20-30% token reduction).

---

### 1.2 Project Charter (Per Project)

| Element | Definition | Owner | Deadline |
|---------|-----------|-------|----------|
| **Project Name** | Unique, no abbreviation | PM | Day 1 |
| **Objective** | Business outcome (1 sentence) | PM | Day 1 |
| **Stakeholders** | List + role + authority level | Orchestrator | Day 1 |
| **Success Criteria** | 3-5 measurable KPIs | PM | Day 1 |
| **Technology Stack** | Approved list (→ Section 2) | Architect | Day 1 |
| **Timeline** | Phases 1-7 durations | Orchestrator | Day 1 |
| **Budget/Resources** | Token budget, agents assigned | Orchestrator | Day 1 |
| **Risk Register** | Top 5 risks + mitigation | Architect | Day 1 |
| **Handoff Owners** | Agent A→B→C→D→E assignments | Orchestrator | Day 1 |

---

### 1.3 Stakeholder Authority Matrix

```
Role              | Scope Decision | Tech Decision | Budget | Risk | Timeline
------------------+----------------+---------------+--------+------+----------
PM / Product      | ✅ APPROVE     | Recommend     | ✅     | ✅   | ✅
Architect         | Input          | ✅ APPROVE    | Input  | ✅   | Input
Dev Lead          | Input          | ✅ VETO       | Input  | ⚠️   | Input
QA Lead           | Input          | Input         | -      | ✅   | Input
Security Officer  | Input          | ⚠️ Escalate   | -      | ✅   | -
Orchestrator      | Monitor        | Validate      | Track  | Sync | ✅ ENFORCE
```

**Escalation Path:** Authority conflict → Orchestrator → User approval.

---

## 2. TECHNOLOGY STACK CONVENTIONS

### 2.1 Approved Stack (Platform Standard)

**Backend Framework:**
```
✅ APPROVED: FastAPI (async, OpenAPI auto-docs, Pydantic validation)
✅ LEGACY: Flask (SoftFactory, maintenance mode)
❌ NOT APPROVED: Django, FastAPI + sync endpoints
```

**Database:**
```
✅ PRIMARY: PostgreSQL 15+ (production)
✅ CACHE: Redis 7+ (sessions, queues)
✅ TESTING: SQLite 3.40+ (local dev only, absolute path required)
❌ NOT APPROVED: MongoDB (unless explicitly approved in ADR)
```

**Frontend Framework:**
```
✅ APPROVED: Next.js 15+ (React 19, server components)
✅ APPROVED: Vanilla JS + semantic HTML (internal tools)
❌ NOT APPROVED: Vue, Angular (platform standard is React)
```

**Authentication:**
```
✅ APPROVED: JWT (HS256 or RS256, 1hr access + 7d refresh)
✅ APPROVED: API Keys (service-to-service, scoped)
⚠️ REVIEW REQUIRED: OAuth 2.0 (external integrations only)
❌ NOT APPROVED: Session cookies (no stateful auth)
```

**Testing Framework:**
```
✅ APPROVED: pytest (unit + integration)
✅ APPROVED: Playwright (E2E browser automation)
✅ APPROVED: unittest (Python standard library fallback)
❌ NOT APPROVED: Mocha+Chai (Node.js, use Playwright instead)
```

**Infrastructure:**
```
✅ APPROVED: Docker containers + Docker Compose (local)
✅ APPROVED: Railway (staging/production)
✅ APPROVED: GitHub Actions (CI/CD)
⚠️ REVIEW REQUIRED: Kubernetes (enterprise, ADR required)
❌ NOT APPROVED: Serverless (lock-in risk)
```

---

### 2.2 Stack Migration Rules

If proposing NEW technology:
1. **Create ADR** in `shared-intelligence/decisions.md`
2. **Risk Assessment:** trade-offs vs. approved stack
3. **Proof of Concept:** working demo (not proposal)
4. **Team Review:** Architect + DevOps sign-off
5. **Success Metrics:** measurable difference (performance, cost, dev velocity)

Example ADR header:
```markdown
## ADR-XXXX: [Decision Title]

**Status:** PROPOSED | ACCEPTED | REJECTED | SUPERSEDED

**Context:** Why current stack insufficient?
**Decision:** Adopt [Technology] because...
**Consequences:** Trade-offs, constraints, impact
**Alternatives Considered:** A, B, C and why rejected
```

---

## 3. CODE QUALITY STANDARDS

### 3.1 Linting & Formatting (Non-Negotiable)

**Python:**
```bash
# Linting: must pass before commit
pylint --disable=C0103,W0212 src/ --fail-under=8.0

# Formatting: enforced by pre-commit hook
black --line-length=100 src/
isort --profile=black src/

# Type checking: 100% of code paths
mypy src/ --strict
```

**JavaScript/TypeScript:**
```bash
# Linting: ESLint
eslint --max-warnings=0 src/

# Formatting: Prettier
prettier --write src/

# Type checking: tsc
tsc --strict --noEmit
```

**Markdown:**
```bash
markdownlint --fix docs/
```

**Rule:** Zero warnings on main branch. Warnings = CI failure.

---

### 3.2 Type Safety (100% Coverage)

**Python:**
```python
# ✅ CORRECT: All parameters and returns typed
def process_user(user_id: int, name: str) -> dict[str, Any]:
    return {"id": user_id, "name": name}

# ❌ WRONG: Missing type hints
def process_user(user_id, name):
    return {"id": user_id, "name": name}
```

**TypeScript:**
```typescript
// ✅ CORRECT: Strict mode, explicit types
interface User {
  id: number;
  name: string;
  role: "admin" | "user";
}
const getUser = (id: number): User => { ... }

// ❌ WRONG: Using 'any'
const getUser = (id: any): any => { ... }
```

---

### 3.3 Test Coverage (Minimum 80%)

**Rule:** No merge without ≥80% coverage on critical paths.

```bash
# Generate coverage report
pytest --cov=src --cov-report=html

# Check coverage
coverage report --fail-under=80
```

**Critical Paths (100% required):**
- Authentication & authorization
- Payment processing
- Data validation
- Error handling
- Database operations

**Non-Critical Paths (80% acceptable):**
- UI components
- Logging helpers
- Utility functions

---

### 3.4 Secret Management (Zero Leaks)

**Rules:**
1. **No secrets in code.** Ever. Use `.env` files (`.gitignore`).
2. **Environment variable pattern:** `PREFIX_NAME` (e.g., `DB_URL`, `JWT_SECRET`)
3. **Validation:** `python -m safety check` (dependency vulnerabilities)
4. **Scanning:** Pre-commit hook runs `detect-secrets` on all files

**Unsafe Patterns (Blocked):**
```python
# ❌ NEVER
password = "hardcoded123"
api_key = os.getenv("API_KEY", "default_key")  # default exposed

# ✅ CORRECT
password = os.getenv("DB_PASSWORD")
if not password:
    raise ValueError("DB_PASSWORD environment variable not set")
```

---

### 3.5 Code Review Checklist (Before Merge)

Every PR must pass:

- [ ] Linting: Zero warnings
- [ ] Type checking: 100% pass
- [ ] Tests: All passing + ≥80% coverage
- [ ] Security: No hardcoded secrets, OWASP Top 10 reviewed
- [ ] Performance: No O(n²) algorithms, no N+1 queries
- [ ] Documentation: Docstrings on all public functions/classes
- [ ] Changelog: Updated CHANGELOG.md (if customer-facing)
- [ ] Backward compatibility: No breaking API changes (or justified ADR)

---

## 4. DOCUMENTATION REQUIREMENTS

### 4.1 Every Project MUST Include

#### 4.1.1 README.md
```markdown
# [Project Name]

**What:** One sentence describing the project
**Why:** Business context / problem solved
**How:** Quick start (5 steps max)

## Installation
```bash
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
```

## Running Locally
```bash
# Start server
python app.py
# Access at http://localhost:8000
```

## API Documentation
See [docs/API.md](./docs/API.md) or visit http://localhost:8000/docs (auto-generated by FastAPI)

## Architecture
See [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)

## Deployment
See [docs/DEPLOYMENT.md](./docs/DEPLOYMENT.md)

## Contributing
See [CONTRIBUTING.md](./CONTRIBUTING.md)
```

#### 4.1.2 ARCHITECTURE.md
```markdown
# Architecture

## Overview
[System diagram: Components + interactions]

## Key Decisions
[List of ADRs affecting this module]

## Data Model
[Entity relationships, key tables]

## API Contract
[Endpoints + example requests/responses]

## Security Considerations
[Auth, encryption, input validation]

## Performance Considerations
[Caching strategy, database indexes, known bottlenecks]
```

#### 4.1.3 API.md
```markdown
# API Documentation

## Authentication
Bearer token in Authorization header

## Endpoints

### GET /api/users/{id}
**Description:** Fetch user by ID
**Parameters:** id (integer)
**Response:** 200 { id, name, email, role }
**Errors:** 404 (not found), 401 (unauthorized)

...
```

#### 4.1.4 DEPLOYMENT.md
```markdown
# Deployment Guide

## Prerequisites
- Docker 24.0+
- PostgreSQL 15+ (production)

## Steps
1. Build image: `docker build -t app:latest .`
2. Push to registry: `docker push registry.example.com/app:latest`
3. Deploy: `kubectl apply -f k8s/`

## Rollback
[Procedure to revert on failure]

## Monitoring
[Health checks, alerts, dashboards]
```

#### 4.1.5 CONTRIBUTING.md
```markdown
# Contributing

## Branch Naming
`feature/{project}/{description}` or `bugfix/{issue-id}`

## Commit Message Format
```
[type]: [description]

[body explaining why, not what]

Fixes #123
```

## Pull Request Template
[See PR_TEMPLATE.md in .github/]

## Code Review SLA
- Team members: 24 hours
- External: 48 hours
```

---

### 4.2 Code Comments (Sparingly)

**Rule:** Code should be self-documenting. Comments explain WHY, not WHAT.

```python
# ❌ BAD: Repeats what code does
x = x + 1  # Increment x

# ✅ GOOD: Explains non-obvious intent
# Use UTC epoch instead of local time to avoid DST edge cases
timestamp = int(time.time())
```

---

### 4.3 Docstring Format (Google Style)

**Python:**
```python
def calculate_subscription_cost(
    base_price: float,
    discount_percent: float = 0,
    tax_rate: float = 0.08
) -> float:
    """Calculate total subscription cost with tax and discount.

    Args:
        base_price: Annual subscription cost in USD
        discount_percent: Percentage discount (0-100)
        tax_rate: Local tax rate as decimal (default: 8%)

    Returns:
        Total cost including tax and discount

    Raises:
        ValueError: If discount_percent < 0 or > 100
    """
    if not 0 <= discount_percent <= 100:
        raise ValueError("discount_percent must be 0-100")
    discounted = base_price * (1 - discount_percent / 100)
    return discounted * (1 + tax_rate)
```

---

## 5. GIT WORKFLOW

### 5.1 Branch Strategy

**Main branch:** `main` (production-ready, always deployable)
**Release branch:** `release/v1.2.3` (hot-fix only)
**Development branch:** Feature or bugfix branches only

**Branch naming:**
```
feature/{project-id}/{description}    # New features
bugfix/{issue-id}                      # Bug fixes
refactor/{component}                   # Code cleanup
docs/{topic}                           # Documentation
```

**Example:**
```bash
feature/M-002/user-authentication
bugfix/123-jwt-expiry-edge-case
refactor/payment-service
docs/api-guide-v2
```

---

### 5.2 Commit Message Standard

**Format:**
```
[type]: [description]

[optional body explaining why]

[optional footer: Co-Authored-By, Fixes, Closes]
```

**Types:** `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`

**Examples:**

```
feat: Add JWT refresh token endpoint

Implements 7-day refresh token rotation to improve security
while reducing authentication service load.

Fixes #245
```

```
fix: Prevent SQLite path duplication in tests

Use absolute path `sqlite:///D:/Project/platform.db` instead
of relative path to avoid creating duplicate databases in
different directories.

Co-Authored-By: Claude Haiku <noreply@anthropic.com>
```

---

### 5.3 Pull Request (PR) Requirements

**Every PR must:**
- [ ] Link to issue or ADR (`Fixes #123` or `Implements ADR-0004`)
- [ ] Pass all CI checks (linting, tests, security scan)
- [ ] Have ≥1 approval from code owner
- [ ] Include changes to tests (if production code changed)
- [ ] Update CHANGELOG.md (if customer-facing)
- [ ] No merge conflicts with `main`

**PR Template:**
```markdown
## Summary
[1-2 sentences: what changed and why?]

## Changes
- Feature A
- Bug fix B
- Refactoring C

## Testing
- [ ] Unit tests added
- [ ] Integration tests pass
- [ ] Manual testing completed (describe)

## Screenshots (if UI changed)
[Include before/after if applicable]

## Checklist
- [ ] Code follows style guide
- [ ] Documentation updated
- [ ] No breaking changes (or ADR filed)
```

---

### 5.4 Main Branch Protection Rules

```
✅ Require status checks (CI/CD)
✅ Require code reviews (1 minimum)
✅ Require up-to-date branches before merge
❌ DO NOT allow force push
❌ DO NOT allow direct commits (PR required)
```

---

### 5.5 Merge Strategy

**Rule:** Squash + merge for feature branches, rebase for hotfixes.

```bash
# Feature branch → main (squash + merge)
git checkout main
git pull origin main
git merge --squash feature/M-002/auth
git commit -m "feat: Implement JWT authentication"

# Hotfix → main (rebase, if commit history important)
git checkout main
git pull
git rebase hotfix/critical-bug
git push origin main
```

---

### 5.6 Release Process

**When cutting release (e.g., v1.2.0):**

```bash
git checkout main
git pull
git tag -a v1.2.0 -m "Release v1.2.0: [highlights]"
git push origin v1.2.0
```

**Deployment triggered automatically** by GitHub Actions workflow.

---

## 6. QUALITY GATES (Enforcement)

| Gate | Owner | Timeline | Pass Criteria |
|------|-------|----------|---------------|
| **Linting** | CI/CD | Pre-commit | 0 warnings |
| **Type Check** | CI/CD | Pre-commit | 100% pass |
| **Unit Tests** | CI/CD | Pre-commit | 100% pass |
| **Coverage** | CI/CD | PR merge | ≥80% |
| **Security Scan** | CI/CD | PR merge | 0 Critical |
| **Code Review** | Dev Team | 24hr SLA | 1 approval |
| **Integration Test** | CI/CD | Post-merge | 100% pass |
| **Performance Test** | QA | Phase 3 | <200ms p99 |

---

## 7. CROSS-REFERENCES

For deeper guidance on related topics:

- **Project governance:** → `SUBPROJECT_CLAUDE_TEMPLATE.md`
- **Workflow & phases:** → `WORKFLOW_PROCESS.md`
- **Handoff gates:** → `CROSS_VALIDATION_CHECKLIST.md`
- **Decision logging:** → `shared-intelligence/decisions.md`
- **Known pitfalls:** → `shared-intelligence/pitfalls.md`
- **Reusable patterns:** → `shared-intelligence/patterns.md`

---

**Version:** 1.0 | **Last Updated:** 2026-02-25 | **Status:** ACTIVE
