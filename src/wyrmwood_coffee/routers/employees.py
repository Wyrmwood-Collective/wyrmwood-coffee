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
)
def create_employee(
    employee: EmployeeCreate,
    db: Annotated[Session, Depends(get_db)],
) -> Employee:
    """Create a new employee and persist it to the database.

    Args:
        employee: The employee payload to create.
        db: Database session dependency.

    Returns:
        The created employee without the password field.

    Raises:
        HTTPException: If the username is already taken.
    """
    employee_data = employee.model_dump()
    employee_data["password"] = hash_password(employee_data["password"])
    new_employee = Employee(**employee_data)
    db.add(new_employee)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        ) from None
    db.refresh(new_employee)
    return new_employee
