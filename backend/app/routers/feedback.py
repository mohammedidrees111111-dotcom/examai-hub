from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.routers.user import get_current_user
from app.models.feedback import Feedback, UsageCredit, UsageLog

router = APIRouter(prefix="/feedback", tags=["Feedback & Credits"])

PRICE_PER_10K_WORDS = 200
CREDITS_FREE = 10000
TOKENS_PER_WORD = 2


class FeedbackSubmit(BaseModel):
    document_id: Optional[str] = None
    analysis_type: str
    rating: int = 0
    helpful: Optional[str] = None
    comment: Optional[str] = None
    prompt_snapshot: Optional[str] = None


@router.post("/submit")
def submit_feedback(
    data: FeedbackSubmit,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    fb = Feedback(
        user_id=current_user.id,
        document_id=data.document_id,
        analysis_type=data.analysis_type,
        rating=data.rating,
        helpful=data.helpful,
        comment=data.comment,
        prompt_snapshot=data.prompt_snapshot,
    )
    db.add(fb)
    db.commit()
    return {"status": "ok", "id": fb.id}


@router.get("/stats")
def feedback_stats(db: Session = Depends(get_db)):
    from sqlalchemy import func
    total = db.query(func.count(Feedback.id)).scalar() or 0
    helpful_count = db.query(func.count(Feedback.id)).filter(Feedback.helpful == "yes").scalar() or 0
    avg_rating = db.query(func.avg(Feedback.rating)).scalar() or 0
    by_type = {}
    for atype in ["teacher_mode", "summarize", "exam_predict"]:
        count = db.query(func.count(Feedback.id)).filter(Feedback.analysis_type == atype).scalar() or 0
        by_type[atype] = count
    return {
        "total": total,
        "helpful": helpful_count,
        "avg_rating": round(float(avg_rating), 2),
        "by_type": by_type,
    }


class CreditBuyRequest(BaseModel):
    tokens: int


@router.get("/credits")
def get_credits(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    credit = db.query(UsageCredit).filter(UsageCredit.user_id == current_user.id).first()
    if not credit:
        credit = UsageCredit(user_id=current_user.id, balance_tokens=CREDITS_FREE)
        db.add(credit)
        db.commit()
        db.refresh(credit)
    return {
        "user_id": current_user.id,
        "balance_tokens": credit.balance_tokens,
        "total_tokens_used": credit.total_tokens_used,
        "total_words_analyzed": credit.total_words_analyzed,
        "plan_type": credit.plan_type,
        "free_credits_given": CREDITS_FREE,
    }


@router.post("/credits/buy")
def buy_credits(
    data: CreditBuyRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    credit = db.query(UsageCredit).filter(UsageCredit.user_id == current_user.id).first()
    if not credit:
        credit = UsageCredit(user_id=current_user.id, balance_tokens=CREDITS_FREE)
        db.add(credit)
        db.commit()
        db.refresh(credit)

    credit.balance_tokens += data.tokens
    credit.plan_type = "credit"
    db.commit()
    db.refresh(credit)
    return {
        "balance_tokens": credit.balance_tokens,
        "added": data.tokens,
        "message": f"Added {data.tokens} tokens. New balance: {credit.balance_tokens}",
    }


def deduct_tokens(db: Session, user_id: int, words: int, analysis_type: str, document_id: str = "") -> dict:
    from app.models.user import User
    user = db.query(User).filter(User.id == user_id).first()

    if user and user.is_premium:
        return {"charged": 0, "remaining": -1, "premium": True}

    credit = db.query(UsageCredit).filter(UsageCredit.user_id == user_id).first()
    if not credit:
        credit = UsageCredit(user_id=user_id, balance_tokens=CREDITS_FREE)
        db.add(credit)
        db.commit()
        db.refresh(credit)

    tokens_needed = words * TOKENS_PER_WORD
    cost_cents = (words / 10000) * PRICE_PER_10K_WORDS

    if credit.balance_tokens < tokens_needed:
        raise HTTPException(
            status_code=402,
            detail=f"Insufficient credits. Need {tokens_needed} tokens, have {credit.balance_tokens}. Buy more at /feedback/credits/buy",
        )

    credit.balance_tokens -= tokens_needed
    credit.total_tokens_used += tokens_needed
    credit.total_words_analyzed += words

    log = UsageLog(
        user_id=user_id,
        document_id=document_id,
        analysis_type=analysis_type,
        words_processed=words,
        tokens_charged=tokens_needed,
        cost_cents=int(cost_cents),
    )
    db.add(log)
    db.commit()
    db.refresh(credit)

    return {"charged": tokens_needed, "remaining": credit.balance_tokens, "premium": False}


@router.get("/usage/history")
def usage_history(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    logs = db.query(UsageLog).filter(UsageLog.user_id == current_user.id).order_by(UsageLog.created_at.desc()).limit(50).all()
    return [{
        "id": l.id,
        "analysis_type": l.analysis_type,
        "words_processed": l.words_processed,
        "tokens_charged": l.tokens_charged,
        "cost_cents": l.cost_cents,
        "created_at": str(l.created_at),
    } for l in logs]
