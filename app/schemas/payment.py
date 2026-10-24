from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import NonEmptyStr


class PaymentWebhook(BaseModel):
    transaction_reference: NonEmptyStr
    payment_type: Literal["ESCROW_LOCK", "STORE_PURCHASE"]
    reference_id: int = Field(gt=0)
    transaction_status: NonEmptyStr


class WebhookResponse(BaseModel):
    detail: str
    applied: bool | None = None
    status: str | None = None
