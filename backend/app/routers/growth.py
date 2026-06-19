import uuid
import random
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func as sqlfunc

from app.database import get_db
from app.routers.user import get_current_user
from app.models.feedback import Referral, SharedAnalysis, Achievement, UsageCredit

router = APIRouter(prefix="/growth", tags=["Growth Engine"])

REFERRAL_BONUS = 500
SHARE_PREVIEW_LENGTH = 800


class ShareRequest(BaseModel):
    title: str = ""
    subject: str = ""
    course: str = ""
    data: dict


class ReferralResponse(BaseModel):
    referral_code: str
    referral_link: str
    total_referrals: int
    credits_earned: int


@router.get("/referral")
def get_referral(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    ref = db.query(Referral).filter(Referral.referrer_id == current_user.id).first()
    if not ref:
        code = _generate_code(current_user.id)
        ref = Referral(referrer_id=current_user.id, referral_code=code, status="active")
        db.add(ref)
        db.commit()
        db.refresh(ref)

    total = db.query(sqlfunc.count(Referral.id)).filter(
        Referral.referrer_id == current_user.id, Referral.status == "completed"
    ).scalar() or 0

    from app.config import settings
    return {
        "referral_code": ref.referral_code,
        "referral_link": f"{settings.FRONTEND_URL}/register?ref={ref.referral_code}",
        "total_referrals": total,
        "credits_earned": total * REFERRAL_BONUS,
    }


@router.post("/referral/apply/{code}")
def apply_referral(
    code: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    ref = db.query(Referral).filter(Referral.referral_code == code).first()
    if not ref:
        raise HTTPException(status_code=404, detail="Invalid referral code")
    if ref.referred_id:
        raise HTTPException(status_code=400, detail="Code already used")

    ref.referred_id = current_user.id
    ref.status = "completed"
    ref.referrer_bonus = REFERRAL_BONUS
    ref.referred_bonus = REFERRAL_BONUS

    referrer_credit = db.query(UsageCredit).filter(UsageCredit.user_id == ref.referrer_id).first()
    if referrer_credit:
        referrer_credit.balance_tokens += REFERRAL_BONUS

    user_credit = db.query(UsageCredit).filter(UsageCredit.user_id == current_user.id).first()
    if user_credit:
        user_credit.balance_tokens += REFERRAL_BONUS

    db.commit()
    return {"status": "applied", "bonus": REFERRAL_BONUS, "message": f"You and your referrer both earned {REFERRAL_BONUS} credits!"}


@router.post("/share")
def share_analysis(
    req: ShareRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    import json
    token = uuid.uuid4().hex[:16]
    shared = SharedAnalysis(
        user_id=current_user.id,
        share_token=token,
        title=req.title or "Study Analysis",
        subject=req.subject or "",
        course=req.course or "",
        data_json=json.dumps(req.data, ensure_ascii=False),
    )
    db.add(shared)
    db.commit()

    from app.config import settings
    return {
        "share_token": token,
        "share_url": f"{settings.FRONTEND_URL}/share/{token}",
        "message": "Share this link with your classmates!",
    }


@router.get("/share/{token}")
def get_shared_analysis(token: str, db: Session = Depends(get_db)):
    shared = db.query(SharedAnalysis).filter(SharedAnalysis.share_token == token).first()
    if not shared:
        raise HTTPException(status_code=404, detail="Shared analysis not found")
    shared.views += 1
    db.commit()
    import json
    return {
        "title": shared.title,
        "subject": shared.subject,
        "course": shared.course,
        "data": json.loads(shared.data_json),
        "views": shared.views,
    }


ACHIEVEMENTS = {
    "first_upload": {"name": "First Upload", "icon": "📄", "desc": "Upload your first document"},
    "first_prediction": {"name": "First Prediction", "icon": "🔮", "desc": "Generate your first exam prediction"},
    "first_summary": {"name": "First Summary", "icon": "📝", "desc": "Create your first AI summary"},
    "seven_day_streak": {"name": "7 Day Streak", "icon": "🔥", "desc": "Use the app 7 days in a row"},
    "ten_uploads": {"name": "Scholar", "icon": "📚", "desc": "Upload 10 documents"},
    "fifty_analyses": {"name": "AI Master", "icon": "🤖", "desc": "Run 50 AI analyses"},
    "first_share": {"name": "Sharer", "icon": "🔗", "desc": "Share your first study pack"},
    "first_referral": {"name": "Recruiter", "icon": "👥", "desc": "Refer your first friend"},
    "five_referrals": {"name": "Influencer", "icon": "🌟", "desc": "Refer 5 friends"},
}


@router.get("/achievements")
def get_achievements(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    earned = db.query(Achievement).filter(Achievement.user_id == current_user.id).all()
    earned_badges = {a.badge for a in earned}
    all_achievements = []
    for badge_id, badge in ACHIEVEMENTS.items():
        all_achievements.append({
            "id": badge_id,
            "name": badge["name"],
            "icon": badge["icon"],
            "desc": badge["desc"],
            "earned": badge_id in earned_badges,
        })
    return {"achievements": all_achievements, "total_earned": len(earned)}


@router.post("/achievements/check")
def check_achievements(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    earned = {a.badge for a in db.query(Achievement).filter(Achievement.user_id == current_user.id).all()}
    new_achievements = []

    from app.models.activity import Activity
    total_activities = db.query(sqlfunc.count(Activity.id)).filter(Activity.user_id == current_user.id).scalar() or 0
    total_uploads = db.query(sqlfunc.count(Activity.id)).filter(Activity.user_id == current_user.id, Activity.action == "file_upload").scalar() or 0
    total_predictions = db.query(sqlfunc.count(Activity.id)).filter(Activity.user_id == current_user.id, Activity.action == "exam_predict").scalar() or 0
    total_summaries = db.query(sqlfunc.count(Activity.id)).filter(Activity.user_id == current_user.id, Activity.action == "summarize").scalar() or 0
    total_shares = db.query(sqlfunc.count(SharedAnalysis.id)).filter(SharedAnalysis.user_id == current_user.id).scalar() or 0
    total_referrals = db.query(sqlfunc.count(Referral.id)).filter(Referral.referrer_id == current_user.id, Referral.status == "completed").scalar() or 0

    checks = [
        ("first_upload", total_uploads >= 1),
        ("first_prediction", total_predictions >= 1),
        ("first_summary", total_summaries >= 1),
        ("ten_uploads", total_uploads >= 10),
        ("fifty_analyses", total_activities >= 50),
        ("first_share", total_shares >= 1),
        ("first_referral", total_referrals >= 1),
        ("five_referrals", total_referrals >= 5),
    ]

    for badge_id, condition in checks:
        if condition and badge_id not in earned:
            ach = Achievement(user_id=current_user.id, badge=badge_id)
            db.add(ach)
            new_achievements.append(ACHIEVEMENTS[badge_id])

    if new_achievements:
        db.commit()

    return {"new_achievements": new_achievements, "total": len(earned) + len(new_achievements)}


@router.get("/score")
def get_score(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    from app.models.activity import Activity
    total = db.query(sqlfunc.count(Activity.id)).filter(Activity.user_id == current_user.id).scalar() or 0
    uploads = db.query(sqlfunc.count(Activity.id)).filter(Activity.user_id == current_user.id, Activity.action == "file_upload").scalar() or 0
    predictions = db.query(sqlfunc.count(Activity.id)).filter(Activity.user_id == current_user.id, Activity.action == "exam_predict").scalar() or 0
    earned_badges = db.query(sqlfunc.count(Achievement.id)).filter(Achievement.user_id == current_user.id).scalar() or 0

    readiness = min(100, (total * 2) + (uploads * 10) + (predictions * 5) + (earned_badges * 15))
    if readiness >= 80: confidence = "Excellent"
    elif readiness >= 50: confidence = "Good"
    else: confidence = "Weak"

    return {
        "study_readiness": readiness,
        "exam_confidence": confidence,
        "total_analyses": total,
        "uploads": uploads,
        "predictions": predictions,
        "achievements": earned_badges,
        "share_text": f"I scored {readiness}/100 on ExamAI Hub! My exam confidence is {confidence}.",
    }


@router.get("/leaderboard")
def leaderboard(db: Session = Depends(get_db)):
    from app.models.activity import Activity
    results = db.query(
        Activity.user_id,
        sqlfunc.count(Activity.id).label("total"),
    ).group_by(Activity.user_id).order_by(sqlfunc.count(Activity.id).desc()).limit(20).all()

    from app.models.user import User
    leaders = []
    for r in results:
        user = db.query(User).filter(User.id == r.user_id).first()
        if user:
            leaders.append({
                "username": user.username[:3] + "***",
                "score": r.total * 10,
                "analyses": r.total,
            })

    return {"leaderboard": leaders, "total_participants": len(results)}


@router.get("/daily-challenge")
def daily_challenge(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    questions = [
        {"q": "What does AI stand for?", "options": ["Artificial Intelligence", "Automated Integration", "Advanced Interface", "Algorithmic Input"], "answer": 0},
        {"q": "Which is NOT a type of machine learning?", "options": ["Supervised", "Unsupervised", "Reinforcement", "Prescriptive"], "answer": 3},
        {"q": "What is backpropagation used for?", "options": ["Training neural networks", "Data preprocessing", "Image compression", "Text formatting"], "answer": 0},
        {"q": "What does CNN stand for?", "options": ["Convolutional Neural Network", "Central Node Network", "Complex Numerical Node", "Cognitive Neural Net"], "answer": 0},
        {"q": "Which language model uses transformers?", "options": ["GPT", "LSTM", "CNN", "SVM"], "answer": 0},
    ]
    random.shuffle(questions)
    return {
        "questions": questions[:5],
        "date": "",
    }


def _generate_code(user_id: int) -> str:
    return f"STUDY{user_id}{uuid.uuid4().hex[:4].upper()}"
