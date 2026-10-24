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
    """Apply a payment callback exactly once and always record the transaction.

    Raises NotFoundError / ConflictError after recording the (unapplied)
    transaction so that provider retries are treated as duplicates.
    """
    if _is_duplicate(db, payload.transaction_reference):
        return WebhookResult(detail=DUPLICATE_DETAIL)

    model, initial_status, success_status = _TRANSITIONS[payload.payment_type]
    record = db.get(model, payload.reference_id)

    transaction = PaymentTransaction(
        transaction_reference=payload.transaction_reference,
        payment_type=payload.payment_type,
        reference_id=payload.reference_id,
        transaction_status=payload.transaction_status,
        applied=False,
    )

    error: NotFoundError | ConflictError | None = None
    result: WebhookResult | None = None
    label = "Contract" if model is Contract else "Hardware order"

    if record is None:
        error = NotFoundError(f"{label} with id {payload.reference_id} not found")
    elif payload.transaction_status != TransactionStatus.SUCCESS.value:
        result = WebhookResult(
            detail=(
                f"transaction_status is '{payload.transaction_status}'; "
                "recorded without changing status"
            ),
            applied=False,
            status=record.status,
        )
    elif record.status != initial_status:
        error = ConflictError(
            f"{label} {payload.reference_id} is in status '{record.status}', "
            f"expected '{initial_status}'"
        )
    else:
        record.status = success_status
        transaction.applied = True
        result = WebhookResult(
            detail="payment applied", applied=True, status=success_status
        )

    db.add(transaction)
    try:
        db.commit()
    except IntegrityError:
        # A concurrent callback with the same reference won the race.
        db.rollback()
        return WebhookResult(detail=DUPLICATE_DETAIL)

    if error is not None:
        raise error
    assert result is not None
    return result
