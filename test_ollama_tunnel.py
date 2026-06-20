import httpx, time
print("Testing Ollama tunnel...")
time.sleep(5)

r = httpx.post("https://ollama.mohammedid99.com/api/generate", json={
    "model": "qwen2.5-coder:1.5b",
    "prompt": "Say hello in one word",
    "stream": False
}, timeout=30)

print(f"Status: {r.status_code}")
if r.status_code == 200:
    resp = r.json().get("response", "")[:100]
    print(f"Response: {resp}")
    print("OLLAMA ONLINE!")
else:
    print(f"Error: {r.text[:200]}")
