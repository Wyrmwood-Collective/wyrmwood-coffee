"""Employee API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from wyrmwood_coffee.database import get_db
from wyrmwood_coffee.models.employee import Employee, EmployeeCreate, EmployeeRead
from wyrmwood_coffee.security import hash_password

router = APIRouter(tags=["employees"])


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
def create_employee(
    session: Annotated[Session, Depends(get_db)],
    payload: EmployeeCreate,
) -> EmployeeRead:
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
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An employee with that username already exists.",
        ) from None
    session.refresh(new_employee)
    return EmployeeRead.model_validate(new_employee)
