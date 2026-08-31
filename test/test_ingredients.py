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
def single_ingredient(db_session):
    # Insert a vendor first to satisfy the foreign key requirement
    vendor = Vendor(name="Direct DB Vendor", contacts=[])
    db_session.add(vendor)
    db_session.commit()
    db_session.refresh(vendor)

    # Insert the ingredient directly into the database
    ingredient = Ingredient(
        name="Sugar",
        purchasing_cost=3.5,
        unit_amount=1000,
        unit_of_measure="mL",
        allergens=["corn"],
        vendor_id=vendor.id,
        active=True,
    )
    db_session.add(ingredient)
    db_session.commit()
    db_session.refresh(ingredient)
    return ingredient


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
    return ingredient_valid_kwargs | {"allergens": "corn"}


@pytest.fixture
def ingredient_invalid_vendor_kwargs(ingredient_valid_kwargs):
    return ingredient_valid_kwargs | {"vendor_id": 9999}


@pytest.fixture
def ingredient_deleted_vendor_kwargs(client, ingredient_valid_kwargs):
    client.delete(f"/vendors/{ingredient_valid_kwargs['vendor_id']}")
    return ingredient_valid_kwargs


# ---------------------------------------------------------
# List Ingredients Tests
# ---------------------------------------------------------


def test_list_ingredients_should_return_ingredients(client, single_ingredient):
    response = client.get("/ingredients")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["id"] == single_ingredient.id
    assert data[0]["name"] == single_ingredient.name


def test_list_ingredients_with_no_ingredients_should_return_empty_list(client):
    response = client.get("/ingredients")

    assert response.status_code == 200
    assert response.json() == []


def test_list_ingredients_with_soft_deleted_ingredient_should_return_empty_list(
    db_session, client, single_ingredient
):
    # Manually soft-delete the ingredient using the new architecture
    single_ingredient.active = False
    single_ingredient.is_deleted = True
    db_session.commit()

    response = client.get("/ingredients")

    assert response.status_code == 200
    # The list should be empty because the only ingredient is deleted
    assert len(response.json()) == 0


# ---------------------------------------------------------
# Get Ingredient Tests
# ---------------------------------------------------------


def test_get_ingredient_should_return_ingredient(client, single_ingredient):
    get_response = client.get(f"/ingredients/{single_ingredient.id}")

    assert get_response.status_code == 200
    data = get_response.json()
    assert data["id"] == single_ingredient.id
    assert data["name"] == single_ingredient.name
    assert data["unit_amount"] == "1000.00"


def test_get_ingredient_with_invalid_id_should_return_404(client):
    response = client.get("/ingredients/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "The ingredient was not found."


def test_get_ingredient_with_malformed_id_should_return_422(client):
    response = client.get("/ingredients/not-a-number")
    assert response.status_code == 422


def test_get_ingredient_with_negative_id_should_return_422(client):
    response = client.get("/ingredients/-5")
    assert response.status_code == 422


def test_get_ingredient_with_soft_deleted_ingredient_should_return_404(
    db_session, client, single_ingredient
):
    # Manually soft-delete the ingredient using the new architecture
    single_ingredient.active = False
    single_ingredient.is_deleted = True
    db_session.commit()

    response = client.get(f"/ingredients/{single_ingredient.id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "The ingredient was not found."


# ---------------------------------------------------------
# Create Ingredient Tests
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


def test_create_ingredient_with_deleted_vendor_should_return_404(
    client, ingredient_deleted_vendor_kwargs
):
    response = client.post("/ingredients", json=ingredient_deleted_vendor_kwargs)
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


def test_create_ingredient_should_persist_to_db(
    db_session, client, ingredient_valid_kwargs
):
    response = client.post("/ingredients", json=ingredient_valid_kwargs)
    ingredient = db_session.get(Ingredient, response.json()["id"])
    assert ingredient is not None


# ==========================================
# UPDATE OPERATIONS
# ==========================================

# --------------------
# Successful Responses
# --------------------


def test_update_ingredient_should_return_ingredient(client, single_ingredient):
    # Full payload for a PUT replacement
    update_payload = {
        "name": "Updated Espresso Beans",
        "purchasing_cost": "4.50",
        "unit_amount": "1000.00",
        "unit_of_measure": "mL",
        "vendor_id": single_ingredient.vendor_id,
        "allergens": [],
        "active": False,
    }

    response = client.put(f"/ingredients/{single_ingredient.id}", json=update_payload)

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Espresso Beans"
    assert data["purchasing_cost"] == "4.50"
    assert data["active"] is False


# --------------------
# Error Responses
# --------------------


def test_update_ingredient_with_invalid_id_should_return_404(client, single_ingredient):
    update_payload = {
        "name": "Ghost Beans",
        "purchasing_cost": "3.00",
        "unit_amount": "500.00",
        "unit_of_measure": "g",
        "vendor_id": single_ingredient.vendor_id,
        "allergens": [],
        "active": True,
    }
    response = client.put("/ingredients/99999", json=update_payload)

    assert response.status_code == 404


def test_update_ingredient_with_invalid_payload_should_return_422(
    client, single_ingredient
):
    # This should fail because it is missing the rest of the required fields
    update_payload = {"purchasing_cost": "not-a-number"}
    response = client.put(f"/ingredients/{single_ingredient.id}", json=update_payload)

    assert response.status_code == 422


def test_update_ingredient_with_invalid_vendor_should_return_404(
    client, single_ingredient
):
    update_payload = {
        "name": "Updated Espresso Beans",
        "purchasing_cost": "4.50",
        "unit_amount": "1000.00",
        "unit_of_measure": "mL",
        "vendor_id": 99999,
        "allergens": [],
        "active": True,
    }
    response = client.put(f"/ingredients/{single_ingredient.id}", json=update_payload)

    assert response.status_code == 404
    assert response.json()["detail"] == "The vendor was not found."


# --------------------
# Side-Effect Tests
# --------------------


def test_update_ingredient_should_persist_to_db(db_session, client, single_ingredient):
    update_payload = {
        "name": "Persisted Update Beans",
        "purchasing_cost": "4.50",
        "unit_amount": "1000.00",
        "unit_of_measure": "mL",
        "vendor_id": single_ingredient.vendor_id,
        "allergens": [],
        "active": True,
    }
    client.put(f"/ingredients/{single_ingredient.id}", json=update_payload)

    db_session.refresh(single_ingredient)
    assert single_ingredient.name == "Persisted Update Beans"


# ==========================================
# DELETE OPERATIONS
# ==========================================

# --------------------
# Successful Responses
# --------------------


def test_delete_ingredient_should_return_none(client, single_ingredient):
    response = client.delete(f"/ingredients/{single_ingredient.id}")
    assert response.status_code == 204


# --------------------
# Error Responses
# --------------------


def test_delete_ingredient_with_invalid_id_should_return_404(client):
    response = client.delete("/ingredients/99999")

    assert response.status_code == 404
    assert response.json()["detail"] == "The ingredient was not found."


def test_delete_ingredient_with_malformed_id_should_return_422(client):
    response = client.delete("/ingredients/not-a-number")
    assert response.status_code == 422


def test_delete_ingredient_with_negative_id_should_return_422(client):
    response = client.delete("/ingredients/-5")
    assert response.status_code == 422


# --------------------
# Side-Effect Tests
# --------------------


def test_delete_ingredient_should_soft_delete_ingredient(
    db_session, client, single_ingredient
):
    client.delete(f"/ingredients/{single_ingredient.id}")

    db_session.refresh(single_ingredient)

    # Assert that the is_deleted flag is updated properly
    assert single_ingredient.is_deleted is True
