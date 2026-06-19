import re
from typing import Optional

_ARABIC_RANGE = r'\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF'
_ARABIC_CHAR = re.compile(fr'[{_ARABIC_RANGE}]')
_LATIN_CHAR = re.compile(r'[a-zA-Z]')
_LATIN_IN_ARABIC = re.compile(r'([\u0600-\u06FF])[a-zA-Z]([\u0600-\u06FF])')
_ARABIC_IN_LATIN = re.compile(r'([a-zA-Z])[\u0600-\u06FF]([a-zA-Z])')
_WEIRD_CHARS = re.compile(r'[^\u0600-\u06FFa-zA-Z0-9\s\.\,\!\?\:\;\-\(\)\[\]\{\}\"\'\/\\@\#\$\%\^\&\*\+\=\<\>\|~\n\r\t\u2000-\u206F]')
_REPEATED_CHAR = re.compile(r'(.)\1{4,}')
_NOISE_SEQUENCE = re.compile(r'[^\s]{30,}')
_WORD_PATTERN = re.compile(r'[\u0600-\u06FFa-zA-Z]{3,}')
_DIACRITICS = re.compile(r'[\u064B-\u065F\u0610-\u061A\u06D6-\u06ED]')
_ALEF_VARIANTS = str.maketrans('أإآ', 'ااا')
_TEH_MARBUTA = str.maketrans('ة', 'ه')
_TATWEEL = re.compile(r'\u0640')
_HINDI_NUMERALS = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')
_RTL_MARK = re.compile(r'[\u200E\u200F\u202A-\u202E]')

_COMMON_ARABIC = frozenset({
    'في','من','على','الى','عن','هذا','هذه','هو','هي','هم','هن','كان','كل','بعض','بين',
    'مع','بعد','قبل','خلال','حول','عند','ليس','لم','لن','لا','ما','ذلك','تلك','الذي',
    'التي','هناك','هنا','حتى','ايضا','فقط','جدا','اخر','اخرى','اخر','اخرى','اي','اي',
    'قد','سوف','يمكن','يجب','يكون','تكون','كما','او','او','ثم','بل','لكن','ولكن','غير',
    'الى','الي','الى','ان','ان','انها','انها','انه','انه','فان','فان','فقد','لقد','وقد',
    'كان','اصبح','اصبح','ظل','بقي','صار','قال','كانت','كانوا',
})


def analyze_text_quality(text: str) -> dict:
    if not text or len(text) < 20:
        return {"passes": False, "score": 0, "issues": ["Text too short"]}

    total_chars = len(text)
    arabic_chars = len(_ARABIC_CHAR.findall(text))
    latin_chars = len(_LATIN_CHAR.findall(text))
    alpha_chars = arabic_chars + latin_chars
    weird_chars = len(_WEIRD_CHARS.findall(text))
    words = _WORD_PATTERN.findall(text)
    word_count = len(words)

    if alpha_chars == 0:
        return {"passes": False, "score": 0, "arabic_ratio": 0, "issues": ["No readable text detected"]}

    arabic_ratio = arabic_chars / max(alpha_chars, 1)
    weird_ratio = weird_chars / max(total_chars, 1)
    is_arabic = arabic_ratio > 0.3

    issues = []
    if weird_ratio > 0.05:
        issues.append(f"High noise ratio: {weird_ratio:.1%} weird characters")
    if word_count < 5:
        issues.append(f"Too few words: {word_count}")

    # Mixed-script detection
    mixed = len(_LATIN_IN_ARABIC.findall(text)) + len(_ARABIC_IN_LATIN.findall(text))
    if mixed > 3 and is_arabic:
        issues.append(f"Mixed-script detected: {mixed} occurrences — text may be corrupted")

    # Check Arabic words are real
    if is_arabic:
        fake_count = 0
        for w in words[:50]:
            w_clean = w.strip()
            if len(w_clean) >= 3 and _ARABIC_CHAR.search(w_clean):
                if not _is_real_arabic_word(w_clean):
                    fake_count += 1
        if fake_count > len(words) * 0.3:
            issues.append(f"High fake-word ratio: {fake_count}/{min(50, len(words))}")

    score = 100
    if weird_ratio > 0.05:
        score -= min(40, int(weird_ratio * 500))
    if mixed > 3:
        score -= min(30, mixed * 3)
    if word_count < 10:
        score -= 50
    if arabic_ratio < 0.3 and is_arabic:
        score -= 20

    score = max(0, min(100, score))

    return {
        "passes": score >= 60,
        "score": score,
        "arabic_ratio": round(arabic_ratio, 2),
        "word_count": word_count,
        "noise_ratio": round(weird_ratio, 4),
        "mixed_script_occurrences": mixed,
        "is_arabic": is_arabic,
        "issues": issues,
    }


def _is_real_arabic_word(word: str) -> bool:
    cleaned = _DIACRITICS.sub('', word)
    if cleaned in _COMMON_ARABIC:
        return True
    if len(cleaned) < 3:
        return False
    has_repeated = bool(_REPEATED_CHAR.search(cleaned))
    if has_repeated:
        return False
    latin_in_word = _LATIN_CHAR.findall(cleaned)
    arabic_in_word = _ARABIC_CHAR.findall(cleaned)
    if latin_in_word and arabic_in_word:
        return False
    return True


def repair_arabic_text(text: str) -> str:
    if not text:
        return text

    text = _RTL_MARK.sub('', text)
    text = _TATWEEL.sub('', text)
    text = text.translate(_HINDI_NUMERALS)
    text = _DIACRITICS.sub('', text)

    latin_in_arabic_fixes = {
        'A': 'ا','a': 'ا','B': 'ب','b': 'ب','T': 'ت','t': 'ت','H': 'ح','h': 'ه',
        'D': 'د','d': 'د','R': 'ر','r': 'ر','S': 'س','s': 'س','N': 'ن','n': 'ن',
        'Q': 'ق','q': 'ق','F': 'ف','f': 'ف','K': 'ك','k': 'ك','L': 'ل','l': 'ل',
        'M': 'م','m': 'م','W': 'و','w': 'و','Y': 'ي','y': 'ي','E': 'ع','e': 'ع',
        'G': 'غ','g': 'غ','C': 'ص','c': 'س','J': 'ج','j': 'ج','Z': 'ز','z': 'ز',
        'X': 'خ','x': 'خ','O': 'ء','o': 'ء','U': 'ع','u': 'ع','I': 'ي','i': 'ي',
        'P': 'ب','p': 'ب','V': 'ف','v': 'ف',
    }

    # Fix Latin surrounded by Arabic: الAول -> الاول
    text = re.sub(r'([\u0600-\u06FF])([a-zA-Z])([\u0600-\u06FF])',
                  lambda m: m.group(1) + latin_in_arabic_fixes.get(m.group(2), m.group(2)) + m.group(3),
                  text)

    # Fix Latin after Arabic at word start: aنّ -> أن (after diacritic removal)
    text = re.sub(r'\b([a-zA-Z])([\u0600-\u06FF]+)',
                  lambda m: latin_in_arabic_fixes.get(m.group(1), m.group(1)) + m.group(2),
                  text)

    return text


def normalize_arabic_text(text: str) -> str:
    if not text:
        return text

    # Remove diacritics (tashkeel)
    text = _DIACRITICS.sub('', text)
    # Normalize alef variants
    text = text.translate(_ALEF_VARIANTS)
    # Normalize teh marbuta (optional - some prefer keeping ة)
    # text = text.translate(_TEH_MARBUTA)

    return text


def quality_gate_extraction(extracted_text: str, filename: str = "") -> dict:
    result = {
        "original_length": len(extracted_text),
        "passed": False,
        "text": extracted_text,
        "actions_taken": [],
        "quality_report": {},
        "arabic_validation": None,
    }

    if len(extracted_text) < 50:
        result["quality_report"] = {"passes": False, "score": 0, "issues": ["Text too short for quality gate"]}
        return result

    from app.services.arabic_extractor import validate_arabic_text

    ar_validation = validate_arabic_text(extracted_text)
    result["arabic_validation"] = ar_validation

    if ar_validation["corruption_detected"]:
        if ar_validation.get("dictionary_ratio", 0) < 0.08:
            result["quality_report"] = {
                "passes": False, "score": ar_validation["score"],
                "issues": [f"Severe Arabic text corruption (dict ratio: {ar_validation['dictionary_ratio']}). Recommendation: {ar_validation['recommendation']}"],
            }
            return result
        repaired = repair_arabic_text(extracted_text)
        repaired = normalize_arabic_text(repaired)
        ar2 = validate_arabic_text(repaired)
        if ar2["score"] > ar_validation["score"]:
            result["text"] = repaired
            result["actions_taken"].append("arabic_repair_applied")
            ar_validation = ar2
        else:
            result["quality_report"] = {
                "passes": False, "score": ar_validation["score"],
                "issues": [f"Arabic text corruption detected (dict ratio: {ar_validation['dictionary_ratio']}). Recommendation: {ar_validation['recommendation']}"],
            }
            return result

    if ar_validation.get("dictionary_ratio", 0) < 0.15 and ar_validation.get("arabic_words", 0) > 20:
        result["quality_report"] = {
            "passes": False, "score": ar_validation["score"],
            "issues": [f"Very low Arabic dictionary match: {ar_validation['dictionary_ratio']} — text may be corrupted"],
        }
        return result

    qr = analyze_text_quality(result["text"])
    result["quality_report"] = qr

    if qr.get("mixed_script_occurrences", 0) > 0:
        repaired = repair_arabic_text(result["text"])
        if repaired != result["text"]:
            result["text"] = repaired
            result["actions_taken"].append("mixed_script_repair_applied")
            qr = analyze_text_quality(repaired)
            result["quality_report"] = qr

    if qr.get("is_arabic", False):
        normalized = normalize_arabic_text(result["text"])
        result["text"] = normalized
        result["actions_taken"].append("arabic_normalized")

    if qr.get("passes", False) and ar_validation["valid"]:
        result["passed"] = True
    elif qr.get("score", 0) >= 40 and not ar_validation["corruption_detected"]:
        result["passed"] = True
        result["actions_taken"].append("marginal_quality_accepted")

    return result


def verify_ai_output(output_type: str, result: dict, input_words: int) -> dict:
    verification = {"passed": True, "issues": [], "action": "accept"}

    if output_type == "summary":
        summary_words = result.get("summary_words", 0) or result.get("summary_length", 0)
        if summary_words == 0 and "summary" in result:
            summary_words = len(result["summary"].split())

        if input_words > 1000 and summary_words < input_words * 0.15:
            verification["passed"] = False
            verification["issues"].append(f"Summary too short: {summary_words}/{input_words} words ({summary_words/max(input_words,1)*100:.1f}%) — minimum 15% required")
            verification["action"] = "reprocess_detailed"

        if input_words > 10000 and summary_words < input_words * 0.25:
            verification["passed"] = False
            verification["issues"].append(f"Large document summary too short: {summary_words}/{input_words} words — minimum 25% for large docs")
            verification["action"] = "reprocess_detailed"

    elif output_type == "questions" or output_type == "prediction":
        questions = result.get("questions", result.get("exam_questions", []))
        if not questions:
            verification["passed"] = False
            verification["issues"].append("No questions generated")
            verification["action"] = "reprocess"
            return verification

        types_found = set()
        for q in questions:
            t = q.get("type", "").lower()
            if "mcq" in t or "multiple" in t or "اختيار" in t:
                types_found.add("mcq")
            if "short" in t or "قصير" in t:
                types_found.add("short_answer")
            if "essay" in t or "مقال" in t:
                types_found.add("essay")
            if "problem" in t or "مسأل" in t or "حل" in t:
                types_found.add("problem")

        if len(types_found) < 2 and len(questions) > 3:
            verification["issues"].append(f"Low question type diversity: only {types_found}")
        if len(questions) < 3:
            verification["passed"] = False
            verification["issues"].append("Too few questions generated")
            verification["action"] = "reprocess"

    elif output_type == "teacher":
        concepts = result.get("key_concepts", [])
        if len(concepts) < 3:
            verification["passed"] = False
            verification["issues"].append("Too few concepts extracted")
            verification["action"] = "reprocess"
        word_count = result.get("total_words", 0)
        if word_count > 5000 and len(concepts) < 8:
            verification["issues"].append(f"Low concept extraction for {word_count} word document")

    return verification
