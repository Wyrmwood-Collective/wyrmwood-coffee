import itertools
from decimal import Decimal

import pytest

from wyrmwood_coffee.models.drink import Drink, DrinkCreate, DrinkIngredientCreateNested
from wyrmwood_coffee.services.drinks import create_drink


@pytest.fixture()
def make_drink(db_session, make_ingredient):
    counter = itertools.count(1)

    def _make_drink(ingredient_specs=None, **kwargs):
        n = next(counter)

        defaults = {
            "name": f"Kelp Shake {n}",
            "description": "Bestselling Bikini Bottom soft drink",
            "type": "soda",
            "markup_percentage": 2.00,
        }
        defaults.update(kwargs)

        specs = ingredient_specs or [{"amount": 2.00, "unit": "oz"}]
        ingredients = [
            DrinkIngredientCreateNested(
                ingredient_id=spec.get("ingredient_id") or make_ingredient().id,
                amount=spec.get("amount", 1.00),
                unit=spec.get("unit", "oz"),
            )
            for spec in specs
        ]

        payload = DrinkCreate(ingredients=ingredients, **defaults)
        return create_drink(db_session, payload)

    return _make_drink


@pytest.fixture()
def drink_payload_factory(make_ingredient):
    def _drink_payload(**overrides):
        ingredient = overrides.pop("_ingredient", None) or make_ingredient()
        defaults = {
            "active": True,
            "name": "Kelp Juice",
            "description": "Bikini Bottom special juice",
            "type": "refresher",
            "markup_percentage": 2,
            "ingredients": [
                {"ingredient_id": ingredient.id, "amount": 1.00, "unit": "fl oz"}
            ],
        }
        defaults.update(overrides)
        return defaults

    return _drink_payload


# ==========================================
# CREATE DRINK
# ==========================================


# --------------------
# Successful Responses
# --------------------
def test_create_drink_should_return_drink(
    client, drink_payload_factory, make_ingredient
):
    ingredient = make_ingredient()
    payload = drink_payload_factory(
        name="Oat Milk Latte",
        description="For oat milk lovers",
        type="coffee",
        _ingredient=ingredient,
    )

    response = client.post("/drinks", json=payload)
    assert response.status_code == 201

    body = response.json()
    assert body["active"] is True
    assert body["name"] == "Oat Milk Latte"
    assert body["description"] == "For oat milk lovers"
    assert body["type"] == "coffee"
    assert Decimal(body["markup_percentage"]) == Decimal("2.00")
    assert len(body["ingredients"]) == 1
    assert body["ingredients"][0]["ingredient_id"] == ingredient.id


def test_create_drink_with_missing_active_should_return_drink_with_active_is_true(
    client, drink_payload_factory
):
    payload = drink_payload_factory()
    del payload["active"]
    response = client.post("/drinks", json=payload)
    assert response.status_code == 201
    assert response.json()["active"] is True


# --------------------
# Error / Invalid Responses
# --------------------
def test_create_drink_with_missing_name_should_return_422(
    client, drink_payload_factory
):
    payload = drink_payload_factory()
    del payload["name"]
    response = client.post("/drinks", json=payload)
    assert response.status_code == 422


def test_create_drink_with_missing_description_should_return_422(
    client, drink_payload_factory
):
    payload = drink_payload_factory()
    del payload["description"]
    response = client.post("/drinks", json=payload)
    assert response.status_code == 422


def test_create_drink_with_missing_type_should_return_422(
    client, drink_payload_factory
):
    payload = drink_payload_factory()
    del payload["type"]
    response = client.post("/drinks", json=payload)
    assert response.status_code == 422


def test_create_drink_with_missing_markup_percentage_should_return_422(
    client, drink_payload_factory
):
    payload = drink_payload_factory()
    del payload["markup_percentage"]
    response = client.post("/drinks", json=payload)
    assert response.status_code == 422


def test_create_drink_with_missing_ingredients_should_return_422(
    client, drink_payload_factory
):
    payload = drink_payload_factory()
    del payload["ingredients"]
    response = client.post("/drinks", json=payload)
    assert response.status_code == 422


def test_create_drink_with_missing_ingredient_id_should_return_422(
    client, drink_payload_factory
):
    payload = drink_payload_factory()
    del payload["ingredients"][0]["ingredient_id"]
    response = client.post("/drinks", json=payload)
    assert response.status_code == 422


def test_create_drink_with_missing_ingredient_amount_should_return_422(
    client, drink_payload_factory
):
    payload = drink_payload_factory()
    del payload["ingredients"][0]["amount"]
    response = client.post("/drinks", json=payload)
    assert response.status_code == 422


def test_create_drink_with_missing_ingredient_unit_should_return_422(
    client, drink_payload_factory
):
    payload = drink_payload_factory()
    del payload["ingredients"][0]["unit"]
    response = client.post("/drinks", json=payload)
    assert response.status_code == 422


def test_create_drink_with_empty_ingredient_list_should_return_422(
    client, drink_payload_factory
):
    payload = drink_payload_factory(ingredients=[])
    response = client.post("/drinks", json=payload)
    assert response.status_code == 422


def test_create_drink_with_negative_ingredient_amount_should_return_422(
    client, drink_payload_factory
):
    payload = drink_payload_factory()
    payload["ingredients"][0]["amount"] = -1
    response = client.post("/drinks", json=payload)
    assert response.status_code == 422


def test_create_drink_with_invalid_ingredient_unit_should_return_422(
    client, drink_payload_factory
):
    payload = drink_payload_factory()
    payload["ingredients"][0]["unit"] = "ton"
    response = client.post("/drinks", json=payload)
    assert response.status_code == 422


def test_create_drink_with_invalid_type_should_return_422(
    client, drink_payload_factory
):
    payload = drink_payload_factory(type="milk tea")
    response = client.post("/drinks", json=payload)
    assert response.status_code == 422


def test_create_drink_with_markup_less_than_one_should_return_422(
    client, drink_payload_factory
):
    payload = drink_payload_factory(markup_percentage=0.9)
    response = client.post("/drinks", json=payload)
    assert response.status_code == 422


def test_create_drink_with_duplicate_name_should_return_409(
    client, drink_payload_factory, make_drink
):
    existing = make_drink(name="Original Drink")
    payload = drink_payload_factory(name=existing.name)
    assert payload["name"] == existing.name

    response = client.post("/drinks", json=payload)
    assert response.status_code == 409


# --------------------
# Side Effects
# --------------------
def test_create_drink_should_persist_to_db(db_session, client, drink_payload_factory):
    response = client.post("/drinks", json=drink_payload_factory())
    drink = db_session.get(Drink, response.json()["id"])
    assert drink is not None


def test_create_drink_with_duplicate_name_should_not_persist(
    db_session, client, drink_payload_factory
):
    client.post("/drinks", json=drink_payload_factory())
    previous_count = db_session.query(Drink).count()

    response = client.post("/drinks", json=drink_payload_factory())
    assert response.status_code == 409

    current_count = db_session.query(Drink).count()
    assert previous_count == current_count
