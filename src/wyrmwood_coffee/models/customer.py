from datetime import datetime
from typing import Annotated

from dateutil.relativedelta import relativedelta
from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    PositiveInt,
    StringConstraints,
    model_validator,
)
from sqlalchemy import Boolean, DateTime, Identity, Integer
from sqlalchemy.orm import Mapped, mapped_column

from wyrmwood_coffee.database import Base

CUSTOMER_ACTIVE_TITLE = "Activity Status"
CUSTOMER_ACTIVE_DESC = "The activity status of the customer"

CUSTOMER_FIRST_NAME_TITLE = "First Name"
CUSTOMER_FIRST_NAME_DESC = "The first name of the customer"

CUSTOMER_LAST_NAME_TITLE = "Last Name"
CUSTOMER_LAST_NAME_DESC = "The last name of the customer"

CUSTOMER_EMAIL_TITLE = "Email"
CUSTOMER_EMAIL_DESC = "The unique email of the customer"

CUSTOMER_PHONE_TITLE = "Phone Number"
CUSTOMER_PHONE_DESC = "The unique phone number of the customer"

CUSTOMER_LOYALTY_POINTS_TITLE = "Loyalty Points"
CUSTOMER_LOYALTY_POINTS_DESC = "The amount of loyalty points the customer has"

CUSTOMER_LOYALTY_EXPIRATION_DATE_TITLE = "Loyalty Points Expiration Date"
CUSTOMER_LOYALTY_EXPIRATION_DATE_DESC = (
    "The loyalty points expires one year after creation"
)

CUSTOMER_ID_TITLE = "Customer ID"
CUSTOMER_ID_DESC = "The generated ID of the customer"


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, Identity(always=True), primary_key=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    first_name: Mapped[str] = mapped_column(nullable=False)
    last_name: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(unique=True, index=True, nullable=True)
    phone: Mapped[str] = mapped_column(unique=True, index=True, nullable=True)
    loyalty_points: Mapped[int] = mapped_column(Integer, nullable=False)
    loyalty_expires_at: Mapped[datetime] = mapped_column(DateTime)


class CustomerBase(BaseModel):
    """Base schema of a customer in the system."""

    active: Annotated[
        bool,
        Field(
            default=True, title=CUSTOMER_ACTIVE_TITLE, description=CUSTOMER_ACTIVE_DESC
        ),
    ]
    first_name: Annotated[
        str, StringConstraints(min_length=1, strip_whitespace=True)
    ] = Field(title=CUSTOMER_FIRST_NAME_TITLE, description=CUSTOMER_FIRST_NAME_DESC)
    last_name: Annotated[
        str, StringConstraints(min_length=1, strip_whitespace=True)
    ] = Field(title=CUSTOMER_LAST_NAME_TITLE, description=CUSTOMER_LAST_NAME_DESC)
    email: EmailStr | None = Field(
        default=None, title=CUSTOMER_EMAIL_TITLE, description=CUSTOMER_EMAIL_DESC
    )
    phone: str | None = Field(
        default=None,
        min_length=10,
        title=CUSTOMER_PHONE_TITLE,
        description=CUSTOMER_PHONE_DESC,
        pattern=r"^\d{3}-\d{3}-\d{4}$",
    )
    loyalty_points: Annotated[
        int,
        Field(
            default=0,
            ge=0,
            title=CUSTOMER_LOYALTY_POINTS_TITLE,
            description=CUSTOMER_LOYALTY_POINTS_DESC,
        ),
    ]

    @model_validator(mode="after")
    def required_email_or_phone(self):
        if not self.email and not self.phone:
            raise ValueError("Email or phone must be provided.")
        return self


class CustomerCreate(CustomerBase):
    """
    Payload for creating a new customer.

    At least email or phone must be provided.
    """

    model_config = ConfigDict(from_attributes=True)

    loyalty_expires_at: datetime = Field(
        default_factory=lambda: datetime.now() + relativedelta(years=1),
        title=CUSTOMER_LOYALTY_EXPIRATION_DATE_TITLE,
        description=CUSTOMER_LOYALTY_EXPIRATION_DATE_DESC,
    )


class CustomerRead(CustomerBase):
    """Customer schema returned from the system."""

    model_config = ConfigDict(from_attributes=True)

    id: PositiveInt = Field(title=CUSTOMER_ID_TITLE, description=CUSTOMER_ID_DESC)
    loyalty_expires_at: datetime = Field(
        title=CUSTOMER_LOYALTY_EXPIRATION_DATE_TITLE,
        description=CUSTOMER_LOYALTY_EXPIRATION_DATE_DESC,
    )
