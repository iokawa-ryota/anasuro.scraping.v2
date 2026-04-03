@echo off
REM Start Flask app and open browser

echo Starting Flask server...

start "Flask Server" /min python app.py

REM Wait for server startup
timeout /t 3 /nobreak

REM Open browser
start http://localhost:5000

exit
