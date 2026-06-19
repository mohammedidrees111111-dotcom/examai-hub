import re
import os
from typing import Optional

_FITZ = None
_PDFPLUMBER = None
_TESSERACT = None

try:
    import fitz as _FITZ
except ImportError:
    pass

try:
    import pdfplumber as _PDFPLUMBER
except ImportError:
    pass

try:
    import pytesseract
    from PIL import Image
    import io
    _TESSERACT = True
except ImportError:
    pass

MAX_FILE_SIZE = 300 * 1024 * 1024

_RE_PAGE_NUMBER = re.compile(r'^\s*\d{1,4}\s*$')
_RE_DOTS_LINE = re.compile(r'\.{4,}')
_RE_CHAPTER_HEADER = re.compile(
    r'(?:Chapter|CHAPTER|Ch\.|Unit|Part|Section|الفصل|الباب|الجزء|الوحدة|القسم)\s*[\d:.\-]+\s*[:\-\u0600-\u06FFa-zA-Z].*',
    re.IGNORECASE
)
_RE_HEADER_FOOTER = re.compile(r'^\s*(?:Page\s*\d+|\d+\s*of\s*\d+|\d+\s*/\s*\d+)\s*$', re.IGNORECASE)
_RE_URL_EMAIL = re.compile(r'(?:https?://\S+|www\.\S+|\S+@\S+\.\S+)')
_RE_REPEATED = re.compile(r'(.{50,}?)\1{2,}')

MIN_TEXT_RATIO = 0.3
MIN_CHARS_PER_PAGE = 50


def detect_pdf_type(file_path: str) -> dict:
    result = {"type": "unknown", "pages": 0, "has_text": False, "text_chars": 0}
    if not _FITZ:
        return result

    try:
        doc = _FITZ.open(file_path)
        result["pages"] = len(doc)
        text_chars = 0
        image_count = 0

        for i in range(min(10, len(doc))):
            page = doc[i]
            text = page.get_text().strip()
            text_chars += len(text)
            images = page.get_images()
            image_count += len(images)

        result["text_chars"] = text_chars
        result["has_text"] = text_chars > (result["pages"] * MIN_CHARS_PER_PAGE)

        if result["has_text"]:
            result["type"] = "text"
        elif image_count > 0:
            result["type"] = "scanned"
        else:
            result["type"] = "empty"

        doc.close()
    except Exception:
        pass

    return result


def extract_pdf(file_path: str) -> dict:
    pdf_type = detect_pdf_type(file_path)
    result = {
        "pages": pdf_type["pages"],
        "type": pdf_type["type"],
        "method": "none",
        "raw_text": "",
        "cleaned_text": "",
        "structured": {"title": "", "chapters": []},
        "quality": {"passed": False, "ratio": 0, "warnings": []},
        "arabic_analysis": {},
    }

    if pdf_type["type"] == "empty":
        result["quality"]["warnings"].append("PDF appears empty")
        return result

    from app.services.arabic_extractor import analyze_arabic_fonts, extract_arabic_multistrategy, validate_arabic_text

    font_info = analyze_arabic_fonts(file_path)
    is_arabic_risky = font_info.get("risky", False)

    if is_arabic_risky:
        ar_result = extract_arabic_multistrategy(file_path, font_info)
        raw = ar_result["text"]
        result["method"] = f"arabic_multi_{ar_result['best_method']}"
        result["arabic_analysis"] = {
            "font_analysis": font_info,
            "quality_score": ar_result["quality_score"],
            "all_scores": ar_result["all_scores"],
            "methods_tried": ar_result["methods_tried"],
        }
        validation = validate_arabic_text(raw)
        result["arabic_analysis"]["validation"] = validation

        if not validation["valid"] and _TESSERACT:
            ocr_text = _extract_with_ocr(file_path, pdf_type["pages"])
            ocr_validation = validate_arabic_text(ocr_text)
            if ocr_validation["score"] > validation["score"]:
                raw = ocr_text
                result["method"] = "ocr_fallback"
                result["arabic_analysis"]["ocr_fallback_applied"] = True
    else:
        raw = _extract_with_fitz(file_path)
        if raw and len(raw) > 50:
            result["method"] = "pymupdf"
            result["raw_text"] = raw
        else:
            raw = _extract_with_pdfplumber(file_path)
            if raw and len(raw) > 50:
                result["method"] = "pdfplumber"
                result["raw_text"] = raw
            else:
                ocr_text = _extract_with_ocr(file_path, pdf_type["pages"])
                if ocr_text and len(ocr_text) > 50:
                    raw = ocr_text
                    result["method"] = "ocr"
                    result["raw_text"] = raw
                    result["quality"]["warnings"].append("PDF required OCR - text may have errors")
                else:
                    raw = extracted_text if extracted_text else ""

    if not raw or len(raw) < 100:
        result["quality"]["warnings"].append("Extraction produced insufficient text")
        return result

    cleaned = _clean_text(raw)
    result["cleaned_text"] = cleaned

    expected_chars = pdf_type["pages"] * 1500
    ratio = len(cleaned) / max(expected_chars, 1)
    result["quality"]["ratio"] = round(ratio, 2)

    if ratio < 0.3:
        result["quality"]["warnings"].append(f"Low extraction ratio: {ratio:.2f} (expected ~{expected_chars} chars)")
    else:
        result["quality"]["passed"] = True

    if _detect_toc_only(cleaned):
        result["quality"]["warnings"].append("Content appears to be only table of contents")
        result["quality"]["passed"] = False

    result["structured"] = _structure_text(cleaned, os.path.basename(file_path))

    return result


def _extract_with_fitz(file_path: str) -> str:
    if not _FITZ:
        return ""
    try:
        doc = _FITZ.open(file_path)
        pages = []
        for page in doc:
            text = page.get_text("text", sort=True)
            if text:
                pages.append(text)
        doc.close()
        return "\n".join(pages)
    except Exception:
        return ""


def _extract_with_pdfplumber(file_path: str) -> str:
    if not _PDFPLUMBER:
        return ""
    try:
        with _PDFPLUMBER.open(file_path) as pdf:
            pages = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
        return "\n".join(pages)
    except Exception:
        return ""


def _extract_with_ocr(file_path: str, total_pages: int) -> str:
    if not _FITZ or not _TESSERACT:
        return ""
    try:
        doc = _FITZ.open(file_path)
        pages = []
        for i, page in enumerate(doc):
            pix = page.get_pixmap(dpi=200)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            text = pytesseract.image_to_string(img, lang="eng+ara")
            if text.strip():
                pages.append(text.strip())
        doc.close()
        return "\n".join(pages)
    except Exception:
        return ""


def _clean_text(text: str) -> str:
    lines = text.split("\n")
    cleaned_lines = []
    seen = set()

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if cleaned_lines and cleaned_lines[-1] != "":
                cleaned_lines.append("")
            continue

        if len(stripped) < 3:
            continue

        if _RE_PAGE_NUMBER.match(stripped) and len(stripped) <= 4:
            continue

        if _RE_HEADER_FOOTER.match(stripped):
            continue

        if _RE_URL_EMAIL.search(stripped):
            stripped = _RE_URL_EMAIL.sub("", stripped).strip()
            if not stripped:
                continue

        dots_count = len(_RE_DOTS_LINE.findall(stripped))
        if dots_count >= 2 and len(stripped) < 80:
            continue

        if _is_title_only_line(stripped, cleaned_lines):
            continue

        normalized = re.sub(r'\s+', ' ', stripped)
        normalized = _fix_broken_encoding(normalized)

        dedup_key = normalized[:100].lower()
        if dedup_key in seen and len(normalized) > 60:
            continue
        seen.add(dedup_key)

        cleaned_lines.append(normalized)

    if cleaned_lines and cleaned_lines[-1] == "":
        cleaned_lines.pop()

    result = "\n".join(cleaned_lines)
    result = _remove_duplicate_paragraphs(result)
    result = _remove_toc_section(result)

    return result.strip()


def _is_title_only_line(line: str, prev_lines: list[str]) -> bool:
    if len(line) > 100:
        return False
    cap_ratio = sum(1 for c in line if c.isupper()) / max(len(line), 1)
    if cap_ratio > 0.7 and len(line.split()) <= 8:
        return True
    if line.isupper() and len(line.split()) <= 6:
        return True
    return False


def _fix_broken_encoding(text: str) -> str:
    replacements = {
        'â€™': "'", 'â€œ': '"', 'â€': '"', 'â€˜': "'", 'â€"': '—',
        'â€¦': '...', 'â€¢': '-', 'â„¢': '(TM)', 'Â': '',
        'ï»¿': '', 'Ã©': 'e', 'Ã¨': 'e', 'Ã': '', 'Å': '',
        'ï¿½': '', 'Â©': '(C)', 'Â®': '(R)',
        'ï¿½ï¿½': '', 'à®': '', 'ã': '', '¼': '1/4', '½': '1/2',
        '¾': '3/4', '€': 'EUR', 'â–': '-', 'â—': '-', 'â˜': '*',
        'âœ“': 'V', 'âœ—': 'X',
        'أ±': '', 'أ©': 'e', 'أ': 'A',
    }
    result = text
    for bad, good in replacements.items():
        result = result.replace(bad, good)
    result = re.sub(r'[^\u0000-\u007F\u0600-\u06FF\u0750-\u077F\u2000-\u206F\n\r\t .,!?;:\-()\[\]{}\'"@#$%^&*+=/\\<>|~`]', '', result)
    result = re.sub(r'\s+', ' ', result)
    return result


def _remove_duplicate_paragraphs(text: str) -> str:
    paragraphs = text.split("\n\n")
    if len(paragraphs) < 3:
        return text
    cleaned = []
    for p in paragraphs:
        if len(cleaned) >= 2 and p.strip() == cleaned[-1].strip():
            continue
        if len(cleaned) >= 3 and p.strip() == cleaned[-2].strip():
            continue
        cleaned.append(p)
    return "\n\n".join(cleaned)


def _remove_toc_section(text: str) -> str:
    lines = text.split("\n")
    if len(lines) < 5:
        return text

    toc_end = 0
    toc_lines_count = 0
    for i, line in enumerate(lines[:max(20, len(lines) // 3)]):
        stripped = line.strip()
        if not stripped:
            if toc_lines_count >= 2:
                toc_end = i
            continue
        has_dots = bool(_RE_DOTS_LINE.search(stripped))
        has_page_ref = bool(re.search(r'\d{1,4}\s*$', stripped))
        if has_dots or (has_page_ref and len(stripped) < 120):
            toc_lines_count += 1
            toc_end = i + 1
        elif toc_lines_count >= 2:
            break

    if toc_end > 2 and toc_lines_count >= 2:
        return "\n".join(lines[toc_end:]).strip()
    return text


def _detect_toc_only(text: str) -> bool:
    lines = [l for l in text.split("\n") if l.strip()]
    if len(lines) < 5:
        return True
    toc_lines = 0
    for line in lines[:len(lines) // 3]:
        if _RE_DOTS_LINE.search(line):
            toc_lines += 1
        elif re.search(r'\d{1,4}\s*$', line.strip()) and len(line.strip()) < 100:
            toc_lines += 1
    return toc_lines > len(lines) * 0.3


def _structure_text(text: str, filename: str = "") -> dict:
    chapters = _detect_chapters(text)
    title = _extract_title(text, filename)

    return {
        "title": title,
        "chapters": chapters,
        "total_chapters": len(chapters),
        "total_words": len(text.split()),
        "total_chars": len(text),
    }


def _extract_title(text: str, filename: str) -> str:
    lines = text.strip().split("\n")
    for line in lines[:10]:
        stripped = line.strip()
        if 5 < len(stripped) < 150 and not stripped.startswith("http"):
            if _RE_DOTS_LINE.search(stripped):
                continue
            if not _RE_PAGE_NUMBER.match(stripped):
                if sum(1 for c in stripped if c.isalpha()) / max(len(stripped), 1) > 0.4:
                    return stripped[:120]
    name = os.path.splitext(filename)[0] if filename else "Document"
    return name.replace("_", " ").replace("-", " ").title()[:100]


def _detect_chapters(text: str) -> list[dict]:
    patterns = [
        (r'(?:^|\n)((?:Chapter|CHAPTER|Ch\.|Unit|Part|Section|الفصل|الباب|الجزء|الوحدة|القسم)\s+[\dIVXivx]+[\.:\-]?\s*.+?)(?:\n|$)', "numbered"),
        (r'(?:^|\n)([A-Z][A-Z\s]{5,60})(?:\n|$)', "caps_title"),
        (r'(?:^|\n)((?:\d+\.\d+\.?\s*|[\d]+[\.\)]\s+)[A-Z\u0600-\u06FF].{10,80})(?:\n|$)', "numbered_list"),
    ]

    chapters = []
    for pattern, style in patterns:
        matches = list(re.finditer(pattern, text, re.MULTILINE))
        if len(matches) >= 2:
            for i, m in enumerate(matches):
                title = m.group(1).strip()
                start = m.end()
                end = matches[i + 1].start() if i + 1 < len(matches) else min(start + 8000, len(text))
                content = text[start:end].strip()
                wc = len(content.split())
                if wc > 40:
                    chapters.append({"title": title[:120], "word_count": wc, "style": style, "preview": content[:200]})
            if chapters:
                break

    if not chapters:
        paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 100]
        for i, p in enumerate(paragraphs[:20]):
            first_line = p.split("\n")[0][:80]
            chapters.append({
                "title": first_line,
                "word_count": len(p.split()),
                "style": "auto_segment",
                "preview": p[:200],
            })

    return chapters


def _chunk_for_ai(chapters: list[dict], max_chunk_words: int = 2000, overlap_words: int = 250) -> list[dict]:
    chunks = []
    for ch in chapters:
        content = ch.get("content", "")
        if not content:
            continue
        words = content.split()
        if len(words) <= max_chunk_words:
            chunks.append({"chapter": ch.get("title", ""), "text": content, "word_count": len(words)})
        else:
            start = 0
            chunk_num = 0
            while start < len(words):
                end = min(start + max_chunk_words, len(words))
                chunk_text = " ".join(words[start:end])
                chunk_num += 1
                chunks.append({
                    "chapter": f"{ch.get('title', '')} (part {chunk_num})",
                    "text": chunk_text,
                    "word_count": end - start,
                })
                start = end - overlap_words
                if start <= 0:
                    start = end
    return chunks
