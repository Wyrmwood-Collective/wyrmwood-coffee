"""Shared FastAPI dependencies."""

import logging
from collections.abc import Callable, Sequence
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from wyrmwood_coffee.database import get_db
from wyrmwood_coffee.models.employee import EmployeeRole
from wyrmwood_coffee.security import decode_access_token

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

DbSession = Annotated[Session, Depends(get_db)]

MANAGER_ROLES: tuple[EmployeeRole, ...] = (
    EmployeeRole.MANAGER,
    EmployeeRole.ADMIN,
)


class CurrentUser(BaseModel):
    """Authenticated employee identity from a JWT."""

    id: int = Field(gt=0)
    role: EmployeeRole


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> CurrentUser:
    """Decode the Bearer JWT and return the caller's id and role."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        sub = payload.get("sub")
        role = payload.get("role")
        if sub is None or role is None:
            raise credentials_exception
        return CurrentUser(id=int(sub), role=EmployeeRole(role))
    except (jwt.PyJWTError, ValueError, TypeError, KeyError) as err:
        raise credentials_exception from err


def require_auth(
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> CurrentUser:
    """Require any authenticated employee."""
    return user


def check_role(
    allowed_roles: Sequence[EmployeeRole | str],
) -> Callable[[CurrentUser], CurrentUser]:
    """Return a dependency that requires the caller's role to be allowed."""
    allowed = frozenset(EmployeeRole(role) for role in allowed_roles)

    def _check_role(
        user: Annotated[CurrentUser, Depends(get_current_user)],
    ) -> CurrentUser:
        if user.role not in allowed:
            logger.info(
                "Unauthorized role attempt",
                extra={
                    "employee_id": user.id,
                    "employee_role": user.role.value,
                    "required_roles": sorted(role.value for role in allowed),
                },
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )
        return user

    return _check_role


require_manager = check_role(MANAGER_ROLES)
