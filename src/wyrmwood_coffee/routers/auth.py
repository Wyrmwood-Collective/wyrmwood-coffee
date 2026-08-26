"""Authentication API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from wyrmwood_coffee.dependencies import DbSession
from wyrmwood_coffee.models.employee import Employee
from wyrmwood_coffee.models.token import Token
from wyrmwood_coffee.security import create_access_token, verify_password

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
    return Token(access_token=access_token, token_type="bearer")
