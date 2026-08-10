from pydantic import BaseModel, Field
from sqlalchemy import JSON, Boolean, Column, Float, Integer, String
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

    # JSON works in PostgreSQL AND SQLite
    allergens = Column(JSON, default=list)


# ---------------------------------------------------------
# PYDANTIC SCHEMAS (Pydantic v2 compliant)
# ---------------------------------------------------------


class IngredientBase(BaseModel):
    active: bool | None = True
    name: str | None = None
    vendor: str | None = None
    purchasing_cost: float | None = None
    unit_amount: float | None = None
    unit_of_measure: str | None = None

    # FIX: mutable default must use Field(default_factory=list)
    allergens: list[str] = Field(default_factory=list)


class IngredientCreate(IngredientBase):
    # Required fields for creation
    name: str
    vendor: str
    purchasing_cost: float
    unit_amount: float
    unit_of_measure: str


class IngredientUpdate(IngredientBase):
    # All fields optional for partial updates
    pass


class IngredientRead(IngredientBase):
    id: int

    # Pydantic v2: from_attributes replaces orm_mode
    model_config = {"from_attributes": True}
