@echo off
echo Step 1: Create GitHub repo
gh repo create examai-hub --public --source=. --remote=origin --push
echo.
echo Step 2: Deploy Frontend to Vercel
echo Open: https://vercel.com/new
echo Import repo: examai-hub
echo Root: frontend
echo Env: NEXT_PUBLIC_API_URL = https://api.examaihub.com
echo.
echo Step 3: Deploy Backend to Render  
echo Open: https://dashboard.render.com
echo New Web Service - Connect GitHub repo
echo Root: backend
echo Build: pip install -r requirements.txt
echo Start: uvicorn app.main:app --host 0.0.0.0 --port $PORT
echo.
echo Step 4: DNS in Namecheap
echo Nameservers: ns1.vercel-dns.com, ns2.vercel-dns.com
echo.
echo Step 5: Add domain to Vercel + Railway
pause
