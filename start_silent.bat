@echo off
REM slot machine start script
REM run Flask 

echo Flask server is starting...

start "Flask Server" /min python app.py

REM wait for server to start
timeout /t 3 /nobreak

REM open browser
start http://localhost:5000

exit
