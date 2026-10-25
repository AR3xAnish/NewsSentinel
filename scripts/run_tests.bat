@echo off
echo ========================================================
echo  Running YGF Automated Test Benchmark Suite
echo ========================================================
cd /d "%~dp0..\backend"
if not exist ".venv\Scripts\pytest.exe" (
    echo [ERROR] pytest executable not found in backend\.venv\Scripts
    pause
    exit /b 1
)
".venv\Scripts\pytest.exe" -v
pause
