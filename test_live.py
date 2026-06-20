import httpx, time
B = "https://examai-hub-api.onrender.com"
print("Waiting for deploy...")
time.sleep(120)

r = httpx.post(f"{B}/auth/register", json={"email": "live2@t.com", "username": "live2", "password": "live123456"}, timeout=20)
print(f"Register: {r.status_code}")
t = r.json()["access_token"]

r2 = httpx.post(f"{B}/payments/create-order", json={"plan": "monthly"}, headers={"Authorization": f"Bearer {t}"}, timeout=20)
d = r2.json()
status = d.get("status", "?")
oid = d.get("order_id", "?")[:25]
approval = d.get("approval_url", "NONE")[:100]

print(f"Status: {status}")
print(f"Order ID: {oid}")
print(f"Approval URL: {approval}")

is_live = "sandbox" not in approval and "paypal.com" in approval
print(f"LIVE PAYPAL: {is_live}")
print("DONE" if is_live else "CHECK CONFIG")
