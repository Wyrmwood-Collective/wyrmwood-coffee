from datetime import date
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import Boolean, Date, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from wyrmwood_coffee.database import Base

PromotionId = Annotated[int, Field(gt=0)]


class Promotion(Base):
    """SQLAlchemy model representing a promotion stored in the database."""

    __tablename__ = "promotions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
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
    promo_code: str = Field(pattern=r"^[A-Z _]+$")
    discount_percentage: Decimal = Field(
        ge=0,
        le=100,
    )
    start_date: date
    end_date: date

    @field_validator("promo_code")
    @classmethod
    def validate_promo_code(cls, value: str) -> str:
        """Require the promo code to contain at least one letter."""
        if not any(character.isalpha() for character in value):
            raise ValueError("Promo code must contain at least one letter.")

        return value

    @model_validator(mode="after")
    def validate_dates(self):
        """Ensure the end date is not before the start date."""
        if self.end_date < self.start_date:
            raise ValueError("End date must be after start date.")

        return self


class PromotionRead(PromotionCreate):
    """Response model returned when viewing a promotion."""

    id: PromotionId

    model_config = ConfigDict(from_attributes=True)
