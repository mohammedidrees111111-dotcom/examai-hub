import re
import random
from collections import Counter

_RE_AR = re.compile(r'[\u0600-\u06FF]')
_RE_EN = re.compile(r'[a-zA-Z]')
_RE_WORDS = re.compile(r'[\u0600-\u06FFa-zA-Z]{3,}')
_RE_SENTENCE = re.compile(r'[.!?\n،؛؟\r]+')
_RE_DEFINITION_EN = re.compile(
    r'(?:is\s+defined\s+as|refers\s+to|is\s+a\s+form\s+of|means\s+that|is\s+the\s+process\s+of|'
    r'is\s+a\s+type\s+of|is\s+an?\s+|are\s+the\s+|consists?\s+of|comprises?\s+|involves?\s+)'
    r'(.{15,300}?)(?:[.!\n]|$)', re.IGNORECASE
)
_RE_DEFINITION_AR = re.compile(
    r'(?:هو|تعرف|يعرف|يقصد به|تعني|يقصد ب|المقصود بـ|عبارة عن|تتكون من|تشمل|تتمثل في)'
    r'(.{15,300}?)(?:[.؛!\n]|$)', re.IGNORECASE
)
_RE_EMPHASIS_EN = re.compile(
    r'(?:important|critical|crucial|essential|key|vital|fundamental|significant|'
    r'note that|remember|do not forget|pay attention|you should|you must)',
    re.IGNORECASE
)
_RE_EMPHASIS_AR = re.compile(
    r'(?:مهم|هام|ملاحظة|انتبه|تذكر|لاحظ أن|يجب أن|من الضروري|أساسي|جوهري|محوري)',
    re.IGNORECASE
)
_RE_COMPARE = re.compile(
    r'(?:unlike|whereas|while|in contrast|compared to|differs from|better than|worse than|'
    r'more than|less than|similar to|same as|however|on the other hand|بينما|مقارنة|على العكس)',
    re.IGNORECASE
)
_RE_LIST = re.compile(r'(?:^|\n)\s*(?:[\d]+[\.\)]\s+|[•\-\*\✓\✔\→]\s+)(.+?)(?:\n|$)', re.MULTILINE)
_RE_CHAPTER = re.compile(
    r'(?:^|\n)\s*(?:Chapter|CHAPTER|Unit|Part|Section|Module|الفصل|الباب|الجزء|الوحدة|القسم)\s*[\dIVXivx]+[\.:\-]?\s*[^\n]{2,120}',
    re.IGNORECASE
)

AR_STOP = frozenset({"في","من","على","عن","هذا","هذه","هو","هي","هم","كل","بعض","بين","مع","بعد","قبل","خلال","حول","عند","ليس","لم","لن","لا","ما","ذلك","تلك","الذي","التي","هناك","هنا","حتى","ايضا","فقط"})
EN_STOP = frozenset({"the","and","for","are","but","not","you","all","any","had","this","that","with","from","they","have","been","were","which","about","would","could","should","what","when","where","there","these"})
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


def _detect_chapters(text: str) -> list[dict]:
    matches = list(_RE_CHAPTER.finditer(text))
    is_ar = _lang(text) == "ar"
    chapters = []
    if len(matches) >= 2:
        for i, m in enumerate(matches):
            start = m.start()
            end = matches[i+1].start() if i+1 < len(matches) else len(text)
            content = text[start:end].strip()
            title = m.group().strip()
            chapters.append({"number": i+1, "title": title[:120], "content": content, "word_count": len(content.split())})
    else:
        paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 80]
        for i, p in enumerate(paragraphs):
            first_line = p.split("\n")[0][:80]
            chapters.append({"number": i+1, "title": first_line, "content": p, "word_count": len(p.split())})
    return chapters


def generate_full_exam(text: str) -> dict:
    lang = _lang(text)
    is_ar = lang == "ar"
    total_words = len(text.split())
    keywords = _keywords(text, min_freq=2, top_n=80)
    if not keywords:
        keywords = _keywords(text, min_freq=1, top_n=80)

    chapters = _detect_chapters(text)
    definitions = _extract_definitions(text, lang)
    emphasis = _RE_EMPHASIS_AR if is_ar else _RE_EMPHASIS_EN
    lists = _RE_LIST.findall(text)
    comparisons = [m.group() for m in _RE_COMPARE.finditer(text)]

    # Rank topics by importance
    text_lower = text.lower()
    ranked = []
    for kw in keywords[:40]:
        freq = text_lower.count(kw.lower())
        signaled = bool(emphasis.search(text[:text_lower.find(kw.lower())+100] + text[max(0, text_lower.find(kw.lower())-100):]))
        is_defined = any(kw.lower() in d["definition"].lower() for d in definitions)
        in_list = any(kw.lower() in l.lower() for l in lists)
        in_compare = any(kw.lower() in c.lower() for c in comparisons)
        score = freq * 3 + (10 if signaled else 0) + (7 if is_defined else 0) + (4 if in_list else 0) + (5 if in_compare else 0)
        ranked.append({"concept": kw, "frequency": freq, "signaled": signaled, "defined": is_defined, "score": score})
    ranked.sort(key=lambda x: x["score"], reverse=True)

    total_marks = 100
    mca_marks = 20
    short_marks = 30
    essay_marks = 30
    problem_marks = 20

    time_minutes = max(60, total_words // 30)
    exam_id = f"EXAM-{random.randint(1000,9999)}"

    mca_questions = _generate_mcq(ranked, keywords, text, definitions, lang, is_ar, 10)
    short_questions = _generate_short_answer(ranked, definitions, lists, text, lang, is_ar, 5)
    essay_questions = _generate_essay(ranked, chapters, comparisons, text, lang, is_ar, 3)
    problem_questions = _generate_problems(ranked, definitions, lists, text, lang, is_ar, 2)

    marking = _generate_marking_scheme(mca_questions, short_questions, essay_questions, problem_questions, is_ar)

    return {
        "exam_id": exam_id,
        "title": "Predicted Exam" if not is_ar else "امتحان متوقع",
        "subject": keywords[0].capitalize() if keywords else "General",
        "total_marks": total_marks,
        "time_minutes": time_minutes,
        "language": lang,
        "instructions": [
            "Read all questions carefully before answering." if not is_ar else "اقرأ جميع الأسئلة بعناية قبل الإجابة.",
            "Write clearly and show all working." if not is_ar else "اكتب بوضوح وأظهر جميع خطوات الحل.",
            "Manage your time — allocate approximately 1 minute per mark." if not is_ar else "نظم وقتك — خصص دقيقة واحدة لكل درجة تقريباً.",
        ],
        "sections": [
            {
                "section": "A" if not is_ar else "أ",
                "title": "Multiple Choice Questions" if not is_ar else "أسئلة اختيار من متعدد",
                "marks": f"{mca_marks} marks" if not is_ar else f"{mca_marks} درجة",
                "questions": mca_questions,
            },
            {
                "section": "B" if not is_ar else "ب",
                "title": "Short Answer Questions" if not is_ar else "أسئلة إجابة قصيرة",
                "marks": f"{short_marks} marks" if not is_ar else f"{short_marks} درجة",
                "questions": short_questions,
            },
            {
                "section": "C" if not is_ar else "ج",
                "title": "Essay Questions" if not is_ar else "أسئلة مقالية",
                "marks": f"{essay_marks} marks" if not is_ar else f"{essay_marks} درجة",
                "instructions": "Answer 2 out of 3 questions." if not is_ar else "أجب عن سؤالين من أصل 3.",
                "questions": essay_questions,
            },
            {
                "section": "D" if not is_ar else "د",
                "title": "Problem Solving" if not is_ar else "حل مسائل",
                "marks": f"{problem_marks} marks" if not is_ar else f"{problem_marks} درجة",
                "questions": problem_questions,
            },
        ],
        "marking_scheme": marking,
        "answer_key": _generate_answer_key(mca_questions, short_questions, essay_questions, problem_questions, is_ar),
        "chapter_coverage": [{"chapter": ch["number"], "title": ch["title"][:80], "questions": max(1, ch["word_count"] // 200)} for ch in chapters],
        "statistics": {
            "total_concepts_analyzed": len(keywords),
            "definitions_used": len(definitions),
            "emphasis_signals_detected": len(emphasis.findall(text)),
            "chapters_covered": len(chapters),
            "prediction_confidence": min(98, 50 + len(ranked)),
        },
    }


def _generate_mcq(ranked, keywords, text, definitions, lang, is_ar, count):
    questions = []
    for i, r in enumerate(ranked[:count]):
        concept = r["concept"]
        contexts = [s[:200] for s in _sentences(text) if concept.lower() in s.lower()]
        ctx = contexts[0] if contexts else concept

        distractors = [k for k in keywords if k.lower() != concept.lower()]
        random.shuffle(distractors)
        wrong = distractors[:3]
        while len(wrong) < 3:
            wrong.append("Option " + chr(65+len(wrong)))

        options = wrong + [concept]
        random.shuffle(options)
        correct_idx = options.index(concept)

        if is_ar:
            if r.get("signaled"):
                q = f'أي مما يلي يعرف "{concept}" بشكل صحيح؟ (إشارة: هذا المفهوم مهم)'
            elif r.get("defined"):
                q = f'ما هو التعريف الصحيح لـ "{concept}"؟'
            else:
                q = f'أي مما يلي يتعلق بـ "{concept}" حسب المادة؟'
            explanation = f'الإجابة الصحيحة هي {chr(65+correct_idx)}) {concept}. {ctx[:100]}'
            distract_explain = f'الخيارات الأخرى غير صحيحة لأنها تشير إلى مفاهيم مختلفة.'
        else:
            if r.get("signaled"):
                q = f'Which of the following correctly defines "{concept}"? (Teacher emphasis: important)'
            elif r.get("defined"):
                q = f'What is the correct definition of "{concept}"?'
            else:
                q = f'Which of the following relates to "{concept}" as presented in the material?'
            explanation = f'Correct answer: {chr(65+correct_idx)}) {concept}. {ctx[:100]}'
            distract_explain = f'Other options are incorrect as they refer to different concepts.'

        questions.append({
            "number": i + 1,
            "question": q,
            "marks": 2,
            "options": [f"{chr(65+j)}) {o}" for j, o in enumerate(options)],
            "correct": chr(65+correct_idx),
            "correct_answer": concept,
            "explanation": {"why_correct": explanation, "why_others_wrong": distract_explain},
        })
    return questions


def _generate_short_answer(ranked, definitions, lists, text, lang, is_ar, count):
    questions = []
    used = set()

    for d in definitions[:count]:
        term = d["term"]
        if term in used:
            continue
        used.add(term)
        if is_ar:
            q = f'عرف "{term}" حسب ما ورد في المادة الدراسية.'
            model_answer = d["definition"][:250]
            marking_points = ["تعريف دقيق", "ذكر الخصائص الرئيسية", "مثال توضيحي"]
            marks = 6
        else:
            q = f'Define "{term}" as presented in the course material.'
            model_answer = d["definition"][:250]
            marking_points = ["Accurate definition", "Mention key characteristics", "Provide example"]
            marks = 6
        questions.append({
            "number": len(questions) + 1, "question": q, "marks": marks,
            "model_answer": model_answer, "marking_points": marking_points,
        })
        if len(questions) >= count:
            break

    for item in lists:
        if len(questions) >= count:
            break
        if is_ar:
            q = f'اذكر واشرح: {item[:100]}'
            model_answer = item[:250]
            marking_points = ["ذكر جميع النقاط", "شرح كل نقطة", "ترتيب منطقي"]
            marks = 6
        else:
            q = f'List and explain: {item[:100]}'
            model_answer = item[:250]
            marking_points = ["List all points", "Explain each point", "Logical order"]
            marks = 6
        questions.append({
            "number": len(questions) + 1, "question": q, "marks": marks,
            "model_answer": model_answer, "marking_points": marking_points,
        })

    return questions[:count]


def _generate_essay(ranked, chapters, comparisons, text, lang, is_ar, count):
    questions = []
    top = ranked[:5]

    for i in range(count):
        concept = top[i]["concept"] if i < len(top) else keywords[0] if keywords else "concept"
        chapter = chapters[i % len(chapters)] if chapters else {"title": "Chapter 1"}
        chapter_title = chapter.get("title", "the material")

        if i == 0 and comparisons:
            comp_word = comparisons[0] if isinstance(comparisons[0], str) else comparisons[0][0]
            if is_ar:
                q = f'ناقش بالتفصيل مفهوم "{concept}" وقارنه بالمفاهيم ذات الصلة كما ورد في {chapter_title}. استشهد بأمثلة من النص.'
                criteria = ["تعريف دقيق (4 درجات)", "مقارنة شاملة (4 درجات)", "أمثلة من النص (4 درجات)", "تنظيم ووضوح (3 درجات)"]
            else:
                q = f'Discuss "{concept}" in detail and compare it with related concepts as presented in {chapter_title}. Use examples from the text.'
                criteria = ["Accurate definition (4 marks)", "Comprehensive comparison (4 marks)", "Examples from text (4 marks)", "Organization and clarity (3 marks)"]
        elif i == 1:
            if is_ar:
                q = f'اشرح أهمية "{concept}" في سياق المادة الدراسية. ناقش تطبيقاته العملية وعلاقته بالمفاهيم الأخرى في المنهج.'
                criteria = ["شرح الأهمية (5 درجات)", "تطبيقات عملية (5 درجات)", "ربط بمفاهيم أخرى (5 درجات)"]
            else:
                q = f'Explain the significance of "{concept}" in the context of this course. Discuss its practical applications and relationship to other concepts in the syllabus.'
                criteria = ["Significance explained (5 marks)", "Practical applications (5 marks)", "Links to other concepts (5 marks)"]
        else:
            if is_ar:
                q = f'حلل دور "{concept}" في {chapter_title}. ناقش كيف يساهم هذا المفهوم في فهم الموضوع ككل.'
                criteria = ["تحليل شامل (5 درجات)", "ربط بالموضوع الكلي (5 درجات)", "أمثلة وتطبيقات (5 درجات)"]
            else:
                q = f'Analyze the role of "{concept}" in {chapter_title}. Discuss how this concept contributes to understanding the subject as a whole.'
                criteria = ["Comprehensive analysis (5 marks)", "Connection to overall subject (5 marks)", "Examples and applications (5 marks)"]

        questions.append({
            "number": len(questions) + 1,
            "question": q,
            "marks": 15,
            "topic": concept,
            "marking_criteria": criteria,
        })

    return questions


def _generate_problems(ranked, definitions, lists, text, lang, is_ar, count):
    questions = []
    for i in range(count):
        concept = ranked[i]["concept"] if i < len(ranked) else "concept"
        dl = definitions[i] if i < len(definitions) else None
        li = lists[i] if i < len(lists) else None

        if is_ar:
            q = f'طبق مفهوم "{concept}" على سيناريو عملي. اشرح خطوات التطبيق والنتيجة المتوقعة.'
            approach = ["فهم المفهوم", "تحديد السيناريو", "تطبيق خطوة بخطوة", "تحليل النتيجة", "استنتاج"]
        else:
            q = f'Apply the concept of "{concept}" to a practical scenario. Explain the steps and expected outcome.'
            approach = ["Understand the concept", "Identify the scenario", "Apply step by step", "Analyze the result", "Draw conclusions"]

        context = dl["definition"][:150] if dl else (li[:150] if li else concept)
        questions.append({
            "number": len(questions) + 1,
            "question": q,
            "marks": 10,
            "context": context,
            "solution_approach": approach,
        })
    return questions


def _generate_marking_scheme(mcq, short, essay, problems, is_ar):
    return {
        "section_a_mcq": {"marks_per_question": 2, "total_questions": len(mcq), "total_marks": len(mcq) * 2},
        "section_b_short": {"marks_per_question": 6, "total_questions": len(short), "total_marks": len(short) * 6} if short else {},
        "section_c_essay": {"marks_per_question": 15, "total_questions": len(essay), "total_marks": len(essay) * 15, "attempt": "2 out of 3" if not is_ar else "2 من 3"} if essay else {},
        "section_d_problems": {"marks_per_question": 10, "total_questions": len(problems), "total_marks": len(problems) * 10} if problems else {},
        "grading_scale": {
            "A": "90-100" if not is_ar else "ممتاز",
            "B": "80-89" if not is_ar else "جيد جداً",
            "C": "70-79" if not is_ar else "جيد",
            "D": "60-69" if not is_ar else "مقبول",
            "F": "Below 60" if not is_ar else "راسب",
        },
    }


def _generate_answer_key(mcq, short, essay, problems, is_ar):
    return {
        "section_a_mcq": [{"number": q["number"], "answer": q["correct"], "explanation": q["explanation"]["why_correct"][:150]} for q in mcq],
        "section_b_short": [{"number": q["number"], "model_answer": q["model_answer"][:200], "key_points": q.get("marking_points", [])} for q in short],
        "section_c_essay": [{"number": q["number"], "topic": q["topic"], "criteria": q["marking_criteria"]} for q in essay],
        "section_d_problems": [{"number": q["number"], "approach": q["solution_approach"]} for q in problems],
    }


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
