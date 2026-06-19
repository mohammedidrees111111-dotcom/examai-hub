@echo off
echo Deploying Frontend to Vercel...
echo.

echo 1. Make sure you have Vercel CLI installed: npm i -g vercel
echo 2. Make sure you have a Vercel account and are logged in: vercel login
echo.

cd /d "%~dp0frontend"

echo Building project...
call npm run build
if %ERRORLEVEL% neq 0 (
    echo Build failed!
    pause
    exit /b 1
)

echo.
echo Deploying to Vercel...
vercel --prod

echo.
echo Frontend deployed!
echo Set your environment variable in Vercel dashboard:
echo   NEXT_PUBLIC_API_URL = https://api.examaihub.com
pause
