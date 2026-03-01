@echo off
REM M-002 Phase 4: PostgreSQL Docker Deployment — Pre-Execution Verification Script
REM Purpose: Verify all prerequisites before running migration
REM Usage: verify_m002_phase4_setup.bat

echo.
echo ==========================================
echo M-002 Phase 4: Setup Verification
echo Date: 2026-02-25
echo ==========================================
echo.

REM Initialize counters
setlocal enabledelayedexpansion
set PASS=0
set FAIL=0
set WARN=0

REM --- System Requirements ---
echo --- System Requirements ---

REM Check Docker
docker --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [PASS] Docker installed
    set /a PASS+=1
) else (
    echo [FAIL] Docker not found. Install Docker Desktop.
    set /a FAIL+=1
)

REM Check docker-compose
docker-compose --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [PASS] docker-compose available
    set /a PASS+=1
) else (
    echo [FAIL] docker-compose not found
    set /a FAIL+=1
)

REM Check Python
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [PASS] Python installed
    set /a PASS+=1
) else (
    echo [FAIL] Python not found
    set /a FAIL+=1
)

echo.
echo --- Project Files ---

REM Check key files
if exist "docker-compose.yml" (
    echo [PASS] docker-compose.yml exists
    set /a PASS+=1
) else (
    echo [FAIL] docker-compose.yml missing
    set /a FAIL+=1
)

if exist "Dockerfile" (
    echo [PASS] Dockerfile exists
    set /a PASS+=1
) else (
    echo [FAIL] Dockerfile missing
    set /a FAIL+=1
)

if exist "scripts\migrate_to_postgres.py" (
    echo [PASS] migrate_to_postgres.py exists
    set /a PASS+=1
) else (
    echo [FAIL] migration script missing
    set /a FAIL+=1
)

if exist ".env" (
    echo [PASS] .env file exists
    set /a PASS+=1
) else (
    echo [FAIL] .env file missing
    set /a FAIL+=1
)

if exist "backend\app.py" (
    echo [PASS] backend/app.py exists
    set /a PASS+=1
) else (
    echo [FAIL] Flask app missing
    set /a FAIL+=1
)

if exist "platform.db" (
    echo [PASS] SQLite database exists
    set /a PASS+=1
) else (
    echo [FAIL] platform.db missing
    set /a FAIL+=1
)

echo.
echo --- Dependencies ---

REM Check psycopg2
python -c "import psycopg2" >nul 2>&1
if %errorlevel% equ 0 (
    echo [PASS] psycopg2-binary installed
    set /a PASS+=1
) else (
    echo [FAIL] psycopg2-binary not installed. Run: pip install psycopg2-binary
    set /a FAIL+=1
)

REM Check Flask
python -c "import flask" >nul 2>&1
if %errorlevel% equ 0 (
    echo [PASS] Flask installed
    set /a PASS+=1
) else (
    echo [FAIL] Flask not installed
    set /a FAIL+=1
)

REM Check SQLAlchemy
python -c "import sqlalchemy" >nul 2>&1
if %errorlevel% equ 0 (
    echo [PASS] SQLAlchemy installed
    set /a PASS+=1
) else (
    echo [FAIL] SQLAlchemy not installed
    set /a FAIL+=1
)

echo.
echo --- Docker Daemon Status ---

REM Check if Docker daemon is running
docker ps >nul 2>&1
if %errorlevel% equ 0 (
    echo [PASS] Docker daemon is RUNNING
    set /a PASS+=1
) else (
    echo [FAIL] Docker daemon NOT RUNNING. Start Docker Desktop and retry.
    set /a FAIL+=1
)

echo.
echo --- SQLite Database Validation ---

REM Check if platform.db exists and is readable
if exist "platform.db" (
    for %%A in (platform.db) do (
        set size=%%~zA
        echo [PASS] SQLite database found (size: !size! bytes)
        set /a PASS+=1
    )
) else (
    echo [FAIL] Cannot read platform.db
    set /a FAIL+=1
)

echo.
echo --- Configuration Files ---

REM Check DATABASE_URL in .env (simple check)
findstr /M "DATABASE_URL" .env >nul 2>&1
if %errorlevel% equ 0 (
    echo [PASS] DATABASE_URL configured in .env
    set /a PASS+=1
) else (
    echo [WARN] DATABASE_URL not found in .env
    set /a WARN+=1
)

REM Check docker-compose.yml PostgreSQL settings
findstr /M "postgres:15-alpine" docker-compose.yml >nul 2>&1
if %errorlevel% equ 0 (
    echo [PASS] PostgreSQL 15-alpine configured
    set /a PASS+=1
) else (
    echo [WARN] PostgreSQL image may differ from expected
    set /a WARN+=1
)

echo.
echo --- Workspace Status ---

REM Check if we're in the project root
if exist "CLAUDE.md" (
    echo [PASS] Working directory is project root
    set /a PASS+=1
) else (
    echo [FAIL] Not in project root. cd D:\Project and retry.
    set /a FAIL+=1
)

echo.
echo ==========================================
echo Verification Summary
echo ==========================================
echo PASS: %PASS%
echo FAIL: %FAIL%
echo WARN: %WARN%
echo.

if %FAIL% equ 0 (
    echo All prerequisites met. Ready to proceed with migration.
    echo.
    echo Next steps:
    echo 1. Start Docker Desktop ^(if not already running^)
    echo 2. Run: docker-compose up -d db
    echo 3. Wait 15 seconds
    echo 4. Run: python scripts/migrate_to_postgres.py
    echo 5. Run: docker-compose up -d
    echo 6. Run: curl http://localhost:8000/health
    echo.
    exit /b 0
) else (
    echo Some prerequisites failed. Please fix issues above and retry.
    echo.
    echo See DEPLOYMENT_CHECKLIST.md Part 1 for detailed instructions.
    exit /b 1
)
