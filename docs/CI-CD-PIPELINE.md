# CI/CD Pipeline Documentation

## Overview

SoftFactory Platform uses a comprehensive CI/CD pipeline built on GitHub Actions, pre-commit hooks, and automated testing. This document covers setup, usage, and best practices.

## Architecture

```
Commit → Pre-commit Hooks → Test Job → Build Job → Deploy Job
         ↓                     ↓           ↓
       Lint              Run Tests    Docker Build
       Format            Coverage      Security Scan
       Security          E2E Tests
```

## Components

### 1. Pre-Commit Hooks

Local hooks run on your machine before commits are created.

**Location:** `.pre-commit-config.yaml`, `.husky/`

**Tools:**
- **Black** - Code formatting
- **isort** - Import sorting
- **Flake8** - Linting
- **mypy** - Type checking
- **Bandit** - Security scanning
- **detect-secrets** - Secret detection
- **Commitlint** - Commit message validation

**Setup:**
```bash
# Run the setup script
bash scripts/setup_ci_cd.sh

# Or manual setup
pip install pre-commit
pre-commit install --hook-stage commit
pre-commit install --hook-stage commit-msg
```

**Usage:**
```bash
# Commit normally (hooks run automatically)
git commit -m "feat: add new feature"

# Run hooks on all files
pre-commit run --all-files

# Bypass hooks (not recommended)
git commit --no-verify
```

### 2. GitHub Actions Workflows

#### test.yml - Testing & Coverage
**Triggers:** Push to main/develop, Pull requests

**Matrix Testing:**
- Python 3.9, 3.10, 3.11
- PostgreSQL 15 service
- Unit, integration, and E2E tests

**Artifacts:**
- Coverage reports (codecov)
- Test results

**Configuration:**
```yaml
- Coverage threshold: 80%
- Minimum green threshold: 90%
- Minimum orange threshold: 80%
```

**Key Steps:**
1. Dependency installation
2. Flake8 linting
3. Type checking with mypy
4. Unit tests
5. Integration tests (with PostgreSQL)
6. E2E tests
7. Coverage reporting to Codecov
8. PR comments with coverage

#### build.yml - Docker Image Building
**Triggers:** Push to main/develop, Tags, Pull requests

**Features:**
- Multi-stage Docker build
- Layer caching for efficiency
- Container registry push
- Trivy security scanning
- SARIF upload to GitHub Security

**Configuration:**
```
Registry: ghcr.io
Image naming: ghcr.io/{owner}/{repo}
Tags: branch, PR, semantic version, SHA
```

#### deploy.yml - Production Deployment
**Triggers:** Semantic version tags (v*), Manual workflow dispatch

**Stages:**
1. **Test** - Run full test suite before deploy
2. **Build** - Build and push Docker image
3. **Deploy Staging** - Optional staging deployment
4. **Deploy Production** - Deploy on version tags
5. **Health Checks** - Verify deployment
6. **Notifications** - Slack alerts

**Requirements:**
- Tests must pass
- Security scans must pass
- Deployment only on version tags (automatic or manual)

**Secrets Required:**
- `DEPLOY_KEY_STAGING` - Deployment credentials
- `DEPLOY_KEY_PROD` - Production credentials
- `SLACK_WEBHOOK` - Notification webhook

#### security.yml - Security Scanning
**Triggers:** Push, Pull requests, Weekly schedule (Sunday 2 AM)

**Scans Performed:**
- **CodeQL** - SAST analysis (Python, JavaScript)
- **Dependency Check** - Vulnerable dependencies
- **Bandit** - Python security issues
- **Semgrep** - Pattern-based security scanning
- **Safety** - Python package vulnerabilities
- **OWASP ZAP** - Dynamic application security
- **TruffleHog** - Secret detection
- **detect-secrets** - High entropy strings

**Output:**
- SARIF reports → GitHub Security tab
- Artifacts for review

#### release.yml - Release & Versioning
**Triggers:** Push to main, Manual dispatch

**Features:**
- Semantic versioning (automatic)
- Changelog generation
- Release notes
- Docker image publishing
- Cross-platform artifact building

**Requirements:**
- Conventional commits for auto-versioning
- Tests must pass
- Security scans must pass

## Commit Message Format

All commits must follow [Conventional Commits](https://www.conventionalcommits.org/) format:

```
type(scope): subject

body

footer
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation
- `style` - Code style (no logic changes)
- `refactor` - Code refactoring
- `perf` - Performance improvements
- `test` - Test additions/changes
- `chore` - Other changes
- `ci` - CI/CD changes
- `security` - Security fixes
- `build` - Build system changes

**Examples:**
```
feat(auth): add JWT token refresh

feat: add OAuth2 integration

fix(api): resolve null pointer in user endpoint

docs: update deployment guide

security: fix OWASP vulnerability in login form
```

## Testing

### Local Testing

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-xdist pytest-timeout pytest-mock

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=backend --cov-report=html

# Run specific test file
pytest tests/unit/test_models.py -v

# Run with specific markers
pytest tests/ -m "not slow" -v

# Run in parallel
pytest tests/ -n auto
```

### Test Structure

```
tests/
├── conftest.py          # Fixtures and configuration
├── unit/                # Unit tests (no external dependencies)
│   ├── test_models.py
│   └── test_edge_cases.py
├── integration/         # Integration tests (with services)
│   ├── test_api_endpoints.py
│   ├── test_services.py
│   └── test_workflows.py
├── e2e/                 # End-to-end tests
│   └── test_user_journeys.py
└── performance/         # Performance tests
```

### Coverage Requirements

- **Minimum:** 80%
- **Target:** 90%+
- **Critical paths:** 100%

View coverage report:
```bash
coverage report
coverage html  # Generate interactive report
```

## Code Quality

### Formatting & Linting

```bash
# Format code with Black
black backend tests --line-length=120

# Sort imports
isort --profile black --line-length 120 backend tests

# Lint with Flake8
flake8 backend tests --max-line-length=120

# Type check with mypy
mypy backend --ignore-missing-imports

# Security check with Bandit
bandit -r backend -ll --skip B101,B601
```

### Pre-Commit Checks

Run all pre-commit checks manually:
```bash
pre-commit run --all-files
```

Skip specific checks:
```bash
# Skip type checking
pre-commit run --all-files --exclude mypy

# Run only specific hook
pre-commit run black --all-files
```

## Docker

### Building Locally

```bash
# Build image
docker build -t softfactory:local .

# Run container
docker run -p 8000:8000 softfactory:local

# Health check
curl http://localhost:8000/health
```

### Multi-Stage Build

The Dockerfile uses multi-stage build for efficiency:

1. **Builder stage** - Installs dependencies
2. **Runtime stage** - Minimal runtime image

Benefits:
- Smaller final image
- Faster deployments
- Better security

## Deployment

### Staging Deployment

Trigger manually:
```bash
# Via GitHub UI: Actions → Deploy to Production → Run workflow
# Select environment: staging
```

### Production Deployment

Automatic on version tags:
```bash
# Create and push version tag
git tag v1.2.3
git push origin v1.2.3
```

Or manual trigger with workflow_dispatch:
```
GitHub UI → Actions → Deploy to Production → Run workflow
```

### Rollback

Automatic rollback on deployment failure.

Manual rollback:
```bash
# Revert to previous version
git tag v1.2.2 <commit-hash>
git push origin v1.2.2
```

## Monitoring & Notifications

### GitHub Actions Status

- View on: https://github.com/{owner}/{repo}/actions
- Filter by workflow, status, branch

### Slack Integration

Configure webhook in GitHub:
1. Create Slack webhook URL
2. Add secret: `SLACK_WEBHOOK`
3. Workflows automatically notify on:
   - Deployment success
   - Deployment failure
   - New releases

### Codecov Integration

View coverage:
- https://codecov.io/gh/{owner}/{repo}
- Coverage reports on PRs
- Trend tracking

## Troubleshooting

### Test Failures

```bash
# Run tests with verbose output
pytest tests/ -vv

# Run with printing enabled
pytest tests/ -s

# Run specific test
pytest tests/unit/test_models.py::TestClass::test_method -v
```

### Pre-Commit Hook Issues

```bash
# Bypass hooks temporarily (not recommended)
git commit --no-verify

# Reset pre-commit cache
pre-commit clean

# Reinstall hooks
pre-commit install --install-hooks
```

### Coverage Below Threshold

```bash
# Check coverage by file
coverage report --skip-covered

# Generate HTML report
coverage html
open htmlcov/index.html

# Find uncovered lines
coverage report -m | grep -v "100%"
```

### Security Scan Failures

Check specific scan results:
- CodeQL: GitHub Security tab → Code scanning alerts
- Bandit: Check workflow logs
- Trivy: Check artifact or Docker registry

### Deployment Failures

1. Check GitHub Actions logs
2. Verify secrets are configured
3. Check deployment environment status
4. Review recent commits for breaking changes

## Best Practices

### Commit Hygiene

- ✅ Write descriptive commit messages
- ✅ Keep commits focused and atomic
- ✅ Review changes before committing
- ✅ Run tests locally before pushing
- ❌ Don't commit secrets or sensitive data
- ❌ Don't commit large binary files
- ❌ Don't force push to main

### Pull Request Workflow

1. Create feature branch: `git checkout -b feat/feature-name`
2. Make changes and commit
3. Push and create PR
4. Wait for CI checks to pass
5. Request code review
6. Address feedback
7. Merge when approved

### Testing

- ✅ Write tests for new features
- ✅ Update tests for changed behavior
- ✅ Run full test suite before pushing
- ✅ Aim for >90% coverage
- ❌ Don't commit with failing tests
- ❌ Don't skip tests with `@pytest.mark.skip`

### Deployment

- ✅ Use semantic versioning
- ✅ Create detailed release notes
- ✅ Tag releases in git
- ✅ Monitor deployment logs
- ✅ Have rollback plan
- ❌ Don't deploy without testing
- ❌ Don't manually edit production

## Security Considerations

### Secrets Management

Secrets are managed through GitHub:
- Settings → Secrets and variables → Actions
- Never commit `.env` files
- Use environment-specific secrets
- Rotate secrets regularly

### Credential Configuration

```bash
# Set secrets in GitHub UI
DEPLOY_KEY_STAGING=***
DEPLOY_KEY_PROD=***
SLACK_WEBHOOK=***
```

### Secret Scanning

- TruffleHog scans for exposed secrets
- detect-secrets finds high-entropy strings
- GitHub native secret scanning enabled
- Alerts on new secret detection

## Performance Optimization

### Workflow Optimization

- Parallel testing across Python versions
- Docker layer caching
- Pre-commit hook caching
- Dependency caching with actions/setup-python

### Build Optimization

- Multi-stage Docker build
- Minimal base images
- Layer ordering (least to most frequently changed)
- BuildKit cache mount

## Maintenance

### Regular Updates

- Update action versions: `@v3` → `@v4`
- Update tool versions in requirements.txt
- Review and update security rules
- Monitor for deprecated features

### Health Checks

```bash
# Verify all workflows
gh workflow list

# Check recent runs
gh run list --workflow=test.yml

# View workflow details
gh workflow view test.yml
```

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [Pre-commit Framework](https://pre-commit.com/)
- [CodeQL Documentation](https://codeql.github.com/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

## Support

For issues or questions:
1. Check GitHub Actions logs
2. Review this documentation
3. Check project README
4. Open an issue on GitHub

---

**Last Updated:** 2026-02-25
**Version:** 1.0
**Maintained By:** DevOps Team
