from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator
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
    promo_code: str = Field(pattern=r"^[ _]*[A-Z][A-Z _]*$")
    discount_percentage: Decimal = Field(
        ge=0,
        le=100,
    )
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def validate_dates(self):
        """Ensure the end date is not before the start date."""
        if self.end_date < self.start_date:
            raise ValueError("End date must be after start date.")

        return self


class PromotionRead(PromotionCreate):
    """Response model returned when viewing a promotion."""

    id: int

    # Allows Pydantic to build the response from a SQLAlchemy Promotion object.
    model_config = ConfigDict(from_attributes=True)
