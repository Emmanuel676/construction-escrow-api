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


def _transaction_count(db_session: Session, reference: str) -> int:
    stmt = (
        select(func.count())
        .select_from(PaymentTransaction)
        .where(PaymentTransaction.transaction_reference == reference)
    )
    return db_session.scalar(stmt) or 0


def test_not_found_does_not_consume_reference(
    client: TestClient, db_session: Session
) -> None:
    payload = _webhook_payload(1)

    response = client.post(WEBHOOK_URL, json=payload)

    assert response.status_code == 404
    assert _transaction_count(db_session, "TXN-YO-112233") == 0

    contract_id = _create_contract(client)
    assert contract_id == 1
    retry = client.post(WEBHOOK_URL, json=payload)

    assert retry.status_code == 200
    assert retry.json()["applied"] is True
    assert retry.json()["status"] == "ESCROW_LOCKED"


def test_conflict_does_not_consume_reference(
    client: TestClient, db_session: Session
) -> None:
    contract_id = _create_contract(client)
    client.post(WEBHOOK_URL, json=_webhook_payload(contract_id))
    conflicting = {
        **_webhook_payload(contract_id),
        "transaction_reference": "TXN-YO-112299",
    }

    response = client.post(WEBHOOK_URL, json=conflicting)

    assert response.status_code == 409
    assert _transaction_count(db_session, "TXN-YO-112299") == 0

    # The same reference is still processed rather than ignored as a duplicate.
    retry = client.post(
        WEBHOOK_URL, json={**conflicting, "transaction_status": "FAILED"}
    )
    assert retry.status_code == 200
    assert retry.json()["applied"] is False
    assert _transaction_count(db_session, "TXN-YO-112299") == 1
