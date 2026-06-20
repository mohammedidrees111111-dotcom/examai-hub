import httpx, time

B = "https://examai-hub-api.onrender.com"
print("Waiting for Render deploy...")
time.sleep(90)

r = httpx.post(f"{B}/auth/register", json={"email": "byok2@test.com", "username": "byok2test", "password": "byok2test12"}, timeout=20)
t = r.json()["access_token"]
h = {"Authorization": f"Bearer {t}"}

r2 = httpx.get(f"{B}/settings/api-keys", headers=h, timeout=15)
print(f"Settings: {r2.status_code}")
if r2.status_code == 200:
    d = r2.json()
    print(f"  Providers: {len(d['providers'])}")
    print(f"  Encryption: {d['encryption_active']}")
    print(f"  Commission: {d['commission_rate']}")

r3 = httpx.post(f"{B}/settings/api-keys/set", json={"provider": "groq", "key": "gsk_test123"}, headers=h, timeout=15)
print(f"Set key: {r3.status_code}")

r4 = httpx.get(f"{B}/settings/api-keys", headers=h, timeout=15)
if r4.status_code == 200:
    for p in r4.json()["providers"]:
        if p["has_key"]:
            print(f"  {p['label']}: key saved")

r5 = httpx.post(f"{B}/settings/api-keys/delete", json={"provider": "groq", "key": ""}, headers=h, timeout=15)
print(f"Delete key: {r5.status_code}")
print("BYOK READY" if r2.status_code == 200 else "FAILED")
