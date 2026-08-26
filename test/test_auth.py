from datetime import UTC, datetime, timedelta

import jwt

from wyrmwood_coffee.settings import settings


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
