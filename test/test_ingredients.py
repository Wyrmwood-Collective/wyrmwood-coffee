import pytest

from wyrmwood_coffee.models.ingredient import Ingredient, IngredientRead
from wyrmwood_coffee.models.vendor import Vendor

# ---------------------------------------------------------
# Fixtures
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
def ingredient_valid_kwargs(client, vendor_kwargs):
    vendor_resp = client.post("/vendors", json=vendor_kwargs)
    vendor_id = vendor_resp.json()["id"]
    return {
        "name": "Sugar",
        "purchasing_cost": 3.5,
        "unit_amount": 1000,
        "unit_of_measure": "mL",
        "allergens": ["corn"],
        "vendor_id": vendor_id,
    }


@pytest.fixture
def ingredient_inactive_kwargs(ingredient_valid_kwargs):
    return ingredient_valid_kwargs | {"active": False}


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
    return ingredient_valid_kwargs | {"purchasing_cost": -5.0}


@pytest.fixture
def ingredient_invalid_unit_amount_kwargs(ingredient_valid_kwargs):
    return ingredient_valid_kwargs | {"unit_amount": -10.0}


@pytest.fixture
def ingredient_invalid_unit_of_measure_kwargs(ingredient_valid_kwargs):
    return ingredient_valid_kwargs | {"unit_of_measure": "invalid-unit"}


@pytest.fixture
def ingredient_invalid_allergens_kwargs(ingredient_valid_kwargs):
    return ingredient_valid_kwargs | {
        "allergens": "corn"
    }  # Intentionally invalid string instead of list


@pytest.fixture
def ingredient_invalid_vendor_kwargs(ingredient_valid_kwargs):
    return ingredient_valid_kwargs | {"vendor_id": 9999}


# ---------------------------------------------------------
# Success Tests (200 / 201)
# ---------------------------------------------------------


def test_create_ingredient_should_return_ingredient(client, ingredient_valid_kwargs):
    response = client.post("/ingredients", json=ingredient_valid_kwargs)
    assert response.status_code == 201
    ingredient = IngredientRead(**response.json())
    expected = ingredient_valid_kwargs | {
        "id": ingredient.id,
        "active": True,
        "purchasing_cost": "3.50",
        "unit_amount": "1000.00",
    }
    assert ingredient.model_dump(mode="json") == expected


def test_create_ingredient_with_inactive_ingredient_should_return_ingredient(
    client, ingredient_inactive_kwargs
):
    response = client.post("/ingredients", json=ingredient_inactive_kwargs)
    assert response.status_code == 201
    assert response.json()["active"] is False


def test_create_ingredient_with_same_name_different_vendor_should_return_ingredient(
    db_session, client, ingredient_valid_kwargs
):

    response1 = client.post("/ingredients", json=ingredient_valid_kwargs)
    assert response1.status_code == 201

    second_vendor = Vendor(name="A Completely Different Vendor", contacts=[])
    db_session.add(second_vendor)
    db_session.commit()
    db_session.refresh(second_vendor)

    second_ingredient_kwargs = ingredient_valid_kwargs.copy()
    second_ingredient_kwargs["vendor_id"] = second_vendor.id

    response2 = client.post("/ingredients", json=second_ingredient_kwargs)

    assert response2.status_code == 201
    assert response2.json()["name"] == response1.json()["name"]
    assert response2.json()["vendor_id"] != response1.json()["vendor_id"]


# ---------------------------------------------------------
# Error Tests (4xx)
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


def test_create_ingredient_with_invalid_vendor_should_return_404(
    client, ingredient_invalid_vendor_kwargs
):
    response = client.post("/ingredients", json=ingredient_invalid_vendor_kwargs)
    assert response.status_code == 404
    assert response.json()["detail"] == "The vendor was not found."


def test_create_ingredient_with_duplicate_name_and_vendor_id_should_return_409(
    client, ingredient_valid_kwargs
):

    client.post("/ingredients", json=ingredient_valid_kwargs)

    response = client.post("/ingredients", json=ingredient_valid_kwargs)

    assert response.status_code == 409
    assert (
        response.json()["detail"]
        == "An ingredient with that name and vendor ID already exists."
    )


# ---------------------------------------------------------
# Side-Effect Tests (Database checks, must come last)
# ---------------------------------------------------------


def test_create_ingredient_should_persist_to_db(
    db_session, client, ingredient_valid_kwargs
):
    response = client.post("/ingredients", json=ingredient_valid_kwargs)
    ingredient = db_session.get(Ingredient, response.json()["id"])
    assert ingredient is not None
