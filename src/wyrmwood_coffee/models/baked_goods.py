from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, PositiveInt, StringConstraints
from sqlalchemy import ARRAY, CheckConstraint, Numeric, String, true
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from wyrmwood_coffee.database import Base


class BakedGood(Base):
    """Represents a baked good as it exists in the database."""

    __tablename__ = "baked_goods"

    id: Mapped[int] = mapped_column(primary_key=True)
    active: Mapped[bool] = mapped_column(server_default=true(), nullable=False)
    name: Mapped[str] = mapped_column(
        String, CheckConstraint("length(name) >= 1"), nullable=False
    )
    description: Mapped[str] = mapped_column(
        String, CheckConstraint("length(description) >= 1"), nullable=False
    )
    purchase_cost: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2),
        CheckConstraint("purchase_cost >= 0.0"),
        nullable=False,
    )
    retail_price: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2),
        CheckConstraint("retail_price >= 0.0"),
        nullable=False,
    )
    allergens: Mapped[list[str]] = mapped_column(
        ARRAY(String), server_default="{}", nullable=False
    )


class BakedGoodBase(BaseModel):
    """Holds the attributes common to all BakedGood models."""

    model_config = ConfigDict(from_attributes=True)

    active: bool = Field(
        default=True,
        title="Active",
        description="Whether or not the baked good is active",
    )
    name: Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)] = (
        Field(title="Name", description="The name of the baked good")
    )
    description: Annotated[
        str, StringConstraints(min_length=1, strip_whitespace=True)
    ] = Field(title="Description", description="A description of the baked good")
    purchase_cost: Annotated[Decimal, Field(ge=0, decimal_places=2, max_digits=10)] = (
        Field(
            title="Purchase Cost",
            description="The purchase cost, in dollars per baked good",
        )
    )
    retail_price: Annotated[Decimal, Field(ge=0, decimal_places=2, max_digits=10)] = (
        Field(
            title="Retail Price",
            description="The retail price, in dollars per baked good",
        )
    )
    allergens: list[str] = Field(
        title="Allergens",
        description="A list of any allergens present in the baked good",
    )


class BakedGoodCreate(BakedGoodBase):
    """Represents a baked good before it has been saved to the database."""


class BakedGoodRead(BakedGoodBase):
    """The baked good representation returned to an API client."""

    id: PositiveInt = Field(
        title="ID", description="The unique identifier for this baked good"
    )
