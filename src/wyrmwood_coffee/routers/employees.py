"""Employee API routes."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from wyrmwood_coffee.dependencies import DbSession, require_manager
from wyrmwood_coffee.logging import ResourceLogger
from wyrmwood_coffee.models.employee import (
    Employee,
    EmployeeCreate,
    EmployeeId,
    EmployeeRead,
    EmployeeUpdate,
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
    if employee is None or employee.is_deleted:
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
        401: {"description": "Could not validate credentials."},
        403: {"description": "Insufficient permissions."},
        409: {"description": "An employee with that username already exists."},
        422: {"description": "The provided EmployeeCreate is malformed or invalid."},
    },
    dependencies=[Depends(require_manager)],
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


@router.put(
    "/employees/{id}",
    status_code=status.HTTP_200_OK,
    response_model=EmployeeRead,
    response_description="The updated employee",
    responses={
        401: {"description": "Could not validate credentials."},
        403: {"description": "Insufficient permissions."},
        404: {"description": "The employee was not found."},
        409: {"description": "An employee with that username already exists."},
        422: {
            "description": (
                "The provided EmployeeUpdate is malformed or invalid, "
                "or the provided path parameter is malformed or invalid."
            )
        },
    },
    dependencies=[Depends(require_manager)],
)
def update_employee(
    session: DbSession,
    id: EmployeeId,
    payload: EmployeeUpdate,
) -> EmployeeRead:
    """
    Update an existing employee.

    Returns the updated employee without the password field.
    The employee's password cannot be updated via this endpoint. If a
    password is provided in the request body, it will be silently ignored.
    """
    # 1. Look up the employee
    employee = session.get(Employee, id)
    if employee is None or employee.is_deleted is True:
        employee_logger.log_resource_not_found(id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The employee was not found.",
        )

    # 2. Apply the updated fields
    update_data = payload.model_dump(exclude={"password"}, exclude_unset=True)

    for key, value in update_data.items():
        setattr(employee, key, value)

    # 3. Save to database with uniqueness safety net
    try:
        session.commit()
        employee_logger.log_resource_updated(employee.id)
    except IntegrityError:
        session.rollback()
        employee_logger.log_attrs_not_unique([Employee.username])
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An employee with that username already exists.",
        ) from None

    session.refresh(employee)

    # 4. Return the updated model
    return EmployeeRead.model_validate(employee)


@router.delete(
    "/employees/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_description="The employee was deleted successfully.",
    responses={
        401: {"description": "Could not validate credentials."},
        403: {"description": "Insufficient permissions."},
        404: {"description": "The employee was not found."},
        422: {"description": "The provided path parameter is malformed or invalid."},
    },
    dependencies=[Depends(require_manager)],
)
def delete_employee(session: DbSession, id: EmployeeId) -> None:
    """
    Soft delete an employee.

    The employee remains in the database for historical records
    but is no longer active or able to log in. As part of
    the successful request, the employee's username is mutated
    (e.g., {username}_deleted_{id}) to free it up for future use.
    """
    employee = session.get(Employee, id)

    # Check if they don't exist OR are already soft-deleted
    if employee is None or employee.is_deleted is True:
        employee_logger.log_resource_not_found(id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The employee was not found.",
        )

    # Deactivate, soft-delete, and release the unique username
    employee.active = False  # type: ignore
    employee.is_deleted = True  # type: ignore
    employee.username = f"{employee.username}_deleted_{employee.id}"  # type: ignore

    session.commit()
    employee_logger.log_resource_deleted(id)
