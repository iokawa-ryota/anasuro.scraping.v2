@echo off
setlocal
REM Setup script - run this once before first use

cd /d "%~dp0"

set "PY_CMD="

echo.
echo ====================================================
echo Slot Store Scraper Web UI - Setup
echo ====================================================
echo.

REM Check Python launcher first, then python.exe
py -3 --version >nul 2>&1
if not errorlevel 1 (
    set "PY_CMD=py -3"
)

if not defined PY_CMD (
    python --version >nul 2>&1
    if not errorlevel 1 (
        set "PY_CMD=python"
    )
)

if not defined PY_CMD (
    echo Error: Python was not found.
    echo.
    echo Install Python 3 and enable the Python Launcher or add Python to PATH.
    echo https://www.python.org/downloads/windows/
    echo.
    pause
    exit /b 1
)

echo Using Python command: %PY_CMD%
echo.

REM Run setup checks
echo Running setup checks...
echo.
%PY_CMD% setup_check.py

if errorlevel 1 (
    echo.
    echo Setup failed.
    echo Please review the messages above.
    echo.
    pause
    exit /b 1
)

echo.
echo ====================================================
echo Setup complete!
echo ====================================================
echo.
echo Use one of the following next time:
echo.
echo   1. Start.bat - launch app and open browser
echo   2. python app\app.py - run Flask directly in this window
echo.
echo ====================================================
echo.

pause
endlocal
