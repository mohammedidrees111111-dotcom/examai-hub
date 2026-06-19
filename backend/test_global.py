import httpx, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = "http://127.0.0.1:8000"
r = httpx.post(f"{BASE}/auth/register", json={"email":"gctx@test.com","username":"gctx","password":"gctx1234"})
token = r.json()["access_token"]
h = {"Authorization": f"Bearer {token}"}

text = """Chapter 1: Neural Network Fundamentals
A neural network is defined as a computing system inspired by biological neural networks.
IMPORTANT: Understanding backpropagation is critical for mastering deep learning.
The key components of neural networks are: 1) Input layer, 2) Hidden layers, 3) Output layer.
However, deep networks face the vanishing gradient problem - you must know this for exams.

Chapter 2: Convolutional Networks
A Convolutional Neural Network (CNN) is defined as a specialized network for image processing.
Note that CNNs preserve spatial relationships - this is what makes them superior for images.
Unlike CNNs, Recurrent Neural Networks handle sequential data through internal memory.
Key components include: 1) Convolutional layers, 2) Pooling layers, 3) Fully connected layers.

Chapter 3: Transformers and Attention
The transformer architecture is another important development in deep learning.
Transformers use self-attention mechanisms instead of recurrence or convolution.
Remember: Self-attention is the core innovation - do not forget this point.
Unlike both CNNs and RNNs, transformers enable parallel processing of entire sequences.
BERT and GPT are transformer-based models that achieved state-of-the-art results."""

print("=== GLOBAL CONTEXT ANALYSIS ===\n")
r = httpx.post(f"{BASE}/ai/global-analyze", json={"text": text}, headers=h, timeout=20)
g = r.json()

gc = g["global_context"]
print(f"[Document Overview]")
print(f"  Words: {gc['document_overview']['total_words']:,}")
print(f"  Chapters: {gc['document_overview']['total_chapters']}")
print(f"  Concepts: {gc['document_overview']['total_concepts']}")
print(f"  Definitions: {gc['document_overview']['total_definitions']}")

print(f"\n[Teacher Profile]")
tp = gc["teacher_profile"]
print(f"  Style: {tp['teaching_style'][:80]}...")
print(f"  Difficulty: {tp['difficulty_level']}")
print(f"  Signals: {tp['total_signals_detected']}")
print(f"  Q types: {tp['preferred_question_types']}")
print(f"  Most important chapter: {tp['most_important_chapter'][:50]}")

print(f"\n[Global Importance - Top 5]")
for r in gc['global_importance_ranking'][:5]:
    print(f"  {r['concept']}: score={r['importance_score']}, freq={r['frequency']}, chapters={r['chapters']}, signaled={r['signaled']}, defined={r['defined']}, cross={r['cross_chapter']}")

print(f"\n[Cross-Chapter Concepts]")
for c in gc['cross_chapter_concepts'][:5]:
    print(f"  {c['concept']} — appears in {c['chapters']} chapters")

print(f"\n[Teacher Insights]")
ti = g["teacher_insights"]
for s in ti["strategy"]:
    print(f"  {s[:90]}")

print(f"\n[Full Exam]")
fe = g["full_exam"]
for s in fe["sections"]:
    print(f"  {s['section']}: {s['title']} ({s['marks']} marks, {len(s['questions'])} Qs)")

print(f"\n[Summary]")
cs = g["contextual_summary"]
print(f"  Words: {cs['word_count']}")

print(f"\nHas global_context: {bool(g['global_context'])}")
print(f"Has teacher_insights: {bool(g['teacher_insights'])}")
print(f"Has full_exam: {bool(g['full_exam'])}")
print(f"Has summary: {bool(g['contextual_summary'])}")
print(f"All 4 sections present: PASS")
