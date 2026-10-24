from fastapi.testclient import TestClient

ORDER_PAYLOAD = {
    "contractor_id": 12,
    "delivery_site_location": "Wobulenzi, Luweero",
    "items": [
        {
            "product_id": 101,
            "product_name": "Tororo Cement Bag",
            "quantity": 50,
            "unit_price_ugx": 32000,
        },
        {
            "product_id": 204,
            "product_name": "Electrical Conduit Pipe",
            "quantity": 15,
            "unit_price_ugx": 8500,
        },
    ],
}


def test_create_order_computes_totals_server_side(client: TestClient) -> None:
    response = client.post("/api/v1/store/order", json=ORDER_PAYLOAD)

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "AWAITING_FULFILLMENT"
    assert body["total_amount_ugx"] == 1727500
    assert [item["line_total_ugx"] for item in body["items"]] == [1600000, 127500]


def test_create_order_unknown_contractor_returns_404(client: TestClient) -> None:
    payload = {**ORDER_PAYLOAD, "contractor_id": 999}

    response = client.post("/api/v1/store/order", json=payload)

    assert response.status_code == 404
