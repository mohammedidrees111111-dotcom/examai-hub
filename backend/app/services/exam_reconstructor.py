import re
import random
from typing import Optional
from collections import Counter

_RE_AR = re.compile(r'[\u0600-\u06FF]')
_RE_EN = re.compile(r'[a-zA-Z]')
_RE_WORDS = re.compile(r'[\u0600-\u06FFa-zA-Z]{3,}')
_RE_SENTENCE = re.compile(r'[.!?\n،؛؟\r]+')
_RE_QUESTION = re.compile(
    r'(?:^|\n)\s*(?:\d+[\.\)]\s*)?(?:What|Which|How|Why|When|Where|Who|Explain|Describe|Define|List|'
    r'Compare|Contrast|Discuss|Analyze|Evaluate|Calculate|Solve|Prove|State|Name|Identify|'
    r'Give|Provide|Outline|Summarize|True or False|T/F|MCQ|Multiple Choice|'
    r'ما|كيف|لماذا|متى|أين|من|اشرح|عرف|قارن|ناقش|حلل|احسب|اذكر|عدد|'
    r'أعط|قدم|لخص|صح أم خطأ|اختيار من متعدد)',
    re.IGNORECASE
)
_RE_QUESTION_TYPE = re.compile(
    r'(MCQ|Multiple Choice|Short Answer|Essay|Problem|T/F|True False|'
    r'صح وخطأ|اختيار|مقالي|مسألة|حل|اشرح|عرف)',
    re.IGNORECASE
)

EN_STOP = frozenset({
    "the","and","for","are","but","not","you","all","any","had","this","that",
    "with","from","they","have","been","were","which","about","would","could",
})
AR_STOP = frozenset({
    "في","من","على","عن","هذا","هذه","هو","هي","هم","كل","بعض","بين",
    "مع","بعد","قبل","خلال","حول","عند","ليس","لم","لن","لا","ما","ذلك",
})
ALL_STOP = AR_STOP | EN_STOP


def _lang(text: str) -> str:
    return "ar" if len(_RE_AR.findall(text[:2000])) > len(_RE_EN.findall(text[:2000])) else "en"


def _keywords(text: str, min_freq: int = 1, top_n: int = 60) -> list[str]:
    words = _RE_WORDS.findall(text.lower())
    lang = _lang(text)
    min_len = 3 if lang == "ar" else 4
    filtered = [w for w in words if len(w) >= min_len and w not in ALL_STOP]
    if not filtered:
        return []
    freq = Counter(filtered)
    return [w for w, c in freq.most_common(top_n) if c >= min_freq]


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in _RE_SENTENCE.split(text) if len(s.strip()) > 10]


def reconstruct_exam(textbook: str, past_exams: str = "", lecture_notes: str = "") -> dict:
    lang = _lang(textbook)
    is_ar = lang == "ar"

    tb_text = textbook.strip()
    pe_text = (past_exams or "").strip()
    ln_text = (lecture_notes or "").strip()

    has_exams = len(pe_text) > 50
    has_notes = len(ln_text) > 50

    tb_kw = set(_keywords(tb_text, min_freq=2, top_n=80))
    pe_kw = set(_keywords(pe_text, min_freq=1, top_n=60)) if has_exams else set()
    ln_kw = set(_keywords(ln_text, min_freq=1, top_n=60)) if has_notes else set()

    all_topics = tb_kw | pe_kw | ln_kw

    alignment = _align_sources(tb_kw, pe_kw, ln_kw, has_exams, has_notes)
    exam_patterns = _mine_exam_patterns(pe_text, lang, is_ar) if has_exams else _infer_patterns(tb_text, lang, is_ar)
    teacher_model = _model_teacher(pe_text, pe_kw, alignment, exam_patterns, lang, is_ar) if has_exams else {}
    reconstruction = _reconstruct_exam_questions(
        alignment, exam_patterns, teacher_model, tb_text, pe_text, ln_text, lang, is_ar, has_exams
    )

    confidence = _calculate_confidence(has_exams, has_notes, len(alignment["cross_source"]), len(all_topics))

    return {
        "exam_prediction_confidence": confidence,
        "source_analysis": {
            "textbook_topics": len(tb_kw),
            "past_exam_topics": len(pe_kw),
            "lecture_topics": len(ln_kw),
            "cross_source_topics": len(alignment["cross_source"]),
        },
        "source_alignment": alignment,
        "exam_patterns_mined": exam_patterns,
        "teacher_behavior_model": teacher_model or _default_teacher_model(is_ar),
        "top_high_probability_topics": alignment["cross_source"][:12],
        "exam_only_topics": alignment["exam_only"][:8],
        "predicted_exam": reconstruction["questions"],
        "trick_questions": reconstruction["tricks"],
        "repeated_patterns_detected": reconstruction["patterns"],
        "last_minute_revision_sheet": _build_revision(alignment, exam_patterns, is_ar),
        "language": lang,
    }


def _align_sources(tb_kw, pe_kw, ln_kw, has_exams, has_notes):
    cross = list(tb_kw & pe_kw) if has_exams else list(tb_kw)
    if has_notes:
        cross = list(set(cross) | (tb_kw & ln_kw) | (pe_kw & ln_kw))

    cross_sorted = sorted(cross, key=lambda k: len(k), reverse=True)

    exam_only = list(pe_kw - tb_kw) if has_exams else []
    textbook_only = list(tb_kw - pe_kw - ln_kw) if has_exams else list(tb_kw)
    lecture_unique = list(ln_kw - tb_kw - pe_kw) if has_notes else []

    return {
        "cross_source": cross_sorted[:25],
        "exam_only": exam_only[:10],
        "textbook_only": textbook_only[:15],
        "lecture_unique": lecture_unique[:8],
        "statistics": {
            "total_unique_topics": len(tb_kw | pe_kw | ln_kw),
            "overlap_percentage": round(len(cross_sorted) / max(len(tb_kw | pe_kw | ln_kw), 1) * 100),
        },
    }


def _mine_exam_patterns(pe_text, lang, is_ar):
    if not pe_text or len(pe_text) < 50:
        return _default_patterns(is_ar)

    questions = _extract_questions(pe_text)
    qtypes = _classify_question_types(questions, lang) if questions else _default_patterns(is_ar)["question_distribution"]

    templates = _find_question_templates(questions, lang)
    repeated = _find_repeated_questions(questions)
    difficulty = _analyze_difficulty(questions)

    return {
        "total_exam_questions_found": len(questions),
        "question_distribution": qtypes,
        "repeated_templates": templates[:8],
        "repeated_questions": repeated[:6],
        "difficulty_analysis": difficulty,
        "question_generation_strategy": _build_strategy(qtypes, templates, is_ar),
    }


def _extract_questions(text):
    questions = []
    for m in _RE_QUESTION.finditer(text):
        start = m.start()
        end = text.find("\n\n", start)
        if end == -1:
            end = min(start + 300, len(text))
        qtext = text[start:end].strip()
        if len(qtext) > 15:
            questions.append(qtext)
    if not questions:
        sentences = _sentences(text)
        questions = sentences[:20]
    return questions


def _classify_question_types(questions, lang):
    types = Counter()
    for q in questions:
        ql = q.lower()
        if re.search(r'(mcq|multiple choice|اختيار|صح وخطأ|true false|t/f)', ql):
            types["MCQ"] += 1
        elif re.search(r'(essay|discuss|analyze|مقالي|ناقش|حلل)', ql):
            types["Essay"] += 1
        elif re.search(r'(solve|calculate|problem|prove|احسب|مسألة|برهن)', ql):
            types["Problem Solving"] += 1
        elif re.search(r'(short answer|explain|describe|define|list|اشرح|عرف|اذكر|عدد)', ql):
            types["Short Answer"] += 1
        else:
            types["Mixed"] += 1

    total = max(sum(types.values()), 1)
    return {k: round(v / total * 100) for k, v in types.most_common()}


def _find_question_templates(questions, lang):
    templates = []
    seen = set()
    for q in questions:
        normalized = re.sub(r'\b\w+\b', '___', q.lower())[:80]
        if normalized not in seen:
            seen.add(normalized)
            templates.append({"template": q[:150], "pattern": normalized[:60]})
    return templates


def _find_repeated_questions(questions):
    if len(questions) < 2:
        return []
    repeated = []
    for i, q1 in enumerate(questions):
        for q2 in questions[i + 1:]:
            q1w = set(q1.lower().split())
            q2w = set(q2.lower().split())
            if q1w and q2w:
                overlap = len(q1w & q2w) / max(len(q1w | q2w), 1)
                if overlap > 0.5:
                    repeated.append({"q1": q1[:100], "q2": q2[:100], "similarity": round(overlap * 100)})
            if len(repeated) >= 4:
                break
        if len(repeated) >= 4:
            break
    return repeated


def _analyze_difficulty(questions):
    if not questions:
        return {"easy": 30, "medium": 50, "hard": 20}

    easy = sum(1 for q in questions if len(q.split()) < 15)
    medium = sum(1 for q in questions if 15 <= len(q.split()) <= 40)
    hard = sum(1 for q in questions if len(q.split()) > 40)
    total = max(easy + medium + hard, 1)
    return {"easy_pct": round(easy / total * 100), "medium_pct": round(medium / total * 100), "hard_pct": round(hard / total * 100)}


def _build_strategy(qtypes, templates, is_ar):
    dominant = max(qtypes.items(), key=lambda x: x[1]) if qtypes else ("Mixed", 100)
    strategy = []
    if is_ar:
        strategy.append(f"نوع الأسئلة السائد: {dominant[0]} ({dominant[1]}%) — ركز تدريبك على هذا النوع")
        if templates:
            strategy.append(f"تم اكتشاف {len(templates)} قالب سؤال — المعلم يعيد استخدام نفس الأنماط")
    else:
        strategy.append(f"Dominant question type: {dominant[0]} ({dominant[1]}%) — focus practice on this type")
        if templates:
            strategy.append(f"{len(templates)} question templates detected — teacher reuses same patterns")
    return strategy


def _model_teacher(pe_text, pe_kw, alignment, exam_patterns, lang, is_ar):
    if not pe_text or len(pe_text) < 50:
        return {}

    cross = alignment.get("cross_source", [])
    exam_only = alignment.get("exam_only", [])

    return {
        "favorite_topics": cross[:8] + exam_only[:4],
        "question_style": exam_patterns.get("question_distribution", {}),
        "repetition_behavior": {
            "repeats_questions": len(exam_patterns.get("repeated_questions", [])) > 0,
            "reuses_templates": len(exam_patterns.get("repeated_templates", [])) > 0,
        },
        "difficulty_preference": exam_patterns.get("difficulty_analysis", {}),
        "inferred_habits": _infer_habits(pe_text, cross, exam_only, is_ar),
    }


def _infer_habits(pe_text, cross, exam_only, is_ar):
    habits = []
    if cross:
        habits.append({
            "habit": "Tests cross-source concepts",
            "evidence": f"Topics like '{cross[0]}' appear in both textbook and exams — high probability repeat",
        })
    if exam_only:
        habits.append({
            "habit": "Has favorite 'surprise' topics",
            "evidence": f"'{exam_only[0]}' appears only in exams — teacher tests beyond the textbook",
        })
    habits.append({
        "habit": "Uses definition-based questions",
        "evidence": "Exam questions ask for precise definitions — memorize key terminology",
    })
    return habits


def _reconstruct_exam_questions(alignment, exam_patterns, teacher_model, tb_text, pe_text, ln_text, lang, is_ar, has_exams):
    cross = alignment.get("cross_source", [])
    exam_only = alignment.get("exam_only", [])
    textbook_only = alignment.get("textbook_only", [])
    qdist = exam_patterns.get("question_distribution", {})
    teacher_favs = teacher_model.get("favorite_topics", cross[:10]) if teacher_model else cross[:10]

    questions = []
    seen_concepts = set()

    # Priority 1: Cross-source topics (book + exam) — VERY HIGH WEIGHT
    for concept in teacher_favs[:6]:
        if concept in seen_concepts:
            continue
        seen_concepts.add(concept)
        source_w = {"textbook_match": concept in set(_keywords(tb_text, min_freq=1)), "past_exam_match": concept in set(_keywords(pe_text, min_freq=1)) if has_exams else False, "lecture_match": concept in set(_keywords(ln_text, min_freq=1))}
        q = _build_question(concept, source_w, tb_text, pe_text, 85, lang, is_ar, "cross-source repeated concept")
        questions.append(q)

    # Priority 2: Exam-only topics — HIGH WEIGHT (teacher favorites)
    for concept in exam_only[:3]:
        if concept in seen_concepts:
            continue
        seen_concepts.add(concept)
        source_w = {"textbook_match": False, "past_exam_match": True, "lecture_match": False}
        q = _build_question(concept, source_w, tb_text, pe_text, 75, lang, is_ar, "exam-only teacher favorite")
        questions.append(q)

    # Priority 3: Textbook-only but emphasized — MEDIUM WEIGHT
    for concept in textbook_only[:3]:
        if concept in seen_concepts:
            continue
        seen_concepts.add(concept)
        source_w = {"textbook_match": True, "past_exam_match": False, "lecture_match": False}
        q = _build_question(concept, source_w, tb_text, pe_text, 55, lang, is_ar, "textbook concept — lower exam probability")
        questions.append(q)

    # Fallback: use textbook keywords
    if len(questions) < 5:
        tb_kw_list = list(set(_keywords(tb_text, min_freq=1, top_n=40)))
        for concept in tb_kw_list:
            if concept in seen_concepts:
                continue
            seen_concepts.add(concept)
            q = _build_question(concept, {"textbook_match": True, "past_exam_match": False, "lecture_match": False}, tb_text, pe_text, 40, lang, is_ar, "textbook content")
            questions.append(q)
            if len(questions) >= 8:
                break

    tricks = _build_trick_questions(cross[:5], is_ar)
    patterns = _detect_repeated_patterns(tb_text, pe_text, cross, has_exams, is_ar)

    return {"questions": questions[:12], "tricks": tricks, "patterns": patterns}


def _build_question(concept, source_w, tb_text, pe_text, base_score, lang, is_ar, reason):
    contexts = []
    for src in [tb_text, pe_text]:
        if src:
            for s in _sentences(src):
                if concept.lower() in s.lower():
                    contexts.append(s[:150])
                    break

    if is_ar:
        question = f'سؤال عن "{concept}": عرف هذا المفهوم واشرح أهميته حسب المادة الدراسية.'
        answer_guide = f'عرف "{concept}" بدقة. اذكر خصائصه وتطبيقاته. استشهد بالمادة.'
        reason_text = f'سبب التوقع: {reason}. تطابق الكتاب: {"نعم" if source_w["textbook_match"] else "لا"}, تطابق الاختبارات السابقة: {"نعم" if source_w["past_exam_match"] else "لا"}.'
    else:
        question = f'Question about "{concept}": Define this concept and explain its significance based on the course material.'
        answer_guide = f'Define "{concept}" precisely. List its characteristics and applications. Cite the course material.'
        reason_text = f'Prediction reason: {reason}. Textbook match: {source_w["textbook_match"]}, Past exam match: {source_w["past_exam_match"]}.'

    score = base_score
    if source_w["past_exam_match"]:
        score = min(98, score + 15)
    if source_w["textbook_match"] and source_w["past_exam_match"]:
        score = min(98, score + 10)

    return {
        "question": question,
        "type": _pick_question_type(source_w, is_ar),
        "answer_guidance": answer_guide,
        "source_weighting": source_w,
        "probability_score": score,
        "reason_this_question_is_likely": reason_text,
    }


def _pick_question_type(source_w, is_ar):
    if source_w["past_exam_match"] and source_w["textbook_match"]:
        return "Essay" if not is_ar else "مقالي"
    elif source_w["past_exam_match"]:
        return "Short Answer" if not is_ar else "إجابة قصيرة"
    return "MCQ" if not is_ar else "اختيار من متعدد"


def _build_trick_questions(concepts, is_ar):
    tricks = []
    for i in range(0, len(concepts) - 1, 2):
        if i + 1 < len(concepts):
            c1, c2 = concepts[i], concepts[i + 1]
            if is_ar:
                tricks.append({"question": f'سؤال فخ: ما الفرق الدقيق بين "{c1}" و "{c2}"؟ غالبا يخلط الطلاب بينهما.', "type": "trap", "guidance": f'ادرس تعريف كل منهما بدقة. "{c1}" يختلف عن "{c2}" في الخصائص الأساسية.'})
            else:
                tricks.append({"question": f'Trap question: What is the exact difference between "{c1}" and "{c2}"? Students often confuse these.', "type": "trap", "guidance": f'Study the precise definition of each. "{c1}" differs from "{c2}" in key characteristics.'})
        if len(tricks) >= 3:
            break
    return tricks


def _detect_repeated_patterns(tb_text, pe_text, cross_topics, has_exams, is_ar):
    patterns = []
    if cross_topics:
        patterns.append({"pattern": "Cross-source repetition", "concepts": cross_topics[:4], "significance": "These concepts appear in multiple sources — extremely high exam probability" if not is_ar else "تظهر في مصادر متعددة — احتمالية ظهورها عالية جدا"})
    if has_exams:
        patterns.append({"pattern": "Exam-driven topics", "explanation": "Topics appearing in past exams are likely to repeat with different wording" if not is_ar else "المواضيع التي ظهرت في اختبارات سابقة من المحتمل تكرارها بصياغة مختلفة"})
    patterns.append({"pattern": "Definition emphasis", "explanation": "Concepts with clear definitions are frequently tested in exams" if not is_ar else "المفاهيم ذات التعريفات الواضحة تختبر بشكل متكرر"})
    return patterns


def _build_revision(alignment, exam_patterns, is_ar):
    cross = alignment.get("cross_source", [])
    exam_only = alignment.get("exam_only", [])

    return {
        "top_priority": cross[:6],
        "exam_favorites": exam_only[:5],
        "study_strategy": [
            "Focus on cross-source topics first — highest exam probability" if not is_ar else "ركز على المواضيع متعددة المصادر أولا — أعلى احتمالية",
            "Memorize definitions for all top-priority concepts" if not is_ar else "احفظ تعريفات جميع مفاهيم الأولوية القصوى",
            "Practice with similar question types to past exams" if not is_ar else "تدرب على أنواع أسئلة مشابهة للاختبارات السابقة",
            "Review exam-only topics — teacher may include surprise questions" if not is_ar else "راجع مواضيع الاختبارات فقط — قد يفاجئك المعلم",
        ],
        "predicted_question_count": len(cross) // 2 + len(exam_only) // 2 + 4,
    }


def _calculate_confidence(has_exams, has_notes, cross_count, total_topics):
    base = 30
    if has_exams:
        base += 35
    if has_notes:
        base += 15
    if cross_count > 5:
        base += min(20, cross_count)
    return min(98, base)


def _default_patterns(is_ar):
    return {
        "total_exam_questions_found": 0,
        "question_distribution": {"MCQ": 40, "Short Answer": 30, "Essay": 20, "Problem Solving": 10},
        "repeated_templates": [],
        "repeated_questions": [],
        "difficulty_analysis": {"easy_pct": 30, "medium_pct": 45, "hard_pct": 25},
        "question_generation_strategy": ["Inferred from textbook structure — no past exams provided"],
    }


def _default_teacher_model(is_ar):
    return {
        "favorite_topics": [],
        "question_style": {},
        "repetition_behavior": {"repeats_questions": False, "reuses_templates": False},
        "difficulty_preference": {},
        "inferred_habits": [{"habit": "Inferred from textbook", "evidence": "No past exams provided — using structural analysis"}],
    }
