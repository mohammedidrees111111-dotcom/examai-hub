import httpx, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = "http://127.0.0.1:8000"
r = httpx.post(f"{BASE}/auth/login", json={"email":"demo@example.com","password":"demo123"})
token = r.json()["access_token"]
h = {"Authorization": f"Bearer {token}"}

textbook = """Chapter 4: Database Systems
A relational database is defined as a collection of data organized into tables with rows and columns.
SQL (Structured Query Language) is used to query and manipulate relational databases.
Normalization is the process of organizing data to reduce redundancy. First Normal Form requires atomic values.
ACID properties (Atomicity, Consistency, Isolation, Durability) ensure reliable transaction processing.
Indexes improve query performance by creating data structures for fast lookup.
Joins combine rows from multiple tables based on related columns. INNER JOIN returns matching rows.
NoSQL databases provide flexible schemas for unstructured data. MongoDB uses document-based storage."""

past_exams = """Question 1: Define a relational database and explain its key components. (Short Answer)
Question 2: Compare SQL and NoSQL databases. Give examples of each. (Essay)
Question 3: What is normalization? List the normal forms. (Short Answer)
Question 4: True or False: ACID stands for Atomicity, Consistency, Isolation, Durability.
Question 5: Explain INNER JOIN with an example. (Short Answer)
Question 6: Define indexing and explain why it is important for performance.
Question 7: Compare and contrast relational databases with document databases."""

lecture_notes = """IMPORTANT: ACID properties will be on the exam. Know them thoroughly.
Remember: The difference between INNER JOIN and OUTER JOIN is critical.
You should understand normalization up to 3NF.
Key concept: Indexes dramatically improve query speed.
Note that: MongoDB is a document database, not relational."""

print("=== MULTI-SOURCE EXAM RECONSTRUCTION ===\n")
r = httpx.post(f"{BASE}/ai/exam-reconstruct", json={
    "textbook": textbook, "past_exams": past_exams, "lecture_notes": lecture_notes
}, headers=h, timeout=30)
t = r.json()

print(f"Confidence: {t['exam_prediction_confidence']}%")

print(f"\n[SOURCE ANALYSIS]")
sa = t["source_analysis"]
print(f"  Textbook: {sa['textbook_topics']} topics")
print(f"  Past exams: {sa['past_exam_topics']} topics")
print(f"  Lectures: {sa['lecture_topics']} topics")
print(f"  Cross-source: {sa['cross_source_topics']} topics (overlap)")

print(f"\n[ALIGNMENT]")
al = t["source_alignment"]
print(f"  Cross-source (book+exam): {', '.join(al['cross_source'][:8])}")
print(f"  Exam-only: {', '.join(al['exam_only'][:5])}")
print(f"  Overlap: {al['statistics']['overlap_percentage']}%")

print(f"\n[EXAM PATTERNS MINED]")
ep = t["exam_patterns_mined"]
print(f"  Questions found: {ep['total_exam_questions_found']}")
print(f"  Distribution: {ep['question_distribution']}")
print(f"  Templates: {len(ep['repeated_templates'])}")
print(f"  Repeated: {len(ep['repeated_questions'])}")

print(f"\n[TEACHER BEHAVIOR]")
tb = t["teacher_behavior_model"]
print(f"  Favorite topics: {', '.join(tb['favorite_topics'][:6])}")
print(f"  Repeats questions: {tb['repetition_behavior']['repeats_questions']}")
print(f"  Habits: {len(tb['inferred_habits'])}")

print(f"\n[PREDICTED EXAM]")
for i, q in enumerate(t["predicted_exam"][:5]):
    sw = q["source_weighting"]
    matches = f"book={sw['textbook_match']} exam={sw['past_exam_match']}"
    print(f"  {i+1}. [{q['type']}] score={q['probability_score']} | {matches}")
    print(f"     {q['reason_this_question_is_likely'][:100]}")

print(f"\n  Tricks: {len(t['trick_questions'])}")
print(f"  Repeated patterns: {len(t['repeated_patterns_detected'])}")
print(f"  Revision: {len(t['last_minute_revision_sheet']['top_priority'])} top + {len(t['last_minute_revision_sheet']['exam_favorites'])} favorites")

print(f"\n[QUALITY CHECKS]")
print(f"  Source weighting present: {all('source_weighting' in q for q in t['predicted_exam'])}")
print(f"  Confidence score: {t['exam_prediction_confidence']}%")
print(f"  Cross-source detection: {len(al['cross_source']) > 0}")
print(f"  Exam-only detection: {len(al['exam_only']) > 0}")
print(f"  Teacher model present: {bool(t['teacher_behavior_model'])}")

print("\n=== MULTI-SOURCE RECONSTRUCTION VALIDATED ===")
