from pydantic import BaseModel, Field, confloat, conlist, constr
from sqlalchemy import Boolean, Column, Float, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import declarative_base

Base = declarative_base()


# ---------------------------------------------------------
# SQLALCHEMY MODEL
# ---------------------------------------------------------
class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True, index=True)
    active = Column(Boolean, default=True)
    name = Column(String, nullable=False)
    vendor = Column(String, nullable=False)
    purchasing_cost = Column(Float, nullable=False)
    unit_amount = Column(Float, nullable=False)
    unit_of_measure = Column(String, nullable=False)
    allergens = Column(ARRAY(String), default=list)


# ---------------------------------------------------------
# PYDANTIC SCHEMAS (Pydantic v2)
# ---------------------------------------------------------

VALID_UNITS = {"ml", "g", "kg", "oz", "lb", "l"}


class IngredientBase(BaseModel):
    active: bool = True

    # Required string fields with whitespace stripping
    name: constr(strip_whitespace=True, min_length=1) | None = None
    vendor: constr(strip_whitespace=True, min_length=1) | None = None

    # Numeric validation
    purchasing_cost: confloat(gt=0) | None = None
    unit_amount: confloat(gt=0) | None = None

    # Unit validation
    unit_of_measure: str | None = None

    # List validation
    allergens: conlist(str, min_length=0) = Field(default_factory=list)

    @classmethod
    def validate_unit(cls, value):
        if value not in VALID_UNITS:
            raise ValueError(
                f"unit_of_measure must be one of: {', '.join(VALID_UNITS)}"
            )
        return value


class IngredientCreate(IngredientBase):
    name: constr(strip_whitespace=True, min_length=1)
    vendor: constr(strip_whitespace=True, min_length=1)
    purchasing_cost: confloat(gt=0)
    unit_amount: confloat(gt=0)
    unit_of_measure: str

    # Custom validation hook
    @classmethod
    def model_validate(cls, data):
        model = super().model_validate(data)
        model.unit_of_measure = cls.validate_unit(model.unit_of_measure)
        return model


class IngredientUpdate(IngredientBase):
    pass


class IngredientRead(IngredientBase):
    id: int
    model_config = {"from_attributes": True}
