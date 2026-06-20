from typing import Optional
import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models.payment import Payment


PAYPAL_BASE = (
    "https://api-m.sandbox.paypal.com"
    if settings.PAYPAL_MODE == "sandbox"
    else "https://api-m.paypal.com"
)


async def get_paypal_token() -> Optional[str]:
    if not settings.PAYPAL_CLIENT_ID or not settings.PAYPAL_CLIENT_SECRET:
        return None
    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
        resp = await client.post(
            f"{PAYPAL_BASE}/v1/oauth2/token",
            data={"grant_type": "client_credentials"},
            auth=(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if resp.status_code == 200:
            return resp.json().get("access_token")
    return None


async def create_paypal_order(amount: float, currency: str = "USD", plan: str = "monthly", user_id: int = 0) -> dict:
    token = await get_paypal_token()
    if not token:
        return {
            "order_id": f"DEMO-{plan.upper()}-{user_id}",
            "approval_url": f"{settings.FRONTEND_URL}/dashboard?payment=demo&order_id=DEMO-{plan.upper()}-{user_id}",
            "status": "demo",
        }

    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
        resp = await client.post(
            f"{PAYPAL_BASE}/v2/checkout/orders",
            json={
                "intent": "CAPTURE",
                "purchase_units": [{
                    "amount": {"currency_code": currency, "value": str(amount)},
                    "description": f"ExamAI Hub - {plan.capitalize()} Plan",
                }],
                "application_context": {
                    "return_url": f"{settings.FRONTEND_URL}/dashboard?payment=success",
                    "cancel_url": f"{settings.FRONTEND_URL}/dashboard?payment=cancelled",
                },
            },
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )
        data = resp.json()
        order_id = data.get("id", "")
        approval_url = None
        for link in data.get("links", []):
            if link.get("rel") == "approve":
                approval_url = link.get("href")
                break

        return {
            "order_id": order_id,
            "approval_url": approval_url,
            "status": data.get("status", "unknown"),
            "return_url": f"{settings.FRONTEND_URL}/dashboard?payment=success&order_id={order_id}",
        }


async def capture_paypal_order(order_id: str) -> dict:
    if order_id.startswith("DEMO-") or not settings.PAYPAL_CLIENT_ID:
        return {"status": "demo_completed", "capture_id": f"CAPTURE-{order_id}"}

    token = await get_paypal_token()
    if not token:
        return {"status": "demo_completed", "capture_id": f"CAPTURE-{order_id}"}

    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
        resp = await client.post(
            f"{PAYPAL_BASE}/v2/checkout/orders/{order_id}/capture",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )
        data = resp.json()
        capture_id = None
        status = data.get("status", "failed")
        for pu in data.get("purchase_units", []):
            for cap in pu.get("payments", {}).get("captures", []):
                capture_id = cap.get("id")
                status = cap.get("status", status)
        return {"status": status, "capture_id": capture_id}


def create_payment_record(db: Session, user_id: int, order_id: str, amount: float, plan: str) -> Payment:
    payment = Payment(
        user_id=user_id,
        paypal_order_id=order_id,
        amount=amount,
        currency="USD",
        status="pending",
        plan=plan,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def update_payment_captured(db: Session, order_id: str, capture_id: str):
    payment = db.query(Payment).filter(Payment.paypal_order_id == order_id).first()
    if payment:
        payment.paypal_capture_id = capture_id
        payment.status = "completed"
        from datetime import datetime, timezone
        payment.completed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(payment)
    return payment


def get_user_payments(db: Session, user_id: int) -> list[Payment]:
    return db.query(Payment).filter(Payment.user_id == user_id).order_by(Payment.created_at.desc()).all()
