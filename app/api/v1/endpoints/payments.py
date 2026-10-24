import hmac

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.schemas.payment import PaymentWebhook, WebhookResponse
from app.services import payment_service
from app.services.exceptions import ConflictError, NotFoundError

router = APIRouter(prefix="/mock-payment", tags=["payments"])


def verify_webhook_secret(
    x_webhook_secret: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> None:
    """Require a matching X-Webhook-Secret header when WEBHOOK_SECRET is configured."""
    expected = settings.WEBHOOK_SECRET
    if not expected:
        return
    if x_webhook_secret is None or not hmac.compare_digest(
        x_webhook_secret.encode(), expected.encode()
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Webhook-Secret header",
        )


@router.post(
    "/webhook",
    response_model=WebhookResponse,
    response_model_exclude_none=True,
    dependencies=[Depends(verify_webhook_secret)],
)
def payment_webhook(
    payload: PaymentWebhook, db: Session = Depends(get_db)
) -> WebhookResponse:
    try:
        result = payment_service.process_webhook(db, payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.detail)
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.detail)
    return WebhookResponse(
        detail=result.detail, applied=result.applied, status=result.status
    )
