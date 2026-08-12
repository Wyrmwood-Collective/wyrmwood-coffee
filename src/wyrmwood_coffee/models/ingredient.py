from pydantic import BaseModel, Field, confloat, conlist, constr, field_validator
from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship

from wyrmwood_coffee.database import Base  # ← DO NOT CHANGE

VALID_UNITS = {"ml", "g", "kg", "oz", "lb", "l"}


class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True, index=True)
    active = Column(Boolean, default=True)

    name = Column(String, nullable=False)
    purchasing_cost = Column(Float, nullable=False)
    unit_amount = Column(Float, nullable=False)
    unit_of_measure = Column(String, nullable=False)
    allergens = Column(ARRAY(String), default=list)

    # NEW: vendor relationship (matches VendorContact)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    vendor = relationship("Vendor")


# ---------------------------------------------------------
# PYDANTIC SCHEMAS (Pydantic v2)
# ---------------------------------------------------------

VALID_UNITS = {"ml", "g", "kg", "oz", "lb", "l"}


class IngredientBase(BaseModel):
    active: bool = True

    name: constr(strip_whitespace=True, min_length=1) | None = None
    purchasing_cost: confloat(gt=0) | None = None
    unit_amount: confloat(gt=0) | None = None
    unit_of_measure: str | None = None
    vendor_id: int | None = None

    allergens: conlist(str, min_length=0) = Field(default_factory=list)

    @field_validator("unit_of_measure")
    def validate_unit(cls, value):
        if value not in VALID_UNITS:
            raise ValueError(
                f"unit_of_measure must be one of: {', '.join(VALID_UNITS)}"
            )
        return value


class IngredientCreate(IngredientBase):
    name: constr(strip_whitespace=True, min_length=1)
    purchasing_cost: confloat(gt=0)
    unit_amount: confloat(gt=0)
    unit_of_measure: str
    vendor_id: int


class IngredientUpdate(IngredientBase):
    pass


class IngredientRead(IngredientBase):
    id: int
    model_config = {"from_attributes": True}
