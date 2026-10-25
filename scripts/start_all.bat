@echo off
echo ========================================================
echo  Launching YGF Local AI News Intelligence Agent
echo ========================================================
echo Starting Backend in a new window...
start "YGF Backend (FastAPI)" cmd /k "%~dp0start_backend.bat"

echo Waiting 2 seconds for backend to bind...
timeout /t 2 /nobreak >nul

echo Starting Frontend in a new window...
start "YGF Frontend (Vite)" cmd /k "%~dp0start_frontend.bat"

echo.
echo Application launched!
echo Backend:  http://127.0.0.1:8000 (Docs: http://127.0.0.1:8000/docs)
echo Frontend: http://localhost:5173
echo.
pause
