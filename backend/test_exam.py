import httpx, sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = "http://127.0.0.1:8000"
r = httpx.post(f"{BASE}/auth/login", json={"email": "demo@example.com", "password": "demo123"})
token = r.json()["access_token"]
h = {"Authorization": f"Bearer {token}"}

text = """Chapter 1: Machine Learning Fundamentals

Machine learning is defined as a subset of artificial intelligence that enables systems to learn from data without explicit programming. Unlike traditional programming where rules are hard-coded, machine learning algorithms discover patterns automatically.

Supervised learning is a type of machine learning where models are trained on labeled data. The algorithm learns a mapping from inputs to outputs. Common algorithms include linear regression, logistic regression, decision trees, and support vector machines. Linear regression predicts continuous values, while logistic regression handles binary classification problems. However, supervised learning requires large amounts of labeled data which can be expensive to obtain.

Unsupervised learning finds hidden patterns in unlabeled data. K-means clustering partitions data into K groups based on similarity. Principal Component Analysis reduces dimensionality while preserving variance. Unlike supervised learning, unsupervised learning does not require labels — but interpreting results can be more challenging.

Reinforcement learning is defined as a learning paradigm where an agent learns by interacting with an environment. The agent receives rewards for good actions and penalties for bad actions. Key algorithms include Q-learning and policy gradients. Interestingly, reinforcement learning has achieved superhuman performance in games like Go and chess, but it requires enormous computational resources.

Deep learning uses neural networks with many layers to learn hierarchical representations. Convolutional neural networks specialize in image processing. Recurrent neural networks handle sequential data. Transformers use attention mechanisms and have revolutionized natural language processing. However, deep learning models are often considered "black boxes" because their decision-making process is difficult to interpret.

The bias-variance tradeoff is a fundamental concept in machine learning. High bias leads to underfitting — the model is too simple to capture patterns. High variance leads to overfitting — the model memorizes training data but fails to generalize. The goal is to find the optimal balance between bias and variance."""

print("=== EXAM ENGINE TEST ===\n")
r = httpx.post(f"{BASE}/ai/exam-prep", json={"text": text}, headers=h, timeout=30)
e = r.json()

print(f"Words analyzed: {e['document_stats']['total_words']}")
print(f"Concepts found: {e['document_stats']['key_concepts_found']}")
print(f"Definitions: {e['document_stats']['definitions_extracted']}")
print(f"Comparisons: {e['document_stats']['comparisons_detected']}")
print(f"Exceptions: {e['document_stats']['exceptions_found']}")

print(f"\nHigh-yield topics: {', '.join(e['high_yield_topics'][:8])}")

print(f"\nMCQ + Short Answer: {len(e['likely_exam_questions'])} questions")
for q in e['likely_exam_questions'][:3]:
    print(f"  [{q['type']}] {q['question'][:80]}...")
    print(f"  Answer: {q.get('correct_answer', 'see full')[:60]}")

print(f"\nEssay questions: {len(e['essay_questions'])}")
for q in e['essay_questions'][:2]:
    print(f"  {q['question'][:80]}...")

print(f"\nProblem-solving: {len(e['problem_solving_questions'])}")
print(f"Tricky questions: {len(e['tricky_questions'])}")
print(f"Teacher traps: {len(e['teacher_trap_patterns'])}")

print(f"\nDifficulty map:")
for level in ["easy", "medium", "hard"]:
    concepts = e['difficulty_map'][level]
    print(f"  {level}: {', '.join(concepts[:4])}")

print(f"\nRevision sheet:")
print(f"  Must memorize: {len(e['revision_sheet']['must_memorize']['definitions'])} defs")
print(f"  Must understand: {len(e['revision_sheet']['must_understand']['concepts'])} concepts")
print(f"  Must practice: {len(e['revision_sheet']['must_practice']['apply_concepts'])} concepts")
print(f"  Quick review cards: {len(e['revision_sheet']['quick_review_cards'])}")
print(f"  Exam tips: {len(e['revision_sheet']['exam_tips'])}")

# Verify explanation quality
mcq = [q for q in e['likely_exam_questions'] if q['type'] == 'mcq']
if mcq:
    print(f"\nQuiz explanation check:")
    print(f"  Has why_correct: {'why_correct' in mcq[0].get('explanation', {})}")
    print(f"  Has why_others_wrong: {'why_others_wrong' in mcq[0].get('explanation', {})}")
    print(f"  Distractors: {len(mcq[0]['options']) - 1}")

print("\n=== PASS ===")
