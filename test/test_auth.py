import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from conftest import _persist_employee

from wyrmwood_coffee.models.token import BlacklistedToken
from wyrmwood_coffee.security import create_access_token, decode_access_token
from wyrmwood_coffee.settings import settings


@pytest.fixture
def active_employee(db_session, employee_kwargs):
    return _persist_employee(db_session, employee_kwargs)


@pytest.fixture
def inactive_employee(db_session, employee_inactive_kwargs):
    return _persist_employee(db_session, employee_inactive_kwargs)


@pytest.fixture
def valid_token(active_employee):
    return create_access_token(
        data={"sub": str(active_employee.id), "role": active_employee.role}
    )


def auth_header(token: str):
    return {"Authorization": f"Bearer {token}"}


def make_expired_token(employee):
    payload = {
        "sub": str(employee.id),
        "role": employee.role,
        "exp": datetime.now(UTC) - timedelta(minutes=1),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(
        payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )


def make_token_bad_signature(employee):
    payload = {
        "sub": str(employee.id),
        "role": employee.role,
        "exp": datetime.now(UTC) + timedelta(minutes=30),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(
        payload, "this-may-or-may-not-be-the-secret", algorithm=settings.jwt_algorithm
    )


def test_login_should_return_token(
    db_session, client, employee_kwargs, persist_employee
):
    employee = persist_employee(employee_kwargs)

    issued_at = datetime.now(UTC)
    response = client.post(
        "/auth/login",
        data={
            "username": employee_kwargs["username"],
            "password": employee_kwargs["password"],
        },
    )
    assert response.status_code == 200

    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"

    payload = jwt.decode(
        body["access_token"],
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )
    assert payload["sub"] == str(employee.id)
    assert payload["role"] == employee.role

    exp = datetime.fromtimestamp(payload["exp"], tz=UTC)
    expected = issued_at + timedelta(minutes=settings.jwt_expiration_minutes)
    assert abs((exp - expected).total_seconds()) < 5


def test_login_with_invalid_password_should_return_401(
    db_session, client, employee_kwargs, persist_employee
):
    persist_employee(employee_kwargs)

    response = client.post(
        "/auth/login",
        data={
            "username": employee_kwargs["username"],
            "password": "WrongPassword1!",
        },
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password."


def test_login_with_invalid_username_should_return_401(
    db_session, client, employee_kwargs, persist_employee
):
    persist_employee(employee_kwargs)

    response = client.post(
        "/auth/login",
        data={
            "username": "nonexistentuser",
            "password": employee_kwargs["password"],
        },
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password."


def test_login_with_inactive_employee_should_return_401(
    db_session, client, employee_inactive_kwargs, persist_employee
):
    employee = persist_employee(employee_inactive_kwargs)

    response = client.post(
        "/auth/login",
        data={
            "username": employee.username,
            "password": employee_inactive_kwargs["password"],
        },
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password."


def test_logout_should_return_204(client, valid_token):
    response = client.post("/auth/logout", headers=auth_header(valid_token))
    assert response.status_code == 204


def test_logout_without_token_should_return_401(client):
    response = client.post("/auth/logout")
    assert response.status_code == 401


def test_logout_with_expired_token_should_return_401(client, active_employee):
    token = make_expired_token(active_employee)
    response = client.post("/auth/logout", headers=auth_header(token))
    assert response.status_code == 401


def test_logout_with_bad_signature_should_return_401(client, active_employee):
    token = make_token_bad_signature(active_employee)
    response = client.post("/auth/logout", headers=auth_header(token))
    assert response.status_code == 401


def test_logout_with_same_token_for_second_attempt_should_return_401(
    client, valid_token
):
    first_attempt = client.post("/auth/logout", headers=auth_header(valid_token))
    assert first_attempt.status_code == 204

    second_attempt = client.post("/auth/logout", headers=auth_header(valid_token))
    assert second_attempt.status_code == 401


def test_logout_should_not_deactive_employee(
    db_session, client, active_employee, valid_token
):
    client.post("/auth/logout", headers=auth_header(valid_token))
    db_session.refresh(active_employee)
    assert active_employee.active is True


def test_logout_should_create_token_blacklist(db_session, client, valid_token):
    jti = decode_access_token(valid_token)["jti"]
    client.post("/auth/logout", headers=auth_header(valid_token))

    token_blacklist = db_session.get(BlacklistedToken, jti)
    assert token_blacklist is not None


def test_logout_with_failure_should_not_create_token_blacklist(
    db_session, client, active_employee
):
    before = db_session.query(BlacklistedToken).count()
    token = make_expired_token(active_employee)
    client.post("/auth/logout", headers=auth_header(token))
    after = db_session.query(BlacklistedToken).count()
    assert after == before


def test_logout_with_repeated_logout_attempts_should_create_one_token_blacklist_row(
    db_session, client, valid_token
):
    client.post("/auth/logout", headers=auth_header(valid_token))
    client.post("/auth/logout", headers=auth_header(valid_token))
    client.post("/auth/logout", headers=auth_header(valid_token))
    jti = decode_access_token(valid_token)["jti"]
    rows = db_session.query(BlacklistedToken).filter(BlacklistedToken.jti == jti).all()
    assert len(rows) == 1
