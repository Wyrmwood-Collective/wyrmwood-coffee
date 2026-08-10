import pytest

from wyrmwood_coffee.models.ingredient import Ingredient, IngredientRead

# ---------------------------------------------------------
# Vendor Fixture (Ingredients require vendor_id)
# ---------------------------------------------------------


@pytest.fixture
def vendor_kwargs():
    return {
        "name": "Domino Sugar Co",
        "contacts": [
            {
                "name": "John Smith",
                "role": "Sales Rep",
                "email": "john@domino.com",
                "phone": "555-555-5555",
            }
        ],
    }


@pytest.fixture
def vendor_id(client, vendor_kwargs):
    response = client.post("/vendors", json=vendor_kwargs)
    return response.json()["id"]


# ---------------------------------------------------------
# Base Ingredient Fixture
# ---------------------------------------------------------


@pytest.fixture
def ingredient_valid_kwargs(vendor_id):
    return {
        "name": "Sugar",
        "purchasing_cost": 3.5,
        "unit_amount": 1000,
        "unit_of_measure": "ml",
        "allergens": ["corn"],
        "vendor_id": vendor_id,
    }


# ---------------------------------------------------------
# Mutated Fixtures
# ---------------------------------------------------------


@pytest.fixture
def ingredient_missing_name_kwargs(ingredient_valid_kwargs):
    kwargs = dict(ingredient_valid_kwargs)
    del kwargs["name"]
    return kwargs


@pytest.fixture
def ingredient_whitespace_name_kwargs(ingredient_valid_kwargs):
    return ingredient_valid_kwargs | {"name": "   "}


@pytest.fixture
def ingredient_invalid_cost_kwargs(ingredient_valid_kwargs):
    return ingredient_valid_kwargs | {"purchasing_cost": "free"}


@pytest.fixture
def ingredient_invalid_unit_amount_kwargs(ingredient_valid_kwargs):
    return ingredient_valid_kwargs | {"unit_amount": -10}


@pytest.fixture
def ingredient_invalid_unit_of_measure_kwargs(ingredient_valid_kwargs):
    return ingredient_valid_kwargs | {"unit_of_measure": "invalid-unit"}


@pytest.fixture
def ingredient_invalid_allergens_kwargs(ingredient_valid_kwargs):
    return ingredient_valid_kwargs | {"allergens": "corn"}  # must be list


@pytest.fixture
def ingredient_inactive_kwargs(ingredient_valid_kwargs):
    return ingredient_valid_kwargs | {"active": False}


# ---------------------------------------------------------
# Creation Tests
# ---------------------------------------------------------


def test_create_ingredient_should_return_ingredient(client, ingredient_valid_kwargs):
    response = client.post("/ingredients", json=ingredient_valid_kwargs)
    assert response.status_code == 201

    ingredient = IngredientRead(**response.json())

    expected = ingredient_valid_kwargs | {
        "id": ingredient.id,
        "active": True,
    }

    assert ingredient.model_dump(mode="json") == expected


def test_create_ingredient_should_persist_to_db(
    db_session, client, ingredient_valid_kwargs
):
    response = client.post("/ingredients", json=ingredient_valid_kwargs)
    ingredient = db_session.get(Ingredient, response.json()["id"])
    assert ingredient is not None


# ---------------------------------------------------------
# Validation Tests (422)
# ---------------------------------------------------------


def test_create_ingredient_with_missing_name_should_return_422(
    client, ingredient_missing_name_kwargs
):
    response = client.post("/ingredients", json=ingredient_missing_name_kwargs)
    assert response.status_code == 422


def test_create_ingredient_with_whitespace_name_should_return_422(
    client, ingredient_whitespace_name_kwargs
):
    response = client.post("/ingredients", json=ingredient_whitespace_name_kwargs)
    assert response.status_code == 422


def test_create_ingredient_with_invalid_cost_should_return_422(
    client, ingredient_invalid_cost_kwargs
):
    response = client.post("/ingredients", json=ingredient_invalid_cost_kwargs)
    assert response.status_code == 422


def test_create_ingredient_with_invalid_unit_amount_should_return_422(
    client, ingredient_invalid_unit_amount_kwargs
):
    response = client.post("/ingredients", json=ingredient_invalid_unit_amount_kwargs)
    assert response.status_code == 422


def test_create_ingredient_with_invalid_unit_of_measure_should_return_422(
    client, ingredient_invalid_unit_of_measure_kwargs
):
    response = client.post(
        "/ingredients", json=ingredient_invalid_unit_of_measure_kwargs
    )
    assert response.status_code == 422


def test_create_ingredient_with_invalid_allergens_should_return_422(
    client, ingredient_invalid_allergens_kwargs
):
    response = client.post("/ingredients", json=ingredient_invalid_allergens_kwargs)
    assert response.status_code == 422


# ---------------------------------------------------------
# Active Flag Test
# ---------------------------------------------------------


def test_create_ingredient_with_active_false_should_return_inactive_ingredient(
    client, ingredient_inactive_kwargs
):
    response = client.post("/ingredients", json=ingredient_inactive_kwargs)
    assert response.status_code == 201
    assert response.json()["active"] is False


# ---------------------------------------------------------
# Retrieval Tests
# ---------------------------------------------------------


def test_get_ingredient_by_id_should_return_ingredient(client, ingredient_valid_kwargs):
    create_response = client.post("/ingredients", json=ingredient_valid_kwargs)
    ingredient_id = create_response.json()["id"]

    response = client.get(f"/ingredients/{ingredient_id}")
    assert response.status_code == 200

    ingredient = IngredientRead(**response.json())
    assert ingredient.name == ingredient_valid_kwargs["name"]
    assert ingredient.vendor_id == ingredient_valid_kwargs["vendor_id"]


def test_get_all_ingredients_should_return_list(client):
    response = client.get("/ingredients")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
