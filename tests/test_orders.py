from fastapi.testclient import TestClient

ORDER_PAYLOAD = {
    "contractor_id": 12,
    "delivery_site_location": "Luweero Town Council, Plot 14",
    "items": [
        {
            "product_id": 101,
            "product_name": "Hima Cement 50kg",
            "quantity": 40,
            "unit_price_ugx": 35000,
        },
        {
            "product_id": 205,
            "product_name": "Y12 Steel Bar",
            "quantity": 25,
            "unit_price_ugx": 42000,
        },
    ],
}


def test_create_order_computes_totals_server_side(client: TestClient) -> None:
    response = client.post("/api/v1/store/order", json=ORDER_PAYLOAD)

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "AWAITING_FULFILLMENT"
    assert body["total_amount_ugx"] == 2450000
    assert [item["line_total_ugx"] for item in body["items"]] == [1400000, 1050000]


def test_create_order_unknown_contractor_returns_404(client: TestClient) -> None:
    payload = {**ORDER_PAYLOAD, "contractor_id": 999}

    response = client.post("/api/v1/store/order", json=payload)

    assert response.status_code == 404
