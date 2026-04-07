@echo off
REM Start Flask app and open browser

cd /d "%~dp0"

set "PY_CMD="
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
    echo Python was not found.
    echo Install Python 3 first, then run setup.bat.
    pause
    exit /b 1
)

echo Starting Flask server...

start "Flask Server" /min %PY_CMD% app\app.py

REM Wait for server startup
timeout /t 3 /nobreak

REM Open browser
start http://localhost:5000

exit
