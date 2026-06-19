import httpx, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = "http://127.0.0.1:8000"
r = httpx.post(f"{BASE}/auth/register", json={"email":"grow@test.com","username":"growth","password":"growth123"})
token = r.json()["access_token"]
h = {"Authorization": f"Bearer {token}"}

# Referral
r = httpx.get(f"{BASE}/growth/referral", headers=h)
ref = r.json()
print(f"Referral code: {ref['referral_code']}")
print(f"Referral link: {ref['referral_link'][:50]}...")

# Score
r = httpx.get(f"{BASE}/growth/score", headers=h)
sc = r.json()
print(f"Score: {sc['study_readiness']}/100 — {sc['exam_confidence']}")
print(f"Share text: {sc['share_text'][:60]}...")

# Achievements
r = httpx.get(f"{BASE}/growth/achievements", headers=h)
ach = r.json()
print(f"Achievements: {ach['total_earned']}/{len(ach['achievements'])}")

# Leaderboard
r = httpx.get(f"{BASE}/growth/leaderboard")
lb = r.json()
print(f"Leaderboard: {len(lb['leaderboard'])} users, {lb['total_participants']} total")

# Share
r = httpx.post(f"{BASE}/growth/share", json={"title":"Test Pack","subject":"AI","course":"CS101","data":{"summary":"Test summary content"}}, headers=h)
sh = r.json()
print(f"Share: {sh['share_url'][:50]}...")

# Daily Challenge
r = httpx.get(f"{BASE}/growth/daily-challenge", headers=h)
dc = r.json()
print(f"Daily challenge: {len(dc['questions'])} questions")

print("\nALL GROWTH ENDPOINTS WORKING")
