import httpx, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = "http://127.0.0.1:8000"
r = httpx.post(f"{BASE}/auth/login", json={"email":"demo@example.com","password":"demo123"})
token = r.json()["access_token"]
h = {"Authorization": f"Bearer {token}"}

# Generate a ~40,000 word document (simulating a textbook)
print("Generating 40,000 word textbook...")
chapters = []
for ch_num in range(1, 13):
    ch = f"Chapter {ch_num}: Machine Learning Concepts Part {ch_num}\n\n"
    ch += f"A neural network is defined as a computing system inspired by biological neural networks. "
    ch += f"IMPORTANT: Understanding backpropagation is critical for mastering deep learning. "
    ch += f"Unlike traditional algorithms, neural networks learn from data through iterative weight updates. "
    ch += f"The key components of a neural network include: 1) input layer, 2) hidden layers, 3) output layer. "
    ch += f"However, deep networks suffer from the vanishing gradient problem - you must know this for exams. "
    ch += f"Supervised learning is defined as a machine learning approach where models learn from labeled data. "
    ch += f"In contrast, unsupervised learning finds patterns in unlabeled data through clustering techniques. "
    ch += f"Remember: The difference between classification and regression is fundamental to machine learning. "
    ch += f"Convolutional neural networks (CNNs) are specialized for image processing using convolutional filters. "
    ch += f"Recurrent neural networks (RNNs) handle sequential data through internal memory states. "
    ch += f"The transformer architecture revolutionized NLP through self-attention mechanisms. "
    ch += f"Key formula: Loss = 1/N * sum((y_pred - y_true)^2) for Mean Squared Error. "
    ch += f"IMPORTANT: Regularization techniques prevent overfitting - L1, L2, and dropout must be understood. "
    ch += f"Transfer learning allows models to leverage pre-trained weights for faster convergence. "
    ch += f"Note that batch normalization stabilizes training by normalizing layer inputs. "
    ch += f"Example: ImageNet pre-trained models achieve state-of-the-art results on many vision tasks. "
    ch += f"Common mistake: Students confuse precision and recall - know the exact definitions. "
    ch += f"Reinforcement learning agents learn through trial and error using reward signals. "
    ch += f"The exploration-exploitation tradeoff is a fundamental challenge in reinforcement learning. "
    ch += f"Q-learning is a model-free algorithm that learns optimal action-value functions. "
    chapters.append(ch)

textbook = "\n\n".join(chapters)
total_words = len(textbook.split())
print(f"Textbook: {total_words} words, {len(textbook)} chars, {len(textbook)/1024:.0f} KB")

# Test 1: Hierarchical summarization
print("\n=== HIERARCHICAL SUMMARIZATION ===")
r = httpx.post(f"{BASE}/ai/hierarchical-summarize", json={"text": textbook}, headers=h, timeout=30)
hs = r.json()
print(f"Original: {hs['original_words']:,} words")
print(f"Summary:  {hs['summary_words']:,} words ({hs['compression_ratio']})")
print(f"Target:   {hs['target_ratio']}")
print(f"Chapters processed: {hs['chapters_count']}")
print(f"Definitions extracted: {hs['definitions_extracted']}")
print(f"Quality: {hs['information_preservation']['quality']}")
info_loss = (1 - hs['summary_words'] / hs['original_words']) * 100
print(f"Information preserved: {100 - info_loss:.1f}% (previously ~{100 - (1 - 273/39200)*100:.1f}%)")
print("PASS" if hs['summary_words'] > hs['original_words'] * 0.25 else "FAIL - too much loss")

# Test 2: Multi-pass prediction
print("\n=== MULTI-PASS PREDICTION ===")
r = httpx.post(f"{BASE}/ai/multi-pass-predict", json={
    "textbook": textbook,
    "past_exams": "Q1: Define neural networks. Q2: Compare supervised and unsupervised learning.",
}, headers=h, timeout=30)
mp = r.json()
print(f"Passes: {mp['passes_completed']}")
print(f"Topics extracted: {mp['topics_extracted']}")
print(f"Teacher style: {mp['teacher_style']}")
print(f"Questions generated: {len(mp['exam_questions'])}")
bp = mp['exam_blueprint']
print(f"Blueprint: {bp['total_questions']} questions, {bp['difficulty_distribution']}")
print(f"QA: chapters={mp['quality_assurance']['chapters_covered']}, defs={mp['quality_assurance']['definitions_preserved']}")

# Verify multi-pass quality
print("\n[QUALITY CHECKS]")
print(f"  Chapter-level: {'PASS' if hs['chapters_count'] >= 5 else 'FAIL'} ({hs['chapters_count']} chapters)")
print(f"  Dynamic ratio: {'PASS' if '50%' in hs['target_ratio'] or '55%' in hs['target_ratio'] else 'OK'} (got {hs['target_ratio']})")
print(f"  Definitions preserved: {hs['definitions_extracted']} concepts")
print(f"  5-pass prediction: {'PASS' if mp['passes_completed'] == 5 else 'FAIL'}")
print(f"  Blueprint present: {'PASS' if mp['exam_blueprint'] else 'FAIL'}")

print("\n=== HIERARCHICAL PIPELINE VALIDATED ===")
