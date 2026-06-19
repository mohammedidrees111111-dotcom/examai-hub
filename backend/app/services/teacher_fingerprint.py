import re
import random
from typing import Optional
from collections import Counter

_RE_AR = re.compile(r'[\u0600-\u06FF]')
_RE_EN = re.compile(r'[a-zA-Z]')
_RE_WORDS = re.compile(r'[\u0600-\u06FFa-zA-Z]{3,}')
_RE_SENTENCE = re.compile(r'[.!?\n،؛؟\r]+')

_EMPHASIS_SIGNALS_AR = [
    (r'(?:مهم|هام|ملاحظة|انتبه|تذكر|لاحظ أن|يجب أن|من الضروري|أساسي|جوهري|محوري)', 3.0),
    (r'(?:بمعنى آخر|بعبارة أخرى|باختصار|خلاصة|الزبدة)', 2.5),
    (r'(?:مثال|مثلا|على سبيل المثال|تطبيق|تطبيقي)', 1.5),
    (r'(?:خطوة|مرحلة|أولا|ثانيا|ثالثا)', 2.0),
]
_EMPHASIS_SIGNALS_EN = [
    (r'(?:important|critical|crucial|essential|key|vital|fundamental|significant)', 3.0),
    (r'(?:note that|remember|do not forget|pay attention|you should|you must|be aware)', 3.0),
    (r'(?:in other words|that is|i\.e\.|to clarify|specifically|namely|put simply)', 2.5),
    (r'(?:for example|e\.g\.|instance|illustration|demonstrate|application)', 1.5),
    (r'(?:step|stage|first|second|third|finally|next|then|after that)', 2.0),
    (r'(?:however|but|although|whereas|unlike|in contrast|on the other hand)', 1.5),
    (r'(?:in summary|to summarize|in conclusion|therefore|thus|consequently|as a result)', 2.0),
    (r'(?:always|never|must|required|mandatory|absolutely|certainly|definitely)', 2.5),
]
_RE_DEFINITION_EN = re.compile(
    r'(?:is\s+defined\s+as|refers\s+to|is\s+a\s+form\s+of|means\s+that|is\s+the\s+process\s+of|'
    r'is\s+a\s+type\s+of|is\s+an?\s+|are\s+the\s+|consists?\s+of|comprises?\s+|involves?\s+)'
    r'(.{15,250}?)(?:[.!\n]|$)', re.IGNORECASE
)
_RE_DEFINITION_AR = re.compile(
    r'(?:هو|تعرف|يعرف|يقصد به|تعني|يقصد ب|المقصود بـ|عبارة عن|تتكون من|تشمل|تتمثل في)'
    r'(.{15,250}?)(?:[.؛!\n]|$)', re.IGNORECASE
)
_RE_LIST = re.compile(r'(?:^|\n)\s*(?:[\d]+[\.\)]\s+|[•\-\*\✓\✔\→]\s+)(.+?)(?:\n|$)', re.MULTILINE)
_RE_COMPARISON = re.compile(
    r'(?:unlike|whereas|while|in contrast|compared to|differs from|better than|worse than|'
    r'more than|less than|similar to|same as|however|on the other hand|بينما|مقارنة|على العكس|'
    r'على النقيض|بالمقابل|يختلف عن|يشبه|مشابه)', re.IGNORECASE
)

AR_STOP = frozenset({
    "في", "من", "على", "الى", "عن", "هذا", "هذه", "هو", "هي", "هم", "كل", "بعض", "بين",
    "مع", "بعد", "قبل", "خلال", "حول", "عند", "ليس", "لم", "لن", "لا", "ما", "ذلك",
})
EN_STOP = frozenset({
    "the", "and", "for", "are", "but", "not", "you", "all", "any", "had", "this", "that",
    "with", "from", "they", "have", "been", "were", "which", "about", "would", "could",
})
ALL_STOP = AR_STOP | EN_STOP


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


def analyze_teacher_fingerprint(text: str) -> dict:
    text = text.strip()
    lang = _lang(text)
    is_ar = lang == "ar"
    sentences = _sentences(text)
    total_words = len(text.split())
    keywords = _keywords(text, min_freq=2, top_n=60)
    if not keywords:
        keywords = _keywords(text, min_freq=1, top_n=60)

    fingerprint = _extract_teaching_style(text, sentences, keywords, lang, is_ar)
    emphasis = _extract_emphasis_map(text, keywords, lang, is_ar)
    signals = _extract_exam_signals(text, lang, is_ar)
    patterns = _reconstruct_exam_patterns(text, sentences, keywords, lang, is_ar)
    predictions = _predict_questions(text, keywords, emphasis, signals, patterns, lang, is_ar)
    exam_sim = _build_exam_simulation(predictions, fingerprint, emphasis, signals, patterns, is_ar)

    return {
        "teacher_profile": fingerprint,
        "emphasis_map": emphasis,
        "hidden_exam_signals": signals,
        "exam_pattern_reconstruction": patterns,
        "high_probability_questions": predictions,
        "predicted_exam": exam_sim,
        "document_stats": {"total_words": total_words, "concepts_found": len(keywords), "language": lang},
    }


def _extract_teaching_style(text, sentences, keywords, lang, is_ar):
    definitions = _extract_definitions(text, lang)
    comparisons = len(_RE_COMPARISON.findall(text))
    lists = len(_RE_LIST.findall(text))
    sentences_count = len(sentences)
    if sentences_count == 0:
        sentences_count = 1

    def_ratio = len(definitions) / max(sentences_count / 10, 1)
    comp_ratio = comparisons / max(sentences_count, 1)
    avg_sentence_len = sum(len(s.split()) for s in sentences) / sentences_count

    if is_ar:
        if def_ratio > 0.5:
            style = "تعريفي — يركز المعلم على المصطلحات والتعاريف الدقيقة"
        elif comp_ratio > 0.15:
            style = "مقارن — يفضل المعلم أسئلة المقارنة والتحليل"
        elif avg_sentence_len > 25:
            style = "شرحي — يشرح المعلم بتفصيل مع أمثلة متعددة"
        else:
            style = "تطبيقي — يركز على التطبيق العملي وحل المشكلات"

        question_pref = _detect_question_preference(text, lang, is_ar)
    else:
        if def_ratio > 0.5:
            style = "Definition-heavy — the teacher emphasizes precise terminology and definitions"
        elif comp_ratio > 0.15:
            style = "Comparative — the teacher favors comparison and analysis questions"
        elif avg_sentence_len > 25:
            style = "Explanatory — the teacher explains in detail with multiple examples"
        else:
            style = "Application-focused — emphasizes practical application and problem-solving"

        question_pref = _detect_question_preference(text, lang, is_ar)

    return {
        "teaching_style": style,
        "formality": "formal" if avg_sentence_len > 18 else "conversational",
        "theory_vs_application": f"{int((1 - (lists / max(sentences_count, 1))) * 100)}% theory / {int((lists / max(sentences_count, 1)) * 100)}% application",
        "avg_concept_frequency": round(len(keywords) / max(sentences_count, 1), 2),
        "definition_density": round(def_ratio, 2),
        "comparison_density": round(comp_ratio, 2),
        "preferred_question_types": question_pref,
    }


def _detect_question_preference(text, lang, is_ar):
    definitions = len(_extract_definitions(text, lang))
    comparisons = len(_RE_COMPARISON.findall(text))
    lists_count = len(_RE_LIST.findall(text))
    total = max(definitions + comparisons + lists_count, 1)

    prefs = []
    if definitions / total > 0.3:
        prefs.append({"type": "MCQ + Short Answer", "weight": round(definitions / total * 100), "reason": "High definition count suggests definition-based testing"})
    if comparisons / total > 0.15:
        prefs.append({"type": "Compare & Contrast", "weight": round(comparisons / total * 100), "reason": "Multiple comparisons indicate compare-and-contrast exam style"})
    if lists_count / total > 0.15:
        prefs.append({"type": "List / Steps", "weight": round(lists_count / total * 100), "reason": "Listed content suggests sequential or enumeration questions"})

    if not prefs:
        prefs.append({"type": "Mixed (MCQ + Short + Essay)", "weight": 100, "reason": "Balanced content"})
    return prefs


def _extract_definitions(text, lang):
    pattern = _RE_DEFINITION_AR if lang == "ar" else _RE_DEFINITION_EN
    defs = []
    seen = set()
    for m in re.finditer(pattern, text):
        d = m.group(1).strip()
        key = d[:60].lower()
        if key not in seen:
            seen.add(key)
            kw = _keywords(d, min_freq=1, top_n=1)
            defs.append({"term": kw[0] if kw else "concept", "definition": d[:250]})
        if len(defs) >= 15:
            break
    return defs


def _extract_emphasis_map(text, keywords, lang, is_ar):
    signals = _EMPHASIS_SIGNALS_AR if is_ar else _EMPHASIS_SIGNALS_EN
    text_lower = text.lower()
    emphasis_scores = {}

    for kw in keywords:
        freq = text_lower.count(kw.lower())
        base = freq * 1.0
        for pattern, weight in signals:
            for m in re.finditer(pattern, text_lower):
                start = max(0, m.start() - 80)
                end = min(len(text_lower), m.end() + 80)
                context = text_lower[start:end]
                if kw.lower() in context:
                    base += weight
        emphasis_scores[kw] = base

    max_score = max(emphasis_scores.values()) if emphasis_scores else 1
    ranked = sorted(emphasis_scores.items(), key=lambda x: x[1], reverse=True)

    return {
        "top_emphasized": [{"concept": k, "intensity": round(v / max_score * 100)} for k, v in ranked[:12]],
        "emphasis_distribution": {
            "high": len([v for _, v in ranked if v / max_score > 0.6]),
            "medium": len([v for _, v in ranked if 0.3 <= v / max_score <= 0.6]),
            "low": len([v for _, v in ranked if v / max_score < 0.3]),
        },
    }


def _extract_exam_signals(text, lang, is_ar):
    signals = _EMPHASIS_SIGNALS_AR if is_ar else _EMPHASIS_SIGNALS_EN
    detected = []
    text_lower = text.lower()

    for pattern, weight in signals:
        for m in re.finditer(pattern, text_lower):
            start = max(0, m.start() - 100)
            end = min(len(text_lower), m.end() + 100)
            context = text[start:end].strip()
            detected.append({
                "signal_word": m.group(),
                "weight": weight,
                "context": context[:200],
                "interpretation": _interpret_signal(m.group(), weight, is_ar),
            })
            if len(detected) >= 15:
                break
        if len(detected) >= 15:
            break

    detected.sort(key=lambda x: x["weight"], reverse=True)
    return detected[:15]


def _interpret_signal(word, weight, is_ar):
    word_lower = word.lower()
    if weight >= 3.0:
        return "HIGH probability exam topic — teacher explicitly marked this" if not is_ar else "احتمال ظهوره في الامتحان عالي جدا — المعلم حدده بشكل صريح"
    elif weight >= 2.0:
        return "MEDIUM-HIGH — teacher repeated or clarified this concept" if not is_ar else "متوسط-عالي — المعلم كرر أو وضح هذا المفهوم"
    else:
        return "MEDIUM — teacher used this as an example or illustration" if not is_ar else "متوسط — استخدمه المعلم كمثال أو توضيح"


def _reconstruct_exam_patterns(text, sentences, keywords, lang, is_ar):
    definitions = _extract_definitions(text, lang)
    comparisons = len(_RE_COMPARISON.findall(text))
    lists = len(_RE_LIST.findall(text))
    key_count = len(keywords)

    difficulty_dist = _estimate_difficulty_distribution(keywords, text)
    trick_patterns = _detect_trick_patterns(keywords, text, lang, is_ar)
    repetition = _analyze_repetition(keywords, text)

    return {
        "difficulty_distribution": difficulty_dist,
        "trick_patterns": trick_patterns,
        "repetition_analysis": repetition,
        "likely_question_count": min(15, max(5, key_count // 3)),
        "definition_based_pct": round(len(definitions) / max(key_count, 1) * 100),
        "comparison_based_pct": round(comparisons / max(len(sentences), 1) * 100),
        "list_based_pct": round(lists / max(len(sentences), 1) * 100),
    }


def _estimate_difficulty_distribution(keywords, text):
    text_lower = text.lower()
    freq = Counter()
    for kw in keywords:
        freq[kw] = text_lower.count(kw.lower())
    if not freq:
        return {"easy_pct": 40, "medium_pct": 40, "hard_pct": 20}

    max_f = max(freq.values())
    easy = sum(1 for kw in keywords if freq[kw] / max_f > 0.7)
    medium = sum(1 for kw in keywords if 0.3 <= freq[kw] / max_f <= 0.7)
    hard = sum(1 for kw in keywords if freq[kw] / max_f < 0.3)
    total = max(easy + medium + hard, 1)

    return {
        "easy_pct": round(easy / total * 100),
        "medium_pct": round(medium / total * 100),
        "hard_pct": round(hard / total * 100),
        "rationale": "Frequent concepts = easier (teacher expects you to know them). Rare concepts = harder (likely trick questions).",
    }


def _detect_trick_patterns(keywords, text, lang, is_ar):
    tricks = []
    for i in range(0, len(keywords) - 2, 3):
        if i + 2 < len(keywords):
            kw1, kw2 = keywords[i], keywords[i + 1]
            if len(kw1) > 3 and len(kw2) > 3 and kw1[:3] == kw2[:3]:
                tricks.append({
                    "pattern": "Similar-name confusion",
                    "concept1": kw1,
                    "concept2": kw2,
                    "risk": "Teacher may use these as MCQ distractors with similar-sounding options",
                })
            if len(tricks) >= 3:
                break

    tricks.append({
        "pattern": "Exception questions",
        "explanation": "Concepts following 'however', 'but', 'except' are likely trick question targets",
    })
    tricks.append({
        "pattern": "Step-order questions",
        "explanation": "Sequential explanation = teacher may ask 'arrange in correct order'",
    })
    return tricks


def _analyze_repetition(keywords, text):
    text_lower = text.lower()
    repeated = []
    for kw in keywords[:15]:
        count = text_lower.count(kw.lower())
        if count >= 3:
            repeated.append({"concept": kw, "repetitions": count, "interpretation": "Teacher considers this important enough to repeat"})
    return repeated[:10]


def _predict_questions(text, keywords, emphasis, signals, patterns, lang, is_ar):
    emphasis_scores = {e["concept"]: e["intensity"] for e in emphasis["top_emphasized"]}
    definitions = _extract_definitions(text, lang)
    lists = _RE_LIST.findall(text)
    comparisons = [(m.group(), text[max(0, m.start() - 50):min(len(text), m.end() + 150)].strip()) for m in _RE_COMPARISON.finditer(text)]

    text_lower = text.lower()
    freq = Counter()
    for kw in keywords:
        freq[kw] = text_lower.count(kw.lower())
    max_freq = max(freq.values()) if freq else 1

    predictions = []

    for kw in keywords[:20]:
        score = 0
        reasons = []

        freq_score = freq[kw] / max_freq * 40
        score += freq_score
        if freq_score > 20:
            reasons.append("High frequency in document")

        emphasis_score = emphasis_scores.get(kw, 0) * 0.35
        score += emphasis_score
        if emphasis_score > 10:
            reasons.append("Teacher explicitly emphasized this concept")

        for s in signals:
            if kw.lower() in s["context"].lower():
                score += s["weight"] * 2
                reasons.append(f"Appears near signal: '{s['signal_word']}'")
                break

        for d in definitions:
            if kw.lower() in d["definition"].lower():
                score += 3
                reasons.append("Part of a key definition")
                break

        for item in lists:
            if kw.lower() in item.lower():
                score += 2
                reasons.append("Appears in a structured list")
                break

        for _, ctx in comparisons[:5]:
            if kw.lower() in ctx.lower():
                score += 2
                reasons.append("Part of a comparison (compare/contrast likely)")
                break

        predictions.append({
            "concept": kw,
            "prediction_score": round(min(score, 100)),
            "probability": "HIGH" if score > 40 else "MEDIUM" if score > 20 else "LOW",
            "reasons": reasons[:3],
        })

    predictions.sort(key=lambda x: x["prediction_score"], reverse=True)
    return predictions[:15]


def _build_exam_simulation(predictions, fingerprint, emphasis, signals, patterns, is_ar):
    high_prob = [p for p in predictions if p["probability"] == "HIGH"]
    medium_prob = [p for p in predictions if p["probability"] == "MEDIUM"]
    definitions = [s for s in signals if s["weight"] >= 2.5]

    exam_questions = []
    for hp in high_prob[:5]:
        q = _make_exam_question(hp, is_ar)
        if q:
            exam_questions.append(q)
    for mp in medium_prob[:3]:
        q = _make_exam_question(mp, is_ar)
        if q:
            exam_questions.append(q)

    trick_questions = []
    for hp in high_prob[:3]:
        tq = _make_trick_question(hp, is_ar)
        trick_questions.append(tq)

    important_defs = []
    for s in signals[:6]:
        important_defs.append({
            "signal": s["signal_word"],
            "context_preview": s["context"][:150],
            "reason": s["interpretation"],
        })

    revision_sheet = _build_revision_sheet(high_prob, medium_prob, definitions, is_ar)

    return {
        "predicted_total_questions": len(exam_questions) + len(trick_questions),
        "high_probability_questions": exam_questions[:8],
        "trick_questions": trick_questions,
        "important_definitions_to_study": important_defs,
        "exam_strategy": _build_exam_strategy(fingerprint, patterns, is_ar),
        "last_minute_revision": revision_sheet,
    }


def _make_exam_question(prediction, is_ar):
    concept = prediction["concept"]
    reasons = prediction.get("reasons", [])

    if is_ar:
        question = f'حسب نمط المعلم، من المتوقع سؤال عن "{concept}". السبب: {"; ".join(reasons[:2])}. اشرح هذا المفهوم مع مثال.'
        answer_guidance = f'عرف "{concept}" بدقة. اذكر خصائصه الرئيسية. قدم مثالا تطبيقيا من المادة.'
        why = f'المعلم يركز على "{concept}" في النص (السبب: {reasons[0] if reasons else "التكرار"}) — هذا يجعل ظهوره في الامتحان مرجحا جدا.'
        question_type = "mixed"
    else:
        question = f'Based on teaching patterns, a question about "{concept}" is highly likely. Reason: {"; ".join(reasons[:2])}. Explain this concept with an example.'
        answer_guidance = f'Define "{concept}" precisely. List its key characteristics. Provide a practical example from the material.'
        why = f'The teacher emphasizes "{concept}" in the text (because: {reasons[0] if reasons else "repetition"}) — making it very likely to appear on the exam.'
        question_type = "mixed"

    return {
        "question": question,
        "type": question_type,
        "predicted_score": prediction["prediction_score"],
        "answer_guidance": answer_guidance,
        "why_teacher_likely_asked_this": why,
    }


def _make_trick_question(prediction, is_ar):
    concept = prediction["concept"]
    if is_ar:
        question = f'سؤال فخ: قد يسأل المعلم عن الفرق بين "{concept}" ومفهوم مشابه. ما الاستثناءات أو الحالات الخاصة المرتبطة بهذا المفهوم؟'
        guidance = "ادرس التعريف الدقيق. لاحظ أي استثناءات مذكورة. قارن بين هذا المفهوم والمفاهيم المتشابهة."
        trap = "المعلمون غالبا يضعون أسئلة تخدع الطلاب بالخلط بين مفاهيم متشابهة — ركز على الفروق الدقيقة."
    else:
        question = f'Trap question: The teacher may ask about the difference between "{concept}" and a similar concept. What exceptions or special cases apply?'
        guidance = "Study the precise definition. Note any exceptions mentioned. Compare this concept with similar ones."
        trap = "Teachers often trick students by asking about similar-but-different concepts — focus on the precise differences."

    return {
        "question": question,
        "type": "trap",
        "guidance": guidance,
        "why_this_is_a_trap": trap,
    }


def _build_exam_strategy(fingerprint, patterns, is_ar):
    style = fingerprint["teaching_style"]
    diff = patterns["difficulty_distribution"]

    if is_ar:
        return [
            f"أسلوب المعلم: {style}",
            f"توزيع الصعوبة: {diff['easy_pct']}% سهل / {diff['medium_pct']}% متوسط / {diff['hard_pct']}% صعب",
            "ركز على التعاريف — المعلم يختبر المصطلحات بدقة",
            "لاحظ المقارنات في النص — أسئلة 'قارن' محتملة جدا",
            "ادرس القوائم والخطوات — قد يطلب ترتيبها",
        ]
    return [
        f"Teacher style: {style}",
        f"Difficulty: {diff['easy_pct']}% easy / {diff['medium_pct']}% medium / {diff['hard_pct']}% hard",
        "Focus on definitions — teacher tests terminology precisely",
        "Note comparisons in the text — 'compare and contrast' questions very likely",
        "Study lists and steps — teacher may ask to arrange them in order",
    ]


def _build_revision_sheet(high_prob, medium_prob, signals, is_ar):
    return {
        "top_5_must_know": [h["concept"] for h in high_prob[:5]],
        "likely_test_concepts": [m["concept"] for m in medium_prob[:5]],
        "teacher_emphasis_signals": [{"signal": s["signal_word"], "context": s["context"][:100]} for s in signals[:5]],
        "study_tips": [
            "Focus on the top 5 concepts — they have the highest exam probability" if not is_ar else "ركز على أهم 5 مفاهيم — احتمالية ظهورها في الامتحان الأعلى",
            "Practice explaining each concept in your own words" if not is_ar else "تدرب على شرح كل مفهوم بكلماتك الخاصة",
            "Create mind maps linking related concepts" if not is_ar else "أنشئ خرائط ذهنية تربط المفاهيم المتعلقة",
            "Solve practice questions for each high-probability topic" if not is_ar else "حل أسئلة تدريبية لكل موضوع عالي الاحتمال",
        ],
    }
