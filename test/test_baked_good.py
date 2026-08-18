from decimal import Decimal

import pytest

from wyrmwood_coffee.models.baked_goods import BakedGood, BakedGoodRead


@pytest.fixture
def baked_good_kwargs():
    return {
        "name": "Chocolate Croissant",
        "description": "A flaky croissant filled with rich chocolate.",
        "purchase_cost": "1.50",
        "retail_price": "3.25",
        "allergens": ["gluten", "dairy"],
    }


@pytest.fixture
def baked_good_inactive_kwargs(baked_good_kwargs):
    return baked_good_kwargs | {"active": False}


@pytest.fixture
def baked_good_empty_allergens_kwargs(baked_good_kwargs):
    return baked_good_kwargs | {"allergens": []}


@pytest.fixture
def baked_good_missing_name_kwargs(baked_good_kwargs):
    kwargs = dict(baked_good_kwargs)
    del kwargs["name"]
    return kwargs


@pytest.fixture
def baked_good_whitespace_name_kwargs(baked_good_kwargs):
    return baked_good_kwargs | {"name": "   "}


@pytest.fixture
def baked_good_missing_description_kwargs(baked_good_kwargs):
    kwargs = dict(baked_good_kwargs)
    del kwargs["description"]
    return kwargs


@pytest.fixture
def baked_good_whitespace_description_kwargs(baked_good_kwargs):
    return baked_good_kwargs | {"description": "   "}


@pytest.fixture
def baked_good_negative_purchase_cost_kwargs(baked_good_kwargs):
    return baked_good_kwargs | {"purchase_cost": "-1.00"}


@pytest.fixture
def baked_good_missing_purchase_cost_kwargs(baked_good_kwargs):
    kwargs = dict(baked_good_kwargs)
    del kwargs["purchase_cost"]
    return kwargs


@pytest.fixture
def baked_good_purchase_cost_too_many_decimals_kwargs(baked_good_kwargs):
    return baked_good_kwargs | {"purchase_cost": "1.505"}


@pytest.fixture
def baked_good_negative_retail_price_kwargs(baked_good_kwargs):
    return baked_good_kwargs | {"retail_price": "-1.00"}


@pytest.fixture
def baked_good_missing_retail_price_kwargs(baked_good_kwargs):
    kwargs = dict(baked_good_kwargs)
    del kwargs["retail_price"]
    return kwargs


@pytest.fixture
def baked_good_retail_price_too_many_decimals_kwargs(baked_good_kwargs):
    return baked_good_kwargs | {"retail_price": "3.255"}


@pytest.fixture
def baked_good_missing_allergens_kwargs(baked_good_kwargs):
    kwargs = dict(baked_good_kwargs)
    del kwargs["allergens"]
    return kwargs


def test_create_baked_good_should_return_baked_good(client, baked_good_kwargs):
    response = client.post("/baked-goods", json=baked_good_kwargs)
    assert response.status_code == 201

    baked_good = BakedGoodRead(**response.json())
    expected = baked_good_kwargs | {"id": baked_good.id, "active": True}
    assert baked_good.model_dump(mode="json") == expected


def test_create_baked_good_with_active_false_should_return_inactive_baked_good(
    client, baked_good_inactive_kwargs
):
    response = client.post("/baked-goods", json=baked_good_inactive_kwargs)
    assert response.status_code == 201
    assert response.json()["active"] is False


def test_create_baked_good_with_empty_allergens_should_return_baked_good(
    client, baked_good_empty_allergens_kwargs
):
    response = client.post("/baked-goods", json=baked_good_empty_allergens_kwargs)
    assert response.status_code == 201
    assert response.json()["allergens"] == []


def test_create_baked_good_with_missing_name_should_return_422(
    client, baked_good_missing_name_kwargs
):
    response = client.post("/baked-goods", json=baked_good_missing_name_kwargs)
    assert response.status_code == 422


def test_create_baked_good_with_whitespace_name_should_return_422(
    client, baked_good_whitespace_name_kwargs
):
    response = client.post("/baked-goods", json=baked_good_whitespace_name_kwargs)
    assert response.status_code == 422


def test_create_baked_good_with_missing_description_should_return_422(
    client, baked_good_missing_description_kwargs
):
    response = client.post("/baked-goods", json=baked_good_missing_description_kwargs)
    assert response.status_code == 422


def test_create_baked_good_with_whitespace_description_should_return_422(
    client, baked_good_whitespace_description_kwargs
):
    response = client.post(
        "/baked-goods", json=baked_good_whitespace_description_kwargs
    )
    assert response.status_code == 422


def test_create_baked_good_with_negative_purchase_cost_should_return_422(
    client, baked_good_negative_purchase_cost_kwargs
):
    response = client.post(
        "/baked-goods", json=baked_good_negative_purchase_cost_kwargs
    )
    assert response.status_code == 422


def test_create_baked_good_with_missing_purchase_cost_should_return_422(
    client, baked_good_missing_purchase_cost_kwargs
):
    response = client.post("/baked-goods", json=baked_good_missing_purchase_cost_kwargs)
    assert response.status_code == 422


def test_create_baked_good_with_purchase_cost_too_many_decimals_should_return_422(
    client, baked_good_purchase_cost_too_many_decimals_kwargs
):
    response = client.post(
        "/baked-goods", json=baked_good_purchase_cost_too_many_decimals_kwargs
    )
    assert response.status_code == 422


def test_create_baked_good_with_negative_retail_price_should_return_422(
    client, baked_good_negative_retail_price_kwargs
):
    response = client.post("/baked-goods", json=baked_good_negative_retail_price_kwargs)
    assert response.status_code == 422


def test_create_baked_good_with_missing_retail_price_should_return_422(
    client, baked_good_missing_retail_price_kwargs
):
    response = client.post("/baked-goods", json=baked_good_missing_retail_price_kwargs)
    assert response.status_code == 422


def test_create_baked_good_with_retail_price_too_many_decimals_should_return_422(
    client, baked_good_retail_price_too_many_decimals_kwargs
):
    response = client.post(
        "/baked-goods", json=baked_good_retail_price_too_many_decimals_kwargs
    )
    assert response.status_code == 422


def test_create_baked_good_with_missing_allergens_should_return_422(
    client, baked_good_missing_allergens_kwargs
):
    response = client.post("/baked-goods", json=baked_good_missing_allergens_kwargs)
    assert response.status_code == 422


def test_create_baked_good_should_persist_to_db(db_session, client, baked_good_kwargs):
    response = client.post("/baked-goods", json=baked_good_kwargs)
    baked_good = db_session.get(BakedGood, response.json()["id"])
    assert baked_good is not None
    assert baked_good.purchase_cost == Decimal("1.50")
    assert isinstance(baked_good.purchase_cost, Decimal)
    assert baked_good.retail_price == Decimal("3.25")
    assert isinstance(baked_good.retail_price, Decimal)
    assert baked_good.allergens == ["gluten", "dairy"]
