from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import Boolean, Date, Numeric, String
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

    discount_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)


class PromotionCreate(BaseModel):
    active: bool
    promo_code: str
    discount_percentage: Decimal = Field(ge=0, le=100)
    start_date: date
    end_date: date

    @field_validator("promo_code")
    @classmethod
    def valid_promo_code(cls, value: str) -> str:
        normalized_character = value.replace("  ", "").replace("_", "")

        if not normalized_character:
            raise ValueError
        ("Promo code must contain atleast one alphanumeric character.")

        if not normalized_character.isalpha():
            raise ValueError
        ("Promo code may contain only letter, spaces, and underscores")

        if value != value.upper():
            raise ValueError
        ("Promo code must be in uppercase.")

        return value

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def parse_dates(cls, value):
        if isinstance(value, date):
            return value

        formats = (
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%m-%d-%Y",
            "%m/%d/%Y",
            "%Y/%d/%m",
            "%Y-%d-%m",
        )

        for date_format in formats:
            try:
                return datetime.strptime(value, date_format).date()
            except ValueError:
                continue

        raise ValueError

    (
        "Date must use YYYY-MM-DD,"
        "YYYY/MM/DD,"
        "MM-DD-YYYY,"
        "MM/DD/YYYY,"
        "YYYY/DD/MM,"
        "or YYYY-DD-MM."
    )

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date < self.start_date:
            raise ValueError("End date must be after start date.")

        return self


class PromotionRead(PromotionCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)
