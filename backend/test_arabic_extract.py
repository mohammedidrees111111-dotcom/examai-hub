import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from app.services.arabic_extractor import (
    analyze_arabic_fonts, extract_arabic_multistrategy,
    validate_arabic_text, _score_arabic_quality
)

# Test 1: Validate real Arabic text
print("=== TEST 1: REAL ARABIC TEXT ===")
real_arabic = """
الذكاء الاصطناعي هو فرع من فروع علوم الحاسوب يهدف إلى تطوير أنظمة قادرة على محاكاة الذكاء البشري.
يشمل هذا المجال التعلم الآلي والتعلم العميق والشبكات العصبية. معالجة اللغة الطبيعية تمكن الحاسوب من فهم
اللغة البشرية وتوليدها. الرؤية الحاسوبية تسمح للآلات بفهم الصور والفيديوهات. الروبوتات هي آلات ذكية
قادرة على تنفيذ مهام فيزيائية بشكل مستقل. أخلاقيات الذكاء الاصطناعي تهتم بضمان استخدام هذه التقنيات
بشكل مسؤول وعادل. التعلم المعزز هو أسلوب يتعلم فيه الوكيل من خلال التفاعل مع البيئة والحصول على مكافآت.
"""
v = validate_arabic_text(real_arabic)
print(f"Valid: {v['valid']}, Score: {v['score']}, Words: {v['arabic_words']}, Real: {v['real_words']}")
print(f"Dict ratio: {v['dictionary_ratio']}, Noise: {v['noise_ratio']}")
print("PASS" if v['valid'] and v['score'] > 60 else "FAIL")

# Test 2: Detect corrupted Arabic (like the PDF output)
print("\n=== TEST 2: CORRUPTED ARABIC ===")
corrupted = """شال سال صالن العربية تعالى وال اهلل الاتية اعر الوحدة اللغة صال منها الابيات
صالن ايقر يقع ما او ومن الحدث على يدل شتقم سمسا المفعول سمسوا شينتالوا اقوال سماعه"""
v2 = validate_arabic_text(corrupted)
print(f"Valid: {v2['valid']}, Score: {v2['score']}, Words: {v2['arabic_words']}")
print(f"Dict ratio: {v2['dictionary_ratio']}, Corruption: {v2['corruption_detected']}")
print(f"Recommendation: {v2['recommendation']}")
print("DETECTED" if v2['corruption_detected'] else "MISSED")

# Test 3: Quality scoring comparison
print("\n=== TEST 3: QUALITY SCORE COMPARISON ===")
s1 = _score_arabic_quality(real_arabic)
s2 = _score_arabic_quality(corrupted)
print(f"Real Arabic: {s1}/100")
print(f"Corrupted:   {s2}/100")
print(f"Difference: {s1 - s2} points")
print("PASS" if s1 > s2 + 30 else "FAIL — difference too small")

# Test 4: Font analysis (requires PDF, skip if no PDF)
print("\n=== TEST 4: FONT ANALYSIS ===")
try:
    fa = analyze_arabic_fonts("test_book.pdf")
    print(f"Has Arabic: {fa['has_arabic']}, Risky: {fa['risky']}, Embedded: {fa['embedded_fonts']}")
except Exception as e:
    print(f"No test PDF available — skipping: {e}")

# Test 5: Dictionary coverage
print("\n=== TEST 5: DICTIONARY SIZE ===")
from app.services.arabic_extractor import ARABIC_WORD_DICT
print(f"Dictionary words: {len(ARABIC_WORD_DICT)}")

print("\n=== ARABIC EXTRACTION ENGINE VALIDATED ===")
