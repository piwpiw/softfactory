@echo off
REM Compatibility wrapper. Canonical script lives under scripts\.
set SCRIPT_DIR=%~dp0
call "%SCRIPT_DIR%scripts\\open_all_pages.bat" %*
