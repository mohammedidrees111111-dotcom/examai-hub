@echo off
echo Deploying Backend to Railway...
echo.

echo 1. Make sure you have Railway CLI installed: npm i -g @railway/cli
echo 2. Make sure you are logged in: railway login
echo.

cd /d "%~dp0backend"

echo Deploying to Railway...
railway up

echo.
echo Backend deployed!
echo Set environment variables in Railway dashboard:
echo   SECRET_KEY = your-production-secret
echo   DATABASE_URL = sqlite:///./school_helper.db
echo   FRONTEND_URL = https://examaihub.com
echo   CORS_ORIGINS = https://examaihub.com
echo   PAYPAL_CLIENT_ID = your_live_client_id
echo   PAYPAL_CLIENT_SECRET = your_live_secret
echo   PAYPAL_MODE = live
pause
