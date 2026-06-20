from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.payment import PaymentOrderCreate, PaymentOrderResponse, PaymentCaptureRequest, PaymentResponse
from app.services.payment_service import (
    create_paypal_order,
    capture_paypal_order,
    create_payment_record,
    update_payment_captured,
    get_user_payments,
)
from app.services.auth_service import get_user_by_id, upgrade_user_to_premium
from app.routers.user import get_current_user, log_activity
from app.config import settings

router = APIRouter(prefix="/payments", tags=["Payments"])

PLAN_PRICES = {"monthly": 9.99, "yearly": 79.99, "lifetime": 149.99}


@router.post("/create-order", response_model=PaymentOrderResponse)
async def create_order(
    req: PaymentOrderCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    amount = PLAN_PRICES.get(req.plan, 9.99)
    result = await create_paypal_order(amount, "USD", req.plan, current_user.id)

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    create_payment_record(db, current_user.id, result["order_id"], amount, req.plan)
    return PaymentOrderResponse(
        order_id=result["order_id"],
        approval_url=result.get("approval_url"),
        status=result["status"],
    )


@router.post("/capture-order")
async def capture_order(
    req: PaymentCaptureRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    from app.models.payment import Payment
    payment = db.query(Payment).filter(
        Payment.paypal_order_id == req.order_id,
        Payment.user_id == current_user.id,
    ).first()
    if not payment and not req.order_id.startswith("DEMO-"):
        raise HTTPException(status_code=404, detail="Order not found or does not belong to you")

    result = await capture_paypal_order(req.order_id)

    capture_id = result.get("capture_id", "")
    update_payment_captured(db, req.order_id, capture_id)

    if result["status"] in ("COMPLETED", "completed", "demo_completed"):
        from app.services.auth_service import upgrade_user_to_premium
        upgrade_user_to_premium(db, current_user.id)
        return {"status": "completed", "capture_id": capture_id, "premium_activated": True}

    return {"status": result["status"], "capture_id": capture_id, "premium_activated": False}


@router.get("/history", response_model=list[PaymentResponse])
def payment_history(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    payments = get_user_payments(db, current_user.id)
    return [PaymentResponse.model_validate(p) for p in payments]


@router.get("/verify-premium")
def verify_premium(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    user = get_user_by_id(db, current_user.id)
    return {
        "is_premium": user.is_premium if user else False,
        "user_id": current_user.id,
    }


class ActivateDemoRequest(BaseModel):
    plan: str = "monthly"


@router.post("/activate-demo")
def activate_demo(
    req: ActivateDemoRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Instantly activate premium. Works only when PayPal is not configured (development mode)."""
    if settings.PAYPAL_CLIENT_ID and settings.PAYPAL_CLIENT_SECRET:
        raise HTTPException(status_code=400, detail="Real payment required. Please use the PayPal checkout flow.")

    amount = PLAN_PRICES.get(req.plan, 9.99)
    order_id = f"DEMO-{req.plan.upper()}-{current_user.id}"
    create_payment_record(db, current_user.id, order_id, amount, req.plan)
    update_payment_captured(db, order_id, f"CAPTURE-{order_id}")
    upgrade_user_to_premium(db, current_user.id)
    log_activity(db, current_user.id, "payment")

    return {
        "status": "completed",
        "premium_activated": True,
        "plan": req.plan,
        "message": f"Premium {req.plan} plan activated instantly!"
    }
