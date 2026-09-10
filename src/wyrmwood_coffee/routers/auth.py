"""Authentication API routes."""

import logging
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from wyrmwood_coffee.dependencies import DbSession, get_token_payload
from wyrmwood_coffee.models.employee import Employee
from wyrmwood_coffee.models.token import BlacklistedToken, Token
from wyrmwood_coffee.security import create_access_token, verify_password

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/login",
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


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={401: {"description": "Missing, invalid, or already-expired token."}},
)
def logout(
    session: DbSession, payload: Annotated[dict, Depends(get_token_payload)]
) -> None:
    """
    Terminate the caller's current session.

    Adds the token's jti to the blacklist so it can no longer be used,
    even thought it hasn't reached its natural expiry yet.
    """
    jti = payload.get("jti")
    if jti is None:
        logger.info(
            "Logout on token without jti", extra={"employee_id": payload.get("sub")}
        )
        return

    expires_at = datetime.fromtimestamp(payload["exp"], tz=UTC)

    session.merge(
        BlacklistedToken(
            jti=jti, expires_at=expires_at, blacklisted_at=datetime.now(UTC)
        )
    )
    session.commit()

    logger.info("Logout successful", extra={"employee_id": payload.get("sub")})
