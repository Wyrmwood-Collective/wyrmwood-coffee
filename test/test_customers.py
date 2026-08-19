import itertools
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


@pytest.fixture()
def make_customer(db_session):
    counter = itertools.count(1)

    def _make_customer(**kwargs):
        n = next(counter)
        defaults = {
            "active": True,
            "first_name": "SpongeBob",
            "last_name": "SquarePants",
            "email": f"ilovegary+{n}@bikinibottom.com",
            "phone": f"929-573-{n:04d}",
            "loyalty_points": 0,
            "loyalty_expires_at": datetime.now(),
        }
        defaults.update(kwargs)
        customer = Customer(**defaults)
        db_session.add(customer)
        db_session.commit()
        db_session.refresh(customer)
        return customer

    return _make_customer


# ==========================================
# READ OPERATIONS
# ==========================================


# --------------------
# Successful Responses
# --------------------
def test_list_customers_should_return_empty_list(client):
    response = client.get("/customers")
    assert response.status_code == 200
    assert response.json() == []


def test_list_customers_should_return_list_of_single_customer(client, make_customer):
    customer_1 = make_customer()
    response = client.get("/customers")
    assert response.status_code == 200

    body = response.json()
    assert len(body) == 1
    assert body[0]["email"] == customer_1.email
    assert body[0]["id"] == customer_1.id
    assert body[0]["first_name"] == customer_1.first_name


def test_list_customers_should_return_list_of_multiple_customers(client, make_customer):
    customer_1 = make_customer()
    customer_2 = make_customer(
        first_name="Gary",
        last_name="Wilson, Jr.",
        email="meowmeow@bikinibottom.com",
        phone="929-421-8975",
    )

    response = client.get("/customers")
    assert response.status_code == 200

    body = response.json()
    assert len(body) == 2

    emails = {c["email"] for c in body}
    assert emails == {customer_1.email, customer_2.email}

    phones = {c["phone"] for c in body}
    assert phones == {customer_1.phone, customer_2.phone}


def test_list_customers_with_inactive_customer_should_return_all_customers(
    client, make_customer
):
    customer_1 = make_customer()
    customer_2 = make_customer(
        active=False,
        first_name="Pearl",
        last_name="Krabs",
        email="boysdontcryfan@bikinibottom.com",
        phone=None,
    )
    response = client.get("/customers")
    assert response.status_code == 200

    body = response.json()
    assert len(body) == 2

    emails = {c["email"] for c in body}
    assert emails == {customer_1.email, customer_2.email}

    phones = {c["phone"] for c in body}
    assert phones == {customer_1.phone, customer_2.phone}


def test_list_customers_with_unset_optional_fields_should_return_null(
    client, make_customer
):
    customer_1 = make_customer(
        first_name="Flying", last_name="Dutchman", phone="881-972-3740", email=None
    )
    response = client.get("/customers")
    assert response.status_code == 200

    body = response.json()
    assert len(body) == 1
    assert body[0]["email"] is None
    assert body[0]["id"] == customer_1.id
    assert body[0]["last_name"] == customer_1.last_name


# --------------------
# Side Effects
# --------------------


def test_list_customers_should_not_modify_data(db_session, client, make_customer):
    make_customer()
    db_session.commit()

    before = db_session.query(Customer).all()
    before_snapshot = [
        (
            c.id,
            c.active,
            c.first_name,
            c.last_name,
            c.email,
            c.phone,
            c.loyalty_points,
            c.loyalty_expires_at,
        )
        for c in before
    ]

    client.get("/customers")
    db_session.expire_all()

    after = db_session.query(Customer).all()
    after_snapshot = [
        (
            c.id,
            c.active,
            c.first_name,
            c.last_name,
            c.email,
            c.phone,
            c.loyalty_points,
            c.loyalty_expires_at,
        )
        for c in after
    ]

    assert before_snapshot == after_snapshot
    assert len(after) == 1


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
