import httpx, re
r = httpx.get("https://examaihub.com", timeout=30, follow_redirects=True)
text = r.text
api_urls = re.findall(r'https?://[^\s\"\'<>]+onrender[^\s\"\'<>]*', text)
print("API URLs in frontend:", api_urls[:3] if api_urls else "NONE FOUND")
local = re.findall(r'127\.0\.0\.1:8000', text)
print("Has localhost fallback:", bool(local))
examai = re.findall(r'examai-hub-api', text)
print("Has examai-hub-api:", bool(examai))
print("Page length:", len(text))
