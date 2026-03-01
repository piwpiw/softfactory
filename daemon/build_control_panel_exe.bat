@echo off
chcp 65001 >NUL
setlocal EnableExtensions

set "NO_PAUSE=0"
if /I "%~1"=="--no-pause" set "NO_PAUSE=1"

set "PROJECT_DIR=%~dp0"
if "%PROJECT_DIR:~-1%"=="\" set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"

echo ========================================
echo Build control_panel.exe (Windows)
echo ========================================
echo.

set "PYTHON_EXE="
set "PYTHON_ARGS="
if exist "%PROJECT_DIR%\.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%PROJECT_DIR%\.venv\Scripts\python.exe"
) else (
    where py.exe >NUL 2>&1
    if not errorlevel 1 (
        py -3 --version >NUL 2>&1
        if not errorlevel 1 (
            set "PYTHON_EXE=py"
            set "PYTHON_ARGS=-3"
        )
    )
    if not defined PYTHON_EXE (
        where python.exe >NUL 2>&1
        if not errorlevel 1 set "PYTHON_EXE=python"
    )
)

if not defined PYTHON_EXE (
    echo [ERROR] Python 3 runtime was not found.
    goto :FAIL
)

echo [1/4] Python: %PYTHON_EXE% %PYTHON_ARGS%
call "%PYTHON_EXE%" %PYTHON_ARGS% --version || goto :FAIL

echo.
echo [2/4] Install/upgrade pyinstaller
call "%PYTHON_EXE%" %PYTHON_ARGS% -m pip install --upgrade pyinstaller || goto :FAIL

echo.
echo [3/4] Build executable
if exist "%PROJECT_DIR%\control_panel.spec" (
    call "%PYTHON_EXE%" %PYTHON_ARGS% -m PyInstaller --noconfirm --clean "%PROJECT_DIR%\control_panel.spec" || goto :FAIL
) else (
    call "%PYTHON_EXE%" %PYTHON_ARGS% -m PyInstaller --noconfirm --clean --onefile --noconsole --name control_panel "%PROJECT_DIR%\control_panel_launcher.py" || goto :FAIL
)

echo.
echo [4/4] Copy build output
if not exist "%PROJECT_DIR%\dist\control_panel.exe" (
    echo [ERROR] Build output not found: dist\control_panel.exe
    goto :FAIL
)
copy /Y "%PROJECT_DIR%\dist\control_panel.exe" "%PROJECT_DIR%\control_panel.exe" >NUL || goto :FAIL

echo.
echo [OK] Created: %PROJECT_DIR%\control_panel.exe
if "%NO_PAUSE%"=="0" pause
exit /b 0

:FAIL
echo.
echo [FAILED] control_panel.exe build failed.
if "%NO_PAUSE%"=="0" pause
exit /b 1
