@echo off
REM Setup script - run this once before first use

echo.
echo ====================================================
echo Slot Store Scraper Web UI - Setup
echo ====================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not available in PATH.
    echo.
    pause
    exit /b 1
)

REM Run setup checks
echo Running setup checks...
echo.
python setup_check.py

if errorlevel 1 (
    echo.
    echo Setup failed.
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
echo   1. start_silent.bat - launch app and open browser
echo   2. python app.py - run Flask directly in this window
echo.
echo ====================================================
echo.

pause
