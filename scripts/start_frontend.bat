@echo off
echo ========================================================
echo  Starting YGF News Intelligence Agent - React Dashboard
echo ========================================================
cd /d "%~dp0..\frontend"
if not exist "node_modules" (
    echo [INFO] Installing frontend dependencies...
    call npm install
)
call npm run dev
pause
