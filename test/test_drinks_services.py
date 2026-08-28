from decimal import Decimal

import pytest
from fastapi import HTTPException, status
from sqlalchemy import func, select

from wyrmwood_coffee.models.drink import (
    DrinkCreate,
    DrinkIngredient,
    DrinkIngredientCreateNested,
)
from wyrmwood_coffee.models.ingredient import Ingredient
from wyrmwood_coffee.services.drinks import (
    build_drink_ingredients,
    calculate_production_cost,
    calculate_sale_price,
    create_drink,
)


@pytest.fixture()
def unused_ingredient_id(db_session):
    def _unused_ingredient_id():
        max_id = db_session.scalar(select(func.max(Ingredient.id))) or 0
        return max_id + 1

    return _unused_ingredient_id


def _make_drink_ingredient(amount: Decimal, cost_per_unit: Decimal) -> DrinkIngredient:
    return DrinkIngredient(
        amount=amount, unit="g", ingredient=Ingredient(purchasing_cost=cost_per_unit)
    )


def test_ingredient_cost_should_round_to_two_decimal_places():
    drink_ingredient = DrinkIngredient(
        amount=Decimal("3"),
        unit="g",
        ingredient=Ingredient(purchasing_cost=Decimal("3.333")),
    )
    assert drink_ingredient.ingredient_cost == Decimal("10.00")


# ==========================================
# BUILD DRINK INGREDIENTS
# ==========================================
def test_build_drink_ingredients_should_return_ingredient_by_id(
    db_session, make_ingredient
):
    ingredient = make_ingredient(purchasing_cost=Decimal("0.65"))
    items = [
        DrinkIngredientCreateNested(
            ingredient_id=ingredient.id, amount=Decimal("4"), unit="oz"
        )
    ]
    result = build_drink_ingredients(db_session, items)

    assert len(result) == 1
    assert result[0].ingredient.id == ingredient.id
    assert result[0].amount == Decimal("4")
    assert result[0].unit == "oz"


def test_build_drink_ingredients_should_compute_ingredient_cost(
    db_session, make_ingredient
):
    ingredient = make_ingredient(purchasing_cost=Decimal("0.85"))
    items = [
        DrinkIngredientCreateNested(
            ingredient_id=ingredient.id, amount=Decimal("6"), unit="fl oz"
        )
    ]
    result = build_drink_ingredients(db_session, items)

    assert result[0].ingredient_cost == Decimal("5.10")


def test_build_drink_ingredients_with_multiple_ingredients_should_return_list(
    db_session, make_ingredient
):
    ingredient_1 = make_ingredient(purchasing_cost=Decimal("0.50"))
    ingredient_2 = make_ingredient(purchasing_cost=Decimal("0.75"))
    items = [
        DrinkIngredientCreateNested(
            ingredient_id=ingredient_1.id, amount=Decimal("5"), unit="g"
        ),
        DrinkIngredientCreateNested(
            ingredient_id=ingredient_2.id, amount=Decimal("7"), unit="g"
        ),
    ]
    result = build_drink_ingredients(db_session, items)

    assert len(result) == 2
    assert {i.ingredient.id for i in result} == {ingredient_1.id, ingredient_2.id}


def test_build_drink_ingredients_with_nonexistent_ingredient_should_return_404(
    db_session, unused_ingredient_id
):
    ingredient = [
        DrinkIngredientCreateNested(
            ingredient_id=unused_ingredient_id(), amount=Decimal("4"), unit="g"
        )
    ]
    with pytest.raises(HTTPException) as exc_info:
        build_drink_ingredients(db_session, ingredient)

    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc_info.value.detail == "The ingredient was not found."


# ==========================================
# CALCULATE PRODUCTION COST
# ==========================================
def test_calculate_production_cost_with_empty_ingredients_list_should_return_zero():
    result = calculate_production_cost([])
    assert result == Decimal("0.00")


def test_calculate_production_cost_with_one_ingredient_should_return_ingredient_cost():
    drink_ingredients = [_make_drink_ingredient(Decimal("1"), Decimal("2.40"))]
    result = calculate_production_cost(drink_ingredients)
    assert result == Decimal("2.40")


def test_calculate_production_cost_with_multiple_ingredients_should_return_sum_cost():
    drink_ingredients = [
        _make_drink_ingredient(Decimal("1"), Decimal("5.25")),
        _make_drink_ingredient(Decimal("1"), Decimal("3.45")),
        _make_drink_ingredient(Decimal("1"), Decimal("8.35")),
    ]
    result = calculate_production_cost(drink_ingredients)
    assert result == Decimal("17.05")


# ==========================================
# CALCULATE SALE PRICE
# ==========================================
def test_calculate_sale_price_should_apply_markup_to_production_cost():
    result = calculate_sale_price(Decimal("3.00"), Decimal("5.00"))
    assert result == Decimal("15.00")


def test_calculate_sale_price_with_markup_of_one_should_return_same_production_cost():
    result = calculate_sale_price(Decimal("1"), Decimal("9.50"))
    assert result == Decimal("9.50")


def test_calculate_sale_price_should_round_to_two_decimal_places():
    result = calculate_sale_price(Decimal("4"), Decimal("7.777"))
    assert result == Decimal("31.11")


def test_calculate_sale_price_with_zero_production_cost_should_return_zero():
    result = calculate_sale_price(Decimal("6.00"), Decimal("0"))
    assert result == Decimal("0")


def test_calculate_sale_price_should_return_two_decimal_places():
    result = calculate_sale_price(Decimal("2"), Decimal("8"))
    assert result == result.quantize(Decimal("0.01"))


# ==========================================
# CREATE DRINK
# ==========================================
def test_create_drink_with_computed_values_should_persist_to_db(
    db_session, make_ingredient
):
    ingredient = make_ingredient(purchasing_cost=Decimal("0.15"))
    payload = DrinkCreate(
        active=True,
        name="Kelp Cola",
        description="World-Famous Soda from Kelp Extract",
        type="soda",
        markup_percentage=Decimal("3"),
        ingredients=[
            DrinkIngredientCreateNested(
                ingredient_id=ingredient.id, amount=Decimal("6"), unit="g"
            )
        ],
    )
    drink = create_drink(db_session, payload)

    assert drink.id is not None
    assert drink.production_cost == Decimal("0.9")
    assert drink.sale_price == Decimal("2.7")


def test_create_drink_with_multiple_ingredients_should_return_computed_values(
    db_session, make_ingredient
):
    ingredient_1 = make_ingredient(purchasing_cost=Decimal("1.45"))
    ingredient_2 = make_ingredient(purchasing_cost=Decimal("0.35"))
    payload = DrinkCreate(
        active=True,
        name="Seahorse Milk",
        description="Organic Fresh Milk from Free-Range Seahorses",
        type="other",
        markup_percentage=Decimal("2"),
        ingredients=[
            DrinkIngredientCreateNested(
                ingredient_id=ingredient_1.id, amount=Decimal("1"), unit="fl oz"
            ),
            DrinkIngredientCreateNested(
                ingredient_id=ingredient_2.id, amount=Decimal("8"), unit="g"
            ),
        ],
    )
    drink = create_drink(db_session, payload)

    assert len(drink.ingredients) == 2
    assert drink.production_cost == Decimal("4.25")
    assert drink.sale_price == Decimal("8.5")
