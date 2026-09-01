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
    calculate_ingredient_cost,
    calculate_production_cost,
    calculate_sale_price,
    convert_unit,
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
        amount=amount,
        unit="g",
        ingredient=Ingredient(
            purchasing_cost=cost_per_unit,
            unit_amount=Decimal("1"),
            unit_of_measure="g",
        ),
    )


# ==========================================
# CONVERT UNIT
# ==========================================
@pytest.mark.parametrize(
    "unit_from, unit_to, amount, expected",
    [
        ("g", "kg", Decimal("0.005"), Decimal("5")),
        ("kg", "g", Decimal("5"), Decimal("0.005")),
        ("oz", "lb", Decimal("4"), Decimal("64")),
    ],
)
def test_convert_unit_with_unit_category_of_mass_should_return_converted_amount(
    unit_from, unit_to, amount, expected
):
    result = convert_unit(
        amount=amount,
        unit_from=unit_from,
        unit_to=unit_to,
    )
    assert result.quantize(Decimal("0.001")) == expected


@pytest.mark.parametrize(
    "unit_from, unit_to, amount, expected",
    [
        ("mL", "L", Decimal("0.005"), Decimal("5")),
        ("L", "mL", Decimal("5"), Decimal("0.005")),
        ("fl oz", "gal", Decimal("16"), Decimal("2048.001")),
    ],
)
def test_convert_unit_with_unit_category_of_volume_should_return_converted_amount(
    unit_from, unit_to, amount, expected
):
    result = convert_unit(
        amount=amount,
        unit_from=unit_from,
        unit_to=unit_to,
    )
    assert result.quantize(Decimal("0.001")) == expected


@pytest.mark.parametrize(
    "unit_from, unit_to, amount, expected",
    [
        ("pumps", "scoops", Decimal("0.5"), Decimal("0.5")),
        ("scoops", "pumps", Decimal("10"), Decimal("10")),
        ("shots", "dashes", Decimal("5"), Decimal("5")),
    ],
)
def test_convert_unit_with_unit_category_of_other_should_return_converted_amount(
    unit_from, unit_to, amount, expected
):
    result = convert_unit(
        amount=amount,
        unit_from=unit_from,
        unit_to=unit_to,
    )
    assert result.quantize(Decimal("0.001")) == expected


def test_convert_unit_with_unknown_ingredient_unit_should_raise_value_error():
    unit_from = "ton"
    with pytest.raises(ValueError, match=f"{unit_from} is an unknown unit to convert"):
        convert_unit(
            amount=Decimal("1"),
            unit_from=unit_from,
            unit_to="g",
        )


def test_convert_unit_with_unknown_drink_unit_should_raise_value_error():
    unit_from = "cubic centimeter"
    with pytest.raises(ValueError, match=f"{unit_from} is an unknown unit to convert"):
        convert_unit(
            amount=Decimal("1"),
            unit_from=unit_from,
            unit_to="mL",
        )


def test_convert_unit_with_different_unit_categories_should_raise_value_error():
    unit_from = "g"
    unit_to = "mL"
    with pytest.raises(ValueError) as exc_info:
        convert_unit(
            amount=Decimal("1"),
            unit_from=unit_from,
            unit_to=unit_to,
        )
    assert "cannot convert between categories" in str(exc_info.value)


# ==========================================
# BUILD DRINK INGREDIENTS
# ==========================================
def test_build_drink_ingredients_should_return_ingredient_by_id(
    db_session, make_ingredient
):
    ingredient = make_ingredient(purchasing_cost=Decimal("0.65"))
    items = [
        DrinkIngredientCreateNested(
            ingredient_id=ingredient.id, amount=Decimal("4"), unit="mL"
        )
    ]
    result = build_drink_ingredients(db_session, items)

    assert len(result) == 1
    assert result[0].ingredient.id == ingredient.id
    assert result[0].amount == Decimal("4")
    assert result[0].unit == "mL"


def test_build_drink_ingredients_with_multiple_ingredients_should_return_list(
    db_session, make_ingredient
):
    ingredient_1 = make_ingredient(purchasing_cost=Decimal("0.50"))
    ingredient_2 = make_ingredient(purchasing_cost=Decimal("0.75"))
    items = [
        DrinkIngredientCreateNested(
            ingredient_id=ingredient_1.id, amount=Decimal("5"), unit="mL"
        ),
        DrinkIngredientCreateNested(
            ingredient_id=ingredient_2.id, amount=Decimal("7"), unit="mL"
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
# CALCULATE INGREDIENT COST
# ==========================================
def test_calculate_ingredient_cost_should_return_cost():
    drink_ingredient = DrinkIngredient(
        amount=Decimal("5"),
        unit="g",
        ingredient=Ingredient(
            purchasing_cost=Decimal("3.25"),
            unit_amount=Decimal("2"),
            unit_of_measure="kg",
        ),
    )
    result = calculate_ingredient_cost(drink_ingredient)
    assert result == Decimal("0.008125")


def test_calculate_ingredient_cost_with_different_categories_should_raise_422():
    drink_ingredient = DrinkIngredient(
        amount=Decimal("1"),
        unit="g",
        ingredient=Ingredient(
            purchasing_cost=Decimal("1"),
            unit_amount=Decimal("1"),
            unit_of_measure="mL",
        ),
    )
    with pytest.raises(HTTPException):
        calculate_ingredient_cost(drink_ingredient)


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
        markup_percentage=Decimal("30"),
        ingredients=[
            DrinkIngredientCreateNested(
                ingredient_id=ingredient.id, amount=Decimal("1400"), unit="mL"
            )
        ],
    )
    drink = create_drink(db_session, payload)

    assert drink.id is not None
    assert drink.production_cost == Decimal("0.04")
    assert drink.sale_price == Decimal("1.20")


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
        markup_percentage=Decimal("6"),
        ingredients=[
            DrinkIngredientCreateNested(
                ingredient_id=ingredient_1.id, amount=Decimal("1000"), unit="mL"
            ),
            DrinkIngredientCreateNested(
                ingredient_id=ingredient_2.id, amount=Decimal("2000"), unit="mL"
            ),
        ],
    )
    drink = create_drink(db_session, payload)

    assert len(drink.ingredients) == 2
    assert drink.production_cost == Decimal("0.43")
    assert drink.sale_price == Decimal("2.58")
