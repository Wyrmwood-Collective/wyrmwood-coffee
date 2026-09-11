from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from wyrmwood_coffee.database import get_db
from wyrmwood_coffee.models.employee import Employee
from wyrmwood_coffee.models.token import BlacklistedToken
from wyrmwood_coffee.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

DbSession = Annotated[Session, Depends(get_db)]

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials.",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_token_payload(
    session: DbSession, token: Annotated[str, Depends(oauth2_scheme)]
) -> dict:
    """Decode the JWT, verify signature/expiry, and reject blacklisted tokens."""

    try:
        payload = decode_access_token(token)
    except jwt.PyJWTError:
        raise credentials_exception from None

    jti = payload.get("jti")
    if jti is not None:
        is_blacklisted = session.scalar(
            select(BlacklistedToken.jti).where(BlacklistedToken.jti == jti)
        )
        if is_blacklisted is not None:
            raise credentials_exception

    return payload


def get_current_employee(
    session: DbSession, payload: Annotated[dict, Depends(get_token_payload)]
) -> Employee:
    """Resolve the authenticated employee from the token payload"""
    employee_id = payload.get("sub")
    if employee_id is None:
        raise credentials_exception

    employee = session.get(Employee, int(employee_id))
    if employee is None or not employee.active:
        raise credentials_exception

    return employee
