from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.schemas.user import UserResponse, UserUpdate
from app.services.auth_service import get_user_by_id, decode_access_token
from app.models.activity import Activity

router = APIRouter(prefix="/user", tags=["User"])


def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Authentication required")
    token = authorization.split(" ", 1)[1]
    payload = decode_access_token(token)
    if not payload:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user_id = int(payload.get("sub", 0))
    user = get_user_by_id(db, user_id)
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="User not found")
    return user


def log_activity(db: Session, user_id: int, action: str):
    activity = Activity(user_id=user_id, action=action)
    db.add(activity)
    db.commit()


@router.get("/me", response_model=UserResponse)
def get_me(current_user=Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
def update_me(data: UserUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if data.full_name is not None:
        current_user.full_name = data.full_name
    if data.username is not None:
        current_user.username = data.username
    db.commit()
    db.refresh(current_user)
    return UserResponse.model_validate(current_user)


@router.get("/stats")
def get_stats(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    counts = {}
    actions = ["exam_predict", "file_upload", "summarize", "teacher_mode"]
    for action in actions:
        count = db.query(func.count(Activity.id)).filter(
            Activity.user_id == current_user.id,
            Activity.action == action,
        ).scalar()
        counts[action] = count or 0

    return {
        "exams_predicted": counts["exam_predict"],
        "files_uploaded": counts["file_upload"],
        "summaries_generated": counts["summarize"],
        "teacher_mode_sessions": counts["teacher_mode"],
        "is_premium": current_user.is_premium,
    }
