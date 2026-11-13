@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================================
echo   ZALO AUTO-REPLY STUDIO - KHOI DONG WEB DASHBOARD
echo   Dia chi quan ly: http://127.0.0.1:8000
echo ========================================================
start "" "http://127.0.0.1:8000"
.\.venv\Scripts\python.exe app.py
pause
