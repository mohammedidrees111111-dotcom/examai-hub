@echo off
title ExamAI Hub - Full System
color 0B

echo.
echo ========================================
echo   EXAMAI HUB - PRODUCTION LAUNCH
echo ========================================
echo.
echo Starting Backend (FastAPI) and Frontend (Next.js)...
echo.

:: Start Backend
echo [1/2] Starting Backend on http://127.0.0.1:8000 ...
start "AI-School-Backend" cmd /c "cd /d "%~dp0backend" && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

:: Wait for backend
echo Waiting for backend to initialize...
timeout /t 5 /nobreak >nul

:: Start Frontend
echo [2/2] Starting Frontend on http://localhost:3000 ...
start "AI-School-Frontend" cmd /c "cd /d "%~dp0frontend" && npm run dev"

echo.
echo ========================================
echo   SYSTEM STARTED
echo ========================================
echo.
echo   Backend:  http://127.0.0.1:8000
echo   API Docs: http://127.0.0.1:8000/docs
echo   Frontend: http://localhost:3000
echo.
echo ========================================
echo.
echo Close this window to stop the launcher.
echo Servers are running in separate windows.
echo.
pause
