from decimal import ROUND_HALF_UP, Decimal

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


def build_drink_ingredients(
    session: DbSession, payload: list[DrinkIngredientCreateNested]
) -> list[DrinkIngredient]:
    """Build the list of ingredients for a unique drink recipe"""
    drink_ingredients = []
    for item in payload:
        ingredient = session.get(Ingredient, item.ingredient_id)
        if ingredient is None:
            ingredient_logger.log_attrs_not_unique([Ingredient.name])
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


def calculate_production_cost(drink_ingredients: list[DrinkIngredient]) -> Decimal:
    """Calculate the purchasing cost sum of all ingredients for a drink recipe"""
    total = sum((i.ingredient_cost for i in drink_ingredients), start=Decimal("0"))
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
