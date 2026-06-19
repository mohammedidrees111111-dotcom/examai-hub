@echo off
title ExamAI Hub - PRODUCTION
color 0A

echo.
echo ========================================
echo   EXAMAI HUB - PRODUCTION MODE
echo ========================================
echo.

:: Build frontend
echo [1/3] Building frontend...
cd /d "%~dp0frontend"
call npm run build
if %ERRORLEVEL% neq 0 (
    echo FRONTEND BUILD FAILED
    pause
    exit /b 1
)
echo Frontend build complete.

:: Start Backend
echo [2/3] Starting Backend on http://127.0.0.1:8000 ...
start "AI-School-Backend" cmd /c "cd /d "%~dp0backend" && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4 --log-level info"

:: Wait for backend
echo Waiting for backend...
timeout /t 6 /nobreak >nul

:: Verify backend
echo Checking backend health...
curl -s http://127.0.0.1:8000/health >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo BACKEND FAILED TO START
    pause
    exit /b 1
)
echo Backend healthy.

:: Start Frontend
echo [3/3] Starting Frontend on http://localhost:3000 ...
start "AI-School-Frontend" cmd /c "cd /d "%~dp0frontend" && npm start"

echo.
echo ========================================
echo   PRODUCTION SYSTEM RUNNING
echo ========================================
echo.
echo   Backend:  http://127.0.0.1:8000
echo   API Docs: http://127.0.0.1:8000/docs
echo   Frontend: http://localhost:3000
echo.
echo ========================================
pause
