import pytest

from wyrmwood_coffee.dependencies import require_auth
from wyrmwood_coffee.main import app
from wyrmwood_coffee.models.purchase import Purchase


@pytest.fixture(autouse=True)
def override_auth():
    """Bypasses the auth requirement for all tests in this file."""
    app.dependency_overrides[require_auth] = lambda: {
        "username": "test",
        "role": "employee",
    }
    yield
    app.dependency_overrides.clear()


def test_create_purchase_with_valid_payload_should_return_purchase(
    db_session, client, make_baked_good
):
    payload = {"items": [{"name": make_baked_good().name, "quantity": 1}]}
    response = client.post("/purchases", json=payload)

    assert response.status_code == 201
    assert response.json()["total"] is not None


def test_create_purchase_with_missing_items_should_return_422(db_session, client):
    payload = {"items": []}
    response = client.post("/purchases", json=payload)

    assert response.status_code == 422


def test_create_purchase_should_persist_to_db(db_session, client, make_baked_good):
    payload = {"items": [{"name": make_baked_good().name, "quantity": 1}]}
    response = client.post("/purchases", json=payload)

    assert response.status_code == 201

    purchase_id = response.json()["id"]
    db_purchase = db_session.get(Purchase, purchase_id)
    assert db_purchase is not None
