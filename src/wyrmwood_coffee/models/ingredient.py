from typing import TYPE_CHECKING, Annotated

from pydantic import BaseModel, Field, StringConstraints, field_validator
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from wyrmwood_coffee.database import Base

if TYPE_CHECKING:
    from wyrmwood_coffee.models.vendor import Vendor


class Ingredient(Base):
    __tablename__ = "ingredients"

    # SATISFIES AC: name combined with vendor are unique
    __table_args__ = (
        UniqueConstraint("name", "vendor_id", name="uq_ingredient_name_vendor"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    active: Mapped[bool] = mapped_column(default=True)

    name: Mapped[str] = mapped_column()
    purchasing_cost: Mapped[float] = mapped_column()
    unit_amount: Mapped[float] = mapped_column()
    unit_of_measure: Mapped[str] = mapped_column()
    allergens: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)

    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"))

    # A simple, one-way relationship that won't crash the Vendor model mapping
    vendor: Mapped["Vendor"] = relationship()


# SATISFIES AC: Exact list of valid units of measure
VALID_UNITS = {
    "g",
    "kg",
    "oz",
    "lb",
    "fl oz",
    "mL",
    "L",
    "gal",
    "pumps",
    "scoops",
    "shots",
    "dashes",
}


class IngredientBase(BaseModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)] = (
        Field(title="Name", description="The name of the ingredient")
    )
    purchasing_cost: Annotated[float, Field(gt=0)] = Field(
        title="Purchasing Cost", description="The cost to purchase the ingredient"
    )
    unit_amount: Annotated[float, Field(gt=0)] = Field(
        title="Unit Amount", description="The amount per unit of measure"
    )
    unit_of_measure: str = Field(
        title="Unit of Measure", description="The unit used to measure this ingredient"
    )
    vendor_id: int = Field(
        title="Vendor ID", description="The ID of the vendor supplying this ingredient"
    )

    active: bool = Field(
        default=True,
        title="Active",
        description="Whether or not the ingredient is active",
    )
    allergens: Annotated[list[str], Field(min_length=0)] = Field(
        default_factory=list,
        title="Allergens",
        description="A list of allergens present in the ingredient",
    )

    @field_validator("unit_of_measure")
    def validate_unit(cls, value):
        if value not in VALID_UNITS:
            raise ValueError(
                f"unit_of_measure must be one of: {', '.join(VALID_UNITS)}"
            )
        return value


class IngredientCreate(IngredientBase):
    """Represents an ingredient before it has been saved to the database."""

    pass


class IngredientRead(IngredientBase):
    """The ingredient representation returned to an API client."""

    id: int = Field(
        title="Ingredient ID", description="The unique identifier for this ingredient"
    )
    model_config = {"from_attributes": True}
