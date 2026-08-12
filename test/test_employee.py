from decimal import Decimal

import bcrypt
import pytest

from wyrmwood_coffee.models.employee import Employee, EmployeeRead


@pytest.fixture
def employee_kwargs():
    return {
        "active": True,
        "first_name": "Ada",
        "last_name": "Lovelace",
        "role": "employee",
        "hourly_rate": 18.5,
        "hire_date": "2024-01-15",
        "username": "alovelace",
        "password": "Password1!",
    }


@pytest.fixture
def employee_inactive_kwargs(employee_kwargs):
    return employee_kwargs | {"active": False}


@pytest.fixture
def employee_missing_active_kwargs(employee_kwargs):
    kwargs = dict(employee_kwargs)
    del kwargs["active"]
    return kwargs


@pytest.fixture
def employee_with_term_date_kwargs(employee_kwargs):
    return employee_kwargs | {"term_date": "2025-06-01"}


@pytest.fixture
def employee_missing_hire_date_kwargs(employee_kwargs):
    kwargs = dict(employee_kwargs)
    del kwargs["hire_date"]
    return kwargs


@pytest.fixture
def employee_missing_first_name_kwargs(employee_kwargs):
    kwargs = dict(employee_kwargs)
    del kwargs["first_name"]
    return kwargs


@pytest.fixture
def employee_whitespace_first_name_kwargs(employee_kwargs):
    return employee_kwargs | {"first_name": "   "}


@pytest.fixture
def employee_invalid_role_kwargs(employee_kwargs):
    return employee_kwargs | {"role": "barista"}


@pytest.fixture
def employee_zero_hourly_rate_kwargs(employee_kwargs):
    return employee_kwargs | {"hourly_rate": 0}


@pytest.fixture
def employee_hourly_rate_too_many_decimals_kwargs(employee_kwargs):
    return employee_kwargs | {"hourly_rate": "18.555"}


@pytest.fixture
def employee_term_date_before_hire_date_kwargs(employee_kwargs):
    return employee_kwargs | {"term_date": "2024-01-14"}


@pytest.fixture
def employee_term_date_equal_hire_date_kwargs(employee_kwargs):
    return employee_kwargs | {"term_date": employee_kwargs["hire_date"]}


@pytest.fixture
def employee_short_password_kwargs(employee_kwargs):
    return employee_kwargs | {"password": "Ab1!"}


@pytest.fixture
def employee_password_no_capital_kwargs(employee_kwargs):
    return employee_kwargs | {"password": "password1!"}


@pytest.fixture
def employee_password_no_number_kwargs(employee_kwargs):
    return employee_kwargs | {"password": "Password!"}


@pytest.fixture
def employee_password_no_special_kwargs(employee_kwargs):
    return employee_kwargs | {"password": "Password1"}


@pytest.fixture
def employee_missing_password_kwargs(employee_kwargs):
    kwargs = dict(employee_kwargs)
    del kwargs["password"]
    return kwargs


def test_create_employee_should_return_employee(client, employee_kwargs):
    response = client.post("/employees", json=employee_kwargs)
    assert response.status_code == 201

    employee = EmployeeRead(**response.json())
    expected = {
        key: value for key, value in employee_kwargs.items() if key != "password"
    } | {
        "id": employee.id,
        "term_date": None,
        "hourly_rate": f"{Decimal(str(employee_kwargs['hourly_rate'])):.2f}",
    }
    assert employee.model_dump(mode="json") == expected
    assert "password" not in response.json()


def test_create_employee_with_term_date_should_return_employee(
    client, employee_with_term_date_kwargs
):
    response = client.post("/employees", json=employee_with_term_date_kwargs)
    assert response.status_code == 201

    employee = EmployeeRead(**response.json())
    expected = {
        key: value
        for key, value in employee_with_term_date_kwargs.items()
        if key != "password"
    } | {
        "id": employee.id,
        "hourly_rate": (
            f"{Decimal(str(employee_with_term_date_kwargs['hourly_rate'])):.2f}"
        ),
    }
    assert employee.model_dump(mode="json") == expected


def test_create_employee_without_active_should_default_to_true(
    client, employee_missing_active_kwargs
):
    response = client.post("/employees", json=employee_missing_active_kwargs)
    assert response.status_code == 201
    assert response.json()["active"] is True


def test_create_employee_with_active_false_should_return_inactive_employee(
    client, employee_inactive_kwargs
):
    response = client.post("/employees", json=employee_inactive_kwargs)
    assert response.status_code == 201
    assert response.json()["active"] is False


def test_create_employee_with_missing_hire_date_should_return_422(
    client, employee_missing_hire_date_kwargs
):
    response = client.post("/employees", json=employee_missing_hire_date_kwargs)
    assert response.status_code == 422


def test_create_employee_with_missing_first_name_should_return_422(
    client, employee_missing_first_name_kwargs
):
    response = client.post("/employees", json=employee_missing_first_name_kwargs)
    assert response.status_code == 422


def test_create_employee_with_whitespace_first_name_should_return_422(
    client, employee_whitespace_first_name_kwargs
):
    response = client.post("/employees", json=employee_whitespace_first_name_kwargs)
    assert response.status_code == 422


def test_create_employee_with_invalid_role_should_return_422(
    client, employee_invalid_role_kwargs
):
    response = client.post("/employees", json=employee_invalid_role_kwargs)
    assert response.status_code == 422


def test_create_employee_with_zero_hourly_rate_should_return_422(
    client, employee_zero_hourly_rate_kwargs
):
    response = client.post("/employees", json=employee_zero_hourly_rate_kwargs)
    assert response.status_code == 422


def test_create_employee_with_hourly_rate_too_many_decimals_should_return_422(
    client, employee_hourly_rate_too_many_decimals_kwargs
):
    response = client.post(
        "/employees", json=employee_hourly_rate_too_many_decimals_kwargs
    )
    assert response.status_code == 422


def test_create_employee_with_term_date_before_hire_date_should_return_422(
    client, employee_term_date_before_hire_date_kwargs
):
    response = client.post(
        "/employees", json=employee_term_date_before_hire_date_kwargs
    )
    assert response.status_code == 422


def test_create_employee_with_term_date_equal_hire_date_should_return_422(
    client, employee_term_date_equal_hire_date_kwargs
):
    response = client.post("/employees", json=employee_term_date_equal_hire_date_kwargs)
    assert response.status_code == 422


def test_create_employee_with_short_password_should_return_422(
    client, employee_short_password_kwargs
):
    response = client.post("/employees", json=employee_short_password_kwargs)
    assert response.status_code == 422


def test_create_employee_with_password_missing_capital_should_return_422(
    client, employee_password_no_capital_kwargs
):
    response = client.post("/employees", json=employee_password_no_capital_kwargs)
    assert response.status_code == 422


def test_create_employee_with_password_missing_number_should_return_422(
    client, employee_password_no_number_kwargs
):
    response = client.post("/employees", json=employee_password_no_number_kwargs)
    assert response.status_code == 422


def test_create_employee_with_password_missing_special_should_return_422(
    client, employee_password_no_special_kwargs
):
    response = client.post("/employees", json=employee_password_no_special_kwargs)
    assert response.status_code == 422


def test_create_employee_with_missing_password_should_return_422(
    client, employee_missing_password_kwargs
):
    response = client.post("/employees", json=employee_missing_password_kwargs)
    assert response.status_code == 422


def test_create_employee_with_duplicate_username_should_return_409(
    client, employee_kwargs
):
    first = client.post("/employees", json=employee_kwargs)
    assert first.status_code == 201

    second = client.post("/employees", json=employee_kwargs)
    assert second.status_code == 409


def test_create_employee_should_persist_to_db(db_session, client, employee_kwargs):
    response = client.post("/employees", json=employee_kwargs)
    employee = db_session.get(Employee, response.json()["id"])
    assert employee is not None
    assert employee.hourly_rate == Decimal("18.5")
    assert isinstance(employee.hourly_rate, Decimal)


def test_create_employee_should_hash_password(db_session, client, employee_kwargs):
    response = client.post("/employees", json=employee_kwargs)
    employee = db_session.get(Employee, response.json()["id"])
    assert employee.password != employee_kwargs["password"]
    assert bcrypt.checkpw(
        employee_kwargs["password"].encode("utf-8"),
        employee.password.encode("utf-8"),
    )
