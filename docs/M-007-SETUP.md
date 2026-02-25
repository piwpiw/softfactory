# M-007 Development Environment Setup Guide

**Version:** 1.0.0
**Date:** 2026-02-26
**Status:** Production-Ready
**Target Audience:** Developers, QA Engineers, DevOps Engineers

---

## Quick Start (5 minutes)

For the impatient:

```bash
git clone https://github.com/your-org/softfactory.git
cd softfactory
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python start_platform.py
# Open http://localhost:8000
```

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Git Repository Setup](#git-repository-setup)
3. [Python Environment](#python-environment)
4. [Backend Setup](#backend-setup)
5. [Frontend Setup](#frontend-setup)
6. [Database Setup](#database-setup)
7. [Running Locally](#running-locally)
8. [Testing](#testing)
9. [Code Quality Tools](#code-quality-tools)
10. [IDE Configuration](#ide-configuration)
11. [Troubleshooting](#troubleshooting)
12. [Useful Commands](#useful-commands)

---

## System Requirements

### Operating Systems

| OS | Version | Status |
|----|---------|--------|
| Windows | 10, 11 | ✅ Supported |
| macOS | 11+ | ✅ Supported |
| Linux | Ubuntu 20.04+, CentOS 7+ | ✅ Supported |

### Software Requirements

| Tool | Minimum | Recommended | How to Check |
|------|---------|-------------|--------------|
| Python | 3.11 | 3.11.9 | `python --version` |
| pip | 23.0 | Latest | `pip --version` |
| git | 2.30 | 2.43+ | `git --version` |
| Node.js | 18.0 | 22.0+ | `node --version` |
| npm | 9.0 | 10.0+ | `npm --version` |

### Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU Cores | 2 | 4 |
| RAM | 2GB | 4GB |
| Disk Space | 5GB | 20GB |
| Internet | 5Mbps | 10Mbps |

### Ports

Make sure these ports are available:
- `8000` - Flask API server
- `5432` - PostgreSQL (if using local)
- `6379` - Redis (if using local)
- `3000` - Frontend dev server (if using Node)

Check if ports are in use:

```bash
# macOS/Linux
lsof -i :8000
lsof -i :5432

# Windows
netstat -ano | findstr :8000
netstat -ano | findstr :5432
```

---

## Git Repository Setup

### 1. Clone Repository

```bash
# HTTPS (if not using SSH keys)
git clone https://github.com/your-org/softfactory.git

# SSH (if you have SSH keys set up)
git clone git@github.com:your-org/softfactory.git

# Navigate to directory
cd softfactory
```

### 2. Configure Git

```bash
# Set your name and email
git config user.name "Your Name"
git config user.email "your.email@example.com"

# Set as global (applies to all projects)
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Verify configuration
git config --list | grep user
```

### 3. Install Pre-commit Hooks

```bash
# Install pre-commit framework
pip install pre-commit

# Install hooks
pre-commit install

# Run hooks on all files
pre-commit run --all-files
```

### 4. Create Feature Branch

```bash
# Pull latest
git pull origin main

# Create feature branch
git checkout -b feature/your-feature-name

# Or create from issue number
git checkout -b feature/123-your-feature-name
```

---

## Python Environment

### 1. Check Python Installation

```bash
# Check version
python --version
python3 --version

# Check pip
pip --version

# Check location
which python  # macOS/Linux
where python  # Windows
```

### 2. Create Virtual Environment

```bash
# Create venv in project directory
python -m venv venv

# Windows: Activate
venv\Scripts\activate

# macOS/Linux: Activate
source venv/bin/activate

# Verify activation (prompt should show (venv))
which python
pip --version
```

### 3. Upgrade pip

```bash
# Upgrade pip
python -m pip install --upgrade pip

# Verify
pip --version
```

### 4. Create .venv Alias (Optional)

For convenience, create a symlink:

```bash
# macOS/Linux
ln -s venv .venv

# Then activate with
source .venv/bin/activate
```

---

## Backend Setup

### 1. Install Dependencies

```bash
# Ensure venv is activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Install from requirements.txt
pip install -r requirements.txt

# Verify installations
pip list | grep -E "Flask|SQLAlchemy|JWT"
```

### 2. Create .env File

Copy the example:

```bash
# Copy template
cp .env.example .env

# Edit with your values
nano .env  # macOS/Linux
notepad .env  # Windows
```

**Minimal .env for development:**

```bash
# Environment
ENVIRONMENT=development
DEBUG=True
LOG_LEVEL=DEBUG

# Server
PORT=8000
HOST=0.0.0.0

# Database (use SQLite for dev)
DATABASE_URL=sqlite:///platform.db

# JWT (use simple key for dev)
JWT_SECRET_KEY=dev-secret-key-change-this
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRES=3600

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# Demo mode (skip OAuth setup)
DEMO_MODE=True
```

### 3. Initialize Database

```bash
# Navigate to project root
cd /path/to/softfactory

# Create tables
python -c "from backend.app import db, create_app; app = create_app(); db.create_all()"

# Verify (should create platform.db)
ls -la platform.db
sqlite3 platform.db ".tables"
```

### 4. Verify Backend

```bash
# Import backend to check for errors
python -c "from backend.app import create_app; app = create_app(); print('Backend OK')"

# Start server for quick test
python start_platform.py
# Press CTRL+C to stop
```

---

## Frontend Setup

### 1. Verify Node.js (Optional)

For frontend development, you'll need Node.js:

```bash
# Check if installed
node --version
npm --version

# If not installed, download from https://nodejs.org/
# Install Node.js 22 LTS
```

### 2. Install Frontend Dependencies

```bash
# Install npm packages
npm install

# Verify installation
npm list --depth=0
```

### 3. Build Frontend (If Using Build Tool)

```bash
# If using webpack/rollup
npm run build

# Output goes to dist/ or build/
ls -la dist/
```

### 4. Frontend Dev Server (Optional)

```bash
# Start dev server (if configured)
npm run dev

# Usually runs on http://localhost:3000
```

---

## Database Setup

### SQLite (Development)

```bash
# Already created in previous step
sqlite3 platform.db

# View tables
.tables

# View schema for a table
.schema users

# Run queries
SELECT * FROM users LIMIT 5;

# Exit
.quit
```

### PostgreSQL (Optional, for Production Testing)

#### Install PostgreSQL

**macOS (Homebrew):**
```bash
brew install postgresql
brew services start postgresql
```

**Windows:**
```
Download from https://www.postgresql.org/download/windows/
Run installer
```

**Linux (Ubuntu):**
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

#### Create Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database and user
CREATE DATABASE softfactory;
CREATE USER softfactory_user WITH PASSWORD 'password';
ALTER ROLE softfactory_user SET client_encoding TO 'utf8';
GRANT ALL PRIVILEGES ON DATABASE softfactory TO softfactory_user;
\q

# Test connection
psql -U softfactory_user -d softfactory
```

#### Update .env

```bash
# Change DATABASE_URL
DATABASE_URL=postgresql://softfactory_user:password@localhost:5432/softfactory
```

#### Initialize Database

```bash
# Create tables
python -c "from backend.app import db, create_app; app = create_app(); db.create_all()"

# Verify
psql -U softfactory_user -d softfactory -c "\dt"
```

---

## Running Locally

### 1. Start Flask Server

```bash
# Ensure venv activated
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Start server
python start_platform.py

# Output should show:
# SoftFactory Platform Starting...
# Demo Mode (No Backend Needed):
#   Login Page:  http://localhost:8000/web/platform/login.html
#   Passkey:     demo2026
# API:
#   Base URL:    http://localhost:8000/api/
```

### 2. Access Application

Open browser:

```
Frontend: http://localhost:8000/web/platform/index.html
API: http://localhost:8000/api/
Health: http://localhost:8000/health
```

### 3. Login Credentials

**Demo User:**
```
Email: demo@softfactory.com
Password: demo123
Passkey: demo2026
```

**Admin User:**
```
Email: admin@softfactory.com
Password: admin123
```

### 4. Stop Server

```bash
# Press CTRL+C in terminal

# Or kill process
kill -9 $(lsof -t -i:8000)  # macOS/Linux
taskkill /F /PID <PID>     # Windows
```

---

## Testing

### Unit Tests

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run specific test file
pytest tests/unit/test_models.py -v

# Run with coverage
pytest tests/unit/ --cov=backend --cov-report=html
```

### Integration Tests

```bash
# Run integration tests
pytest tests/integration/ -v

# With database
pytest tests/integration/test_api_endpoints.py -v

# With specific marker
pytest tests/ -m "not slow" -v
```

### Full Test Suite

```bash
# Run all tests with coverage
pytest tests/ -v --cov=backend --cov-report=term-missing

# Generate HTML coverage report
pytest tests/ --cov=backend --cov-report=html
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### API Testing

```bash
# Manual testing with curl
curl http://localhost:8000/health
curl -H "Authorization: Bearer demo_token" http://localhost:8000/api/sns/linkinbio

# Use curl script
bash scripts/test_api.sh

# Use Postman
# Import collection: docs/postman/M-007-API.postman_collection.json
```

---

## Code Quality Tools

### Linting

```bash
# Install linting tools
pip install flake8 pylint

# Check code style
flake8 backend/ --max-line-length=120

# Detailed lint report
pylint backend/
```

### Code Formatting

```bash
# Install formatting tools
pip install black isort

# Format code
black backend/

# Sort imports
isort backend/

# Check without modifying
black --check backend/
```

### Type Checking

```bash
# Install mypy
pip install mypy

# Check types
mypy backend/ --ignore-missing-imports
```

### Security Scanning

```bash
# Install security tools
pip install bandit safety

# Check for security issues
bandit -r backend/

# Check for known vulnerabilities
safety check
```

### All-in-One Quality Check

```bash
# Run all checks
./scripts/check_quality.sh

# Or manually
flake8 backend/ && black --check backend/ && mypy backend/ && bandit -r backend/
echo "✅ All checks passed!"
```

---

## IDE Configuration

### VS Code

#### Extensions

```
Install:
- Python
- Pylance
- Flask
- SQLAlchemy
- Thunder Client (for API testing)
```

#### Settings (.vscode/settings.json)

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": ["--line-length=120"],
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "[python]": {
    "editor.defaultFormatter": "ms-python.python",
    "editor.formatOnSave": true
  }
}
```

#### Launch Configuration (.vscode/launch.json)

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Flask",
      "type": "python",
      "request": "launch",
      "module": "flask",
      "env": {
        "FLASK_APP": "backend.app",
        "FLASK_ENV": "development"
      },
      "args": ["run"],
      "jinja": true,
      "justMyCode": false
    }
  ]
}
```

### PyCharm

1. **Open Project**
   - File → Open → Select softfactory folder

2. **Configure Python Interpreter**
   - PyCharm → Preferences → Project → Python Interpreter
   - Click gear icon → Add → Existing Environment
   - Select venv/bin/python (macOS/Linux) or venv\Scripts\python.exe (Windows)

3. **Enable Flask Support**
   - Preferences → Languages & Frameworks → Flask
   - Check "Enable Flask Support"

4. **Run Configuration**
   - Run → Edit Configurations
   - Click + → Python
   - Script path: start_platform.py
   - Click OK

5. **Start Debugging**
   - Run → Run or Debug (F9)

---

## Troubleshooting

### Virtual Environment Issues

**Problem:** `venv activation doesn't work`

```bash
# Recreate venv
rm -rf venv  # macOS/Linux
rmdir /S venv  # Windows

# Create fresh
python -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Reinstall
pip install -r requirements.txt
```

**Problem:** `Command not found: python3`

```bash
# Install Python 3.11
# Download from https://www.python.org/downloads/

# Or use package manager
# macOS: brew install python@3.11
# Ubuntu: sudo apt-get install python3.11
# Windows: Use installer
```

### Database Issues

**Problem:** `sqlite3.OperationalError: unable to open database file`

```bash
# Check file permissions
ls -la platform.db

# Recreate database
rm platform.db
python -c "from backend.app import db, create_app; app = create_app(); db.create_all()"

# Or use absolute path in .env
DATABASE_URL=sqlite:////absolute/path/to/platform.db
```

**Problem:** `PostgreSQL connection refused`

```bash
# Check if PostgreSQL is running
pg_isready  # macOS/Linux
sc query postgresql-x64-14  # Windows

# Start PostgreSQL
brew services start postgresql  # macOS
sudo systemctl start postgresql  # Linux
# Windows: Use Services app or pgAdmin
```

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'backend'`

```bash
# Check if in correct directory
pwd  # Should be softfactory/

# Add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"  # macOS/Linux
set PYTHONPATH=%PYTHONPATH%;%cd%  # Windows
```

**Problem:** `ImportError: cannot import name 'create_app'`

```bash
# Check backend/app.py exists
ls -la backend/app.py

# Verify imports
python -c "import backend.app; print('OK')"
```

### Port Already in Use

**Problem:** `Address already in use`

```bash
# Find process using port
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill process
kill -9 <PID>  # macOS/Linux
taskkill /PID <PID> /F  # Windows

# Or use different port
flask run --port 8001
```

### Dependencies

**Problem:** `pip install fails`

```bash
# Clear pip cache
pip cache purge

# Upgrade pip
python -m pip install --upgrade pip

# Retry with --no-cache-dir
pip install -r requirements.txt --no-cache-dir

# Check for conflicting packages
pip check
```

---

## Useful Commands

### Virtual Environment

```bash
# Activate
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Deactivate
deactivate

# Show active environment
which python  # macOS/Linux
where python  # Windows

# List installed packages
pip list

# Freeze requirements
pip freeze > requirements-lock.txt
```

### Flask

```bash
# Run development server
python start_platform.py

# Run with Flask CLI
flask run

# Run with reload
flask run --reload

# Run on specific port
flask run --port 8001

# Debug mode
FLASK_ENV=development FLASK_DEBUG=1 python start_platform.py
```

### Database

```bash
# SQLite
sqlite3 platform.db
sqlite3 platform.db ".tables"
sqlite3 platform.db "SELECT COUNT(*) FROM users;"

# PostgreSQL
psql -U softfactory_user -d softfactory
psql -U softfactory_user -d softfactory -c "SELECT * FROM users LIMIT 5;"
```

### Git

```bash
# View status
git status

# View branches
git branch -a

# Create branch
git checkout -b feature/123-name

# Commit changes
git add .
git commit -m "feat: add new feature"

# Push to remote
git push origin feature/123-name

# Create pull request
# Via GitHub web interface or gh CLI
gh pr create --title "Feature: Add new feature" --body "Description..."

# Pull latest
git pull origin main

# Rebase
git rebase origin/main

# View log
git log --oneline | head -20
```

### Testing

```bash
# Run tests
pytest tests/

# With coverage
pytest tests/ --cov=backend

# Specific test
pytest tests/unit/test_models.py::test_user_creation

# Verbose output
pytest tests/ -v

# Show print statements
pytest tests/ -s

# Run with markers
pytest tests/ -m "unit"
```

### Code Quality

```bash
# Format code
black backend/

# Sort imports
isort backend/

# Lint
flake8 backend/

# Type check
mypy backend/

# Security check
bandit -r backend/
```

---

## Useful Aliases (Optional)

Add to `.bashrc` or `.zshrc`:

```bash
# Activate venv
alias venv='source venv/bin/activate'

# Run Flask
alias flask-run='python start_platform.py'

# Run tests
alias test='pytest tests/ -v'

# Run quality checks
alias qa='flake8 backend/ && black --check backend/ && mypy backend/'

# Git shortcuts
alias gs='git status'
alias gb='git branch'
alias gc='git commit'
alias gp='git push'
alias gl='git log --oneline'
```

Then reload:

```bash
source ~/.bashrc  # or ~/.zshrc
```

---

## Next Steps

1. ✅ **Setup complete** - Environment ready for development
2. 📖 **Read documentation** - See docs/M-007-API-SPEC.md for API details
3. 🧪 **Run tests** - `pytest tests/ -v` to verify everything works
4. 🚀 **Start coding** - Create your feature branch and implement changes
5. 📝 **Create PR** - Submit pull request for code review

---

## Getting Help

- **Documentation:** See `docs/` folder
- **API Spec:** `docs/M-007-API-SPEC.md`
- **Deployment:** `docs/M-007-DEPLOYMENT.md`
- **Issues:** Create GitHub issue with details
- **Discord:** Join development server for help

---

**Document maintained by:** Team J (Documentation + Deployment)
**Last reviewed:** 2026-02-26
**Status:** Production-Ready ✅
