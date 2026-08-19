from datetime import date
from decimal import Decimal

import bcrypt
import pytest
from sqlalchemy import func, select

from wyrmwood_coffee.models.employee import EMPLOYEE_ID_MAX, Employee, EmployeeRead
from wyrmwood_coffee.security import hash_password


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


def _persist_employee(db_session, kwargs):
    term_date = kwargs.get("term_date")
    employee = Employee(
        active=kwargs["active"],
        first_name=kwargs["first_name"],
        last_name=kwargs["last_name"],
        role=kwargs["role"],
        hourly_rate=Decimal(str(kwargs["hourly_rate"])),
        hire_date=date.fromisoformat(kwargs["hire_date"]),
        term_date=date.fromisoformat(term_date) if term_date else None,
        username=kwargs["username"],
        password=hash_password(kwargs["password"]),
    )
    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)
    return employee


def _expected_employee_json(kwargs, employee_id):
    expected = {key: value for key, value in kwargs.items() if key != "password"} | {
        "id": employee_id,
        "hourly_rate": f"{Decimal(str(kwargs['hourly_rate'])):.2f}",
    }
    expected.setdefault("term_date", None)
    return expected


@pytest.fixture
def persisted_employee(db_session, employee_kwargs):
    return _persist_employee(db_session, employee_kwargs)


@pytest.fixture
def persisted_inactive_employee(db_session, employee_inactive_kwargs):
    return _persist_employee(db_session, employee_inactive_kwargs)


@pytest.fixture
def persisted_employees(db_session, employee_kwargs):
    second_kwargs = employee_kwargs | {
        "first_name": "Grace",
        "last_name": "Hopper",
        "username": "ghopper",
    }
    first = _persist_employee(db_session, employee_kwargs)
    second = _persist_employee(db_session, second_kwargs)
    return first, second


@pytest.fixture
def unused_employee_id(db_session):
    def _unused_employee_id():
        max_id = db_session.scalar(select(func.max(Employee.id))) or 0
        return max_id + 1

    return _unused_employee_id


def test_list_employees_with_no_employees_should_return_empty_list(client):
    response = client.get("/employees")
    assert response.status_code == 200
    assert response.json() == []


def test_list_employees_with_single_employee_should_return_employees(
    client, persisted_employee, employee_kwargs
):
    response = client.get("/employees")
    assert response.status_code == 200

    body = response.json()
    assert len(body) == 1
    employee = EmployeeRead(**body[0])
    assert employee.model_dump(mode="json") == _expected_employee_json(
        employee_kwargs, persisted_employee.id
    )
    assert "password" not in body[0]
    assert "password" not in EmployeeRead.model_fields


def test_list_employees_with_multiple_employees_should_return_employees(
    client, persisted_employees, employee_kwargs
):
    first, second = persisted_employees
    second_kwargs = employee_kwargs | {
        "first_name": "Grace",
        "last_name": "Hopper",
        "username": "ghopper",
    }
    response = client.get("/employees")
    assert response.status_code == 200

    body = response.json()
    assert len(body) == 2
    by_id = {item["id"]: EmployeeRead(**item).model_dump(mode="json") for item in body}
    assert by_id[first.id] == _expected_employee_json(employee_kwargs, first.id)
    assert by_id[second.id] == _expected_employee_json(second_kwargs, second.id)

    for item in body:
        assert "password" not in item
    assert "password" not in EmployeeRead.model_fields


def test_list_employees_with_inactive_employee_should_return_employees(
    db_session, client, persisted_employee, employee_inactive_kwargs
):
    inactive_kwargs = employee_inactive_kwargs | {"username": "inactive_user"}
    inactive = _persist_employee(db_session, inactive_kwargs)
    response = client.get("/employees")
    assert response.status_code == 200

    body = response.json()
    assert len(body) == 2
    by_id = {item["id"]: item for item in body}
    assert by_id[persisted_employee.id]["active"] is True
    assert by_id[inactive.id]["active"] is False
    assert by_id[inactive.id]["username"] == inactive.username


def test_list_employees_with_term_date_should_return_employees(
    db_session, client, employee_with_term_date_kwargs
):
    employee = _persist_employee(db_session, employee_with_term_date_kwargs)
    response = client.get("/employees")
    assert response.status_code == 200

    body = response.json()
    assert len(body) == 1
    assert body[0]["term_date"] == employee_with_term_date_kwargs["term_date"]
    assert EmployeeRead(**body[0]).model_dump(mode="json") == _expected_employee_json(
        employee_with_term_date_kwargs, employee.id
    )


def test_list_employees_with_trailing_slash_should_return_employees(
    client, persisted_employee
):
    response = client.get("/employees/")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == persisted_employee.id


def test_list_employees_should_not_modify_data(db_session, client, persisted_employee):
    before = (
        persisted_employee.id,
        persisted_employee.active,
        persisted_employee.first_name,
        persisted_employee.last_name,
        persisted_employee.username,
        persisted_employee.hourly_rate,
        persisted_employee.hire_date,
        persisted_employee.term_date,
        persisted_employee.password,
    )

    response = client.get("/employees")
    assert response.status_code == 200
    db_session.expire_all()

    after = db_session.get(Employee, before[0])
    assert after is not None
    assert (
        after.id,
        after.active,
        after.first_name,
        after.last_name,
        after.username,
        after.hourly_rate,
        after.hire_date,
        after.term_date,
        after.password,
    ) == before


def test_get_employee_should_return_employee(
    client, persisted_employees, employee_kwargs
):
    target, other = persisted_employees
    response = client.get(f"/employees/{target.id}")
    assert response.status_code == 200

    employee = EmployeeRead(**response.json())
    expected = {
        key: value for key, value in employee_kwargs.items() if key != "password"
    } | {
        "id": target.id,
        "term_date": None,
        "hourly_rate": f"{Decimal(str(employee_kwargs['hourly_rate'])):.2f}",
    }
    assert employee.model_dump(mode="json") == expected
    assert employee.id != other.id
    assert "password" not in response.json()
    assert "password" not in EmployeeRead.model_fields


def test_get_employee_with_inactive_employee_should_return_employee(
    client, persisted_inactive_employee
):
    response = client.get(f"/employees/{persisted_inactive_employee.id}")
    assert response.status_code == 200
    assert response.json()["id"] == persisted_inactive_employee.id
    assert response.json()["active"] is False


def test_get_employee_with_leading_zero_id_should_return_employee(
    client, persisted_employee
):
    response = client.get(f"/employees/0{persisted_employee.id}")
    assert response.status_code == 200
    assert response.json()["id"] == persisted_employee.id


def test_get_employee_with_trailing_slash_should_return_employee(
    client, persisted_employee
):
    response = client.get(f"/employees/{persisted_employee.id}/")
    assert response.status_code == 200
    assert response.json()["id"] == persisted_employee.id


def test_get_employee_with_padded_whitespace_id_should_return_employee(
    client, persisted_employee
):
    leading = client.get(f"/employees/%20{persisted_employee.id}")
    trailing = client.get(f"/employees/{persisted_employee.id}%20")
    assert leading.status_code == 200
    assert trailing.status_code == 200
    assert leading.json()["id"] == persisted_employee.id
    assert trailing.json()["id"] == persisted_employee.id


def test_get_employee_with_nonexistent_id_should_return_404(client, unused_employee_id):
    response = client.get(f"/employees/{unused_employee_id()}")
    assert response.status_code == 404
    assert response.json()["detail"] == "The employee was not found."


def test_get_employee_with_zero_id_should_return_422(client):
    response = client.get("/employees/0")
    assert response.status_code == 422


def test_get_employee_with_negative_id_should_return_422(client):
    response = client.get("/employees/-1")
    assert response.status_code == 422


def test_get_employee_with_non_integer_id_should_return_422(client):
    response = client.get("/employees/abc")
    assert response.status_code == 422


def test_get_employee_with_internal_whitespace_id_should_return_422(
    client, persisted_employee
):
    response = client.get(f"/employees/{persisted_employee.id}%205")
    assert response.status_code == 422


def test_get_employee_with_only_whitespace_id_should_return_422(client):
    response = client.get("/employees/%20%20")
    assert response.status_code == 422


def test_get_employee_with_float_id_should_return_422(client):
    response = client.get("/employees/1.5")
    assert response.status_code == 422


def test_get_employee_with_id_exceeding_postgres_integer_max_should_return_422(client):
    response = client.get(f"/employees/{EMPLOYEE_ID_MAX + 1}")
    assert response.status_code == 422


def test_get_employee_with_overflowing_id_should_return_422(client):
    response = client.get("/employees/99999999999999999999")
    assert response.status_code == 422


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
