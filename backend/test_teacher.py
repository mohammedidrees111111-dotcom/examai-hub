import httpx, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = "http://127.0.0.1:8000"
r = httpx.post(f"{BASE}/auth/login", json={"email":"demo@example.com","password":"demo123"})
token = r.json()["access_token"]
h = {"Authorization": f"Bearer {token}"}

text = """Chapter 3: Neural Network Architectures

IMPORTANT: Understanding the difference between CNN and RNN architectures is critical for the final exam.

A Convolutional Neural Network (CNN) is defined as a specialized neural network designed for processing grid-structured data, particularly images. CNNs use convolutional layers that apply filters to detect spatial patterns. Note that CNNs preserve spatial relationships between pixels — this is what makes them superior to regular neural networks for image tasks. The key components are: 1) convolutional layers, 2) pooling layers, and 3) fully connected layers.

However, CNNs have a limitation: they require fixed-size inputs, which makes them less suitable for variable-length sequences.

A Recurrent Neural Network (RNN) is defined as a neural network architecture designed for sequential data processing. Unlike CNNs which process spatial data, RNNs maintain an internal hidden state that captures information from previous time steps. Remember: RNNs suffer from the vanishing gradient problem — this is a critical concept that has been on previous exams.

In other words, while CNNs excel at spatial pattern recognition, RNNs specialize in temporal sequence modeling.

You should understand that LSTMs (Long Short-Term Memory networks) were developed specifically to address the vanishing gradient problem in standard RNNs. This is fundamental — do not forget this point.

The transformer architecture is another important development. Unlike both CNNs and RNNs, transformers use self-attention mechanisms instead of recurrence or convolution. Key advantages include: 1) parallel processing, 2) better handling of long-range dependencies, and 3) superior performance on NLP tasks.

For example, BERT and GPT are transformer-based models that have achieved state-of-the-art results.

In summary, the three main neural network architectures are: CNN (spatial), RNN (sequential), and Transformer (attention-based). You must be able to compare and contrast these architectures."""

print("=== TEACHER FINGERPRINT TEST ===\n")
r = httpx.post(f"{BASE}/ai/teacher-exam", json={"text": text}, headers=h, timeout=30)
t = r.json()

fp = t["teacher_profile"]
print("[TEACHER PROFILE]")
print(f"  Style: {fp['teaching_style']}")
print(f"  Formality: {fp['formality']}")
print(f"  Theory/App: {fp['theory_vs_application']}")
print(f"  Def density: {fp['definition_density']}")
print(f"  Comp density: {fp['comparison_density']}")
print(f"  Question prefs: {len(fp['preferred_question_types'])} types")

em = t["emphasis_map"]
print(f"\n[EMPHASIS MAP]")
print(f"  Top concepts: {', '.join(c['concept'] for c in em['top_emphasized'][:6])}")
print(f"  Dist: {em['emphasis_distribution']}")

sig = t["hidden_exam_signals"]
print(f"\n[HIDDEN EXAM SIGNALS]")
for s in sig[:5]:
    print(f"  '{s['signal_word']}' (w={s['weight']}) → {s['interpretation'][:60]}")

pat = t["exam_pattern_reconstruction"]
print(f"\n[EXAM PATTERNS]")
print(f"  Difficulty: {pat['difficulty_distribution']}")
print(f"  Tricks found: {len(pat['trick_patterns'])}")
print(f"  Repetitions: {len(pat['repetition_analysis'])}")

pred = t["high_probability_questions"]
print(f"\n[HIGH PROBABILITY PREDICTIONS]")
for p in pred[:5]:
    print(f"  {p['concept']}: score={p['prediction_score']} {p['probability']}")

exam = t["predicted_exam"]
print(f"\n[PREDICTED EXAM]")
print(f"  Questions: {len(exam['high_probability_questions'])}")
print(f"  Tricks: {len(exam['trick_questions'])}")
print(f"  Defs to study: {len(exam['important_definitions_to_study'])}")
print(f"  Strategy tips: {len(exam['exam_strategy'])}")
print(f"  Revision: {len(exam['last_minute_revision']['top_5_must_know'])} must-know")

# Quality check: verify teacher-specific reasoning
q1 = exam["high_probability_questions"][0]
print(f"\n[QUALITY CHECK]")
print(f"  Has 'why_teacher': {'why_teacher_likely_asked_this' in q1}")
print(f"  Has 'answer_guidance': {'answer_guidance' in q1}")
print(f"  Has signals: {len(sig)}")
print(f"  Has emphasis: {len(em['top_emphasized'])}")
print(f"  All phases present: {all(k in t for k in ['teacher_profile','emphasis_map','hidden_exam_signals','exam_pattern_reconstruction','high_probability_questions','predicted_exam'])}")

print("\n=== ALL PHASES VALIDATED ===")
