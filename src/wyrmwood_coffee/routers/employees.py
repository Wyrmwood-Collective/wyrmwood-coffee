"""Employee API routes."""

import logging

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from wyrmwood_coffee.dependencies import DbSession
from wyrmwood_coffee.logging import ResourceLogger
from wyrmwood_coffee.models.employee import (
    Employee,
    EmployeeCreate,
    EmployeeId,
    EmployeeRead,
)
from wyrmwood_coffee.security import hash_password

employee_logger = ResourceLogger(logging.getLogger(__name__), Employee)
router = APIRouter(tags=["employees"])


@router.get(
    "/employees",
    status_code=status.HTTP_200_OK,
    response_model=list[EmployeeRead],
    response_description="The list of all employees",
)
def list_employees(session: DbSession) -> list[EmployeeRead]:
    """
    Retrieve a list of all employees.

    Returns each employee without the password field.
    """
    employees = session.scalars(select(Employee)).all()
    return [EmployeeRead.model_validate(employee) for employee in employees]


@router.get(
    "/employees/{id}",
    status_code=status.HTTP_200_OK,
    response_model=EmployeeRead,
    response_description="The requested employee",
    responses={
        404: {"description": "The employee was not found."},
        422: {"description": "The provided path parameter is malformed or invalid."},
    },
)
def get_employee(session: DbSession, id: EmployeeId) -> EmployeeRead:
    """
    Retrieve a single employee by ID.

    Returns the employee without the password field.
    """
    employee = session.get(Employee, id)
    if employee is None:
        employee_logger.log_resource_not_found(id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The employee was not found.",
        )
    return EmployeeRead.model_validate(employee)


@router.post(
    "/employees",
    status_code=status.HTTP_201_CREATED,
    response_model=EmployeeRead,
    response_description="The newly created employee",
    responses={
        409: {"description": "An employee with that username already exists."},
        422: {"description": "The provided EmployeeCreate is malformed or invalid."},
    },
)
def create_employee(session: DbSession, payload: EmployeeCreate) -> EmployeeRead:
    """
    Create a new employee and persist it to the database.

    Returns the created employee without the password field.
    """
    employee_data = payload.model_dump()
    employee_data["password"] = hash_password(employee_data["password"])
    new_employee = Employee(**employee_data)
    session.add(new_employee)
    try:
        session.commit()
        employee_logger.log_resource_created(new_employee.id)
    except IntegrityError:
        session.rollback()
        employee_logger.log_attrs_not_unique([Employee.username])
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An employee with that username already exists.",
        ) from None
    session.refresh(new_employee)
    return EmployeeRead.model_validate(new_employee)
