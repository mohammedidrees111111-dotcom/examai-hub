import re
import uuid
import os
import json
from typing import Optional
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache

ARABIC_STOP_WORDS = frozenset({
    "في", "من", "على", "الى", "عن", "هذا", "هذه", "هو", "هي", "هم", "هن",
    "أن", "ان", "إن", "ان", "كان", "كانت", "كانوا", "كل", "بعض", "بين",
    "مع", "بعد", "قبل", "خلال", "حول", "فوق", "تحت", "عند", "ليس", "لم",
    "لن", "لا", "ما", "ماذا", "كيف", "أين", "متى", "لماذا", "ذلك", "تلك",
    "الذي", "التي", "الذين", "هناك", "هنا", "نحو", "حتى", "أيضا", "فقط",
    "جدا", "اخر", "اخرى", "آخر", "أخرى", "اي", "أي", "قد", "سوف", "سيكون",
    "يمكن", "يجب", "كانت", "يكون", "تكون", "وكذلك", "بما", "حيث", "كما",
    "او", "أو", "ثم", "بل", "لكن", "ولكن", "غير", "على", "الي", "إلى",
    "و", "ثم", "الا", "إلا", "انها", "إنها", "انه", "إنه", "فإن", "فان",
    "فقد", "لقد", "وقد", "كان", "اصبح", "أصبح", "ظل", "بقي", "صار",
    "التي", "الذي", "اللذان", "اللتان", "الذين", "الاتي", "الائي",
    "منذا", "منذ", "مذ", "حيثما", "اينما", "أينما", "كيفما", "اذا", "إذا",
    "لو", "لولا", "كلما", "ال", "لل", "ب", "ك", "ل", "ف", "ثم",
})

ENGLISH_STOP_WORDS = frozenset({
    "this", "that", "with", "from", "they", "have", "been", "were", "which", "their",
    "about", "would", "could", "should", "what", "when", "where", "there", "these",
    "those", "other", "after", "before", "while", "being", "also", "such", "then",
    "only", "very", "into", "more", "some", "each", "over", "under", "than",
    "the", "and", "for", "are", "but", "not", "you", "all", "any", "had",
    "her", "was", "one", "our", "out", "has", "did", "get", "its", "let",
    "now", "see", "she", "two", "who", "him", "how", "can", "his", "use",
})

ALL_STOP_WORDS = ARABIC_STOP_WORDS | ENGLISH_STOP_WORDS

_RE_ARABIC_CHAR = re.compile(r'[\u0600-\u06FF]')
_RE_ENGLISH_CHAR = re.compile(r'[a-zA-Z]')
_RE_WORDS = re.compile(r'[\u0600-\u06FFa-zA-Z]{3,}')
_RE_SENTENCE_SPLIT = re.compile(r'[.!?\n،؛؟\r]+')
_RE_NON_ALPHA = re.compile(r'[^\u0600-\u06FFa-zA-Z\s]')

DOCUMENTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "documents")
os.makedirs(DOCUMENTS_DIR, exist_ok=True)

CHUNK_SIZE = 4000
CHUNK_OVERLAP = 400
MAX_WORKERS = min(32, (os.cpu_count() or 4) + 4)


@lru_cache(128)
def _detect_language_cached(text_hash: int, text_preview: str) -> str:
    ar = len(_RE_ARABIC_CHAR.findall(text_preview))
    en = len(_RE_ENGLISH_CHAR.findall(text_preview))
    return "ar" if ar > en else "en"


def _detect_language(text: str) -> str:
    ar = len(_RE_ARABIC_CHAR.findall(text[:2000]))
    en = len(_RE_ENGLISH_CHAR.findall(text[:2000]))
    return "ar" if ar > en else "en"


def _split_sentences(text: str) -> list[str]:
    parts = _RE_SENTENCE_SPLIT.split(text)
    return [p.strip() for p in parts if len(p.strip()) > 10]


def _extract_keywords(text: str, min_freq: int = 2, top_n: int = 80) -> list[str]:
    words = _RE_WORDS.findall(text.lower())
    lang = _detect_language(text)
    min_len = 3 if lang == "ar" else 4
    filtered = [w for w in words if len(w) >= min_len and w not in ALL_STOP_WORDS]
    if not filtered:
        return []
    freq = Counter(filtered)
    result = [w for w, c in freq.most_common(top_n) if c >= min_freq]
    return sorted(result, key=lambda w: (freq[w], len(w)), reverse=True)


def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[dict]:
    chunks = []
    start = 0
    text_len = len(text)
    chunk_num = 0

    while start < text_len:
        end = min(start + chunk_size, text_len)
        raw = text[start:end]

        if end < text_len:
            last_dot = max(raw.rfind("."), raw.rfind("\n"), raw.rfind("؟"), raw.rfind(";"))
            if last_dot > chunk_size // 2:
                end = start + last_dot + 1
                raw = text[start:end]

        chunk_num += 1
        sentences = _split_sentences(raw)
        keywords = _extract_keywords(raw, min_freq=1, top_n=15)

        chunks.append({
            "i": chunk_num,
            "text": raw.strip(),
            "w": len(raw.split()),
            "kw": keywords[:10],
        })

        start = end - overlap if end < text_len else text_len
        if start <= 0:
            start = end

    return chunks


def _process_chunk_predict(chunk: dict, offset: int, lang: str, is_ar: bool, questions_per: int, all_keywords: list[str]) -> list[dict]:
    sentences = _split_sentences(chunk["text"])
    chunk_kws = chunk.get("kw", [])
    combined_kws = list(dict.fromkeys(chunk_kws + all_keywords))
    return _generate_questions(chunk["text"], sentences, questions_per, lang, is_ar, offset, combined_kws)


def _process_chunk_summarize(chunk: dict, lang: str, is_ar: bool) -> list[tuple]:
    sentences = _split_sentences(chunk["text"])
    chunk_kws = chunk.get("kw", [])
    scored = []
    for j, s in enumerate(sentences):
        score = 0
        s_lower = s.lower()
        for kw in chunk_kws[:8]:
            if kw.lower() in s_lower:
                score += 2
        pos_ratio = j / max(len(sentences) - 1, 1)
        if pos_ratio < 0.15 or pos_ratio > 0.85:
            score += 1
        wl = len(s.split())
        if 8 < wl < 60:
            score += 1
        if len(s) > 30:
            score += 0.5
        scored.append((s, score))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:3]


def _generate_questions(text: str, sentences: list[str], num: int, lang: str, is_ar: bool, offset: int = 0, keywords: Optional[list[str]] = None) -> list[dict]:
    if not keywords:
        keywords = _extract_keywords(text, min_freq=2)
    if not keywords:
        keywords = _extract_keywords(text, min_freq=1)

    TEMPLATES_AR = [
        'املأ الفراغ: "{blank}"',
        'أي مما يلي يشرح "{keyword}" بشكل أفضل؟',
        'ما الفكرة الرئيسية للنص؟\n\n"{passage}"',
        'حسب النص، أي عبارة عن "{keyword}" صحيحة؟',
        'صح أم خطأ: "{statement}"',
    ]
    TEMPLATES_EN = [
        'Fill in the blank: "{blank}"',
        'Which of the following best explains "{keyword}"?',
        'What is the main idea?\n\n"{passage}"',
        'According to the text, which statement about "{keyword}" is correct?',
        'True or False: "{statement}"',
    ]
    TYPES_AR = ["املأ-الفراغ", "تعريف", "فكرة-رئيسية", "فهم", "صح-وخطأ"]
    TYPES_EN = ["fill-blank", "definition", "main-idea", "comprehension", "true-false"]

    templates = TEMPLATES_AR if is_ar else TEMPLATES_EN
    type_labels = TYPES_AR if is_ar else TYPES_EN

    sorted_sentences = sorted(sentences, key=len, reverse=True)
    target = min(len(sorted_sentences), num)
    questions = []

    for i in range(target):
        sentence = sorted_sentences[i]
        ks = sentence[:250]
        qtype = (i + offset) % 5
        kw = keywords[(i + offset) % len(keywords)]

        if qtype == 0:
            blank = ks
            for k in sorted(keywords, key=len, reverse=True):
                if k in blank and k.lower() not in ALL_STOP_WORDS:
                    blank = blank.replace(k, "________", 1)
                    break
            question = templates[0].replace("{blank}", blank)
        elif qtype == 1:
            question = templates[1].replace("{keyword}", kw)
        elif qtype == 2:
            passage = ks[:200] + ("..." if len(ks) > 200 else "")
            question = templates[2].replace("{passage}", passage)
        elif qtype == 3:
            question = templates[3].replace("{keyword}", kw)
        else:
            question = templates[4].replace("{statement}", ks[:120])

        wrong = [k for k in keywords if k.lower() != kw.lower()]
        import random
        random.seed((i + offset) * 7)
        if len(wrong) >= 3:
            wrong = random.sample(wrong, 3)
        while len(wrong) < 3:
            wrong.append("خيار بديل" if is_ar else "alternative")
        correct = kw
        options = wrong + [correct]
        random.shuffle(options)

        questions.append({
            "question": question,
            "options": options[:4],
            "answer": correct,
            "type": type_labels[qtype],
            "language": lang,
        })

    return questions


def predict_exam_questions(text: str, num_questions: int = 5) -> list[dict]:
    text = text.strip()
    lang = _detect_language(text)
    is_ar = lang == "ar"

    if len(text) > 8000:
        return _parallel_large_predict(text, num_questions, lang, is_ar)

    sentences = _split_sentences(text)
    if len(sentences) < 3:
        msg = "المحتوى قصير جدا. يرجى توفير مادة دراسية أطول." if is_ar else "Content too short."
        return [{"question": msg, "options": [], "answer": ""}]

    return _generate_questions(text, sentences, num_questions, lang, is_ar)


def _parallel_large_predict(text: str, num_questions: int, lang: str, is_ar: bool) -> list[dict]:
    chunks = _chunk_text(text, chunk_size=5000)
    all_keywords = _extract_keywords(text, min_freq=3, top_n=40) or _extract_keywords(text, min_freq=1, top_n=40)

    best_chunks = sorted(chunks, key=lambda c: len(c.get("kw", [])), reverse=True)[:min(8, len(chunks))]
    q_per_chunk = max(1, num_questions // max(1, len(best_chunks)))
    extra = num_questions - (q_per_chunk * len(best_chunks))

    questions = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {}
        for i, chunk in enumerate(best_chunks):
            n = q_per_chunk + (1 if i < extra else 0)
            if n <= 0:
                continue
            futures[executor.submit(_process_chunk_predict, chunk, i * 100, lang, is_ar, n, all_keywords)] = i

        results_by_index = {}
        for future in as_completed(futures):
            idx = futures[future]
            try:
                results_by_index[idx] = future.result(timeout=30)
            except Exception:
                results_by_index[idx] = []

        for i in sorted(results_by_index):
            questions.extend(results_by_index[i])

    return questions[:num_questions]


def teacher_mode_explain(text: str, topic: Optional[str] = None) -> dict:
    text = text.strip()
    lang = _detect_language(text)
    is_ar = lang == "ar"

    if len(text) > 10000:
        return _parallel_large_teacher(text, topic, lang, is_ar)
    return _teacher_mode_single(text, topic, lang, is_ar)


def _parallel_large_teacher(text: str, topic: Optional[str], lang: str, is_ar: bool) -> dict:
    chunks = _chunk_text(text, chunk_size=4000)
    total_words = sum(c["w"] for c in chunks)
    all_keywords = _extract_keywords(text, min_freq=3, top_n=30) or _extract_keywords(text, min_freq=1, top_n=30)

    all_bullets = []
    all_sections = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_bullets = executor.submit(_collect_bullets_parallel, chunks[:12], all_keywords)
        future_sections = executor.submit(_collect_sections_parallel, chunks[:12])
        try:
            all_bullets = future_bullets.result(timeout=30)
        except Exception:
            pass
        try:
            all_sections = future_sections.result(timeout=30)
        except Exception:
            pass

    if total_words > 30000:
        diff = "متقدم جدا" if is_ar else "Very Advanced"
    elif total_words > 10000:
        diff = "متقدم" if is_ar else "Advanced"
    elif total_words > 3000:
        diff = "متوسط" if is_ar else "Intermediate"
    else:
        diff = "مبتدئ" if is_ar else "Beginner"

    if is_ar:
        summary = f"مستند من {total_words} كلمة ({len(chunks)} مقطع). المواضيع: {', '.join(all_keywords[:8])}."
        resources = [
            "راجع تعريفات المفاهيم الأساسية", "تدرب على أسئلة نموذجية",
            "أنشئ بطاقات تعليمية", "اكتب ملخصا بكلماتك", "درّس المادة لزميل", "حل تمارين نهاية الفصل",
        ]
    else:
        summary = f"Document of {total_words} words ({len(chunks)} sections). Topics: {', '.join(all_keywords[:8])}."
        resources = [
            "Review key concept definitions", "Practice with sample questions",
            "Create flashcards", "Write a summary in your own words",
            "Teach this to a classmate", "Complete end-of-chapter exercises",
        ]

    return {
        "summary": summary, "key_concepts": all_keywords[:15],
        "difficulty_level": diff,
        "suggested_study_time": f"{max(30, total_words // 30)} {'دقيقة' if is_ar else 'minutes'}",
        "topic": topic or (_guess_topic(all_keywords, text)),
        "bullet_points": all_bullets[:15],
        "sections": all_sections[:20],
        "recommended_resources": resources,
        "total_words": total_words, "total_chunks": len(chunks), "language": lang,
    }


def _teacher_mode_single(text: str, topic: Optional[str], lang: str, is_ar: bool) -> dict:
    sentences = _split_sentences(text)
    wc = len(text.split())
    keywords = _extract_keywords(text, min_freq=2) or _extract_keywords(text, min_freq=1)
    sections = _split_into_sections(text)

    if wc > 1500:
        diff = "متقدم" if is_ar else "Advanced"
    elif wc > 400:
        diff = "متوسط" if is_ar else "Intermediate"
    else:
        diff = "مبتدئ" if is_ar else "Beginner"

    if is_ar:
        summary = f"مادة من {wc} كلمة. تركز على: {', '.join(keywords[:8])}." if keywords else f"مستند من {wc} كلمة."
        resources = ["راجع تعريفات المفاهيم", "تدرب على أسئلة نموذجية", "أنشئ بطاقات تعليمية", "اكتب ملخصا", "درّس المادة لزميل"]
    else:
        summary = f"Material of {wc} words. Focuses on: {', '.join(keywords[:8])}." if keywords else f"Document of {wc} words."
        resources = ["Review definitions", "Practice with sample questions", "Create flashcards", "Write a summary", "Teach a classmate"]

    return {
        "summary": summary, "key_concepts": keywords[:12], "difficulty_level": diff,
        "suggested_study_time": f"{max(10, wc // 30)} {'دقيقة' if is_ar else 'minutes'}",
        "topic": topic or _guess_topic(keywords, text),
        "bullet_points": _generate_bullet_points(sentences, keywords),
        "sections": sections, "recommended_resources": resources,
        "total_words": wc, "total_chunks": 1, "language": lang,
    }


def summarize_text(text: str, max_length: Optional[int] = 200) -> dict:
    text = text.strip()
    lang = _detect_language(text)
    is_ar = lang == "ar"

    if len(text) > 12000:
        return _parallel_large_summarize(text, lang, is_ar)
    return _summarize_single(text, lang, is_ar)


def _parallel_large_summarize(text: str, lang: str, is_ar: bool) -> dict:
    chunks = _chunk_text(text, chunk_size=5000)
    total_words = sum(c["w"] for c in chunks)
    all_keywords = _extract_keywords(text, min_freq=3, top_n=30) or _extract_keywords(text, min_freq=1, top_n=30)

    all_scored = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(_process_chunk_summarize, chunk, lang, is_ar): i for i, chunk in enumerate(chunks[:15])}
        for future in as_completed(futures):
            try:
                all_scored.extend(future.result(timeout=30))
            except Exception:
                pass

    all_scored.sort(key=lambda x: x[1], reverse=True)
    selected = [s[0] for s in all_scored[:25]]
    sep = " " if is_ar else ". "
    summary = sep.join(selected)
    if not summary.endswith("."):
        summary += "."

    return {
        "original_length": total_words, "summary_length": len(summary.split()),
        "summary": summary, "keywords": all_keywords[:15],
        "compression_ratio": f"{len(summary.split()) / max(total_words, 1) * 100:.1f}%",
        "sections": len(chunks), "total_chunks": len(chunks), "language": lang,
    }


def _summarize_single(text: str, lang: str, is_ar: bool) -> dict:
    sentences = _split_sentences(text)
    wc = len(text.split())
    if len(sentences) <= 5:
        return {
            "original_length": wc, "summary_length": wc, "summary": text,
            "keywords": _extract_keywords(text, min_freq=1)[:10],
            "compression_ratio": "100%", "sections": 1, "total_chunks": 1, "language": lang,
        }

    keywords = _extract_keywords(text, min_freq=2) or _extract_keywords(text, min_freq=1)
    scored = []
    for i, s in enumerate(sentences):
        score = 0
        sl = s.lower()
        for kw in keywords:
            if kw.lower() in sl:
                score += 2
        pos = i / max(len(sentences) - 1, 1)
        if pos < 0.15 or pos > 0.85:
            score += 1
        wl = len(s.split())
        if 8 < wl < 60:
            score += 1
        if len(s) > 30:
            score += 0.5
        scored.append((s, i, score))

    scored.sort(key=lambda x: x[2], reverse=True)
    target = max(3, min(len(sentences) // 3, 20))
    top = sorted(scored[:target], key=lambda x: x[1])
    selected = [s[0] for s in top]
    sep = " " if is_ar else ". "
    summary = sep.join(selected)
    if not summary.endswith("."):
        summary += "."

    return {
        "original_length": wc, "summary_length": len(summary.split()),
        "summary": summary, "keywords": keywords[:12],
        "compression_ratio": f"{len(summary.split()) / max(wc, 1) * 100:.1f}%",
        "sections": len(_split_into_sections(text)), "total_chunks": 1, "language": lang,
    }


def _collect_bullets_parallel(chunks: list[dict], all_keywords: list[str]) -> list[str]:
    bullets = []
    seen = set()
    for chunk in chunks:
        sentences = _split_sentences(chunk["text"])
        for s in sentences[:5]:
            prefix = s[:80]
            if prefix in seen:
                continue
            found = False
            for kw in all_keywords[:8]:
                if kw.lower() in s.lower():
                    bullets.append(f"{kw}: {s[:150]}{'...' if len(s) > 150 else ''}")
                    seen.add(prefix)
                    found = True
                    break
            if not found and len(bullets) < 8:
                bullets.append(s[:150] + ("..." if len(s) > 150 else ""))
                seen.add(prefix)
            if len(bullets) >= 15:
                return bullets
    return bullets


def _collect_sections_parallel(chunks: list[dict]) -> list[dict]:
    sections = []
    for chunk in chunks:
        for para in chunk["text"].split("\n\n")[:2]:
            p = para.strip()
            if len(p) > 40:
                sections.append({
                    "number": len(sections) + 1,
                    "preview": p[:150] + ("..." if len(p) > 150 else ""),
                    "word_count": len(p.split()),
                    "sentences": len(_split_sentences(p)),
                })
            if len(sections) >= 20:
                return sections
    return sections


def _split_into_sections(text: str) -> list[dict]:
    paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 30]
    if len(paragraphs) <= 1:
        paragraphs = [text]
    sections = []
    for i, p in enumerate(paragraphs[:15]):
        sections.append({
            "number": i + 1, "preview": p[:150] + ("..." if len(p) > 150 else ""),
            "word_count": len(p.split()), "sentences": len(_split_sentences(p)),
        })
    return sections


def _guess_topic(keywords: list[str], text: str = "") -> str:
    if not keywords:
        return "عام" if _detect_language(text) == "ar" else "General"
    kw = keywords[0]
    return kw if any('\u0600' <= c <= '\u06FF' for c in kw) else kw.capitalize()


def _generate_bullet_points(sentences: list[str], keywords: list[str]) -> list[str]:
    if not sentences:
        lang = _detect_language(" ".join(keywords) if keywords else "")
        return ["لا يوجد محتوى كاف."] if lang == "ar" else ["No content to summarize."]
    result = []
    seen = set()
    for s in sentences[:20]:
        for kw in keywords[:8]:
            if kw.lower() in s.lower() and s[:80] not in seen:
                result.append(f"{kw}: {s[:180]}{'...' if len(s) > 180 else ''}")
                seen.add(s[:80])
                break
        if len(result) >= 12:
            break
    return result[:12]


def save_document(text: str, filename: str = "") -> str:
    doc_id = uuid.uuid4().hex[:12]
    chunks = _chunk_text(text)
    # Store compact: full text + chunk indices only
    meta = {
        "id": doc_id, "file": filename,
        "chars": len(text), "words": len(text.split()),
        "chunks": [{"i": c["i"], "start": c.get("start_char", c["i"] * CHUNK_SIZE), "kw": c["kw"]} for c in chunks],
        "text": text,
    }
    with open(os.path.join(DOCUMENTS_DIR, f"{doc_id}.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False)
    return doc_id


def load_document(doc_id: str) -> Optional[dict]:
    path = os.path.join(DOCUMENTS_DIR, f"{doc_id}.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        doc = json.load(f)
    return {"full_text": doc["text"], "filename": doc.get("file", ""), "total_chars": doc["chars"], "total_words": doc["words"], "chunks": doc["chunks"]}


def get_chunk_text(doc_id: str, chunk_index: int) -> Optional[str]:
    doc = load_document(doc_id)
    if not doc:
        return None
    full = doc["full_text"]
    start = chunk_index * CHUNK_SIZE
    end = min(start + CHUNK_SIZE + CHUNK_OVERLAP, len(full))
    return full[start:end]
