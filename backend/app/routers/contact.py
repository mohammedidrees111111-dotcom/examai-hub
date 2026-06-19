from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/contact", tags=["Contact"])


class ContactRequest(BaseModel):
    name: str
    email: str
    message: str


@router.post("")
def submit_contact(req: ContactRequest):
    # In production, send email or store in DB
    # For now, log to console and return success
    print(f"[CONTACT] {req.name} <{req.email}>: {req.message[:200]}")
    return {"status": "ok", "message": "Message received. We will respond within 24 hours."}
