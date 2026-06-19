import re
from typing import Optional, Any
from collections import Counter

_RE_ARABIC_CHAR = re.compile(r'[\u0600-\u06FF]')
_RE_ENGLISH_CHAR = re.compile(r'[a-zA-Z]')
_RE_WORDS = re.compile(r'[\u0600-\u06FFa-zA-Z]{3,}')
_RE_SENTENCE_SPLIT = re.compile(r'[.!?\n،؛؟\r]+')
_RE_CHAPTER = re.compile(r'(?:Chapter|CHAPTER|Ch\.|الفصل|الباب|الجزء|Chapter\s+\d+|CHAPTER\s+\d+|[IVX]+\.)\s*[:\-\u0600-\u06FFa-zA-Z0-9\s]+', re.IGNORECASE)
_RE_HEADING = re.compile(r'^(?:#{1,3}\s+|(?:[A-Z][A-Z\s]{3,})|(?:\d+[\.\)]\s+[A-Z]))', re.MULTILINE)

from app.services.ai_service import (
    _detect_language, _split_sentences, _extract_keywords,
    _chunk_text, ALL_STOP_WORDS, CHUNK_SIZE,
)


def detect_chapters(text: str) -> list[dict]:
    chapters = []
    matches = list(_RE_CHAPTER.finditer(text))
    lang = _detect_language(text)
    is_ar = lang == "ar"

    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else min(start + 5000, len(text))
        chapter_text = text[start:end].strip()
        title = m.group().strip()
        word_count = len(chapter_text.split())
        keywords = _extract_keywords(chapter_text, min_freq=1, top_n=8)

        chapters.append({
            "number": i + 1,
            "title": title[:120],
            "start_char": start,
            "word_count": word_count,
            "keywords": keywords[:5],
            "preview": chapter_text[:200] + ("..." if len(chapter_text) > 200 else ""),
        })

    if not chapters:
        paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 100]
        for i, p in enumerate(paragraphs[:20]):
            chapters.append({
                "number": i + 1,
                "title": (f"Section {i+1}" if not is_ar else f"القسم {i+1}"),
                "word_count": len(p.split()),
                "keywords": _extract_keywords(p, min_freq=1, top_n=5)[:5],
                "preview": p[:200] + ("..." if len(p) > 200 else ""),
            })

    return chapters


def extract_definitions(text: str) -> list[dict]:
    lang = _detect_language(text)
    is_ar = lang == "ar"

    patterns_ar = [
        (r'(?:هو|تعرف|يعرف|يقصد به|تعني|يقصد ب|المقصود بـ)\s*(.{20,200}?)[.؛\n]', 1),
    ]
    patterns_en = [
        (r'(?:is\s+defined\s+as|refers\s+to|is\s+a\s+form\s+of|means|is\s+the\s+)\s*(.{20,200}?)[.\n]', 1),
    ]

    patterns = patterns_ar if is_ar else patterns_en
    definitions = []
    seen = set()

    for pattern, group in patterns:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            definition = m.group(group).strip()
            if definition not in seen:
                seen.add(definition)
                keywords = _extract_keywords(definition, min_freq=1, top_n=3)
                definitions.append({
                    "term": keywords[0] if keywords else "concept",
                    "definition": definition[:250],
                })
            if len(definitions) >= 8:
                break
        if definitions:
            break

    if not definitions:
        sentences = _split_sentences(text)
        for s in sentences[:10]:
            if len(s.split()) > 8:
                kw = _extract_keywords(s, min_freq=1, top_n=1)
                definitions.append({
                    "term": kw[0] if kw else "concept",
                    "definition": s[:250],
                })
            if len(definitions) >= 5:
                break

    return definitions[:10]


def rank_importance(text: str) -> list[dict]:
    keywords = _extract_keywords(text, min_freq=2, top_n=30)
    if not keywords:
        keywords = _extract_keywords(text, min_freq=1, top_n=30)

    freq = Counter()
    text_lower = text.lower()
    for kw in keywords:
        freq[kw] = text_lower.count(kw.lower())

    max_freq = max(freq.values()) if freq else 1
    ranked = []

    for kw in keywords[:20]:
        f = freq.get(kw, 1)
        ratio = f / max_freq
        if ratio > 0.5:
            importance = "high"
        elif ratio > 0.2:
            importance = "medium"
        else:
            importance = "low"

        sentences_containing = []
        for s in _split_sentences(text):
            if kw.lower() in s.lower():
                sentences_containing.append(s[:120])
            if len(sentences_containing) >= 2:
                break

        ranked.append({
            "concept": kw,
            "frequency": f,
            "importance": importance,
            "context": sentences_containing,
        })

    return ranked[:15]


def generate_flashcards(text: str, count: int = 10) -> list[dict]:
    lang = _detect_language(text)
    is_ar = lang == "ar"

    keywords = _extract_keywords(text, min_freq=2, top_n=count * 2)
    if not keywords:
        keywords = _extract_keywords(text, min_freq=1, top_n=count * 2)

    flashcards = []
    sentences = _split_sentences(text)

    front_label = "Front" if not is_ar else "السؤال"
    back_label = "Back" if not is_ar else "الجواب"

    for i, kw in enumerate(keywords[:count]):
        definition = f"A key concept in this material related to {kw}."
        for s in sentences:
            if kw.lower() in s.lower():
                definition = s[:250]
                break

        flashcards.append({
            "id": i + 1,
            "front": f"What is '{kw}'?" if not is_ar else f"ما هو '{kw}'؟",
            "back": definition,
            "concept": kw,
            "difficulty": "medium" if len(definition.split()) > 20 else "easy",
        })

    return flashcards


def generate_study_plan(text: str, available_days: int = 7) -> dict:
    lang = _detect_language(text)
    is_ar = lang == "ar"

    chapters = detect_chapters(text)
    total_words = len(text.split())
    total_chapters = len(chapters)
    chapters_per_day = max(1, total_chapters // max(1, available_days))
    words_per_day = total_words // max(1, available_days)

    plan_days = []
    for day in range(available_days):
        start_ch = day * chapters_per_day
        end_ch = min(start_ch + chapters_per_day, total_chapters)
        day_chapters = chapters[start_ch:end_ch]

        if not day_chapters:
            break

        plan_days.append({
            "day": day + 1,
            "title": f"Day {day + 1}" if not is_ar else f"اليوم {day + 1}",
            "chapters": [c["title"][:80] for c in day_chapters],
            "estimated_words": sum(c["word_count"] for c in day_chapters),
            "tasks": [
                "Read the assigned sections carefully" if not is_ar else "اقرأ الأقسام المخصصة بعناية",
                "Highlight key terms and definitions" if not is_ar else "حدد المصطلحات والتعريفات الأساسية",
                "Answer end-of-section questions" if not is_ar else "أجب عن أسئلة نهاية القسم",
                "Create summary notes" if not is_ar else "أنشئ ملاحظات تلخيصية",
            ],
        })

    return {
        "total_days": len(plan_days),
        "total_chapters": total_chapters,
        "total_words": total_words,
        "words_per_day": words_per_day,
        "chapters_per_day": chapters_per_day,
        "language": lang,
        "plan": plan_days,
    }


def generate_cheatsheet(text: str) -> dict:
    lang = _detect_language(text)
    is_ar = lang == "ar"

    keywords = _extract_keywords(text, min_freq=2, top_n=15)
    definitions = extract_definitions(text)
    importance = rank_importance(text)

    return {
        "title": f"Cheatsheet: {keywords[0] if keywords else 'Study'}" if not is_ar else f"ملخص سريع: {keywords[0] if keywords else 'دراسة'}",
        "must_know_terms": keywords[:10] if not is_ar else keywords[:10],
        "high_importance": [i for i in importance if i["importance"] == "high"][:5],
        "definitions": definitions[:8],
        "study_tips": [
            "Focus on high-importance concepts first" if not is_ar else "ركز على المفاهيم عالية الأهمية أولا",
            "Use flashcards for key terms" if not is_ar else "استخدم البطاقات التعليمية للمصطلحات",
            "Practice explaining each concept out loud" if not is_ar else "تدرب على شرح كل مفهوم بصوت عال",
            "Review the summary at the end of each session" if not is_ar else "راجع الملخص في نهاية كل جلسة",
        ],
        "language": lang,
    }


def structured_document_analysis(text: str) -> dict:
    lang = _detect_language(text)
    is_ar = lang == "ar"
    total_words = len(text.split())

    chapters = detect_chapters(text)
    keywords = _extract_keywords(text, min_freq=2, top_n=30)
    if not keywords:
        keywords = _extract_keywords(text, min_freq=1, top_n=30)
    definitions = extract_definitions(text)
    importance = rank_importance(text)

    if total_words > 30000:
        difficulty = "very_advanced" if not is_ar else "متقدم جدا"
    elif total_words > 10000:
        difficulty = "advanced" if not is_ar else "متقدم"
    elif total_words > 3000:
        difficulty = "intermediate" if not is_ar else "متوسط"
    else:
        difficulty = "beginner" if not is_ar else "مبتدئ"

    return {
        "document_info": {
            "total_words": total_words,
            "total_chapters": len(chapters),
            "language": lang,
            "difficulty_level": difficulty,
        },
        "chapters": chapters,
        "main_topics": keywords[:10],
        "subtopics": keywords[10:25] if len(keywords) > 10 else [],
        "key_definitions": definitions,
        "importance_ranking": importance[:12],
        "possible_exam_questions": [
            {"question": f"Define '{kw}' and explain its significance." if not is_ar else f"عرف '{kw}' واشرح أهميته.",
             "importance": imp["importance"],
             "concept": kw}
            for kw, imp in [(r["concept"], r) for r in importance[:5]]
        ],
        "language": lang,
    }
