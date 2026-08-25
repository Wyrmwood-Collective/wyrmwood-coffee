"""Authentication API routes."""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from wyrmwood_coffee.dependencies import DbSession
from wyrmwood_coffee.models.employee import Employee
from wyrmwood_coffee.models.token import Token
from wyrmwood_coffee.security import create_access_token, verify_password

logger = logging.getLogger(__name__)
router = APIRouter(tags=["auth"])


@router.post(
    "/auth/login",
    status_code=status.HTTP_200_OK,
    response_model=Token,
    response_description="The generated JWT access token",
    responses={
        401: {
            "description": "Incorrect username or password.",
        },
        422: {
            "description": "The provided Login is malformed or invalid.",
        },
    },
)
def login(
    session: DbSession,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    """
    Authenticate an employee and return a JWT access token.

    Accepts standard OAuth2 form data (username, password).
    """
    employee = session.scalars(
        select(Employee).where(Employee.username == form_data.username)
    ).first()

    if (
        employee is None
        or not employee.active
        or not verify_password(form_data.password, employee.password)
    ):
        extra: dict[str, Any] = {"employee_username": form_data.username}
        if employee is None:
            extra["login_failure_reason"] = "employee_not_found"
        elif not employee.active:
            extra["employee_id"] = employee.id
            extra["login_failure_reason"] = "employee_inactive"
        else:
            extra["employee_id"] = employee.id
            extra["login_failure_reason"] = "invalid_password"

        logger.info("Login failure", extra=extra)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={
            "sub": str(employee.id),
            "role": employee.role,
        }
    )

    logger.info(
        "Login successful",
        extra={"employee_id": employee.id, "employee_username": employee.username},
    )
    return Token(access_token=access_token, token_type="bearer")
