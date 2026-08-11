from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import Boolean, Date, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from wyrmwood_coffee.database import Base


class Promotion(Base):
    __tablename__ = "promotions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    promo_code: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False,
    )

    discount_percentage: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)


class PromotionCreate(BaseModel):
    active: bool
    promo_code: str
    discount_percentage: float = Field(ge=0, le=100)
    start_date: date
    end_date: date


@field_validator("promo_code")
@classmethod
def validate_promo_code(cls, value: str) -> str:
    normalized_character = value.replace(" ", "").replace("_", "")

    if not normalized_character:
        raise ValueError("Promo code must contain at least one letter.")

    if not normalized_character.isalpha():
        raise ValueError(
            "Promo code may contain only letters, spaces, and underscores."
        )

    if value != value.upper():
        raise ValueError("Promo code must be in uppercase.")

    return value


@model_validator(mode="after")
def validate_dates(self):
    if self.end_date < self.start_date:
        raise ValueError("End date must be after start date.")

    return self


class PromotionRead(PromotionCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)
