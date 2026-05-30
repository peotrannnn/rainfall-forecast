@echo off
setlocal
cd /d "%~dp0\.."
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8007" ^| findstr "LISTENING"') do (
  taskkill /PID %%a /F >nul 2>nul
)
start "rainfall-model-server" /min python -B web_app\server.py --host 127.0.0.1 --port 8007
timeout /t 6 /nobreak >nul
start "" "http://127.0.0.1:8007/"
