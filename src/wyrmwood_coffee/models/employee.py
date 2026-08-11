import re
from datetime import date
from enum import StrEnum
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PositiveInt,
    StringConstraints,
    field_validator,
)
from sqlalchemy import Boolean, Date, Float, Identity, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from wyrmwood_coffee.database import Base

EMPLOYEE_ACTIVE_TITLE = "Active"
EMPLOYEE_ACTIVE_DESC = "Whether the employee is currently active"

EMPLOYEE_FIRST_NAME_TITLE = "First Name"
EMPLOYEE_FIRST_NAME_DESC = "The employee's first name"

EMPLOYEE_LAST_NAME_TITLE = "Last Name"
EMPLOYEE_LAST_NAME_DESC = "The employee's last name"

EMPLOYEE_ROLE_TITLE = "Role"
EMPLOYEE_ROLE_DESC = "The employee's role in the company"

EMPLOYEE_HOURLY_RATE_TITLE = "Hourly Rate"
EMPLOYEE_HOURLY_RATE_DESC = "The employee's hourly rate in dollars"

EMPLOYEE_HIRE_DATE_TITLE = "Hire Date"
EMPLOYEE_HIRE_DATE_DESC = "The date the employee was hired"

EMPLOYEE_TERM_DATE_TITLE = "Termination Date"
EMPLOYEE_TERM_DATE_DESC = "The date the employee was terminated, if applicable"

EMPLOYEE_USERNAME_TITLE = "Username"
EMPLOYEE_USERNAME_DESC = "The employee's username for system access"

EMPLOYEE_PASSWORD_TITLE = "Password"
EMPLOYEE_PASSWORD_DESC = (
    "The employee's password for system access. "
    "Must be at least 8 characters and include a capital letter, "
    "a number, and a special character."
)

EMPLOYEE_ID_TITLE = "Employee ID"
EMPLOYEE_ID_DESC = "The unique identifier of the employee"

PASSWORD_SPECIAL_CHARS = r"!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?`~"


class EmployeeRole(StrEnum):
    """Allowed employee roles."""

    EMPLOYEE = "employee"
    MANAGER = "manager"
    ADMIN = "admin"


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(Integer, Identity(always=True), primary_key=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)
    hourly_rate: Mapped[float] = mapped_column(Float, nullable=False)
    hire_date: Mapped[date] = mapped_column(Date, nullable=False)
    term_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)


class EmployeeBase(BaseModel):
    """Shared employee fields."""

    active: Annotated[
        bool, Field(title=EMPLOYEE_ACTIVE_TITLE, description=EMPLOYEE_ACTIVE_DESC)
    ]
    first_name: Annotated[
        str, StringConstraints(min_length=1, strip_whitespace=True)
    ] = Field(title=EMPLOYEE_FIRST_NAME_TITLE, description=EMPLOYEE_FIRST_NAME_DESC)
    last_name: Annotated[
        str, StringConstraints(min_length=1, strip_whitespace=True)
    ] = Field(title=EMPLOYEE_LAST_NAME_TITLE, description=EMPLOYEE_LAST_NAME_DESC)
    role: Annotated[
        EmployeeRole, Field(title=EMPLOYEE_ROLE_TITLE, description=EMPLOYEE_ROLE_DESC)
    ]
    hourly_rate: Annotated[
        float,
        Field(
            gt=0,
            title=EMPLOYEE_HOURLY_RATE_TITLE,
            description=EMPLOYEE_HOURLY_RATE_DESC,
        ),
    ]
    hire_date: Annotated[
        date, Field(title=EMPLOYEE_HIRE_DATE_TITLE, description=EMPLOYEE_HIRE_DATE_DESC)
    ]
    term_date: Annotated[
        date | None,
        Field(title=EMPLOYEE_TERM_DATE_TITLE, description=EMPLOYEE_TERM_DATE_DESC),
    ] = None
    username: Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)] = (
        Field(title=EMPLOYEE_USERNAME_TITLE, description=EMPLOYEE_USERNAME_DESC)
    )


class EmployeeCreate(EmployeeBase):
    """Payload for creating a new employee."""

    password: Annotated[str, StringConstraints(min_length=8)] = Field(
        title=EMPLOYEE_PASSWORD_TITLE, description=EMPLOYEE_PASSWORD_DESC
    )

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, value: str) -> str:
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain at least one capital letter")
        if not re.search(r"[0-9]", value):
            raise ValueError("Password must contain at least one number")
        if not re.search(rf"[{PASSWORD_SPECIAL_CHARS}]", value):
            raise ValueError("Password must contain at least one special character")
        return value


class EmployeeRead(EmployeeBase):
    """Employee schema returned from the system."""

    model_config = ConfigDict(from_attributes=True)

    id: PositiveInt = Field(title=EMPLOYEE_ID_TITLE, description=EMPLOYEE_ID_DESC)
