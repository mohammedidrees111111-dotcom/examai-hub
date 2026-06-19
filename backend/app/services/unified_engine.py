import re
from typing import Optional
from collections import Counter

_RE_AR = re.compile(r'[\u0600-\u06FF]')
_RE_EN = re.compile(r'[a-zA-Z]')
_RE_WORDS = re.compile(r'[\u0600-\u06FFa-zA-Z]{3,}')
_RE_SENTENCE = re.compile(r'[.!?\n،؛؟\r]+')

AR_STOP = frozenset({
    "في","من","على","عن","هذا","هذه","هو","هي","هم","كل","بعض","بين","مع","بعد","قبل",
    "خلال","حول","عند","ليس","لم","لن","لا","ما","ذلك","تلك","الذي","التي","هناك",
})
EN_STOP = frozenset({
    "the","and","for","are","but","not","you","all","any","had","this","that","with",
    "from","they","have","been","were","which","about","would","could",
})
ALL_STOP = AR_STOP | EN_STOP

_EMPHASIS_EN = re.compile(
    r'(?:important|critical|crucial|essential|key|vital|fundamental|significant|'
    r'note that|remember|do not forget|pay attention|you should|you must|be aware|'
    r'always|never|must|required|mandatory|absolutely|definitely)',
    re.IGNORECASE
)
_EMPHASIS_AR = re.compile(
    r'(?:مهم|هام|ملاحظة|انتبه|تذكر|لاحظ أن|يجب أن|من الضروري|أساسي|جوهري|محوري|دائما|أبدا)',
    re.IGNORECASE
)
_RE_DEF_EN = re.compile(
    r'(?:is\s+defined\s+as|refers\s+to|is\s+a\s+form\s+of|means\s+that|is\s+the\s+process\s+of|'
    r'is\s+a\s+type\s+of|is\s+an?\s+|are\s+the\s+|consists?\s+of|comprises?\s+|involves?\s+)'
    r'(.{15,250}?)(?:[.!\n]|$)', re.IGNORECASE
)
_RE_DEF_AR = re.compile(
    r'(?:هو|تعرف|يعرف|يقصد به|تعني|يقصد ب|المقصود بـ|عبارة عن|تتكون من|تشمل|تتمثل في)'
    r'(.{15,250}?)(?:[.؛!\n]|$)', re.IGNORECASE
)
_RE_LIST = re.compile(r'(?:^|\n)\s*(?:[\d]+[\.\)]\s+|[•\-\*\✓\✔\→]\s+)(.+?)(?:\n|$)', re.MULTILINE)
_RE_COMPARE = re.compile(
    r'(?:unlike|whereas|while|in contrast|compared to|differs from|better than|worse than|'
    r'more than|less than|similar to|same as|however|on the other hand|بينما|مقارنة|على العكس)',
    re.IGNORECASE
)
_RE_QUESTION = re.compile(
    r'(?:^|\n)\s*(?:\d+[\.\)]\s*)?(?:What|Which|How|Why|When|Where|Who|Explain|Describe|'
    r'Define|List|Compare|Contrast|Discuss|Analyze|Evaluate|Calculate|Solve|Prove|'
    r'ما|كيف|لماذا|متى|أين|من|اشرح|عرف|قارن|ناقش|حلل|احسب|اذكر|عدد)',
    re.IGNORECASE
)


def _lang(text: str) -> str:
    return "ar" if len(_RE_AR.findall(text[:2000])) > len(_RE_EN.findall(text[:2000])) else "en"


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in _RE_SENTENCE.split(text) if len(s.strip()) > 10]


def _keywords(text: str, min_freq: int = 2, top_n: int = 60) -> list[str]:
    words = _RE_WORDS.findall(text.lower())
    lang = _lang(text)
    min_len = 3 if lang == "ar" else 4
    filtered = [w for w in words if len(w) >= min_len and w not in ALL_STOP]
    if not filtered:
        return []
    freq = Counter(filtered)
    return [w for w, c in freq.most_common(top_n) if c >= min_freq]


def unified_academic_analysis(textbook: str, past_exams: str = "", lecture_notes: str = "") -> dict:
    lang = _lang(textbook)
    is_ar = lang == "ar"
    has_exams = len((past_exams or "").strip()) > 50

    textbook = textbook.strip()
    past_exams = (past_exams or "").strip()
    lecture_notes = (lecture_notes or "").strip()

    all_text = textbook + " " + past_exams + " " + lecture_notes
    all_kw = _keywords(all_text, min_freq=2, top_n=80)
    if not all_kw:
        all_kw = _keywords(all_text, min_freq=1, top_n=80)
    tb_kw = set(_keywords(textbook, min_freq=1, top_n=60))
    pe_kw = set(_keywords(past_exams, min_freq=1, top_n=50)) if has_exams else set()

    # --- STEP 1: Exam-Oriented Summarization ---
    exam_material = _extract_exam_study_material(all_text, all_kw, lang, is_ar)

    # --- STEP 2: Teacher Behavior Model ---
    teacher_fp = _analyze_teacher(textbook, past_exams, lecture_notes, all_kw, tb_kw, pe_kw, lang, is_ar, has_exams)

    # --- STEP 3: Exam Prediction (weighted) ---
    predictions = _predict_weighted_exam(all_kw, tb_kw, pe_kw, teacher_fp, textbook, past_exams, lang, is_ar, has_exams)

    # --- STEP 4: Cross-Validation ---
    validated = _cross_validate(predictions, teacher_fp, exam_material, all_kw, is_ar)

    confidence = _calc_confidence(validated, has_exams, len(tb_kw & pe_kw) if has_exams else 0)

    return {
        "exam_study_material": exam_material,
        "teacher_fingerprint": teacher_fp,
        "predicted_exam": validated["questions"],
        "confidence_score": confidence,
        "cross_validation": validated["report"],
        "language": lang,
    }


def _extract_exam_study_material(text, keywords, lang, is_ar):
    definitions = _extract_defs(text, lang)
    lists = _RE_LIST.findall(text)
    comparisons = [(m.group(), text[max(0, m.start()-40):min(len(text), m.end()+120)].strip())
                   for m in _RE_COMPARE.finditer(text)]

    text_lower = text.lower()
    emphasis_pattern = _EMPHASIS_AR if is_ar else _EMPHASIS_EN
    signaled = []
    for m in emphasis_pattern.finditer(text_lower):
        ctx = text[max(0, m.start()-80):min(len(text), m.end()+80)].strip()
        signaled.append({"signal": m.group(), "context": ctx[:200]})

    tricky = _find_tricky_points(comparisons, definitions, is_ar)

    return {
        "must_know": [
            {"concept": kw, "reason": "High frequency + definition available" if any(
                kw.lower() in d["definition"].lower() for d in definitions
            ) else "High frequency concept"}
            for kw in keywords[:12]
        ],
        "high_yield_topics": keywords[:15],
        "core_definitions": [{"term": d["term"], "definition": d["definition"][:200]} for d in definitions[:8]],
        "formulas_and_steps": lists[:8],
        "teacher_emphasis_signals": [s for s in signaled[:8] if any(
            kw.lower() in s["context"].lower() for kw in keywords[:15]
        )],
        "tricky_points": tricky,
        "common_exam_mistakes": _common_mistakes(is_ar),
        "study_priority_order": [
            {"rank": i+1, "topic": kw, "action": f"Memorize definition + practice questions" if not is_ar else f"احفظ التعريف + تدرب على الأسئلة"}
            for i, kw in enumerate(keywords[:10])
        ],
    }


def _extract_defs(text, lang):
    pattern = _RE_DEF_AR if lang == "ar" else _RE_DEF_EN
    defs = []
    seen = set()
    for m in re.finditer(pattern, text):
        d = m.group(1).strip()
        key = d[:60].lower()
        if key not in seen:
            seen.add(key)
            kw = _keywords(d, min_freq=1, top_n=1)
            defs.append({"term": kw[0] if kw else "concept", "definition": d[:250]})
        if len(defs) >= 12:
            break
    return defs


def _find_tricky_points(comparisons, definitions, is_ar):
    tricky = []
    for _, ctx in comparisons[:3]:
        tricky.append({"point": ctx[:200], "why_tricky": "Compare/contrast questions are common trap sources" if not is_ar else "أسئلة المقارنة مصدر شائع للفخاخ"})
    if len(definitions) >= 2:
        d1, d2 = definitions[0], definitions[1]
        tricky.append({"point": f"'{d1['term']}' vs '{d2['term']}' — similar concepts that students confuse", "why_tricky": "Teachers love asking the difference between similar terms" if not is_ar else "المعلمون يحبون سؤال الفرق بين المصطلحات المتشابهة"})
    return tricky[:6]


def _common_mistakes(is_ar):
    if is_ar:
        return [
            "الخلط بين المصطلحات المتشابهة", "حفظ التعريف بدون فهم التطبيق",
            "تجاهل الاستثناءات المذكورة", "عدم التدرب على أسئلة المقارنة",
            "إهمال القوائم والخطوات المرتبة",
        ]
    return [
        "Confusing similar-sounding terms", "Memorizing definition without understanding application",
        "Ignoring exceptions mentioned in text", "Not practicing comparison questions",
        "Skipping ordered lists and step-by-step processes",
    ]


def _analyze_teacher(textbook, past_exams, lecture_notes, all_kw, tb_kw, pe_kw, lang, is_ar, has_exams):
    definitions = _extract_defs(textbook, lang)
    comparisons = len(_RE_COMPARE.findall(textbook + " " + past_exams))
    lists = len(_RE_LIST.findall(textbook))
    sentences = _sentences(textbook)

    def_ratio = len(definitions) / max(len(sentences) / 10, 1)
    comp_ratio = comparisons / max(len(sentences), 1)

    if is_ar:
        if def_ratio > 0.5:
            style = "تعريفي — يركز المعلم على المصطلحات والتعاريف"
        elif comp_ratio > 0.15:
            style = "مقارن — يفضل المعلم أسئلة المقارنة"
        else:
            style = "متوازن"
    else:
        if def_ratio > 0.5:
            style = "Definition-heavy — teacher emphasizes precise terminology"
        elif comp_ratio > 0.15:
            style = "Comparative — teacher favors compare-and-contrast"
        else:
            style = "Balanced"

    qtypes = _infer_question_types(definitions, comparisons, lists, has_exams, is_ar)
    cross = list(tb_kw & pe_kw) if has_exams else list(tb_kw)[:10]
    emphasis = _EMPHASIS_AR if is_ar else _EMPHASIS_EN
    repeated = []
    for kw in list(all_kw)[:15]:
        count = (textbook + " " + past_exams).lower().count(kw.lower())
        signaled = bool(emphasis.search((textbook + " " + past_exams)))
        if count >= 3 or signaled:
            repeated.append({"concept": kw, "frequency": count, "explicitly_signaled": signaled})

    difficulty = _estimate_difficulty(all_kw, textbook + " " + past_exams)

    return {
        "teaching_style": style,
        "question_style": qtypes,
        "difficulty_bias": difficulty,
        "repetition_patterns": repeated[:10],
        "likely_exam_question_count": min(15, max(5, len(all_kw) // 2)),
        "cross_source_favorites": cross[:8],
        "emphasis_triggers_detected": len([m for m in emphasis.finditer(textbook + " " + past_exams)]),
    }


def _infer_question_types(definitions, comparisons, lists, has_exams, is_ar):
    def_count = len(definitions) if isinstance(definitions, list) else definitions
    comp_count = comparisons if isinstance(comparisons, int) else len(comparisons)
    list_count = lists if isinstance(lists, int) else len(lists)
    types = []
    if has_exams:
        types.append({"type": "MCQ + Short Answer" if not is_ar else "اختياري + قصير", "weight": 45})
        types.append({"type": "Essay" if not is_ar else "مقالي", "weight": 30})
        types.append({"type": "Problem Solving" if not is_ar else "حل مسائل", "weight": 25})
    else:
        types.append({"type": "Short Answer" if not is_ar else "إجابة قصيرة", "weight": 40})
        types.append({"type": "MCQ" if not is_ar else "اختياري", "weight": 35})
        types.append({"type": "Essay" if not is_ar else "مقالي", "weight": 25})
    return types


def _estimate_difficulty(keywords, text):
    text_lower = text.lower()
    freq = Counter()
    for kw in keywords:
        freq[kw] = text_lower.count(kw.lower())
    if not freq:
        return "Medium"
    max_f = max(freq.values())
    high_count = sum(1 for kw in keywords if freq[kw] / max_f > 0.5)
    ratio = high_count / max(len(keywords), 1)
    if ratio > 0.5:
        return "Easy-biased" 
    elif ratio > 0.25:
        return "Medium"
    return "Hard-biased"


def _predict_weighted_exam(all_kw, tb_kw, pe_kw, teacher_fp, textbook, past_exams, lang, is_ar, has_exams):
    definitions = _extract_defs(textbook, lang)
    cross = list(set(all_kw) & tb_kw & pe_kw) if has_exams else list(tb_kw)[:10]
    exam_only = list(pe_kw - tb_kw) if has_exams else []
    tb_only = list(tb_kw - pe_kw) if has_exams else []

    questions = []
    seen = set()

    # PAST EXAMS WEIGHT: 50%
    for concept in (cross + exam_only)[:6]:
        if concept in seen:
            continue
        seen.add(concept)
        score = 95 if concept in cross else 75
        q = _build_exam_question(concept, score, "past_exam_match", definitions, textbook, is_ar)
        questions.append(q)

    # TEACHER BEHAVIOR WEIGHT: 30%
    rep = teacher_fp.get("repetition_patterns", [])
    for r in rep:
        concept = r["concept"]
        if concept in seen:
            continue
        seen.add(concept)
        score = 80 if r.get("explicitly_signaled") else 65
        q = _build_exam_question(concept, score, "teacher_emphasis", definitions, textbook, is_ar)
        questions.append(q)
        if len([q for q in questions if q.get("source") == "teacher_emphasis"]) >= 4:
            break

    # TEXTBOOK WEIGHT: 20%
    for concept in tb_only[:4]:
        if concept in seen:
            continue
        seen.add(concept)
        q = _build_exam_question(concept, 40, "textbook_only", definitions, textbook, is_ar)
        questions.append(q)

    questions.sort(key=lambda x: x["probability"], reverse=True)
    return questions[:15]


def _build_exam_question(concept, base_score, source, definitions, textbook, is_ar):
    contexts = [s[:150] for s in _sentences(textbook) if concept.lower() in s.lower()]
    context = contexts[0] if contexts else concept
    is_defined = any(concept.lower() in d["definition"].lower() for d in definitions)

    if is_ar:
        if is_defined:
            question = f'عرف "{concept}" واشرح أهميته حسب المادة.'
        else:
            question = f'ناقش مفهوم "{concept}" مع ذكر الأمثلة من النص.'
        reason_map = {
            "past_exam_match": f'سبب: ظهر في اختبارات سابقة — تكرار بنسبة عالية ({base_score}%).',
            "teacher_emphasis": f'سبب: المعلم ركز على "{concept}" في المحاضرات ({base_score}%).',
            "textbook_only": f'سبب: موجود في الكتاب لكن لم يظهر في اختبارات سابقة ({base_score}%).',
        }
    else:
        if is_defined:
            question = f'Define "{concept}" and explain its significance as presented in the material.'
        else:
            question = f'Discuss the concept of "{concept}" with examples from the text.'
        reason_map = {
            "past_exam_match": f'Reason: Appeared in past exams — high repetition probability ({base_score}%).',
            "teacher_emphasis": f'Reason: Teacher emphasized "{concept}" in lectures ({base_score}%).',
            "textbook_only": f'Reason: Present in textbook but not in past exams ({base_score}%).',
        }

    qtype = "Short Answer" if not is_ar else "إجابة قصيرة"
    if base_score >= 80:
        qtype = "Essay" if not is_ar else "مقالي"
    elif base_score <= 50:
        qtype = "MCQ" if not is_ar else "اختيار من متعدد"

    return {
        "question": question,
        "type": qtype,
        "probability": base_score,
        "answer_guidance": f"Key concept: {concept}. Context: {context}" if not is_ar else f"المفهوم: {concept}. السياق: {context}",
        "reason": reason_map.get(source, ""),
        "source": source,
    }


def _cross_validate(predictions, teacher_fp, exam_material, all_kw, is_ar):
    report = {"checks": [], "removed": [], "adjusted": [], "verified": 0, "total": len(predictions)}

    must_know_terms = {m["concept"].lower() for m in exam_material["must_know"]}
    teacher_favs = {t["concept"].lower() for t in teacher_fp.get("repetition_patterns", [])}
    difficulty = teacher_fp.get("difficulty_bias", "Medium")

    validated = []
    for q in predictions:
        concept_words = set(q.get("answer_guidance", "").lower().split())
        concept_match = any(kw in concept_words for kw in must_know_terms)

        if concept_match:
            q["probability"] = min(100, q["probability"] + 5)
            report["adjusted"].append(f"Boosted '{q['question'][:40]}...' — matches must-know list")
            report["verified"] += 1
        elif q["probability"] < 45 and not concept_match:
            q["probability"] = max(5, q["probability"] - 10)
            report["adjusted"].append(f"Reduced '{q['question'][:40]}...' — low confidence, no must-know match")

        if q["probability"] >= 30:
            validated.append(q)
        else:
            report["removed"].append(f"Removed: '{q['question'][:40]}...' — below threshold")

    report["checks"].append(f"Consistency: {'PASS' if report['verified'] > 0 else 'LOW'}")
    report["checks"].append(f"Teacher-difficulty alignment: {difficulty}")
    report["checks"].append(f"Cross-source verified questions: {report['verified']}/{report['total']}")

    return {"questions": validated[:12], "report": report}


def _calc_confidence(validated, has_exams, cross_count):
    base = 35
    if has_exams:
        base += 30
    if cross_count > 3:
        base += min(20, cross_count * 2)
    verified = validated["report"]["verified"]
    if verified >= 3:
        base += 15
    return min(98, base)
