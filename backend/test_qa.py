import httpx, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = "http://127.0.0.1:8000"
r = httpx.post(f"{BASE}/auth/register", json={"email":"qa3@test.com","username":"qa3test","password":"qa3test123"})
token = r.json()["access_token"]
h = {"Authorization": f"Bearer {token}"}

text = """Deep learning is a subset of machine learning using neural networks.
Convolutional networks process images through filters.
Recurrent networks handle sequences via hidden states.
IMPORTANT: Transformers use self-attention mechanisms.
Unlike CNNs which process spatial data, RNNs handle sequential data.
The training steps are: 1) Forward pass, 2) Loss calculation, 3) Backpropagation."""

r = httpx.post(f"{BASE}/ai/qa-summarize", json={"text": text}, headers=h, timeout=10)
qa = r.json()
print(f"Questions: {qa['total_questions']}")
print(f"Chapters: {qa['chapters_covered']}")
for ch in qa["chapters"]:
    print(f"\n[Ch {ch['chapter']}] {ch['title'][:60]}")
    for q in ch["qa_pairs"]:
        print(f"  [{q['type']}] {q['question'][:80]}")
        print(f"    A: {q['answer'][:100]}...")
print(f"\nDefinitions: {len(qa['all_definitions'])}")
print("\nPASS" if qa['total_questions'] >= 3 else "FAIL - too few questions")
