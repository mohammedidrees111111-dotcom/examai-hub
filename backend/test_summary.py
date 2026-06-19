import httpx, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = "http://127.0.0.1:8000"
r = httpx.post(f"{BASE}/auth/register", json={"email":"sum@test.com","username":"sumtest","password":"sumtest123"})
token = r.json()["access_token"]
h = {"Authorization": f"Bearer {token}"}

# Build ~5000 word text across multiple chapters
chapters = []
for i in range(20):
    ch = f"Chapter {i+1}: Topic {i+1}\n\n"
    ch += f"Deep learning is a subset of machine learning using neural networks with many layers. "
    ch += f"Convolutional neural networks process image data through convolutional filters. "
    ch += f"Recurrent neural networks handle sequential data like text and speech. "
    ch += f"IMPORTANT: The transformer architecture uses self-attention mechanisms for parallel processing. "
    ch += f"Transfer learning allows pre-trained models to be fine-tuned for specific tasks. "
    ch += f"Unlike traditional algorithms, neural networks learn features automatically from raw data. "
    ch += f"Reinforcement learning agents learn through trial and error using reward signals. "
    chapters.append(ch)
text = "\n\n".join(chapters)
total = len(text.split())
print(f"Total words: {total}")

r = httpx.post(f"{BASE}/ai/summarize", json={"text": text}, headers=h, timeout=30)
s = r.json()
print(f"Original: {s['original_length']:,} words")
print(f"Summary:  {s['summary_length']:,} words ({s['compression_ratio']})")
print(f"Language: {s['language']}")
print(f"Quality:  {s['information_preservation']['quality']}")
ratio = s['summary_length'] / s['original_length'] * 100
print(f"\nPreserved: {ratio:.1f}%")
print("PASS - Good summary" if ratio > 15 else "FAIL - Too short")
print("PASS - Keywords found" if len(s['keywords']) > 5 else "FAIL - No keywords")
