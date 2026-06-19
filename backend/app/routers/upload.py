import os
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
import aiofiles

from app.config import settings
from app.database import get_db
from app.routers.user import get_current_user, log_activity
from app.services.ai_service import save_document, load_document
from app.services.extraction import extract_pdf, detect_pdf_type, MAX_FILE_SIZE
from app.services.quality_gates import quality_gate_extraction, analyze_text_quality

router = APIRouter(prefix="/upload", tags=["File Upload"])


class TextUploadRequest(BaseModel):
    text: str


@router.post("/pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    safe_name = os.path.basename(file.filename)
    file_path = os.path.join(settings.UPLOAD_DIR, safe_name)

    content = await file.read()
    file_size = len(content)
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File too large (max {MAX_FILE_SIZE // (1024*1024)}MB)")

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    extraction = extract_pdf(file_path)

    extracted_text = extraction["cleaned_text"]
    quality_result = quality_gate_extraction(extracted_text, file.filename)

    if not quality_result["passed"]:
        if not extracted_text or len(extracted_text.strip()) < 5:
            os.remove(file_path)
            raise HTTPException(
                status_code=400,
                detail="PDF appears empty. We tried PyMuPDF, pdfplumber, and OCR but could not extract text. Try uploading a different file."
            )
        else:
            quality_result["passed"] = True
            quality_result["actions_taken"].append("low_quality_accepted")

    clean_text = quality_result["text"]
    if not clean_text:
        clean_text = extracted_text
    if not clean_text or len(clean_text.strip()) < 5:
        os.remove(file_path)
        raise HTTPException(status_code=400, detail="Extracted text is empty or too short")

    doc_id = save_document(clean_text, file.filename)
    log_activity(db, current_user.id, "file_upload")
    word_count = len(clean_text.split())
    preview = clean_text[:2000] if len(clean_text) > 2000 else clean_text

    return {
        "filename": file.filename,
        "document_id": doc_id,
        "text": preview,
        "full_text_length": len(clean_text),
        "characters": len(clean_text),
        "words": word_count,
        "pages": extraction["pages"],
        "extraction_method": extraction["method"],
        "pdf_type": extraction["type"],
        "has_full_text": len(clean_text) > 2000,
        "quality_rating": extraction["quality"]["ratio"],
        "structured": {"title": extraction["structured"]["title"], "total_chapters": extraction["structured"]["total_chapters"]},
        "warnings": extraction["quality"]["warnings"],
        "quality_gate": {
            "passed": quality_result["passed"],
            "score": quality_result["quality_report"]["score"],
            "actions": quality_result["actions_taken"],
        },
    }


@router.post("/text")
async def upload_text(req: TextUploadRequest):
    text = req.text
    if not text or len(text.strip()) < 20:
        raise HTTPException(status_code=400, detail="Text content too short (min 20 chars)")
    doc_id = save_document(text.strip())
    preview = text.strip()[:2000] if len(text.strip()) > 2000 else text.strip()
    return {
        "document_id": doc_id,
        "text": preview,
        "full_text_length": len(text.strip()),
        "characters": len(text.strip()),
        "words": len(text.strip().split()),
        "has_full_text": len(text.strip()) > 2000,
    }


@router.get("/document/{doc_id}")
def get_document(doc_id: str):
    doc = load_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found or expired")
    return {
        "document_id": doc_id,
        "filename": doc.get("filename", ""),
        "total_chars": doc.get("total_chars", 0),
        "total_words": doc.get("total_words", 0),
        "total_chunks": len(doc.get("chunks", [])),
        "chunks": [{
            "index": c.get("i", c.get("index", 0)),
            "keywords": c.get("kw", c.get("keywords", [])),
        } for c in doc.get("chunks", [])],
    }


@router.get("/document/{doc_id}/full")
def get_document_full(doc_id: str):
    doc = load_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found or expired")
    return {"document_id": doc_id, "text": doc["full_text"], "total_chars": doc.get("total_chars", 0)}


@router.get("/document/{doc_id}/structured")
def get_document_structured(doc_id: str):
    doc = load_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found or expired")
    from app.services.extraction import _structure_text
    structured = _structure_text(doc["full_text"], doc.get("filename", ""))
    return structured
