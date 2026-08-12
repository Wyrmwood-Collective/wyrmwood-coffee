from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from sqlalchemy import Boolean, Date, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from wyrmwood_coffee.database import Base


class Promotion(Base):
    """SQLAlchemy model representing a promotion stored in the database."""

    __tablename__ = "promotions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    promo_code: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False,
    )
    discount_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)


class PromotionCreate(BaseModel):
    """Request model used when creating a new promotion."""

    active: bool
    promo_code: str
    discount_percentage: Decimal
    start_date: date
    end_date: date

    @field_validator("discount_percentage", mode="before")
    @classmethod
    def valid_discount_percentage(cls, value):
        """Validate that the discount is numeric and between 0 and 100."""

        # Reject values containing letters or other non-numeric characters.
        if not str(value).replace(".", "", 1).isdigit():
            raise ValueError("Discount percentage must be between 0 and 100.")

        # Convert the incoming value to Decimal for precise storage/calculation.
        value = Decimal(str(value))

        # Reject discounts outside the approved range.
        if value < 0 or value > 100:
            raise ValueError("Discount percentage must be between 0 and 100.")

        return value

    @field_validator("promo_code")
    @classmethod
    def valid_promo_code(cls, value: str) -> str:
        """
        Validate the promo code format.

        Promo codes may contain uppercase letters, spaces, and underscores.
        """

        # Temporarily remove allowed separators so only letters remain.
        normalized_character = value.replace(" ", "").replace("_", "")

        # Prevent empty codes or codes containing only spaces/underscores.
        if not normalized_character:
            raise ValueError("Promo code must contain at least one letter.")

        # Reject numbers and unsupported special characters.
        if not normalized_character.isalpha():
            raise ValueError(
                "Promo code may contain only letters, spaces, and underscores."
            )

        # Promo codes must be entered using uppercase letters.
        if value != value.upper():
            raise ValueError("Promo code must be in uppercase.")

        return value

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def parse_dates(cls, value):
        """Convert an accepted date format into a Python date object."""

        # If Pydantic already converted the value, no further parsing is needed.
        if isinstance(value, date):
            return value

        # Accepted input formats for promotion start and end dates.
        formats = (
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%m-%d-%Y",
            "%m/%d/%Y",
            "%Y/%d/%m",
            "%Y-%d-%m",
        )

        # Try each supported format until one successfully parses.
        for date_format in formats:
            try:
                return datetime.strptime(value, date_format).date()
            except ValueError:
                continue

        raise ValueError(
            "Date must use YYYY-MM-DD, YYYY/MM/DD, MM-DD-YYYY, "
            "MM/DD/YYYY, YYYY/DD/MM, or YYYY-DD-MM."
        )

    @model_validator(mode="after")
    def validate_dates(self):
        """Validate that the promotion end date is not before its start date."""

        if self.end_date < self.start_date:
            raise ValueError("End date must be after start date.")

        return self


class PromotionRead(PromotionCreate):
    """Response model returned when viewing a promotion."""

    id: int

    # Allows Pydantic to build the response from a SQLAlchemy Promotion object.
    model_config = ConfigDict(from_attributes=True)
