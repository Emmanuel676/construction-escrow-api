from fastapi.testclient import TestClient

CONTRACT_PAYLOAD = {
    "engineer_name": "John Doe",
    "client_name": "Luweero Property Developers Ltd",
    "project_location": "Luweero Town",
    "milestone_title": "Foundation Concrete Pour",
    "milestone_budget_ugx": 35000000,
}


def test_create_contract_returns_201_with_pending_status(client: TestClient) -> None:
    response = client.post("/api/v1/contracts/create", json=CONTRACT_PAYLOAD)

    assert response.status_code == 201
    body = response.json()
    assert body["id"] > 0
    assert body["status"] == "PENDING_PAYMENT"
    assert body["milestone_budget_ugx"] == 35000000
    assert body["project_location"] == "Luweero Town"


def test_create_contract_outside_luweero_returns_422(client: TestClient) -> None:
    payload = {**CONTRACT_PAYLOAD, "project_location": "Kampala Central"}

    response = client.post("/api/v1/contracts/create", json=payload)

    assert response.status_code == 422
    assert "Luweero" in response.text
