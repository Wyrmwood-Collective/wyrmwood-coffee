"""Shared FastAPI dependencies."""

import logging
from collections.abc import Callable, Sequence
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from wyrmwood_coffee.database import get_db
from wyrmwood_coffee.models.employee import Employee, EmployeeRole
from wyrmwood_coffee.models.token import BlacklistedToken
from wyrmwood_coffee.security import decode_access_token

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

DbSession = Annotated[Session, Depends(get_db)]

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials.",
    headers={"WWW-Authenticate": "Bearer"},
)

MANAGER_ROLES: tuple[EmployeeRole, ...] = (
    EmployeeRole.MANAGER,
    EmployeeRole.ADMIN,
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


def require_auth(
    employee: Annotated[Employee, Depends(get_current_employee)],
) -> Employee:
    """Require any authenticated employee."""
    return employee


def check_role(
    allowed_roles: Sequence[EmployeeRole | str],
) -> Callable[[Employee], Employee]:
    """Return a dependency that requires the caller's role to be allowed."""
    allowed = frozenset(EmployeeRole(role) for role in allowed_roles)

    def _check_role(
        employee: Annotated[Employee, Depends(get_current_employee)],
    ) -> Employee:
        employee_role = EmployeeRole(employee.role)
        if employee_role not in allowed:
            logger.info(
                "Unauthorized role attempt",
                extra={
                    "employee_id": employee.id,
                    "employee_role": employee_role.value,
                    "required_roles": sorted(role.value for role in allowed),
                },
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )
        return employee

    return _check_role


require_manager = check_role(MANAGER_ROLES)
