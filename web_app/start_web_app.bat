@echo off
setlocal
cd /d "%~dp0\.."
start "rainfall-model-server" /min python -B web_app\server.py --host 127.0.0.1 --port 8007
timeout /t 6 /nobreak >nul
start "" "http://127.0.0.1:8007/"
