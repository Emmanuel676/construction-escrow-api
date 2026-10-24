from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import PaymentTransaction
from tests.test_contracts import CONTRACT_PAYLOAD

WEBHOOK_URL = "/api/v1/mock-payment/webhook"


def _create_contract(client: TestClient) -> int:
    response = client.post("/api/v1/contracts/create", json=CONTRACT_PAYLOAD)
    assert response.status_code == 201
    return response.json()["id"]


def _webhook_payload(contract_id: int) -> dict[str, str | int]:
    return {
        "transaction_reference": "TXN-YO-112233",
        "payment_type": "ESCROW_LOCK",
        "reference_id": contract_id,
        "transaction_status": "SUCCESS",
    }


def test_successful_webhook_locks_escrow(client: TestClient) -> None:
    contract_id = _create_contract(client)

    response = client.post(WEBHOOK_URL, json=_webhook_payload(contract_id))

    assert response.status_code == 200
    assert response.json()["applied"] is True
    assert response.json()["status"] == "ESCROW_LOCKED"


def test_duplicate_webhook_is_ignored(client: TestClient, db_session: Session) -> None:
    contract_id = _create_contract(client)
    payload = _webhook_payload(contract_id)
    client.post(WEBHOOK_URL, json=payload)

    response = client.post(WEBHOOK_URL, json=payload)

    assert response.status_code == 200
    assert response.json() == {"detail": "duplicate callback ignored"}
    count = db_session.scalar(select(func.count()).select_from(PaymentTransaction))
    assert count == 1
