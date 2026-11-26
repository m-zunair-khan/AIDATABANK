@echo off
title NEXUS AI - Frontier Model Registry
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

echo ========================================================
echo        LAUNCHING AI MODEL REGISTRY WEB DASHBOARD
echo ========================================================
echo.
REM Prevent accidental CMD QuickEdit freeze on click
reg add HKCU\Console /v QuickEdit /t REG_DWORD /d 0 /f >nul 2>&1
echo [*] Opening browser to http://localhost:8501 ...
start http://localhost:8501
echo [*] Starting Streamlit server...
echo.
echo NOTE: If the window title shows "Select", press ENTER to resume.
echo.
.\venv\Scripts\python.exe -m streamlit run app.py
pause
