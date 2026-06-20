from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.routers.user import get_current_user
from app.services.encryption import encrypt_api_key, decrypt_api_key, is_encryption_available

router = APIRouter(prefix="/settings", tags=["Settings"])


class ApiKeySet(BaseModel):
    provider: str
    key: str


class ApiKeyTest(BaseModel):
    provider: str


@router.get("/api-keys")
def list_api_keys(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return {
        "providers": [
            {"name": "groq", "label": "Groq", "has_key": bool(current_user.api_key_groq), "url": "https://console.groq.com/keys", "free_tier": "1000 req/day"},
            {"name": "openai", "label": "OpenAI", "has_key": bool(current_user.api_key_openai), "url": "https://platform.openai.com/api-keys", "free_tier": "Free credits"},
            {"name": "gemini", "label": "Google Gemini", "has_key": bool(current_user.api_key_gemini), "url": "https://aistudio.google.com/apikey", "free_tier": "1500 req/day"},
            {"name": "deepseek", "label": "DeepSeek", "has_key": bool(current_user.api_key_deepseek), "url": "https://platform.deepseek.com/api_keys", "free_tier": "Free credits"},
        ],
        "encryption_active": is_encryption_available(),
        "commission_rate": "0%",
        "note": "Your keys are encrypted. You pay your provider directly. We never charge your API usage.",
    }


@router.post("/api-keys/set")
def set_api_key(
    data: ApiKeySet,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    encrypted = encrypt_api_key(data.key)
    if not encrypted:
        raise HTTPException(status_code=500, detail="Encryption not configured")

    field_map = {
        "groq": "api_key_groq",
        "openai": "api_key_openai",
        "gemini": "api_key_gemini",
        "deepseek": "api_key_deepseek",
    }

    field = field_map.get(data.provider)
    if not field:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {data.provider}")

    setattr(current_user, field, encrypted)
    db.commit()

    return {"status": "saved", "provider": data.provider}


@router.post("/api-keys/delete")
def delete_api_key(
    data: ApiKeySet,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    field_map = {
        "groq": "api_key_groq",
        "openai": "api_key_openai",
        "gemini": "api_key_gemini",
        "deepseek": "api_key_deepseek",
    }

    field = field_map.get(data.provider)
    if not field:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {data.provider}")

    setattr(current_user, field, "")
    db.commit()

    return {"status": "deleted", "provider": data.provider}


@router.post("/api-keys/test")
def test_api_key(
    data: ApiKeyTest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    field_map = {
        "groq": "api_key_groq",
        "openai": "api_key_openai",
        "gemini": "api_key_gemini",
        "deepseek": "api_key_deepseek",
    }

    field = field_map.get(data.provider)
    if not field:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {data.provider}")

    encrypted = getattr(current_user, field, "")
    key = decrypt_api_key(encrypted)
    if not key:
        raise HTTPException(status_code=400, detail="No key set for this provider")

    import httpx

    if data.provider == "groq":
        r = httpx.get("https://api.groq.com/openai/v1/models", headers={"Authorization": f"Bearer {key}"}, timeout=10)
        ok = r.status_code == 200
    elif data.provider == "openai":
        r = httpx.get("https://api.openai.com/v1/models", headers={"Authorization": f"Bearer {key}"}, timeout=10)
        ok = r.status_code == 200
    elif data.provider == "gemini":
        r = httpx.get(f"https://generativelanguage.googleapis.com/v1beta/models?key={key}", timeout=10)
        ok = r.status_code == 200
    elif data.provider == "deepseek":
        r = httpx.get("https://api.deepseek.com/v1/models", headers={"Authorization": f"Bearer {key}"}, timeout=10)
        ok = r.status_code == 200
    else:
        ok = False

    return {"status": "valid" if ok else "invalid", "provider": data.provider}


def get_user_api_key(db: Session, user_id: int, provider: str) -> str:
    from app.services.auth_service import get_user_by_id
    user = get_user_by_id(db, user_id)
    if not user:
        return ""

    field_map = {
        "groq": "api_key_groq",
        "openai": "api_key_openai",
        "gemini": "api_key_gemini",
        "deepseek": "api_key_deepseek",
    }

    field = field_map.get(provider, "")
    if not field:
        return ""

    encrypted = getattr(user, field, "")
    return decrypt_api_key(encrypted)
