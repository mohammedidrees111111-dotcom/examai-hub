from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.ai_service import (
    predict_exam_questions,
    teacher_mode_explain,
    summarize_text,
    load_document,
)
from app.services.analysis_engine import (
    structured_document_analysis,
    generate_flashcards,
    generate_study_plan,
    generate_cheatsheet,
)
from app.services.exam_engine import generate_exam_prep
from app.services.teacher_fingerprint import analyze_teacher_fingerprint
from app.services.exam_reconstructor import reconstruct_exam
from app.services.learning_engine import LearningState
from app.services.unified_engine import unified_academic_analysis
from app.services.hierarchical_summarizer import hierarchical_summarize, multi_pass_prediction, generate_qa_summary
from app.services.quality_gates import verify_ai_output, quality_gate_extraction
from app.services.full_exam_generator import generate_full_exam
from app.services.global_context import generate_global_analysis
from app.services.ai_llm import ai_summarize, ai_exam_prep, ai_teacher_mode, ai_qa_generate, GROQ_AVAILABLE
from app.services.ai_router import route_ai, is_any_ai_available
from app.routers.user import get_current_user, log_activity
from app.routers.feedback import deduct_tokens

router = APIRouter(prefix="/ai", tags=["AI Features"])


class ExamPredictRequest(BaseModel):
    text: Optional[str] = None
    document_id: Optional[str] = None
    num_questions: Optional[int] = 5


class ExamPredictResponse(BaseModel):
    questions: list[dict]
    total: int


def _charge_usage(db: Session, user_id: int, text: str, analysis_type: str, document_id: str = ""):
    words = len(text.split())
    try:
        return deduct_tokens(db, user_id, words, analysis_type, document_id)
    except HTTPException as e:
        if e.status_code == 402:
            raise HTTPException(
                status_code=402,
                detail=f"Insufficient credits. You need {words * 2} tokens for {words} words. Upgrade to Premium for unlimited or buy credits at /feedback/credits/buy",
            )
        raise


@router.post("/exam-predict", response_model=ExamPredictResponse)
def exam_predict(
    req: ExamPredictRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    text = _resolve_text(req.text, req.document_id)
    if not text or len(text.strip()) < 20:
        raise HTTPException(status_code=400, detail="Text content too short. Please provide more material.")
    _charge_usage(db, current_user.id, text, "exam_predict", req.document_id or "")

    ai = route_ai(text, "exam_predict", user_id=current_user.id)
    if ai["ai_powered"]:
        log_activity(db, current_user.id, "exam_predict")
        return ExamPredictResponse(
            questions=[{"question": ai["result"], "options": [], "answer": "", "type": "ai_generated", "model": ai["model"]}],
            total=1
        )

    questions = predict_exam_questions(text, req.num_questions or 5)
    log_activity(db, current_user.id, "exam_predict")
    return ExamPredictResponse(questions=questions, total=len(questions))


class TeacherModeRequest(BaseModel):
    text: Optional[str] = None
    document_id: Optional[str] = None
    topic: Optional[str] = None


@router.post("/teacher-mode")
def teacher_mode(
    req: TeacherModeRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    text = _resolve_text(req.text, req.document_id)
    if not text or len(text.strip()) < 20:
        raise HTTPException(status_code=400, detail="Text content too short. Please provide more material.")
    _charge_usage(db, current_user.id, text, "teacher_mode", req.document_id or "")

    ai = route_ai(text, "teacher_mode", user_id=current_user.id)
    if ai["ai_powered"]:
        log_activity(db, current_user.id, "teacher_mode")
        return {"summary": ai["result"], "key_concepts": [], "difficulty_level": "intermediate", "suggested_study_time": "30 minutes", "topic": "AI Analysis", "bullet_points": [], "recommended_resources": [], "model": ai["model"], "ai_powered": True}

    result = teacher_mode_explain(text, req.topic)
    log_activity(db, current_user.id, "teacher_mode")
    return result


class SummarizeRequest(BaseModel):
    text: Optional[str] = None
    document_id: Optional[str] = None
    max_length: Optional[int] = 200


@router.post("/summarize")
def summarize(
    req: SummarizeRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    text = _resolve_text(req.text, req.document_id)
    if not text or len(text.strip()) < 20:
        raise HTTPException(status_code=400, detail="Text content too short. Please provide more material.")
    _charge_usage(db, current_user.id, text, "summarize", req.document_id or "")

    ai = route_ai(text, "summarize", max_tokens=2500, user_id=current_user.id)
    if ai["ai_powered"]:
        log_activity(db, current_user.id, "summarize")
        return {
            "original_length": len(text.split()),
            "summary_length": len(ai["result"].split()),
            "summary": ai["result"],
            "keywords": [],
            "compression_ratio": f"{len(ai['result'].split()) / max(len(text.split()), 1) * 100:.1f}%",
            "model": ai["model"],
            "ai_powered": True,
        }

    result = hierarchical_summarize(text)
    mapped = {
        "original_length": result["original_words"],
        "summary_length": result["summary_words"],
        "summary": result["full_summary"],
        "keywords": result["global_keywords"],
        "compression_ratio": result["compression_ratio"],
        "sections": result["chapters_count"],
        "total_chunks": result["chapters_count"],
        "language": result["language"],
        "information_preservation": result["information_preservation"],
    }
    log_activity(db, current_user.id, "summarize")
    return mapped


class AnalysisRequest(BaseModel):
    text: Optional[str] = None
    document_id: Optional[str] = None


class FlashcardRequest(BaseModel):
    text: Optional[str] = None
    document_id: Optional[str] = None
    count: Optional[int] = 10


class StudyPlanRequest(BaseModel):
    text: Optional[str] = None
    document_id: Optional[str] = None
    days: Optional[int] = 7


@router.post("/analyze")
def analyze_document(
    req: AnalysisRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    text = _resolve_text(req.text, req.document_id)
    if not text or len(text.strip()) < 20:
        raise HTTPException(status_code=400, detail="Text content too short.")
    _charge_usage(db, current_user.id, text, "analyze", req.document_id or "")
    result = structured_document_analysis(text)
    log_activity(db, current_user.id, "analyze")
    return result


@router.post("/flashcards")
def flashcards(
    req: FlashcardRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    text = _resolve_text(req.text, req.document_id)
    if not text or len(text.strip()) < 20:
        raise HTTPException(status_code=400, detail="Text content too short.")
    _charge_usage(db, current_user.id, text, "flashcards", req.document_id or "")
    result = generate_flashcards(text, req.count or 10)
    log_activity(db, current_user.id, "flashcards")
    return {"flashcards": result, "total": len(result)}


@router.post("/study-plan")
def study_plan(
    req: StudyPlanRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    text = _resolve_text(req.text, req.document_id)
    if not text or len(text.strip()) < 20:
        raise HTTPException(status_code=400, detail="Text content too short.")
    _charge_usage(db, current_user.id, text, "study_plan", req.document_id or "")
    result = generate_study_plan(text, req.days or 7)
    log_activity(db, current_user.id, "study_plan")
    return result


@router.post("/cheatsheet")
def cheatsheet(
    req: AnalysisRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    text = _resolve_text(req.text, req.document_id)
    if not text or len(text.strip()) < 20:
        raise HTTPException(status_code=400, detail="Text content too short.")
    _charge_usage(db, current_user.id, text, "cheatsheet", req.document_id or "")
    result = generate_cheatsheet(text)
    log_activity(db, current_user.id, "cheatsheet")
    return result


@router.post("/exam-prep")
def exam_prep(
    req: AnalysisRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    text = _resolve_text(req.text, req.document_id)
    if not text or len(text.strip()) < 20:
        raise HTTPException(status_code=400, detail="Text content too short.")
    _charge_usage(db, current_user.id, text, "exam_prep", req.document_id or "")
    result = generate_exam_prep(text)
    log_activity(db, current_user.id, "exam_predict")
    return result


@router.post("/teacher-exam")
def teacher_exam(
    req: AnalysisRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    text = _resolve_text(req.text, req.document_id)
    if not text or len(text.strip()) < 20:
        raise HTTPException(status_code=400, detail="Text content too short.")
    _charge_usage(db, current_user.id, text, "teacher_exam", req.document_id or "")
    result = analyze_teacher_fingerprint(text)
    log_activity(db, current_user.id, "exam_predict")
    return result


class ExamReconstructRequest(BaseModel):
    textbook: Optional[str] = None
    textbook_document_id: Optional[str] = None
    past_exams: Optional[str] = None
    lecture_notes: Optional[str] = None


@router.post("/exam-reconstruct")
def exam_reconstruct(
    req: ExamReconstructRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    textbook = _resolve_text(req.textbook, req.textbook_document_id)
    if not textbook or len(textbook.strip()) < 20:
        raise HTTPException(status_code=400, detail="Textbook content too short. This is required.")
    past_exams = req.past_exams or ""
    lecture_notes = req.lecture_notes or ""

    total_words = len(textbook.split()) + len(past_exams.split()) + len(lecture_notes.split())
    _charge_usage(db, current_user.id, textbook, "exam_reconstruct", req.textbook_document_id or "")
    result = reconstruct_exam(textbook, past_exams, lecture_notes)
    log_activity(db, current_user.id, "exam_predict")
    return result


class LearningRequest(BaseModel):
    textbook: Optional[str] = None
    textbook_document_id: Optional[str] = None
    past_exams: Optional[str] = None
    feedback: Optional[list[dict]] = None


@router.post("/exam-predict-learn")
def exam_predict_learn(
    req: LearningRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    textbook = _resolve_text(req.textbook, req.textbook_document_id)
    if not textbook or len(textbook.strip()) < 20:
        raise HTTPException(status_code=400, detail="Textbook content required.")

    past_exams = req.past_exams or ""
    state = LearningState(current_user.id)

    if req.feedback:
        for fb in req.feedback:
            topic = fb.get("topic", "")
            correct = fb.get("correct", False)
            partial = fb.get("partial", False)
            pattern = fb.get("pattern", "")
            if topic:
                state.register_feedback(topic, correct, partial)
            if pattern:
                state.register_pattern_feedback(pattern, fb.get("accurate", False))

    base_predictions = reconstruct_exam(textbook, past_exams)
    base_high_prob = base_predictions.get("top_high_probability_topics", [])
    high_prob_dicts = [{"concept": t, "prediction_score": 80} for t in base_high_prob]

    adjusted = state.apply_learning_to_topics(high_prob_dicts) if high_prob_dicts else []

    if base_predictions.get("predicted_exam"):
        for i, q in enumerate(base_predictions["predicted_exam"]):
            if i < len(adjusted):
                concept = list(adjusted[i].values())[0] if isinstance(adjusted[i], dict) else ""
            base_predictions["predicted_exam"][i]["learning_adjustment"] = adjusted[i].get("learning_adjustment", 0) if i < len(adjusted) else 0

    state.record_confidence(base_predictions.get("exam_prediction_confidence", 50))
    state.record_fingerprint({"teaching_style": "adaptive"})
    learning_report = state.get_learning_report()
    state.save()

    _charge_usage(db, current_user.id, textbook, "exam_predict_learn", req.textbook_document_id or "")
    log_activity(db, current_user.id, "exam_predict")

    return {
        "exam_prediction": base_predictions,
        "confidence_score": base_predictions.get("exam_prediction_confidence", 50),
        "learning_updates": {
            "updated_high_value_topics": learning_report["updated_high_value_topics"],
            "decreased_topics": learning_report["decreased_topics"],
            "new_detected_patterns": learning_report["new_detected_patterns"],
        },
        "teacher_fingerprint_update": learning_report["teacher_fingerprint_update"],
        "iteration": learning_report["iteration"],
    }


@router.post("/unified")
def unified_analysis(
    req: ExamReconstructRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    textbook = _resolve_text(req.textbook, req.textbook_document_id)
    if not textbook or len(textbook.strip()) < 20:
        raise HTTPException(status_code=400, detail="Textbook content required.")
    past_exams = req.past_exams or ""
    lecture_notes = req.lecture_notes or ""

    _charge_usage(db, current_user.id, textbook, "unified", req.textbook_document_id or "")
    result = unified_academic_analysis(textbook, past_exams, lecture_notes)
    log_activity(db, current_user.id, "exam_predict")
    return result


class HierarchicalSummaryRequest(BaseModel):
    text: Optional[str] = None
    document_id: Optional[str] = None
    target_ratio: Optional[float] = None


@router.post("/hierarchical-summarize")
def hierarchical_summary(
    req: HierarchicalSummaryRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    text = _resolve_text(req.text, req.document_id)
    if not text or len(text.strip()) < 50:
        raise HTTPException(status_code=400, detail="Text too short. Minimum 50 characters.")
    _charge_usage(db, current_user.id, text, "hierarchical_summarize", req.document_id or "")
    result = hierarchical_summarize(text, req.target_ratio)

    # AI Verifier: check summary quality
    verification = verify_ai_output("summary", result, result["original_words"])
    if not verification["passed"] and result["summary_words"] < result["original_words"] * 0.15:
        result = hierarchical_summarize(text, max(0.6, req.target_ratio or 0.55))
        verification = verify_ai_output("summary", result, result["original_words"])

    result["verification"] = verification
    log_activity(db, current_user.id, "summarize")
    return result


@router.post("/multi-pass-predict")
def multi_pass_predict(
    req: ExamReconstructRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    textbook = _resolve_text(req.textbook, req.textbook_document_id)
    if not textbook or len(textbook.strip()) < 50:
        raise HTTPException(status_code=400, detail="Textbook content required.")
    past_exams = req.past_exams or ""
    lecture_notes = req.lecture_notes or ""
    _charge_usage(db, current_user.id, textbook, "multi_pass_predict", req.textbook_document_id or "")
    result = multi_pass_prediction(textbook, past_exams, lecture_notes)

    verification = verify_ai_output("questions", result, len(textbook.split()))
    if not verification["passed"]:
        result = multi_pass_prediction(textbook, past_exams, lecture_notes)
        verification = verify_ai_output("questions", result, len(textbook.split()))

    result["verification"] = verification
    log_activity(db, current_user.id, "exam_predict")
    return result


@router.post("/qa-summarize")
def qa_summarize(
    req: AnalysisRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    text = _resolve_text(req.text, req.document_id)
    if not text or len(text.strip()) < 30:
        raise HTTPException(status_code=400, detail="Text content too short. Minimum 30 characters.")
    _charge_usage(db, current_user.id, text, "qa_summarize", req.document_id or "")

    ai = route_ai(text, "qa_generate", user_id=current_user.id)
    if ai["ai_powered"]:
        log_activity(db, current_user.id, "summarize")
        return {"format": "qa", "total_questions": 0, "chapters_covered": 1, "total_words": len(text.split()), "chapters": [{"chapter": 1, "title": "AI Q&A", "qa_pairs": [{"type": "ai_generated", "question": "AI Generated Q&A", "answer": ai["result"]}]}], "all_definitions": [], "language": "en", "model": ai["model"], "ai_powered": True}

    result = generate_qa_summary(text)
    log_activity(db, current_user.id, "summarize")
    return result


@router.post("/full-exam")
def full_exam(
    req: AnalysisRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    text = _resolve_text(req.text, req.document_id)
    if not text or len(text.strip()) < 30:
        raise HTTPException(status_code=400, detail="Text too short. Minimum 30 characters.")
    _charge_usage(db, current_user.id, text, "full_exam", req.document_id or "")
    result = generate_full_exam(text)
    log_activity(db, current_user.id, "exam_predict")
    return result


@router.post("/global-analyze")
def global_analyze(
    req: AnalysisRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    text = _resolve_text(req.text, req.document_id)
    if not text or len(text.strip()) < 50:
        raise HTTPException(status_code=400, detail="Text too short. Minimum 50 characters.")
    _charge_usage(db, current_user.id, text, "global_analyze", req.document_id or "")
    result = generate_global_analysis(text)
    log_activity(db, current_user.id, "exam_predict")
    return result


def _resolve_text(text: Optional[str], doc_id: Optional[str]) -> str:
    if doc_id:
        doc = load_document(doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found or expired")
        return doc.get("full_text", "")
    return text or ""
