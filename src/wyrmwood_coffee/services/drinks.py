from decimal import ROUND_HALF_UP, Decimal
from enum import Enum

from fastapi import HTTPException, status

from wyrmwood_coffee.dependencies import DbSession
from wyrmwood_coffee.models.drink import (
    Drink,
    DrinkCreate,
    DrinkIngredient,
    DrinkIngredientCreateNested,
)
from wyrmwood_coffee.models.ingredient import Ingredient
from wyrmwood_coffee.routers.ingredients import ingredient_logger


class UnitCategory(Enum):
    MASS = "mass"
    VOLUME = "volume"
    OTHER = "other"


UNIT_TO_BASE = {
    "g": (UnitCategory.MASS, Decimal("1")),
    "kg": (UnitCategory.MASS, Decimal("1000")),
    "oz": (UnitCategory.MASS, Decimal("28.349523125")),
    "lb": (UnitCategory.MASS, Decimal("453.59237")),
    "mL": (UnitCategory.VOLUME, Decimal("1")),
    "fl oz": (UnitCategory.VOLUME, Decimal("29.5735")),
    "L": (UnitCategory.VOLUME, Decimal("1000")),
    "gal": (UnitCategory.VOLUME, Decimal("3785.41")),
    "pumps": (UnitCategory.OTHER, Decimal("1")),
    "scoops": (UnitCategory.OTHER, Decimal("1")),
    "shots": (UnitCategory.OTHER, Decimal("1")),
    "dashes": (UnitCategory.OTHER, Decimal("1")),
}


def convert_unit(
    amount: Decimal,
    unit_from: str,
    unit_to: str,
) -> Decimal:
    """Convert ingredient units to drink recipe units"""
    if unit_from not in UNIT_TO_BASE:
        raise ValueError(f"{unit_from} is an unknown unit to convert")
    if unit_to not in UNIT_TO_BASE:
        raise ValueError(f"{unit_to} is an unknown unit to convert")
    category_from, factor_from = UNIT_TO_BASE[unit_from]
    category_to, factor_to = UNIT_TO_BASE[unit_to]
    if category_from != category_to:
        raise ValueError(
            f"cannot convert between categories: "
            f"{unit_from} ({category_from}) to {unit_to} ({category_to})"
        )
    return amount * (factor_to / factor_from)


def build_drink_ingredients(
    session: DbSession, payload: list[DrinkIngredientCreateNested]
) -> list[DrinkIngredient]:
    """Build the list of ingredients for a unique drink recipe"""
    drink_ingredients = []
    for item in payload:
        ingredient = session.get(Ingredient, item.ingredient_id)
        if ingredient is None:
            ingredient_logger.log_resource_not_found(item.ingredient_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The ingredient was not found.",
            )
        drink_ingredients.append(
            DrinkIngredient(
                ingredient=ingredient,
                amount=item.amount,
                unit=item.unit,
            )
        )
    return drink_ingredients


def calculate_ingredient_cost(drink_ingredient: DrinkIngredient) -> Decimal:
    """Calculate the ingredient cost after unit conversion"""
    ingredient = drink_ingredient.ingredient
    unit_cost = ingredient.purchasing_cost / ingredient.unit_amount
    try:
        converted_amount = convert_unit(
            amount=drink_ingredient.amount,
            unit_from=ingredient.unit_of_measure,
            unit_to=drink_ingredient.unit,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(e)
        ) from e
    return unit_cost * converted_amount


def calculate_production_cost(drink_ingredients: list[DrinkIngredient]) -> Decimal:
    """Calculate the purchasing cost sum of all ingredients for a drink recipe"""
    total = sum(
        (calculate_ingredient_cost(di) for di in drink_ingredients), start=Decimal("0")
    )
    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_sale_price(
    markup_percentage: Decimal, production_cost: Decimal
) -> Decimal:
    """Calculate the sale price of a drink"""
    return (markup_percentage * production_cost).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )


def create_drink(session: DbSession, payload: DrinkCreate) -> Drink:
    """Construct a drink recipe with list of required ingredients and computed values"""
    drink_ingredients = build_drink_ingredients(session, payload.ingredients)
    production_cost = calculate_production_cost(drink_ingredients)
    sale_price = calculate_sale_price(payload.markup_percentage, production_cost)
    drink = Drink(
        active=payload.active,
        name=payload.name,
        description=payload.description,
        type=payload.type,
        ingredients=drink_ingredients,
        markup_percentage=payload.markup_percentage,
        production_cost=production_cost,
        sale_price=sale_price,
    )
    session.add(drink)
    session.commit()
    session.refresh(drink)
    return drink
