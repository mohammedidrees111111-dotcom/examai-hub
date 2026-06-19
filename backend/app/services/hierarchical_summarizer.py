import re
from typing import Optional
from collections import Counter

_RE_AR = re.compile(r'[\u0600-\u06FF]')
_RE_EN = re.compile(r'[a-zA-Z]')
_RE_WORDS = re.compile(r'[\u0600-\u06FFa-zA-Z]{3,}')
_RE_SENTENCE = re.compile(r'[.!?\n،؛؟\r]+')
_RE_CHAPTER = re.compile(
    r'(?:^|\n)\s*(?:Chapter|CHAPTER|Unit|Part|Section|Module|الفصل|الباب|الجزء|الوحدة|القسم)\s*[\dIVXivx]+[\.:\-]?\s*[^\n]{2,120}',
    re.IGNORECASE
)
_RE_HEADING = re.compile(r'^(?:#{1,3}\s+|(?:[A-Z][A-Z\s]{8,60}))', re.MULTILINE)
_RE_DEFINITION_EN = re.compile(
    r'(?:is\s+defined\s+as|refers\s+to|is\s+a\s+form\s+of|means\s+that|is\s+the\s+process\s+of|'
    r'is\s+a\s+type\s+of|is\s+an?\s+|are\s+the\s+|consists?\s+of|comprises?\s+|involves?\s+)'
    r'(.{15,300}?)(?:[.!\n]|$)', re.IGNORECASE
)
_RE_DEFINITION_AR = re.compile(
    r'(?:هو|تعرف|يعرف|يقصد به|تعني|يقصد ب|المقصود بـ|عبارة عن|تتكون من|تشمل|تتمثل في)'
    r'(.{15,300}?)(?:[.؛!\n]|$)', re.IGNORECASE
)
_RE_COMPARE = re.compile(
    r'(?:unlike|whereas|while|in contrast|compared to|differs from|better than|worse than|'
    r'more than|less than|similar to|same as|however|on the other hand|بينما|مقارنة|على العكس|'
    r'بالمقابل|يختلف عن|يشبه|مشابه)', re.IGNORECASE
)
_RE_EXCEPTION = re.compile(
    r'(?:however|but|except|unless|although|though|despite|notwithstanding|'
    r'on the contrary|interestingly|surprisingly|notably|لكن|ولكن|إلا|عدا|ما عدا|غير أن|'
    r'باستثناء|على الرغم)', re.IGNORECASE
)
_RE_EMPHASIS_EN = re.compile(
    r'(?:important|critical|crucial|essential|key|vital|fundamental|significant|'
    r'note that|remember|do not forget|pay attention|you should|you must|be aware|'
    r'always|never|must|required|mandatory|absolutely|definitely)',
    re.IGNORECASE
)
_RE_EMPHASIS_AR = re.compile(
    r'(?:مهم|هام|ملاحظة|انتبه|تذكر|لاحظ أن|يجب أن|من الضروري|أساسي|جوهري|محوري|دائما|أبدا|'
    r'لا تنس|تأكد|انتبه جيدا|ركز على)', re.IGNORECASE
)

AR_STOP = frozenset({
    "في","من","على","عن","هذا","هذه","هو","هي","هم","كل","بعض","بين","مع","بعد","قبل",
    "خلال","حول","عند","ليس","لم","لن","لا","ما","ذلك","تلك","الذي","التي","هناك",
})
EN_STOP = frozenset({
    "the","and","for","are","but","not","you","all","any","had","this","that","with",
    "from","they","have","been","were","which","about","would","could","should","what",
})
ALL_STOP = AR_STOP | EN_STOP


def _lang(text: str) -> str:
    return "ar" if len(_RE_AR.findall(text[:2000])) > len(_RE_EN.findall(text[:2000])) else "en"


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in _RE_SENTENCE.split(text) if len(s.strip()) > 10]


def _keywords(text: str, min_freq: int = 2, top_n: int = 80) -> list[str]:
    words = _RE_WORDS.findall(text.lower())
    lang = _lang(text)
    min_len = 3 if lang == "ar" else 4
    filtered = [w for w in words if len(w) >= min_len and w not in ALL_STOP]
    if not filtered:
        return []
    freq = Counter(filtered)
    return [w for w, c in freq.most_common(top_n) if c >= min_freq]


def _dynamic_compression_ratio(total_words: int) -> float:
    if total_words < 5000:
        return 0.75
    elif total_words < 15000:
        return 0.65
    elif total_words < 40000:
        return 0.55
    elif total_words < 80000:
        return 0.50
    else:
        return 0.45


def _detect_chapters(text: str) -> list[dict]:
    chapters = []
    matches = list(_RE_CHAPTER.finditer(text))
    is_ar = _lang(text) == "ar"

    if len(matches) >= 2:
        for i, m in enumerate(matches):
            start = m.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            content = text[start:end].strip()
            title = m.group().strip()
            paragraphs = content.split("\n\n")
            sections = _split_into_sections(content)
            chapters.append({
                "number": i + 1,
                "title": title[:120],
                "content": content,
                "word_count": len(content.split()),
                "sections": sections,
                "keywords": _keywords(content, min_freq=1, top_n=15),
            })
    else:
        paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 80]
        for i, p in enumerate(paragraphs):
            first_line = p.split("\n")[0][:80]
            chapters.append({
                "number": i + 1,
                "title": first_line,
                "content": p,
                "word_count": len(p.split()),
                "sections": _split_into_sections(p),
                "keywords": _keywords(p, min_freq=1, top_n=10),
            })

    return chapters


def _split_into_sections(text: str) -> list[dict]:
    paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 50]
    sections = []
    for i, p in enumerate(paragraphs[:20]):
        sections.append({
            "number": i + 1,
            "content": p,
            "word_count": len(p.split()),
            "sentence_count": len(_sentences(p)),
            "has_definition": bool(_RE_DEFINITION_EN.search(p) or _RE_DEFINITION_AR.search(p)),
            "has_comparison": bool(_RE_COMPARE.search(p)),
            "has_exception": bool(_RE_EXCEPTION.search(p)),
            "is_emphasized": bool((_RE_EMPHASIS_EN.search(p) or _RE_EMPHASIS_AR.search(p))),
            "keywords": _keywords(p, min_freq=1, top_n=8),
        })
    return sections


def _extract_important_sentences(text: str, target_ratio: float) -> list[str]:
    sentences = _sentences(text)
    if not sentences:
        return []

    keywords = _keywords(text, min_freq=2, top_n=30)
    if not keywords:
        keywords = _keywords(text, min_freq=1, top_n=30)

    emphasis_pattern = _RE_EMPHASIS_EN if _lang(text) == "en" else _RE_EMPHASIS_AR

    scored = []
    for i, s in enumerate(sentences):
        score = 0
        s_lower = s.lower()

        for kw in keywords:
            if kw.lower() in s_lower:
                score += 1.5

        if _RE_DEFINITION_EN.search(s) or _RE_DEFINITION_AR.search(s):
            score += 4
        if _RE_COMPARE.search(s):
            score += 3
        if _RE_EXCEPTION.search(s):
            score += 2.5
        if emphasis_pattern.search(s):
            score += 4

        position_ratio = i / max(len(sentences) - 1, 1)
        if position_ratio < 0.1 or position_ratio > 0.9:
            score += 1

        word_len = len(s.split())
        if 10 < word_len < 80:
            score += 1

        scored.append((s, i, score))

    scored.sort(key=lambda x: x[2], reverse=True)
    target_count = max(5, int(len(sentences) * target_ratio))
    top_sentences = sorted(scored[:target_count], key=lambda x: x[1])
    return [s[0] for s in top_sentences]


def hierarchical_summarize(text: str, target_ratio: Optional[float] = None) -> dict:
    text = text.strip()
    lang = _lang(text)
    is_ar = lang == "ar"
    total_words = len(text.split())

    if target_ratio is None:
        target_ratio = _dynamic_compression_ratio(total_words)

    chapters = _detect_chapters(text)
    chapter_summaries = []
    all_keywords = []
    all_definitions = []

    for ch in chapters:
        ch_keywords = _keywords(ch["content"], min_freq=1, top_n=12)
        all_keywords.extend(ch_keywords)

        ch_defs = _extract_definitions(ch["content"], lang)
        all_definitions.extend(ch_defs)

        important_sentences = _extract_important_sentences(ch["content"], target_ratio)
        section_summaries = []
        for sec in ch.get("sections", [])[:10]:
            sec_text = sec.get("content", "")
            sec_important = _extract_important_sentences(sec_text, target_ratio)
            section_summaries.append({
                "section": sec["number"],
                "summary": " ".join(sec_important)[:500],
                "word_count": sec.get("word_count", 0),
                "has_definition": sec.get("has_definition", False),
                "has_comparison": sec.get("has_comparison", False),
                "is_emphasized": sec.get("is_emphasized", False),
            })

        chapter_summaries.append({
            "number": ch["number"],
            "title": ch["title"],
            "original_words": ch["word_count"],
            "summary_words": len(" ".join(important_sentences).split()),
            "summary": " ".join(important_sentences),
            "sections": section_summaries,
            "key_concepts": ch_keywords[:8],
        })

    all_keywords_unique = list(dict.fromkeys(all_keywords))[:30]
    all_defs_unique = {d["definition"][:80]: d for d in all_definitions}.values()

    sep = " " if is_ar else ". "
    full_summary = sep.join(ch["summary"] for ch in chapter_summaries)
    summary_words = len(full_summary.split())

    actual_ratio = summary_words / max(total_words, 1) * 100

    return {
        "original_words": total_words,
        "summary_words": summary_words,
        "compression_ratio": f"{actual_ratio:.1f}%",
        "target_ratio": f"{target_ratio * 100:.0f}%",
        "chapters_count": len(chapters),
        "chapters": chapter_summaries,
        "global_keywords": all_keywords_unique,
        "definitions_extracted": [{"term": d["term"], "definition": d["definition"][:250]} for d in list(all_defs_unique)[:15]],
        "full_summary": full_summary,
        "information_preservation": {
            "definitions_kept": len(list(all_defs_unique)),
            "chapters_processed": len(chapters),
            "quality": "high" if actual_ratio >= 25 else "medium" if actual_ratio >= 15 else "low_reprocess",
        },
        "language": lang,
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


def multi_pass_prediction(text: str, past_exams: str = "", lecture_notes: str = "") -> dict:
    lang = _lang(text)
    is_ar = lang == "ar"
    all_text = text + " " + (past_exams or "") + " " + (lecture_notes or "")

    # PASS 1: Extract all topics
    topics = _keywords(all_text, min_freq=2, top_n=80)
    if not topics:
        topics = _keywords(all_text, min_freq=1, top_n=80)

    # PASS 2: Rank importance
    text_lower = all_text.lower()
    emphasis = _RE_EMPHASIS_AR if is_ar else _RE_EMPHASIS_EN
    ranked = []
    for kw in topics[:40]:
        freq = text_lower.count(kw.lower())
        signaled = bool(emphasis.search(all_text[:text_lower.find(kw.lower()) + 100] + all_text[max(0, text_lower.find(kw.lower()) - 100):]))
        is_defined = bool((_RE_DEFINITION_EN if lang == "en" else _RE_DEFINITION_AR).search(all_text))
        score = freq * 3 + (8 if signaled else 0) + (5 if is_defined else 0)
        ranked.append({"concept": kw, "frequency": freq, "signaled": signaled, "defined": is_defined, "importance_score": score})
    ranked.sort(key=lambda x: x["importance_score"], reverse=True)

    # PASS 3: Analyze teacher style
    definitions = _extract_definitions(text, lang)
    comparisons = len(_RE_COMPARE.findall(text))
    if is_ar:
        style = "تعريفي" if len(definitions) > 5 else "متوازن"
    else:
        style = "Definition-heavy" if len(definitions) > 5 else "Balanced"

    # PASS 4: Build exam blueprint
    blueprint = {
        "total_questions": min(20, max(8, len(topics) // 3)),
        "difficulty_distribution": {"easy": 25, "medium": 45, "hard": 30},
        "question_types": {
            "mcq": 35, "short_answer": 30, "essay": 20, "problem_solving": 15,
        },
        "topic_coverage": [r["concept"] for r in ranked[:15]],
    }

    # PASS 5: Generate exam
    exam_questions = []
    for i, r in enumerate(ranked[:15]):
        concept = r["concept"]
        contexts = [s[:150] for s in _sentences(text) if concept.lower() in s.lower()]
        ctx = contexts[0] if contexts else concept

        if is_ar:
            if r["signaled"]:
                q = f'عرف "{concept}" واشرح أهميته. (إشارة المعلم: هذا المفهوم مهم)'
            else:
                q = f'ناقش "{concept}" حسب ما ورد في المادة الدراسية.'
            reason = f'نتيجة Pass {i%5+1}: {"تكرار عالي" if r["frequency"] > 2 else "تعريف أساسي" if r["defined"] else "مفهوم مهم"}'
            qtype = "مقالي" if r["importance_score"] > 20 else "إجابة قصيرة"
        else:
            if r["signaled"]:
                q = f'Define "{concept}" and explain its significance. (Teacher signal: this concept is important)'
            else:
                q = f'Discuss "{concept}" as presented in the course material.'
            reason = f'Pass {i%5+1} result: {"High frequency" if r["frequency"] > 2 else "Core definition" if r["defined"] else "Key concept"}'
            qtype = "Essay" if r["importance_score"] > 20 else "Short Answer"

        exam_questions.append({
            "question": q,
            "type": qtype,
            "probability": min(100, r["importance_score"] * 4),
            "answer_guidance": f"Context: {ctx}",
            "reason": reason,
        })

    return {
        "passes_completed": 5,
        "topics_extracted": len(topics),
        "importance_ranking": ranked[:20],
        "teacher_style": style,
        "exam_blueprint": blueprint,
        "exam_questions": exam_questions,
        "quality_assurance": {
            "chapters_covered": len(_detect_chapters(text)),
            "definitions_preserved": len(definitions),
            "comparisons_detected": comparisons,
            "all_passes_executed": True,
        },
        "language": lang,
    }


def generate_qa_summary(text: str) -> dict:
    lang = _lang(text)
    is_ar = lang == "ar"
    total_words = len(text.split())

    chapters = _detect_chapters(text)
    definitions = _extract_definitions(text, lang)

    emphasis = _RE_EMPHASIS_AR if is_ar else _RE_EMPHASIS_EN
    qa_chapters = []

    for ch in chapters:
        ch_content = ch["content"]
        ch_keywords = _keywords(ch_content, min_freq=1, top_n=10)
        ch_sentences = _sentences(ch_content)
        qa_pairs = []

        for d in definitions[:5]:
            if d["term"].lower() in ch_content.lower():
                q = f'What is "{d["term"]}"?' if not is_ar else f'ما هو "{d["term"]}"؟'
                a = d["definition"][:300]
                qa_pairs.append({"type": "definition", "question": q, "answer": a})
                if len(qa_pairs) >= 3:
                    break

        for kw in ch_keywords[:8]:
            if any(kw.lower() in p["question"].lower() for p in qa_pairs):
                continue
            contexts = [s[:250] for s in ch_sentences if kw.lower() in s.lower()]
            ctx = contexts[0] if contexts else kw
            signaled = bool(emphasis.search(ch_content))
            if signaled:
                q = f'Explain "{kw}" and why it is important.' if not is_ar else f'اشرح "{kw}" ولماذا هو مهم.'
            else:
                q = f'What is "{kw}"?' if not is_ar else f'ما هو "{kw}"؟'
            qa_pairs.append({"type": "concept", "question": q, "answer": ctx})
            if len(qa_pairs) >= 6:
                break

        if len(ch_keywords) >= 2:
            kw1, kw2 = ch_keywords[0], ch_keywords[1]
            q = f'Compare "{kw1}" and "{kw2}".' if not is_ar else f'قارن بين "{kw1}" و "{kw2}".'
            ctx1 = " ".join([s[:120] for s in ch_sentences if kw1.lower() in s.lower()][:1])
            ctx2 = " ".join([s[:120] for s in ch_sentences if kw2.lower() in s.lower()][:1])
            qa_pairs.append({"type": "comparison", "question": q, "answer": f'"{kw1}": {ctx1}\n"{kw2}": {ctx2}'})

        for s in ch_sentences:
            if re.search(r'\d+[\.\)]', s) and len(s) > 30:
                q = "List the key points mentioned." if not is_ar else "اذكر النقاط الرئيسية المذكورة."
                qa_pairs.append({"type": "enumeration", "question": q, "answer": s[:300]})
                break

        if qa_pairs:
            qa_chapters.append({
                "chapter": ch["number"],
                "title": ch["title"],
                "qa_pairs": qa_pairs[:8],
            })

    return {
        "format": "qa",
        "total_questions": sum(len(c["qa_pairs"]) for c in qa_chapters),
        "chapters_covered": len(qa_chapters),
        "total_words": total_words,
        "chapters": qa_chapters,
        "all_definitions": [{"term": d["term"], "definition": d["definition"][:250]} for d in definitions[:10]],
        "language": lang,
    }
