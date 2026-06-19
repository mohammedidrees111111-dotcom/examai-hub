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
    r'note that|remember|do not forget|pay attention|you should|you must|be aware|'
    r'always|never|must|required|mandatory|absolutely|definitely)',
    re.IGNORECASE
)
_RE_EMPHASIS_AR = re.compile(
    r'(?:مهم|هام|ملاحظة|انتبه|تذكر|لاحظ أن|يجب أن|من الضروري|أساسي|جوهري|محوري|دائما|أبدا|'
    r'لا تنس|تأكد|انتبه جيدا|ركز على)', re.IGNORECASE
)
_RE_COMPARE = re.compile(
    r'(?:unlike|whereas|while|in contrast|compared to|differs from|better than|worse than|'
    r'more than|less than|similar to|same as|however|on the other hand|بينما|مقارنة|على العكس|'
    r'بالمقابل|يختلف عن|يشبه|مشابه)', re.IGNORECASE
)
_RE_EXCEPTION = re.compile(
    r'(?:however|but|except|unless|although|though|despite|notwithstanding|'
    r'interestingly|surprisingly|notably|لكن|ولكن|إلا|عدا|ما عدا|غير أن|'
    r'باستثناء|على الرغم)', re.IGNORECASE
)
_RE_LIST = re.compile(r'(?:^|\n)\s*(?:[\d]+[\.\)]\s+|[•\-\*\✓\✔\→]\s+)(.+?)(?:\n|$)', re.MULTILINE)

AR_STOP = frozenset({"في","من","على","عن","هذا","هذه","هو","هي","هم","كل","بعض","بين","مع","بعد","قبل","خلال","حول","عند","ليس","لم","لن","لا","ما","ذلك","تلك","الذي","التي","هناك","هنا","حتى","ايضا","فقط"})
EN_STOP = frozenset({"the","and","for","are","but","not","you","all","any","had","this","that","with","from","they","have","been","were","which","about","would","could","should","what","when","where","there","these","those"})
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


class GlobalContext:
    def __init__(self, text: str):
        self.text = text
        self.lang = _lang(text)
        self.is_ar = self.lang == "ar"
        self.total_words = len(text.split())
        self.all_keywords = _keywords(text, min_freq=2, top_n=100) or _keywords(text, min_freq=1, top_n=100)

        self.emphasis_pattern = _RE_EMPHASIS_AR if self.is_ar else _RE_EMPHASIS_EN
        self.definition_pattern = _RE_DEFINITION_AR if self.is_ar else _RE_DEFINITION_EN

        self.chapters = self._analyze_chapters()
        self.global_definitions = self._extract_all_definitions()
        self.concept_map = self._build_concept_map()
        self.importance_ranking = self._rank_global_importance()
        self.teacher_profile = self._build_teacher_profile()
        self.relationships = self._build_relationships()

    def _analyze_chapters(self) -> list[dict]:
        matches = list(_RE_CHAPTER.finditer(self.text))
        chapters = []
        if len(matches) >= 2:
            for i, m in enumerate(matches):
                start = m.start()
                end = matches[i+1].start() if i+1 < len(matches) else len(self.text)
                content = self.text[start:end].strip()
                title = m.group().strip()
                ch_kw = _keywords(content, min_freq=1, top_n=15)
                ch_defs = self._extract_defs(content)
                ch_emphasis = len(self.emphasis_pattern.findall(content))
                ch_compares = len(_RE_COMPARE.findall(content))
                ch_exceptions = len(_RE_EXCEPTION.findall(content))
                ch_lists = _RE_LIST.findall(content)
                chapters.append({
                    "number": i+1,
                    "title": title[:120],
                    "content": content,
                    "word_count": len(content.split()),
                    "keywords": ch_kw,
                    "definitions": ch_defs,
                    "emphasis_count": ch_emphasis,
                    "comparison_count": ch_compares,
                    "exception_count": ch_exceptions,
                    "lists": ch_lists[:5],
                    "importance": self._chapter_importance(content, ch_kw),
                })
        else:
            paragraphs = [p.strip() for p in self.text.split("\n\n") if len(p.strip()) > 80]
            for i, p in enumerate(paragraphs):
                ch_kw = _keywords(p, min_freq=1, top_n=10)
                chapters.append({
                    "number": i+1,
                    "title": p.split("\n")[0][:80],
                    "content": p,
                    "word_count": len(p.split()),
                    "keywords": ch_kw,
                    "definitions": self._extract_defs(p),
                    "emphasis_count": len(self.emphasis_pattern.findall(p)),
                    "comparison_count": len(_RE_COMPARE.findall(p)),
                    "exception_count": len(_RE_EXCEPTION.findall(p)),
                    "lists": _RE_LIST.findall(p)[:3],
                    "importance": 5,
                })
        return chapters

    def _chapter_importance(self, content, keywords) -> int:
        score = 0
        score += len(self.emphasis_pattern.findall(content)) * 3
        score += len(_RE_DEFINITION_EN.findall(content) or _RE_DEFINITION_AR.findall(content)) * 2
        score += len(_RE_COMPARE.findall(content)) * 2
        score += len(keywords) * 1
        return min(100, score)

    def _extract_defs(self, text):
        pattern = _RE_DEFINITION_AR if self.is_ar else _RE_DEFINITION_EN
        defs = []
        seen = set()
        for m in re.finditer(pattern, text):
            d = m.group(1).strip()
            key = d[:60].lower()
            if key not in seen:
                seen.add(key)
                kw = _keywords(d, min_freq=1, top_n=1)
                defs.append({"term": kw[0] if kw else "concept", "definition": d[:250]})
        return defs[:8]

    def _extract_all_definitions(self) -> list[dict]:
        all_defs = []
        seen = set()
        for ch in self.chapters:
            for d in ch.get("definitions", []):
                key = d["term"].lower()
                if key not in seen:
                    seen.add(key)
                    all_defs.append(d)
        return all_defs[:20]

    def _build_concept_map(self) -> dict:
        text_lower = self.text.lower()
        concept_map = {}
        for kw in self.all_keywords[:60]:
            freq = text_lower.count(kw.lower())
            chapters_present = []
            for ch in self.chapters:
                if kw.lower() in ch["content"].lower():
                    chapters_present.append(ch["number"])
            signaled = bool(self.emphasis_pattern.search(
                self.text[max(0, text_lower.find(kw.lower())-100):text_lower.find(kw.lower())+150]
            ))
            is_defined = any(kw.lower() in d["definition"].lower() for d in self.global_definitions)
            concept_map[kw] = {
                "total_frequency": freq,
                "chapters_appearing": chapters_present,
                "chapter_count": len(chapters_present),
                "explicitly_signaled": signaled,
                "has_definition": is_defined,
                "is_cross_chapter": len(chapters_present) > 1,
            }
        return concept_map

    def _rank_global_importance(self) -> list[dict]:
        text_lower = self.text.lower()
        ranked = []
        for kw in self.all_keywords[:60]:
            cm = self.concept_map.get(kw, {})
            freq = cm.get("total_frequency", text_lower.count(kw.lower()))
            ch_count = cm.get("chapter_count", 1)
            signaled = cm.get("explicitly_signaled", False)
            defined = cm.get("has_definition", False)
            cross = cm.get("is_cross_chapter", False)
            score = freq * 3 + (ch_count * 5) + (15 if signaled else 0) + (10 if defined else 0) + (8 if cross else 0)
            ranked.append({"concept": kw, "frequency": freq, "chapters": ch_count, "signaled": signaled, "defined": defined, "cross_chapter": cross, "importance_score": score})
        ranked.sort(key=lambda x: x["importance_score"], reverse=True)
        return ranked[:40]

    def _build_teacher_profile(self) -> dict:
        total_emphasis = sum(ch.get("emphasis_count", 0) for ch in self.chapters)
        total_defs = len(self.global_definitions)
        total_compares = sum(ch.get("comparison_count", 0) for ch in self.chapters)
        total_exceptions = sum(ch.get("exception_count", 0) for ch in self.chapters)
        chapter_count = len(self.chapters)
        if chapter_count == 0:
            chapter_count = 1

        avg_emphasis = total_emphasis / chapter_count
        def_ratio = total_defs / max(chapter_count, 1)

        if self.is_ar:
            if def_ratio > 2:
                style = "أكاديمي صارم — يركز بشكل كبير على التعاريف والمصطلحات الدقيقة"
            elif avg_emphasis > 3:
                style = "توجيهي — يعطي إشارات واضحة للمواضيع المهمة في الامتحان"
            elif total_compares > chapter_count:
                style = "تحليلي — يفضل أسئلة المقارنة والتحليل العميق"
            else:
                style = "متوازن — يمزج بين التعاريف والتطبيقات والتحليل"

            question_prefs = []
            if total_defs > 5: question_prefs.append("أسئلة تعريفية (عرف، اشرح)")
            if total_compares > 3: question_prefs.append("أسئلة مقارنة (قارن، وازن)")
            if total_exceptions > 2: question_prefs.append("أسئلة استثناءات (فخاخ)")
            if avg_emphasis > 2: question_prefs.append("أسئلة على المواضيع المؤكد عليها")

            difficulty = "صعب" if avg_emphasis > 5 else "متوسط" if avg_emphasis > 2 else "سهل"
        else:
            if def_ratio > 2:
                style = "Rigorous Academic — heavily emphasizes precise definitions and terminology"
            elif avg_emphasis > 3:
                style = "Guided — gives clear signals about what's important for the exam"
            elif total_compares > chapter_count:
                style = "Analytical — favors comparison questions and deep analysis"
            else:
                style = "Balanced — mixes definitions, applications, and analysis"

            question_prefs = []
            if total_defs > 5: question_prefs.append("Definition questions (Define, Explain)")
            if total_compares > 3: question_prefs.append("Comparison questions (Compare, Contrast)")
            if total_exceptions > 2: question_prefs.append("Exception/trap questions")
            if avg_emphasis > 2: question_prefs.append("Questions on emphasized topics")

            difficulty = "Hard" if avg_emphasis > 5 else "Medium" if avg_emphasis > 2 else "Easy"

        return {
            "teaching_style": style,
            "preferred_question_types": question_prefs,
            "difficulty_level": difficulty,
            "emphasis_frequency": round(avg_emphasis, 1),
            "definition_density": round(def_ratio, 1),
            "comparison_frequency": total_compares,
            "exception_frequency": total_exceptions,
            "total_signals_detected": total_emphasis,
            "most_important_chapter": max(self.chapters, key=lambda c: c.get("importance", 0)).get("title", "") if self.chapters else "",
        }

    def _build_relationships(self) -> list[dict]:
        relationships = []
        seen_pairs = set()
        for kw in self.all_keywords[:30]:
            cm = self.concept_map.get(kw, {})
            if cm.get("is_cross_chapter"):
                related = []
                for kw2 in self.all_keywords[:30]:
                    if kw2 == kw:
                        continue
                    cm2 = self.concept_map.get(kw2, {})
                    shared = set(cm.get("chapters_appearing", [])) & set(cm2.get("chapters_appearing", []))
                    if len(shared) >= 2:
                        pair = tuple(sorted([kw, kw2]))
                        if pair not in seen_pairs:
                            seen_pairs.add(pair)
                            related.append({"concept": kw2, "shared_chapters": len(shared)})
                if related:
                    relationships.append({"concept": kw, "chapter_count": cm.get("chapter_count", 0), "related_to": related[:5]})
        return relationships[:15]

    def get_full_context(self) -> dict:
        return {
            "document_overview": {
                "total_words": self.total_words,
                "total_chapters": len(self.chapters),
                "language": self.lang,
                "total_concepts": len(self.all_keywords),
                "total_definitions": len(self.global_definitions),
            },
            "teacher_profile": self.teacher_profile,
            "global_importance_ranking": self.importance_ranking[:20],
            "cross_chapter_concepts": [r for r in self.importance_ranking if r.get("cross_chapter")][:10],
            "concept_relationships": self.relationships[:10],
            "chapter_analysis": [{
                "number": ch["number"],
                "title": ch["title"],
                "word_count": ch["word_count"],
                "importance": ch["importance"],
                "top_concepts": ch["keywords"][:8],
                "definitions_count": len(ch.get("definitions", [])),
                "emphasis_signals": ch.get("emphasis_count", 0),
            } for ch in self.chapters],
            "exam_prediction_insights": {
                "high_probability_topics": [r["concept"] for r in self.importance_ranking[:12] if r["importance_score"] > 30],
                "definition_heavy": len(self.global_definitions) > 8,
                "comparison_heavy": sum(ch.get("comparison_count", 0) for ch in self.chapters) > len(self.chapters),
                "exception_heavy": sum(ch.get("exception_count", 0) for ch in self.chapters) > 5,
                "chapters_most_likely_tested": [ch["title"][:60] for ch in sorted(self.chapters, key=lambda c: c.get("importance", 0), reverse=True)[:3]],
            },
        }


def generate_global_analysis(text: str) -> dict:
    ctx = GlobalContext(text)
    context = ctx.get_full_context()

    is_ar = ctx.is_ar
    imp = ctx.importance_ranking
    defs = ctx.global_definitions
    chapters = ctx.chapters

    # Exam Section using global context
    mcq = _gen_mcq_global(imp, ctx.all_keywords, ctx.text, defs, is_ar, 8)
    short = _gen_short_global(imp, defs, chapters, is_ar, 4)
    essay = _gen_essay_global(imp, chapters, ctx.concept_map, is_ar, 3)
    problems = _gen_problems_global(imp, defs, is_ar, 2)

    # Teacher insights
    insights = _gen_teacher_insights(ctx, imp, is_ar)

    # Summary using global understanding
    summary_text = _gen_contextual_summary(ctx, is_ar)

    return {
        "global_context": context,
        "teacher_insights": insights,
        "full_exam": {
            "sections": [
                {"section": "A", "title": "MCQ" if not is_ar else "اختياري", "marks": len(mcq)*2, "questions": mcq},
                {"section": "B", "title": "Short Answer" if not is_ar else "إجابة قصيرة", "marks": len(short)*6, "questions": short},
                {"section": "C", "title": "Essay" if not is_ar else "مقالي", "marks": len(essay)*15, "questions": essay},
                {"section": "D", "title": "Problem Solving" if not is_ar else "مسائل", "marks": len(problems)*10, "questions": problems},
            ],
        },
        "contextual_summary": summary_text,
        "language": ctx.lang,
    }


def _gen_mcq_global(ranked, keywords, text, defs, is_ar, count):
    import random
    questions = []
    for i, r in enumerate(ranked[:count]):
        concept = r["concept"]
        contexts = [s[:200] for s in _sentences(text) if concept.lower() in s.lower()]
        ctx = contexts[0] if contexts else concept
        wrong = [k for k in keywords if k.lower() != concept.lower()]
        random.shuffle(wrong)
        distractors = wrong[:3]
        while len(distractors) < 3:
            distractors.append("Option " + chr(65+len(distractors)))
        options = distractors + [concept]
        random.shuffle(options)
        correct_idx = options.index(concept)

        if is_ar:
            q = f'حسب النص، أي مما يلي يعرف "{concept}"؟'
            exp = f'الإجابة الصحيحة: {concept}. {ctx[:100]}'
        else:
            q = f'Based on the text, which defines "{concept}"?'
            exp = f'Correct: {concept}. {ctx[:100]}'

        questions.append({
            "number": i+1, "marks": 2, "question": q,
            "options": [f"{chr(65+j)}) {o}" for j, o in enumerate(options)],
            "correct": chr(65+correct_idx), "correct_answer": concept, "explanation": exp,
        })
    return questions


def _gen_short_global(ranked, defs, chapters, is_ar, count):
    questions = []
    used = set()
    for d in defs[:count]:
        if d["term"] in used:
            continue
        used.add(d["term"])
        ch = next((c for c in chapters if d["term"].lower() in c["content"].lower()), None)
        chapter_hint = f" (mentioned in {ch['title'][:60]})" if ch else ""
        if is_ar:
            q = f'عرف "{d["term"]}" حسب المادة{chapter_hint}.'
        else:
            q = f'Define "{d["term"]}" as presented in the material{chapter_hint}.'
        questions.append({
            "number": len(questions)+1, "marks": 6, "question": q,
            "model_answer": d["definition"][:250],
        })
        if len(questions) >= count:
            break
    return questions


def _gen_essay_global(ranked, chapters, concept_map, is_ar, count):
    questions = []
    cross = [r for r in ranked if r.get("cross_chapter")][:count]
    for r in cross:
        cm = concept_map.get(r["concept"], {})
        ch_nums = cm.get("chapters_appearing", [])
        ch_names = [c["title"][:50] for c in chapters if c["number"] in ch_nums]
        span = ", ".join(ch_names[:3]) if ch_names else "multiple chapters"
        if is_ar:
            q = f'"{r["concept"]}" يظهر عبر {span}. ناقش هذا المفهوم بشكل شامل مع أمثلة من كل المواضع.'
        else:
            q = f'"{r["concept"]}" appears across {span}. Discuss this concept comprehensively with examples from each context.'
        questions.append({"number": len(questions)+1, "marks": 15, "question": q, "topic": r["concept"], "spans_chapters": len(ch_nums)})
    return questions


def _gen_problems_global(ranked, defs, is_ar, count):
    import random
    questions = []
    for i in range(min(count, len(ranked))):
        r = ranked[i]
        d = defs[i] if i < len(defs) else None
        ctx = d["definition"][:150] if d else r["concept"]
        if is_ar:
            q = f'طبق "{r["concept"]}" على مشكلة واقعية. اشرح الحل خطوة بخطوة.'
        else:
            q = f'Apply "{r["concept"]}" to a real-world problem. Show your step-by-step solution.'
        questions.append({"number": len(questions)+1, "marks": 10, "question": q, "context": ctx})
    return questions


def _gen_teacher_insights(ctx, ranked, is_ar):
    tp = ctx.teacher_profile
    cross = len([r for r in ranked if r.get("cross_chapter")])

    if is_ar:
        strategy = [
            f"أسلوب المعلم: {tp['teaching_style']}",
            f"مستوى الصعوبة المتوقع: {tp['difficulty_level']}",
            f"عدد الإشارات المهمة المكتشفة: {tp['total_signals_detected']} إشارة",
            f"أكثر فصل مرجح في الامتحان: {tp['most_important_chapter'][:60]}",
            f"عدد المفاهيم المتكررة عبر الفصول: {cross} مفهوم",
            "نصيحة: ركز على المفاهيم المتكررة عبر الفصول — احتمال ظهورها في الامتحان أعلى بكثير.",
        ]
    else:
        strategy = [
            f"Teaching style: {tp['teaching_style']}",
            f"Predicted difficulty: {tp['difficulty_level']}",
            f"Emphasis signals detected: {tp['total_signals_detected']}",
            f"Most likely chapter on exam: {tp['most_important_chapter'][:60]}",
            f"Cross-chapter concepts: {cross}",
            "Tip: Focus on concepts appearing across multiple chapters — much higher exam probability.",
        ]

    return {
        "strategy": strategy,
        "question_types_to_practice": tp.get("preferred_question_types", []),
        "concepts_to_memorize": [r["concept"] for r in ranked[:8] if r.get("defined")],
        "concepts_to_compare": [r["concept"] for r in ranked if r.get("cross_chapter")][:5],
        "top_10_most_important": [{"concept": r["concept"], "score": r["importance_score"]} for r in ranked[:10]],
    }


def _gen_contextual_summary(ctx, is_ar):
    chapters = ctx.chapters
    imp = ctx.importance_ranking

    if is_ar:
        lines = [f"تحليل شامل لـ {len(chapters)} فصل ({ctx.total_words} كلمة)"]
        lines.append(f"أسلوب المعلم: {ctx.teacher_profile['teaching_style']}")
        lines.append("")
        for ch in chapters:
            lines.append(f"الفصل {ch['number']}: {ch['title'][:80]}")
            lines.append(f"المفاهيم الأساسية: {', '.join(ch['keywords'][:6])}")
            signals = ch.get('emphasis_count', 0)
            if signals > 0:
                lines.append(f"إشارات مهمة: {signals}")
            lines.append("")
        lines.append("أهم 5 مفاهيم شاملة:")
        for r in imp[:5]:
            lines.append(f"- {r['concept']} (تكرار: {r['frequency']}, عبر {r['chapters']} فصل)")
    else:
        lines = [f"Comprehensive analysis of {len(chapters)} chapters ({ctx.total_words} words)"]
        lines.append(f"Teaching style: {ctx.teacher_profile['teaching_style']}")
        lines.append("")
        for ch in chapters:
            lines.append(f"Chapter {ch['number']}: {ch['title'][:80]}")
            lines.append(f"Key concepts: {', '.join(ch['keywords'][:6])}")
            signals = ch.get('emphasis_count', 0)
            if signals > 0:
                lines.append(f"Emphasis signals: {signals}")
            lines.append("")
        lines.append("Top 5 Global Concepts:")
        for r in imp[:5]:
            lines.append(f"- {r['concept']} (freq: {r['frequency']}, across {r['chapters']} chapters)")

    return {"text": "\n".join(lines), "word_count": len("\n".join(lines).split())}
