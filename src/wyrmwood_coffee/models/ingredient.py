from typing import TYPE_CHECKING, Annotated

from pydantic import BaseModel, Field, StringConstraints, field_validator
from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from wyrmwood_coffee.database import Base  # ← DO NOT CHANGE

# NEW: Import Vendor only during type checking to prevent circular imports
if TYPE_CHECKING:
    from .vendor import (
        Vendor,  # Adjust this import path if vendor.py is in a different folder
    )


class Ingredient(Base):
    __tablename__ = "ingredients"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    active: Mapped[bool] = mapped_column(default=True)

    name: Mapped[str] = mapped_column()
    purchasing_cost: Mapped[float] = mapped_column()
    unit_amount: Mapped[float] = mapped_column()
    unit_of_measure: Mapped[str] = mapped_column()
    allergens: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)

    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"))
    vendor: Mapped["Vendor"] = relationship(back_populates="ingredients")


# ---------------------------------------------------------
# PYDANTIC SCHEMAS (Pydantic v2)
# ---------------------------------------------------------

VALID_UNITS = {"ml", "g", "kg", "oz", "lb", "l"}


class IngredientBase(BaseModel):
    # 1. REQUIRED fields go first (no defaults)
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    purchasing_cost: Annotated[float, Field(gt=0)]
    unit_amount: Annotated[float, Field(gt=0)]
    unit_of_measure: str
    vendor_id: int

    # 2. OPTIONAL fields go last (has defaults)
    active: bool = True
    allergens: Annotated[list[str], Field(min_length=0)] = Field(default_factory=list)

    @field_validator("unit_of_measure")
    def validate_unit(cls, value):
        if value not in VALID_UNITS:
            raise ValueError(
                f"unit_of_measure must be one of: {', '.join(VALID_UNITS)}"
            )
        return value


class IngredientCreate(IngredientBase):
    # Inherits all the required fields from Base perfectly. No overrides needed!
    pass


class IngredientRead(IngredientBase):
    id: int
    model_config = {"from_attributes": True}


class IngredientUpdate(BaseModel):
    # For updates, it's best practice to not inherit from the strict base
    # to avoid Pylance variance errors. We make everything optional here.
    active: bool | None = None
    name: (
        Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)] | None
    ) = None
    purchasing_cost: Annotated[float, Field(gt=0)] | None = None
    unit_amount: Annotated[float, Field(gt=0)] | None = None
    unit_of_measure: str | None = None
    vendor_id: int | None = None
    allergens: Annotated[list[str], Field(min_length=0)] | None = None

    @field_validator("unit_of_measure")
    def validate_unit(cls, value):
        # We must allow None to pass through for updates
        if value is not None and value not in VALID_UNITS:
            raise ValueError(
                f"unit_of_measure must be one of: {', '.join(VALID_UNITS)}"
            )
        return value
