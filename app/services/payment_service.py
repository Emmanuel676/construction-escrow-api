from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Contract, HardwareOrder, PaymentTransaction
from app.models.enums import (
    ContractStatus,
    OrderStatus,
    PaymentType,
    TransactionStatus,
)
from app.schemas.payment import PaymentWebhook
from app.services.exceptions import ConflictError, NotFoundError

DUPLICATE_DETAIL = "duplicate callback ignored"

# payment_type -> (model, required initial status, status after a successful payment)
_TRANSITIONS: dict[str, tuple[type[Contract] | type[HardwareOrder], str, str]] = {
    PaymentType.ESCROW_LOCK.value: (
        Contract,
        ContractStatus.PENDING_PAYMENT.value,
        ContractStatus.ESCROW_LOCKED.value,
    ),
    PaymentType.STORE_PURCHASE.value: (
        HardwareOrder,
        OrderStatus.AWAITING_FULFILLMENT.value,
        OrderStatus.PAID_PROCESSING.value,
    ),
}


@dataclass(frozen=True)
class WebhookResult:
    detail: str
    applied: bool | None = None
    status: str | None = None


def _is_duplicate(db: Session, transaction_reference: str) -> bool:
    stmt = select(PaymentTransaction.id).where(
        PaymentTransaction.transaction_reference == transaction_reference
    )
    return db.scalar(stmt) is not None


def process_webhook(db: Session, payload: PaymentWebhook) -> WebhookResult:
    """Apply a payment callback at most once per transaction_reference.

    A reference is consumed (persisted) only when the payment is applied or a
    non-SUCCESS status is recorded. NotFoundError / ConflictError are raised
    without persisting anything, so a provider retry with the same reference
    is processed normally once the underlying record is fixed.
    """
    if _is_duplicate(db, payload.transaction_reference):
        return WebhookResult(detail=DUPLICATE_DETAIL)

    model, initial_status, success_status = _TRANSITIONS[payload.payment_type]
    label = "Contract" if model is Contract else "Hardware order"
    record = db.get(model, payload.reference_id)

    if record is None:
        raise NotFoundError(f"{label} with id {payload.reference_id} not found")

    is_success = payload.transaction_status == TransactionStatus.SUCCESS.value
    if is_success and record.status != initial_status:
        raise ConflictError(
            f"{label} {payload.reference_id} is in status '{record.status}', "
            f"expected '{initial_status}'"
        )

    if is_success:
        record.status = success_status
        result = WebhookResult(
            detail="payment applied", applied=True, status=success_status
        )
    else:
        result = WebhookResult(
            detail=(
                f"transaction_status is '{payload.transaction_status}'; "
                "recorded without changing status"
            ),
            applied=False,
            status=record.status,
        )

    db.add(
        PaymentTransaction(
            transaction_reference=payload.transaction_reference,
            payment_type=payload.payment_type,
            reference_id=payload.reference_id,
            transaction_status=payload.transaction_status,
            applied=is_success,
        )
    )
    try:
        db.commit()
    except IntegrityError:
        # A concurrent callback with the same reference won the race; the
        # rollback also discards this request's status change.
        db.rollback()
        return WebhookResult(detail=DUPLICATE_DETAIL)

    return result
