import httpx, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = "http://127.0.0.1:8000"
r = httpx.post(f"{BASE}/auth/register", json={"email":"exam@test.com","username":"examtest","password":"examtest123"})
token = r.json()["access_token"]
h = {"Authorization": f"Bearer {token}"}

text = """Chapter 1: Deep Learning Foundations
Deep learning is defined as a subset of machine learning that uses neural networks with many layers.
IMPORTANT: Backpropagation is the key algorithm for training neural networks.
A neural network consists of: 1) Input layer, 2) Hidden layers, 3) Output layer.
Unlike traditional algorithms, neural networks learn features automatically from raw data.
However, deep networks require large amounts of labeled data and significant computational resources.

Chapter 2: Convolutional Neural Networks
A Convolutional Neural Network (CNN) is defined as a specialized neural network for image processing.
CNNs use convolutional filters to detect spatial patterns like edges and textures.
The key components of a CNN are: 1) Convolutional layers, 2) Pooling layers, 3) Fully connected layers.
Note that CNNs preserve spatial relationships between pixels - this is critical for image recognition.
Unlike CNNs, Recurrent Neural Networks (RNNs) process sequential data through internal memory states.

Chapter 3: Transformers and Attention
The transformer architecture is another important development in deep learning.
Transformers use self-attention mechanisms instead of recurrence or convolution.
Key advantages include: 1) Parallel processing, 2) Long-range dependency handling, 3) Superior NLP performance.
Remember: BERT and GPT are transformer-based models. You must know the difference between encoder and decoder architectures."""

r = httpx.post(f"{BASE}/ai/full-exam", json={"text": text}, headers=h, timeout=15)
exam = r.json()
print(f"Exam ID: {exam['exam_id']}")
print(f"Total marks: {exam['total_marks']}")
print(f"Time: {exam['time_minutes']} min")
print(f"Chapters covered: {len(exam['chapter_coverage'])}")
for s in exam["sections"]:
    print(f"\nSection {s['section']}: {s['title']} ({s['marks']})")
    for q in s["questions"]:
        print(f"  Q{q['number']}: [{q['marks']}m] {q['question'][:80]}...")
        if q.get("correct"):
            print(f"    Answer: {q['correct']}) {q.get('correct_answer','')[:40]}")
        if q.get("model_answer"):
            print(f"    Model answer available: {len(q['model_answer'])} chars")
        if q.get("marking_criteria"):
            print(f"    Criteria: {len(q['marking_criteria'])} items")
print(f"\nPrediction confidence: {exam['statistics']['prediction_confidence']}%")
print(f"Has answer key: {'answer_key' in exam}")
print(f"Has marking scheme: {'marking_scheme' in exam}")
print("\nPASS" if exam['total_marks'] == 100 else "FAIL - not 100 marks")
