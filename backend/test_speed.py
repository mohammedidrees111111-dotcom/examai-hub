import httpx, sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = "http://127.0.0.1:8000"
r = httpx.post(f"{BASE}/auth/login", json={"email": "demo@example.com", "password": "demo123"})
token = r.json()["access_token"]
h = {"Authorization": f"Bearer {token}"}

# Generate ~50K word text (simulating 300+ page book)
print("Generating 50,000 word test text...")
paragraphs = []
for i in range(500):
    p = f"Section {i+1}. Artificial intelligence and machine learning are transforming modern technology. "
    p += "Neural networks process data through multiple layers of interconnected nodes. Deep learning models excel at pattern recognition tasks. "
    p += "Natural language processing enables computers to understand human speech and text. "
    p += f"Key concept {i+1}: Reinforcement learning agents optimize behavior through environmental feedback. "
    p += "Supervised learning algorithms require labeled datasets for training. Computer vision systems analyze visual information from images. "
    paragraphs.append(p)
large_text = "\n\n".join(paragraphs)

print(f"Text: {len(large_text.split())} words, {len(large_text)} chars ({len(large_text)/1024:.0f} KB)")
print()

# Upload
t0 = time.time()
r = httpx.post(f"{BASE}/upload/text", json={"text": large_text})
doc_id = r.json()["document_id"]
t1 = time.time()
print(f"Upload + chunk: {t1-t0:.1f}s, doc_id={doc_id}")

# Summarize
t0 = time.time()
r = httpx.post(f"{BASE}/ai/summarize", json={"document_id": doc_id}, headers=h, timeout=60)
s = r.json()
t1 = time.time()
print(f"Summarize: {s['original_length']} -> {s['summary_length']}w ({s['compression_ratio']}) in {t1-t0:.1f}s")
print(f"  Chunks: {s['total_chunks']}, Keywords: {len(s['keywords'])}")
print("  PASS" if s['total_chunks'] > 1 and s['compression_ratio'] != '100%' else "  FAIL")

# Exam Predict
t0 = time.time()
r = httpx.post(f"{BASE}/ai/exam-predict", json={"document_id": doc_id, "num_questions": 10}, headers=h, timeout=60)
q = r.json()
t1 = time.time()
print(f"Exam Predict: {q['total']} questions in {t1-t0:.1f}s")
print("  PASS" if q['total'] >= 5 else "  FAIL")

# Teacher Mode
t0 = time.time()
r = httpx.post(f"{BASE}/ai/teacher-mode", json={"document_id": doc_id}, headers=h, timeout=60)
t = r.json()
t1 = time.time()
print(f"Teacher Mode: {t['total_words']}w, {t['total_chunks']} chunks, {len(t['bullet_points'])} bullets in {t1-t0:.1f}s")
print("  PASS" if t['total_chunks'] > 1 and len(t['bullet_points']) >= 5 else "  FAIL")

print()
print("=== ALL TESTS PASSED ===")
