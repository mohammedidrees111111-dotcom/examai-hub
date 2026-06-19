import re
import random
from typing import Optional
from collections import Counter

_RE_AR = re.compile(r'[\u0600-\u06FF]')
_RE_EN = re.compile(r'[a-zA-Z]')
_RE_WORDS = re.compile(r'[\u0600-\u06FFa-zA-Z]{3,}')
_RE_SENTENCE = re.compile(r'[.!?\n،؛؟\r]+')
_RE_DEFINITION_EN = re.compile(
    r'(?:is\s+defined\s+as|refers\s+to|is\s+a\s+form\s+of|means\s+that|is\s+the\s+process\s+of|'
    r'is\s+a\s+type\s+of|is\s+an?\s+|are\s+the\s+|consists?\s+of|comprises?\s+|involves?\s+)'
    r'(.{15,200}?)(?:[.!\n]|$)', re.IGNORECASE
)
_RE_DEFINITION_AR = re.compile(
    r'(?:هو|تعرف|يعرف|يقصد به|تعني|يقصد ب|المقصود بـ|عبارة عن|تتكون من|تشمل|تتمثل في)'
    r'(.{15,200}?)(?:[.؛!\n]|$)', re.IGNORECASE
)
_RE_LIST = re.compile(r'(?:^|\n)\s*(?:[\d]+[\.\)]\s+|[•\-\*\✓\✔\→]\s+)(.+?)(?:\n|$)', re.MULTILINE)
_RE_COMPARISON = re.compile(
    r'(?:unlike|whereas|while|in contrast|compared to|differs from|better than|'
    r'worse than|more than|less than|similar to|same as|however|on the other hand)',
    re.IGNORECASE
)
_RE_FORMULA = re.compile(r'[=+\-*/^∑∏∫√∞≈≠≤≥±→⇒⇔∇∂]')
_RE_EXCEPTION = re.compile(
    r'(?:however|but|except|unless|although|though|despite|notwithstanding|'
    r'on the contrary|interestingly|surprisingly|notably)',
    re.IGNORECASE
)

AR_STOP = frozenset({
    "في", "من", "على", "الى", "عن", "هذا", "هذه", "هو", "هي", "هم", "هن",
    "أن", "ان", "كان", "كل", "بعض", "بين", "مع", "بعد", "قبل", "خلال",
    "حول", "عند", "ليس", "لم", "لن", "لا", "ما", "ذلك", "تلك", "الذي",
    "التي", "هناك", "حتى", "أيضا", "فقط", "قد", "سوف", "يمكن", "يجب",
})
EN_STOP = frozenset({
    "the", "and", "for", "are", "but", "not", "you", "all", "any", "had",
    "this", "that", "with", "from", "they", "have", "been", "were", "which",
    "about", "would", "could", "should", "what", "when", "where", "there",
})
ALL_STOP = AR_STOP | EN_STOP


def _lang(text: str) -> str:
    return "ar" if len(_RE_AR.findall(text[:2000])) > len(_RE_EN.findall(text[:2000])) else "en"


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in _RE_SENTENCE.split(text) if len(s.strip()) > 10]


def _keywords(text: str, min_freq: int = 2, top_n: int = 50) -> list[str]:
    words = _RE_WORDS.findall(text.lower())
    lang = _lang(text)
    min_len = 3 if lang == "ar" else 4
    filtered = [w for w in words if len(w) >= min_len and w not in ALL_STOP]
    if not filtered:
        return []
    freq = Counter(filtered)
    result = [w for w, c in freq.most_common(top_n) if c >= min_freq]
    return sorted(result, key=lambda w: (freq[w], len(w)), reverse=True)


def _extract_definitions(text: str, lang: str) -> list[dict]:
    pattern = _RE_DEFINITION_AR if lang == "ar" else _RE_DEFINITION_EN
    definitions = []
    seen = set()
    for m in re.finditer(pattern, text):
        d = m.group(1).strip()
        key = d[:80].lower()
        if key not in seen:
            seen.add(key)
            kw = _keywords(d, min_freq=1, top_n=1)
            definitions.append({"term": kw[0] if kw else "concept", "definition": d[:250]})
        if len(definitions) >= 15:
            break

    if not definitions:
        sentences = _sentences(text)
        for s in sentences[:20]:
            kw = _keywords(s, min_freq=1, top_n=1)
            if kw:
                definitions.append({"term": kw[0], "definition": s[:250]})
            if len(definitions) >= 8:
                break

    return definitions[:15]


def _extract_lists(text: str) -> list[str]:
    items = []
    for m in _RE_LIST.finditer(text):
        item = m.group(1).strip()
        if 10 < len(item) < 200 and item not in items:
            items.append(item)
    return items[:20]


def _extract_comparisons(text: str) -> list[dict]:
    matches = []
    for m in _RE_COMPARISON.finditer(text):
        start = max(0, m.start() - 50)
        end = min(len(text), m.end() + 150)
        context = text[start:end].strip()
        matches.append({"trigger": m.group(), "context": context[:250]})
    return matches[:10]


def _extract_exceptions(text: str) -> list[str]:
    exceptions = []
    for m in _RE_EXCEPTION.finditer(text):
        start = m.start()
        end = min(len(text), start + 200)
        context = text[start:end].strip()
        exc = _sentences(context)
        if exc:
            exceptions.append(exc[0][:200])
    seen = set()
    unique = []
    for e in exceptions:
        key = e[:60]
        if key not in seen:
            seen.add(key)
            unique.append(e)
    return unique[:10]


def _rank_importance(keywords: list[str], text: str) -> list[dict]:
    text_lower = text.lower()
    freq = Counter()
    for kw in keywords:
        freq[kw] = text_lower.count(kw.lower())

    if not freq:
        return []

    max_f = max(freq.values())
    ranked = []

    for kw in keywords[:30]:
        f = freq[kw]
        ratio = f / max_f
        if ratio > 0.6:
            imp = "high"
        elif ratio > 0.25:
            imp = "medium"
        else:
            imp = "low"

        contexts = []
        for s in _sentences(text):
            if kw.lower() in s.lower():
                contexts.append(s[:150])
            if len(contexts) >= 2:
                break

        ranked.append({"concept": kw, "frequency": f, "importance": imp, "context": contexts})

    return ranked[:20]


def generate_exam_prep(text: str) -> dict:
    text = text.strip()
    lang = _lang(text)
    is_ar = lang == "ar"

    keywords = _keywords(text, min_freq=2, top_n=60)
    if not keywords:
        keywords = _keywords(text, min_freq=1, top_n=60)

    definitions = _extract_definitions(text, lang)
    lists = _extract_lists(text)
    comparisons = _extract_comparisons(text)
    exceptions = _extract_exceptions(text)
    ranked = _rank_importance(keywords, text)
    questions = _generate_all_questions(text, keywords, definitions, lists, comparisons, ranked, lang, is_ar)
    tricky = _generate_trick_questions(keywords, definitions, text, lang, is_ar)
    teacher_traps = _detect_teacher_traps(comparisons, exceptions, text, lang, is_ar)
    revision_sheet = _build_revision_sheet(keywords, definitions, ranked, lists, lang, is_ar)

    high_yield = [r for r in ranked if r["importance"] in ("high", "medium")][:10]

    return {
        "document_stats": {
            "total_words": len(text.split()),
            "key_concepts_found": len(keywords),
            "definitions_extracted": len(definitions),
            "comparisons_detected": len(comparisons),
            "exceptions_found": len(exceptions),
        },
        "high_yield_topics": [r["concept"] for r in high_yield],
        "definition_focus_list": definitions,
        "likely_exam_questions": questions["standard"],
        "essay_questions": questions["essay"],
        "problem_solving_questions": questions["problem"],
        "tricky_questions": tricky,
        "teacher_trap_patterns": teacher_traps,
        "difficulty_map": {
            "easy": [r["concept"] for r in ranked if r["importance"] == "low"][:8],
            "medium": [r["concept"] for r in ranked if r["importance"] == "medium"][:8],
            "hard": [r["concept"] for r in ranked if r["importance"] == "high"][:8],
        },
        "revision_sheet": revision_sheet,
        "language": lang,
    }


def _generate_all_questions(text, keywords, definitions, lists, comparisons, ranked, lang, is_ar):
    standard = []
    essay = []
    problem = []

    # MCQ
    mcq_count = min(8, len(ranked))
    for i, r in enumerate(ranked[:mcq_count]):
        q = _make_mcq(r, keywords, lang, is_ar)
        if q:
            standard.append(q)

    # Short answer
    for d in definitions[:4]:
        q = _make_short_answer(d, lang, is_ar)
        if q:
            standard.append(q)

    # From lists
    for item in lists[:3]:
        q = _make_list_question(item, lang, is_ar)
        if q:
            standard.append(q)

    # Essay questions
    if len(comparisons) >= 2:
        c = comparisons[0]
        essay.append(_make_essay_comparison(c, lang, is_ar))
    for r in ranked[:2]:
        essay.append(_make_essay_concept(r, lang, is_ar))

    # Problem-solving
    for d in definitions[:3]:
        problem.append(_make_problem_question(d, lang, is_ar))
    for item in lists[:2]:
        problem.append(_make_application_question(item, lang, is_ar))

    return {"standard": standard[:15], "essay": essay[:5], "problem": problem[:5]}


def _make_mcq(ranked_item: dict, all_keywords: list[str], lang: str, is_ar: bool) -> Optional[dict]:
    concept = ranked_item["concept"]
    contexts = ranked_item.get("context", [])
    context = contexts[0] if contexts else concept

    wrong = _make_distractors(concept, all_keywords)
    correct_answer = concept

    if is_ar:
        question = f'ما أفضل وصف للمصطلح "{concept}" حسب النص؟'
        explanation_correct = f'"{concept}" هو المصطلح الصحيح لأنه يرتبط مباشرة بـ: {context[:100]}'
        explanation_wrong = "الخيارات الأخرى غير صحيحة لأنها تشير إلى مفاهيم مختلفة غير مرتبطة مباشرة بهذا السياق."
    else:
        question = f'Which of the following best describes "{concept}" based on the text?'
        explanation_correct = f'"{concept}" is correct because it directly relates to: {context[:100]}'
        explanation_wrong = "Other options are incorrect because they refer to different concepts not directly supported by this context."

    options = wrong + [correct_answer]
    random.shuffle(options)
    return {
        "type": "mcq",
        "question": question,
        "options": options[:4],
        "correct_answer": correct_answer,
        "explanation": {
            "why_correct": explanation_correct,
            "why_others_wrong": explanation_wrong,
        },
    }


def _make_short_answer(definition: dict, lang: str, is_ar: bool) -> Optional[dict]:
    term = definition["term"]
    defn = definition["definition"]
    keywords_in_def = _keywords(defn, min_freq=1, top_n=2)

    if is_ar:
        question = f'عرف "{term}" حسب ما ورد في النص.'
        answer = defn[:250]
        explanation = f'الإجابة مستخرجة من التعريف الوارد في النص. المصطلحات الأساسية: {", ".join(keywords_in_def[:3])}.'
    else:
        question = f'Define "{term}" as presented in the text.'
        answer = defn[:250]
        explanation = f'Answer derived from the text definition. Key terms: {", ".join(keywords_in_def[:3])}.'

    return {
        "type": "short_answer",
        "question": question,
        "correct_answer": answer,
        "explanation": explanation,
    }


def _make_list_question(item: str, lang: str, is_ar: bool) -> Optional[dict]:
    if is_ar:
        question = f'اذكر: {item[:80]} مع تفسير موجز.'
        answer = item[:250]
    else:
        question = f'List and briefly explain: {item[:80]}'
        answer = item[:250]

    return {
        "type": "short_answer",
        "question": question,
        "correct_answer": answer,
        "explanation": "Answer directly from the text. The listed item provides the key points needed.",
    }


def _make_essay_comparison(comparison: dict, lang: str, is_ar: bool) -> dict:
    trigger = comparison["trigger"]
    context = comparison["context"]

    if is_ar:
        question = f'قارن بين المفاهيم المذكورة في هذا السياق: "{context[:150]}" مع ذكر أوجه التشابه والاختلاف.'
    else:
        question = f'Compare and contrast the concepts discussed in this passage: "{context[:150]}" Discuss similarities and differences with specific examples from the text.'

    return {
        "type": "essay",
        "question": question,
        "guidance": {
            "key_points": [trigger, "similarities", "differences", "examples from text"],
            "suggested_length": "250-500 words" if not is_ar else "250-500 كلمة",
        },
    }


def _make_essay_concept(ranked_item: dict, lang: str, is_ar: bool) -> dict:
    concept = ranked_item["concept"]
    contexts = ranked_item.get("context", [])

    if is_ar:
        question = f'ناقش مفهوم "{concept}" بالتفصيل. اشرح أهميته، تطبيقاته، وعلاقته بالمفاهيم الأخرى في النص.'
    else:
        question = f'Discuss "{concept}" in detail. Explain its significance, applications, and how it relates to other concepts in the text.'

    return {
        "type": "essay",
        "question": question,
        "guidance": {
            "key_points": [concept, "significance", "applications", "relationships to other concepts"],
            "suggested_length": "300-600 words" if not is_ar else "300-600 كلمة",
            "context": contexts[:2],
        },
    }


def _make_problem_question(definition: dict, lang: str, is_ar: bool) -> dict:
    term = definition["term"]

    if is_ar:
        question = f'قدم مثالا عمليا يطبق فيه مفهوم "{term}". اشرح خطوات التطبيق والنتيجة المتوقعة.'
    else:
        question = f'Provide a practical example applying the concept of "{term}". Show the steps and expected outcome.'

    return {
        "type": "problem_solving",
        "question": question,
        "approach": f"1. Define {term}. 2. Identify a scenario. 3. Apply {term} to scenario. 4. Predict outcome.",
    }


def _make_application_question(item: str, lang: str, is_ar: bool) -> dict:
    if is_ar:
        question = f'كيف يمكن تطبيق: "{item[:100]}" في سيناريو واقعي؟ اشرح بمثال.'
    else:
        question = f'How would you apply: "{item[:100]}" in a real-world scenario? Explain with an example.'

    return {
        "type": "problem_solving",
        "question": question,
        "approach": "1. Understand the concept. 2. Choose relevant scenario. 3. Apply step by step. 4. Discuss implications.",
    }


def _generate_trick_questions(keywords, definitions, text, lang, is_ar):
    tricky = []
    if len(keywords) < 3:
        return tricky

    # Trick 1: Similar concept confusion
    for i in range(min(3, len(keywords) - 1)):
        kw1 = keywords[i]
        kw2 = keywords[i + 1] if i + 1 < len(keywords) else keywords[0]

        if is_ar:
            q = f'أي العبارات التالية صحيحة: "{kw1}" و "{kw2}" هما نفس المفهوم.'
        else:
            q = f'True or False: "{kw1}" and "{kw2}" refer to the same concept in the text.'

        tricky.append({
            "type": "trick_true_false",
            "question": q,
            "correct_answer": "False - they are distinct concepts in the text.",
            "trap_explanation": "Professor trap: similar-sounding terms are often confused. Always check precise definitions.",
        })

    # Trick 2: Exception questions
    for exc in _extract_exceptions(text)[:2]:
        if is_ar:
            q = f'حسب النص: "{exc[:120]}" — ما الاستثناء المهم المذكور هنا؟'
        else:
            q = f'The text states: "{exc[:120]}" — what is the critical exception mentioned?'

        tricky.append({
            "type": "trick_exception",
            "question": q,
            "correct_answer": "The exception challenges the general rule - students who miss exceptions lose marks.",
            "trap_explanation": "Teachers love testing exceptions to general rules. Always note the 'however' and 'except' parts.",
        })

    return tricky[:6]


def _detect_teacher_traps(comparisons, exceptions, text, lang, is_ar):
    traps = []

    if comparisons:
        traps.append({
            "pattern": "Comparison confusion",
            "description": "Teachers ask to compare concepts — students who only define one lose half the marks.",
            "found_in_text": comparisons[0]["trigger"],
        })

    if exceptions:
        traps.append({
            "pattern": "Exception questions",
            "description": "Teachers ask 'what is the exception to...' — most students only memorize the rule.",
            "found_in_text": exceptions[0][:100],
        })

    if is_ar:
        traps.append({
            "pattern": "تسلسل الخطوات",
            "description": "يطلب الأستاذ ترتيب الخطوات بالترتيب الصحيح — معظم الطلاب يخلطون الترتيب.",
        })
        traps.append({
            "pattern": "التعاريف الدقيقة",
            "description": "أسئلة 'عرف' تتطلب الدقة في المصطلحات — الإجابات التقريبية لا تحصل على الدرجة الكاملة.",
        })
    else:
        traps.append({
            "pattern": "Sequential steps",
            "description": "Professors ask 'list the steps in order' — most students mix up the sequence.",
        })
        traps.append({
            "pattern": "Precise definitions",
            "description": "'Define' questions require exact terminology — approximate answers don't get full marks.",
        })

    return traps


def _build_revision_sheet(keywords, definitions, ranked, lists, lang, is_ar):
    return {
        "must_memorize": {
            "definitions": [{"term": d["term"], "definition": d["definition"][:150]} for d in definitions[:10]],
            "key_terms": keywords[:15],
        },
        "must_understand": {
            "concepts": [r["concept"] for r in ranked if r["importance"] == "high"][:8],
            "relationships": [f"{keywords[i]} ↔ {keywords[i + 1]}" for i in range(0, min(8, len(keywords) - 1), 2)],
        },
        "must_practice": {
            "apply_concepts": [r["concept"] for r in ranked if r["importance"] in ("high", "medium")][:6],
            "list_items": lists[:6],
        },
        "quick_review_cards": [{"term": d["term"], "definition": d["definition"][:120]} for d in definitions[:8]],
        "exam_tips": [
            "Focus on definitions — they appear in 40%+ of exam questions" if not is_ar else "ركز على التعاريف — تظهر في 40%+ من أسئلة الامتحان",
            "Practice comparison questions — professors love them" if not is_ar else "تدرب على أسئلة المقارنة — الأساتذة يفضلونها",
            "Note all exceptions and 'however' statements" if not is_ar else "لاحظ جميع الاستثناءات وعبارات 'لكن' و'غير'",
            "Create mind maps connecting concepts" if not is_ar else "أنشئ خرائط ذهنية تربط المفاهيم",
        ],
    }


def _make_distractors(correct: str, all_keywords: list[str]) -> list[str]:
    candidates = [k for k in all_keywords if k.lower() != correct.lower()]
    random.shuffle(candidates)
    return candidates[:3]
