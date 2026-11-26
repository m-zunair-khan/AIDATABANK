@echo off
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
reg add HKCU\Console /v QuickEdit /t REG_DWORD /d 0 /f >nul 2>&1

echo ===================================================================
echo             AI MODEL REGISTRY - DBMS ^& DSA PLATFORM
echo ===================================================================
echo.
echo Choose an option to start:
echo [1] Start Interactive Web Frontend (Streamlit Dashboard)
echo [2] Start REST API Backend (FastAPI + Swagger Docs)
echo [3] Run Automated Test Suite (Verify 17 Tables ^& 12 DSA Algorithms)
echo [4] Re-seed Database (Populate 100+ Models)
echo.
set /p opt="Enter choice [1-4] (default is 1): "
if "%opt%"=="" set opt=1

if "%opt%"=="1" (
    echo.
    echo [*] Opening browser to http://localhost:8501 ...
    start http://localhost:8501
    echo [*] Launching Streamlit Web Frontend on http://localhost:8501 ...
    .\venv\Scripts\python.exe -m streamlit run app.py
) else if "%opt%"=="2" (
    echo.
    echo [*] Starting FastAPI Backend Server on http://localhost:8000 ...
    echo [*] Interactive API Swagger Docs: http://localhost:8000/docs
    .\venv\Scripts\python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
) else if "%opt%"=="3" (
    echo.
    echo [*] Running Test Suite...
    .\venv\Scripts\python.exe test_api.py
) else if "%opt%"=="4" (
    echo.
    echo [*] Seeding Database...
    .\venv\Scripts\python.exe seed_database.py
) else (
    echo Invalid choice. Starting Web Frontend...
    .\venv\Scripts\python.exe -m streamlit run app.py
)

pause
