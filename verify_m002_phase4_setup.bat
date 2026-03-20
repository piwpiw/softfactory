@echo off
REM Compatibility wrapper. Canonical script lives under scripts\.
set SCRIPT_DIR=%~dp0
call "%SCRIPT_DIR%scripts\\verify_m002_phase4_setup.bat" %*
