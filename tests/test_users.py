from fastapi.testclient import TestClient


def test_get_profile_returns_trust_badges(client: TestClient) -> None:
    response = client.get("/api/v1/users/profile/4")

    assert response.status_code == 200
    assert response.json() == {
        "user_id": 4,
        "name": "Alex Mukasa",
        "role": "Civil Engineer",
        "is_identity_verified_by_laboremus": True,
        "is_credentials_verified_by_verify_ug": True,
        "cloud_storage_blueprint_url": None,
    }


def test_get_profile_unknown_user_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/users/profile/999")

    assert response.status_code == 404
