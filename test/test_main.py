import pytest

from wyrmwood_coffee.models.ingredient import IngredientRead

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
    assert response.status_code == 201
    return response.json()["id"]


# ---------------------------------------------------------
# Ingredient Payload for Main Endpoint Test
# ---------------------------------------------------------


@pytest.fixture
def ingredient_payload(vendor_id):
    return {
        "name": "Sugar",
        "purchasing_cost": 3.5,
        "unit_amount": 1000,
        "unit_of_measure": "ml",
        "allergens": ["corn"],
        "vendor_id": vendor_id,
    }


# ---------------------------------------------------------
# Main Endpoint Tests
# ---------------------------------------------------------


def test_create_ingredient(client, ingredient_payload):
    response = client.post("/ingredients", json=ingredient_payload)
    assert response.status_code == 201

    ingredient = IngredientRead(**response.json())

    expected = ingredient_payload | {
        "id": ingredient.id,
        "active": True,
    }

    assert ingredient.model_dump(mode="json") == expected
