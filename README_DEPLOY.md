# ExamAI Hub — Deployment Guide

## Prerequisites

- GitHub account
- Vercel account (free)
- Railway account ($5/month)
- Domain name
- PayPal Business account (for live payments)

---

## Step 1: Push to GitHub

```bash
git init
git add .
git commit -m "Production-ready v1.0"
git remote add origin https://github.com/YOUR_USER/examaihub.git
git push -u origin main
```

---

## Step 2: Deploy Backend (Railway)

1. Go to https://railway.app
2. New Project → Deploy from GitHub repo
3. Select your repo
4. Set root directory to `backend`
5. Add environment variables:

```
SECRET_KEY=generate-a-random-64-char-string
DATABASE_URL=sqlite:///./school_helper.db
FRONTEND_URL=https://examaihub.com
CORS_ORIGINS=https://examaihub.com
PAYPAL_CLIENT_ID=your_live_client_id
PAYPAL_CLIENT_SECRET=your_live_secret
PAYPAL_MODE=live
```

6. Deploy — Railway auto-detects Python from `runtime.txt`
7. Get your Railway URL: `https://your-app.railway.app`
8. Set custom domain: `api.examaihub.com`

---

## Step 3: Deploy Frontend (Vercel)

1. Go to https://vercel.com
2. Import your GitHub repo
3. Set root directory to `frontend`
4. Framework: Next.js (auto-detected)
5. Add environment variable:

```
NEXT_PUBLIC_API_URL=https://api.examaihub.com
```

6. Deploy
7. Set custom domain: `examaihub.com`

---

## Step 4: Configure Domain DNS

1. In your domain registrar (Namecheap/GoDaddy):
   - Add CNAME record: `www` → `cname.vercel-dns.com`
   - Add CNAME record: `api` → `your-app.railway.app`

2. In Vercel dashboard → Domains → Add `examaihub.com`

---

## Step 5: PayPal Live

1. Go to https://developer.paypal.com
2. Create a **Live** app
3. Copy Client ID and Secret
4. Update Railway environment variables:
   - `PAYPAL_CLIENT_ID` = live client ID
   - `PAYPAL_CLIENT_SECRET` = live secret
   - `PAYPAL_MODE` = `live`

---

## Step 6: Google AdSense (Optional)

1. Go to https://adsense.google.com
2. Add your site: `https://examaihub.com`
3. Copy the AdSense code
4. Replace `ca-pub-XXXXXXXXXXXXXXXX` in:
   - `frontend/src/app/layout.tsx` (line with `pagead2.googlesyndication.com`)
   - `frontend/src/components/AdBanner.tsx` (data-ad-client)
   - `frontend/public/ads.txt` (publisher ID)
5. Redeploy frontend
6. Wait 1-2 weeks for approval

---

## Quick Local Test

```bash
# Development
start_all.bat

# Production mode (local)
start_prod.bat
```

---

## URLs After Deployment

| Service | URL |
|---------|-----|
| Website | https://examaihub.com |
| API | https://api.examaihub.com |
| API Docs | https://api.examaihub.com/docs |
| Privacy | https://examaihub.com/privacy |
| Terms | https://examaihub.com/terms |

## Support

- Contact: https://examaihub.com/contact
- Report issues on GitHub
