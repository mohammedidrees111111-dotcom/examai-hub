from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PaymentOrderCreate(BaseModel):
    plan: str = "monthly"


class PaymentOrderResponse(BaseModel):
    order_id: str
    approval_url: Optional[str] = None
    status: str


class PaymentCaptureRequest(BaseModel):
    order_id: str


class PaymentResponse(BaseModel):
    id: int
    paypal_order_id: str
    paypal_capture_id: Optional[str] = None
    amount: float
    currency: str
    status: str
    plan: str
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
