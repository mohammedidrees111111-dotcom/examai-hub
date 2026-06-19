import sys
sys.path.insert(0, ".")
from app.services.arabic_extractor import validate_arabic_text
from app.services.quality_gates import quality_gate_extraction

real = "في هذا الكتاب سوف نتعلم اساسيات اللغة العربية من القواعد والنحو والصرف والبلاغة والادب والشعر والنثر والمقال والقصة والرواية والقراءة والكتابة والاستماع والتحدث"
corr = "شال سال صالن العربية تعالى وال اهلل الاتية اعر الوحدة اللغة صال منها الابيات سورةS ضحىV سمسا"

v1 = validate_arabic_text(real)
v2 = validate_arabic_text(corr)
print(f"Real: valid={v1['valid']}, score={v1['score']}, ratio={v1['dictionary_ratio']}")
print(f"Corr: valid={v2['valid']}, score={v2['score']}, ratio={v2['dictionary_ratio']}")
print(f"Gap: {v1['score'] - v2['score']} points")

g1 = quality_gate_extraction(real)
g2 = quality_gate_extraction(corr)
print(f"Quality gate real: passed={g1['passed']}")
print(f"Quality gate corr: passed={g2['passed']}, issues={g2['quality_report'].get('issues', [])}")

print()
checks = [
    ("Arabic text classified correctly", v1['valid'] and not v2['valid']),
    ("Quality gate rejects corrupted", not g2['passed']),
    ("Quality gate accepts real", g1['passed']),
    ("Corruption detected", v2['corruption_detected']),
]
for label, result in checks:
    print(f"[{'PASS' if result else 'FAIL'}] {label}")
