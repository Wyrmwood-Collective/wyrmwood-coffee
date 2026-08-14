from datetime import datetime

import pytest
from dateutil.relativedelta import relativedelta

from wyrmwood_coffee.models.customer import Customer


@pytest.fixture()
def base_customer_kwargs():
    return {
        "first_name": "SpongeBob",
        "last_name": "SquarePants",
        "email": "ilovegary@bikinibottom.com",
        "phone": "929-573-0156",
    }


# ==========================================
# CREATE OPERATIONS
# ==========================================


# --------------------
# Successful Responses
# --------------------
def test_create_customer_should_return_customer(client, base_customer_kwargs):
    response = client.post("/customers", json=base_customer_kwargs)
    assert response.status_code == 201


def test_create_customer_with_valid_complete_request_body_should_return_correct_body(
    client, base_customer_kwargs
):
    response = client.post("/customers", json=base_customer_kwargs)
    body = response.json()
    assert body["active"] is True
    assert body["first_name"] == "SpongeBob"
    assert body["last_name"] == "SquarePants"
    assert body["email"] == "ilovegary@bikinibottom.com"
    assert body["phone"] == "929-573-0156"
    assert body["loyalty_points"] == 0
    assert body["id"] > 0


def test_create_customer_with_no_phone_should_return_201(client, base_customer_kwargs):
    payload = {**base_customer_kwargs, "phone": None}
    response = client.post("/customers", json=payload)
    assert response.status_code == 201


def test_create_customer_with_no_email_should_return_201(client, base_customer_kwargs):
    payload = {**base_customer_kwargs, "email": None}
    response = client.post("/customers", json=payload)
    assert response.status_code == 201


def test_create_customer_should_set_loyalty_expiration_one_year_out(
    client, base_customer_kwargs
):
    response = client.post("/customers", json=base_customer_kwargs)
    expires_at = datetime.fromisoformat(response.json()["loyalty_expires_at"])
    expected = datetime.now() + relativedelta(years=1)
    assert abs((expires_at - expected).total_seconds()) < 60


# --------------------
# Error / Invalid Responses
# --------------------
def test_create_customer_with_missing_required_field_should_return_422(
    client, base_customer_kwargs
):
    payload = {**base_customer_kwargs, "first_name": None}
    response = client.post("/customers", json=payload)
    assert response.status_code == 422


def test_create_customer_with_no_email_or_phone_should_return_422(
    client, base_customer_kwargs
):
    payload = {**base_customer_kwargs, "email": None, "phone": None}
    response = client.post("/customers", json=payload)
    assert response.status_code == 422
    assert "Email or phone must be provided" in response.json()["detail"][0]["msg"]


def test_create_customer_with_duplicate_phone_should_return_409(
    client, base_customer_kwargs
):
    dupe_payload = {
        **base_customer_kwargs,
        "first_name": "Patrick",
        "last_name": "Star",
        "email": "ilovekrustykrab@bikinibottom.com",
    }
    client.post("/customers", json=base_customer_kwargs)
    response = client.post("/customers", json=dupe_payload)
    assert response.status_code == 409
    assert "already registered" in response.json()["detail"]


def test_create_customer_with_duplicate_email_should_return_409(
    client, base_customer_kwargs
):
    dupe_payload = {
        **base_customer_kwargs,
        "first_name": "Squidward",
        "last_name": "Tentacles",
        "phone": "774-802-9315",
    }
    client.post("/customers", json=base_customer_kwargs)
    response = client.post("/customers", json=dupe_payload)
    assert response.status_code == 409
    assert "already registered" in response.json()["detail"]


@pytest.mark.parametrize(
    "email",
    [
        "ilovemoney.com",
        "@bikinibottom.com",
        "krustykrab@",
    ],
)
def test_create_customer_with_malformatted_email_should_return_422(client, email):
    payload = {"first_name": "Eugene", "last_name": "Krabs", "email": email}
    response = client.post("/customers", json=payload)
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert ("not a valid email address" in e["msg"] for e in errors)


@pytest.mark.parametrize(
    "phone",
    [
        "12345678910",
        "12345",
        "abcdefghij",
    ],
)
def test_create_customer_with_malformatted_phone_should_return_422(client, phone):
    payload = {"first_name": "Sandy", "last_name": "Cheeks", "phone": phone}
    response = client.post("/customers", json=payload)
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert ("should match pattern" in e["msg"] for e in errors)


def test_create_customer_with_negative_loyalty_points_should_return_422(
    client, base_customer_kwargs
):
    payload = {**base_customer_kwargs, "loyalty_points": -1}
    response = client.post("/customers", json=payload)
    assert response.status_code == 422


def test_create_customer_with_first_name_is_whitespace_should_return_422(
    client, base_customer_kwargs
):
    payload = {**base_customer_kwargs, "first_name": "   "}
    response = client.post("/customers", json=payload)
    assert response.status_code == 422


# --------------------
# Side Effects
# --------------------
def test_create_customer_should_persist_to_db(db_session, client, base_customer_kwargs):
    response = client.post("/customers", json=base_customer_kwargs)
    customer = db_session.get(Customer, response.json()["id"])
    assert customer is not None


def test_create_customer_with_duplicate_email_should_not_persist(
    db_session, client, base_customer_kwargs
):
    dupe_payload = {
        **base_customer_kwargs,
        "first_name": "Doodle",
        "last_name": "Bob",
        "email": "ilovegary@bikinibottom.com",
    }
    client.post("/customers", json=base_customer_kwargs)
    previous_count = db_session.query(Customer).count()

    response = client.post("/customers", json=dupe_payload)
    assert response.status_code == 409

    current_count = db_session.query(Customer).count()
    assert previous_count == current_count
