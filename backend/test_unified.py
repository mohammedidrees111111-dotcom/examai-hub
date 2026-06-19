import httpx, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = "http://127.0.0.1:8000"
r = httpx.post(f"{BASE}/auth/login", json={"email":"demo@example.com","password":"demo123"})
token = r.json()["access_token"]
h = {"Authorization": f"Bearer {token}"}

textbook = """IMPORTANT: Understanding neural networks is critical for the final exam.
A neural network is defined as a computing system inspired by biological neural networks.
Note that backpropagation is the key algorithm for training — you must know this.
Convolutional Neural Networks (CNNs) are specialized for image processing tasks.
Unlike CNNs which process spatial data, Recurrent Neural Networks handle sequential data.
The transformer architecture is another important development. It uses self-attention instead of recurrence.
You should understand that the three main architectures are: 1) CNN, 2) RNN, 3) Transformer.
Remember: The difference between supervised and unsupervised learning is fundamental."""

past_exams = """Q1: Define a neural network. (Short Answer)
Q2: Compare CNNs and RNNs, giving examples of their applications. (Essay)
Q3: What is backpropagation and why is it important? (Short Answer)
Q4: Explain supervised vs unsupervised learning with examples. (Essay)
Q5: Describe the transformer architecture and its key innovation."""

lecture_notes = """CRITICAL: Backpropagation will definitely be on the exam.
The teacher spent 20 minutes explaining CNN vs RNN — this is a major exam topic.
Key point: Self-attention mechanism is the core innovation of transformers.
Always remember: CNNs for images, RNNs for sequences. Do not confuse these."""

print("=== UNIFIED INTELLIGENCE ENGINE ===\n")
r = httpx.post(f"{BASE}/ai/unified", json={
    "textbook": textbook, "past_exams": past_exams, "lecture_notes": lecture_notes
}, headers=h, timeout=30)
u = r.json()

print(f"[CONFIDENCE] {u['confidence_score']}%")

print(f"\n[EXAM STUDY MATERIAL]")
esm = u["exam_study_material"]
print(f"  Must know: {len(esm['must_know'])} concepts")
print(f"  High yield: {len(esm['high_yield_topics'])} topics")
print(f"  Definitions: {len(esm['core_definitions'])}")
print(f"  Formulas/steps: {len(esm['formulas_and_steps'])}")
print(f"  Teacher signals: {len(esm['teacher_emphasis_signals'])}")
print(f"  Tricky points: {len(esm['tricky_points'])}")
print(f"  Common mistakes: {len(esm['common_exam_mistakes'])}")
print(f"  Study priorities: {len(esm['study_priority_order'])}")

print(f"\n[TEACHER FINGERPRINT]")
tf = u["teacher_fingerprint"]
print(f"  Style: {tf['teaching_style']}")
print(f"  Difficulty bias: {tf['difficulty_bias']}")
print(f"  Question types: {len(tf['question_style'])}")
for qt in tf['question_style']:
    print(f"    {qt['type']}: {qt['weight']}%")
print(f"  Repetition patterns: {len(tf['repetition_patterns'])}")
for rp in tf['repetition_patterns'][:4]:
    print(f"    {rp['concept']}: freq={rp['frequency']} signaled={rp['explicitly_signaled']}")
print(f"  Emphasis triggers: {tf['emphasis_triggers_detected']}")
print(f"  Cross-source favorites: {', '.join(tf['cross_source_favorites'][:5])}")

print(f"\n[PREDICTED EXAM] ({len(u['predicted_exam'])} questions)")
for i, q in enumerate(u['predicted_exam'][:6]):
    print(f"  {i+1}. [{q['type']}] p={q['probability']}% src={q['source']}")
    print(f"     {q['reason'][:90]}")

print(f"\n[CROSS-VALIDATION]")
cv = u["cross_validation"]
print(f"  Verified: {cv['verified']}/{cv['total']}")
print(f"  Removed: {len(cv['removed'])} weak questions")
print(f"  Adjusted: {len(cv['adjusted'])} scores")
for c in cv['checks']:
    print(f"  Check: {c}")

# Quality verification
print(f"\n[QUALITY]")
print(f"  All 3 sections present: {all(k in u for k in ['exam_study_material','teacher_fingerprint','predicted_exam'])}")
print(f"  Cross-validation present: {'cross_validation' in u}")
print(f"  Confidence score: {u['confidence_score']}%")
print(f"  Questions have probability: {all('probability' in q for q in u['predicted_exam'])}")
print(f"  Questions have reason: {all('reason' in q for q in u['predicted_exam'])}")

print("\n=== UNIFIED ENGINE VALIDATED ===")
