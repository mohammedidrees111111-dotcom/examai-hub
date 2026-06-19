from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from app.database import get_db
from app.schemas.user import UserRegister, UserLogin, TokenResponse, UserResponse
from app.services.auth_service import (
    create_user,
    authenticate_user,
    create_access_token,
    get_user_by_email,
)

logger = logging.getLogger("examai-hub")
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(data: UserRegister, db: Session = Depends(get_db)):
    try:
        existing = get_user_by_email(db, data.email)
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        user = create_user(db, data)
        token = create_access_token({"sub": str(user.id), "email": user.email})
        logger.info(f"User registered: {data.email}")
        return TokenResponse(
            access_token=token,
            user=UserResponse.model_validate(user),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed for {data.email}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Registration failed. Please try again later.")


@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin, db: Session = Depends(get_db)):
    try:
        user = authenticate_user(db, data.email, data.password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        token = create_access_token({"sub": str(user.id), "email": user.email})
        logger.info(f"User logged in: {data.email}")
        return TokenResponse(
            access_token=token,
            user=UserResponse.model_validate(user),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed for {data.email}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Login failed. Please try again later.")
