from decimal import Decimal
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)
from sqlalchemy import Boolean, ForeignKey, Identity, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from wyrmwood_coffee.database import Base
from wyrmwood_coffee.models.ingredient import VALID_UNITS, Ingredient

VALID_TYPES = {"coffee", "tea", "soda", "refresher", "other"}

DRINK_INGREDIENT_ID_TITLE = "Ingredient ID"
DRINK_INGREDIENT_ID_DESC = "The unique identifier of the ingredient"

DRINK_INGREDIENT_AMOUNT_TITLE = "Ingredient Amount"
DRINK_INGREDIENT_AMOUNT_DESC = "The ingredient required for the drink recipe"

DRINK_INGREDIENT_UNIT_TITLE = "Ingredient Unit"
DRINK_INGREDIENT_UNIT_DESC = "The ingredient's unit of measurement"

DRINK_ACTIVE_TITLE = "Drink Activity Status"
DRINK_ACTIVE_DESC = "The activity status of the drink"

DRINK_NAME_TITLE = "Drink Name"
DRINK_NAME_DESC = "The drink recipe name"

DRINK_DESCRIPTION_TITLE = "Drink Description"
DRINK_DESCRIPTION_DESC = "The drink's description"

DRINK_TYPE_TITLE = "Drink Type"
DRINK_TYPE_DESC = (
    "The type of drink and must be one: coffee, tea, soda, refresher, other"
)

DRINK_MARKUP_TITLE = "Markup Percentage"
DRINK_MARKUP_DESC = "The drink's markup percentage"

DRINK_INGREDIENTS_TITLE = "Drink Ingredients"
DRINK_INGREDIENTS_DESC = "The ingredients required for the drink recipe"

DRINK_ID_TITLE = "Drink ID"
DRINK_ID_DESC = "The unique identifier of the drink"

DRINK_PRODUCTION_COST_TITLE = "Drink Production Cost"
DRINK_PRODUCTION_COST_DESC = (
    "The purchasing cost sum of all ingredients required for the drink"
)

DRINK_SALE_PRICE_TITLE = "Drink Sale Price"
DRINK_SALE_PRICE_DESC = (
    "The product of the drink's markup percentage and production cost"
)


class DrinkIngredient(Base):
    __tablename__ = "drink_ingredients"

    drink_id: Mapped[int] = mapped_column(ForeignKey("drinks.id"), primary_key=True)
    ingredient_id: Mapped[int] = mapped_column(
        ForeignKey("ingredients.id"), primary_key=True
    )
    drink: Mapped["Drink"] = relationship(back_populates="ingredients")
    ingredient: Mapped["Ingredient"] = relationship(back_populates="drinks")
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    unit: Mapped[str] = mapped_column(nullable=False)


class Drink(Base):
    __tablename__ = "drinks"

    id: Mapped[int] = mapped_column(Integer, Identity(always=True), primary_key=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    name: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(nullable=False)
    ingredients: Mapped[list["DrinkIngredient"]] = relationship(
        back_populates="drink", cascade="all, delete-orphan"
    )
    type: Mapped[str] = mapped_column(nullable=False)
    production_cost: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    markup_percentage: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    sale_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)


class DrinkIngredientBase(BaseModel):
    """Base schema of an ingredient for a unique drink in the system."""

    ingredient_id: int = Field(
        gt=0, title=DRINK_INGREDIENT_ID_TITLE, description=DRINK_INGREDIENT_ID_DESC
    )
    amount: Annotated[
        Decimal,
        Field(
            gt=0,
            title=DRINK_INGREDIENT_AMOUNT_TITLE,
            description=DRINK_INGREDIENT_AMOUNT_DESC,
        ),
    ]
    unit: Annotated[
        str,
        Field(
            title=DRINK_INGREDIENT_UNIT_TITLE, description=DRINK_INGREDIENT_UNIT_DESC
        ),
    ]


class DrinkIngredientCreateNested(DrinkIngredientBase):
    """Input schema for attaching an existing ingredient to a new drink recipe."""

    @field_validator("unit")
    def validate_unit(cls, value):
        if value not in VALID_UNITS:
            raise ValueError(f"unit must be one of: {', '.join(VALID_UNITS)}")
        return value

    model_config = ConfigDict(from_attributes=True)


class DrinkIngredientRead(DrinkIngredientBase):
    """Represents an ingredient for a unique drink recipe in the system."""

    model_config = ConfigDict(from_attributes=True)
    pass


class DrinkBase(BaseModel):
    """Base schema of a drink recipe in the system."""

    active: Annotated[
        bool,
        Field(default=True, title=DRINK_ACTIVE_TITLE, description=DRINK_ACTIVE_DESC),
    ]
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)] = (
        Field(title=DRINK_NAME_TITLE, description=DRINK_NAME_DESC)
    )
    description: Annotated[str, StringConstraints(min_length=1)] = Field(
        title=DRINK_DESCRIPTION_TITLE, description=DRINK_DESCRIPTION_DESC
    )
    type: Annotated[str, Field(title=DRINK_TYPE_TITLE, description=DRINK_TYPE_DESC)]
    markup_percentage: Annotated[
        Decimal, Field(ge=1, title=DRINK_MARKUP_TITLE, description=DRINK_MARKUP_DESC)
    ]

    @field_validator("type")
    def validate_type(cls, value):
        if value not in VALID_TYPES:
            raise ValueError(f"type must be one of: {', '.join(VALID_TYPES)}")
        return value


class DrinkCreate(DrinkBase):
    """Input schema for creating a new drink recipe."""

    ingredients: list[DrinkIngredientCreateNested] = Field(
        min_length=1,
        title=DRINK_INGREDIENTS_TITLE,
        description=DRINK_INGREDIENTS_DESC,
    )

    @field_validator("ingredients")
    def validate_unique_ingredient_ids(cls, value):
        ingredient_ids = [item.ingredient_id for item in value]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise ValueError("duplicate ingredient_id in ingredients")
        return value

    model_config = ConfigDict(from_attributes=True)


class DrinkRead(DrinkBase):
    """Represents a new drink recipe in the system."""

    id: int = Field(title=DRINK_ID_TITLE, description=DRINK_ID_DESC)
    ingredients: list[DrinkIngredientRead] = Field(
        min_length=1,
        title=DRINK_INGREDIENTS_TITLE,
        description=DRINK_INGREDIENTS_DESC,
    )
    production_cost: Annotated[
        Decimal,
        Field(
            title=DRINK_PRODUCTION_COST_TITLE, description=DRINK_PRODUCTION_COST_DESC
        ),
    ]
    sale_price: Annotated[
        Decimal, Field(title=DRINK_SALE_PRICE_TITLE, description=DRINK_SALE_PRICE_DESC)
    ]

    @model_validator(mode="after")
    def check_sale_price_greater_than_production_cost(self):
        if self.sale_price < self.production_cost:
            raise ValueError("sale price cannot be less than production cost")
        return self

    model_config = ConfigDict(from_attributes=True)
