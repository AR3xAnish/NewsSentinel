@echo off
echo ========================================================
echo  Starting YGF News Intelligence Agent - FastAPI Backend
echo ========================================================
cd /d "%~dp0..\backend"
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found in backend\.venv
    echo Please run python -m venv .venv and install requirements.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pause
