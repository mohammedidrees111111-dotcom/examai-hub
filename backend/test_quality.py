import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from app.services.quality_gates import analyze_text_quality, repair_arabic_text, quality_gate_extraction, verify_ai_output

# Test 1: Clean Arabic text
print("=== TEST 1: CLEAN ARABIC TEXT ===")
clean = "الذكاء الاصطناعي هو فرع من فروع علوم الحاسوب يهدف إلى تطوير أنظمة قادرة على محاكاة الذكاء البشري. يشمل هذا المجال التعلم الآلي والتعلم العميق والشبكات العصبية."
qr = analyze_text_quality(clean)
print(f"Score: {qr['score']}, Passes: {qr['passes']}, Arabic: {qr['arabic_ratio']}")
print(f"Issues: {qr['issues']}")
print("PASS" if qr["passes"] else "FAIL")

# Test 2: Corrupted Arabic text (mixed script)
print("\n=== TEST 2: CORRUPTED ARABIC (MIXED SCRIPT) ===")
corrupted = "شّال aنّ aتيي الAول الAحزاب سّال قال النظام التعليمي"
qr2 = analyze_text_quality(corrupted)
print(f"Score: {qr2['score']}, Mixed: {qr2['mixed_script_occurrences']}")
print(f"Issues: {qr2['issues']}")
print("DETECTED" if qr2['mixed_script_occurrences'] > 0 else "MISSED")

repaired = repair_arabic_text(corrupted)
print(f"\nBefore: {corrupted}")
print(f"After:  {repaired}")
qr3 = analyze_text_quality(repaired)
print(f"After repair score: {qr3['score']}, Mixed: {qr3['mixed_script_occurrences']}")
print("PASS" if qr3['score'] > qr2['score'] else "NO IMPROVEMENT")

# Test 3: Full quality gate pipeline
print("\n=== TEST 3: QUALITY GATE PIPELINE ===")
result = quality_gate_extraction(corrupted)
print(f"Passed: {result['passed']}, Actions: {result['actions_taken']}")
print(f"Original length: {result['original_length']}")
print(f"Final text (first 100): {result['text'][:100]}")
print("PASS" if result["passed"] or "mixed_script_repair_applied" in result['actions_taken'] else "FAIL")

# Test 4: AI Verifier - summary too short
print("\n=== TEST 4: AI VERIFIER — REJECT BAD SUMMARY ===")
bad_summary = {"summary_words": 200, "summary": "x " * 200}
v1 = verify_ai_output("summary", bad_summary, 40000)
print(f"39K doc -> 200 words: passed={v1['passed']}, action={v1['action']}")
print("REJECTED" if not v1['passed'] and v1['action'] == 'reprocess_detailed' else "ACCEPTED (wrong)")

good_summary = {"summary_words": 22000, "summary": "x " * 22000}
v2 = verify_ai_output("summary", good_summary, 40000)
print(f"39K doc -> 22K words: passed={v2['passed']}, action={v2['action']}")
print("PASS" if v2['passed'] else "FAIL")

# Test 5: AI Verifier - low question diversity
print("\n=== TEST 5: AI VERIFIER — QUESTION DIVERSITY ===")
bad_questions = {"questions": [
    {"type": "Short Answer"}, {"type": "Short Answer"}, {"type": "Short Answer"}
]}
vq1 = verify_ai_output("questions", bad_questions, 1000)
print(f"3x same type: issues={vq1['issues']}")
print("WARNED" if len(vq1['issues']) > 0 else "NO WARNING (wrong)")

good_questions = {"questions": [
    {"type": "MCQ"}, {"type": "Short Answer"}, {"type": "Essay"}, {"type": "Problem Solving"}
]}
vq2 = verify_ai_output("questions", good_questions, 1000)
print(f"4 different types: passed={vq2['passed']}, issues={vq2['issues']}")
print("PASS" if vq2['passed'] else "FAIL")

print("\n=== ALL QUALITY GATE TESTS ===")
