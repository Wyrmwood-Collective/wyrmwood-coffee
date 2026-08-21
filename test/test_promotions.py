from decimal import Decimal

import pytest

from wyrmwood_coffee.models.promotions import Promotion, PromotionRead


@pytest.fixture
def promotion_kwargs():
    return {
        "active": True,
        "promo_code": "SUMMER_SALE",
        "discount_percentage": 50,
        "start_date": "2026-06-01",
        "end_date": "2026-06-30",
    }


@pytest.fixture
def second_promotion_kwargs(promotion_kwargs):
    return promotion_kwargs | {
        "promo_code": "WINTER_SALE",
        "discount_percentage": 25,
        "start_date": "2026-12-01",
        "end_date": "2026-12-31",
    }


@pytest.fixture
def single_promotion(
    db_session,
    promotion_kwargs,
):
    promotion = Promotion(**promotion_kwargs)

    db_session.add(promotion)
    db_session.commit()
    db_session.refresh(promotion)

    return promotion


@pytest.fixture
def promotion_missing_promo_code_kwargs(promotion_kwargs):
    kwargs = dict(promotion_kwargs)
    del kwargs["promo_code"]
    return kwargs


@pytest.fixture
def promotion_blank_promo_code_kwargs(promotion_kwargs):
    return promotion_kwargs | {"promo_code": " "}


@pytest.fixture
def promotion_numeric_promo_code_kwargs(promotion_kwargs):
    return promotion_kwargs | {"promo_code": 101}


@pytest.fixture
def promotion_lowercase_promo_code_kwargs(promotion_kwargs):
    return promotion_kwargs | {"promo_code": "summersale"}


@pytest.fixture
def promotion_invalid_character_kwargs(promotion_kwargs):
    return promotion_kwargs | {"promo_code": "!@$&*"}


@pytest.fixture
def promotion_invalid_start_date_kwargs(promotion_kwargs):
    return promotion_kwargs | {"start_date": "2006/01/03"}


@pytest.fixture
def promotion_invalid_end_date_month_first_kwargs(promotion_kwargs):
    return promotion_kwargs | {"end_date": "09-08-2003"}


@pytest.fixture
def promotion_invalid_end_date_day_middle_kwargs(promotion_kwargs):
    return promotion_kwargs | {"end_date": "2003-31-09"}


@pytest.fixture
def promotion_invalid_end_date_year_middle_kwargs(promotion_kwargs):
    return promotion_kwargs | {"end_date": "09-2009-04"}


@pytest.fixture
def promotion_start_date_after_end_date_kwargs(promotion_kwargs):
    return promotion_kwargs | {
        "start_date": "2026-04-05",
        "end_date": "2026-04-01",
    }


@pytest.fixture
def promotion_discount_too_high_kwargs(promotion_kwargs):
    return promotion_kwargs | {"discount_percentage": 101}


@pytest.fixture
def promotion_negative_discount_kwargs(promotion_kwargs):
    return promotion_kwargs | {"discount_percentage": -9}


@pytest.fixture
def promotion_non_numeric_discount_kwargs(promotion_kwargs):
    return promotion_kwargs | {"discount_percentage": "RADIO!"}


@pytest.fixture
def promotion_symbol_discount_kwargs(promotion_kwargs):
    return promotion_kwargs | {"discount_percentage": "_"}


# ==========================================
# LIST OPERATIONS
# ==========================================

# --------------------
# Successful Responses
# --------------------


def test_list_promotions_with_multiple_promotions_should_return_all_promotions(
    db_session,
    client,
    promotion_kwargs,
    second_promotion_kwargs,
):
    first_promotion = Promotion(**promotion_kwargs)
    second_promotion = Promotion(**second_promotion_kwargs)

    db_session.add_all(
        [
            first_promotion,
            second_promotion,
        ]
    )
    db_session.commit()

    response = client.get("/promotions")

    assert response.status_code == 200
    assert len(response.json()) == 2

    promo_codes = [promotion["promo_code"] for promotion in response.json()]

    assert promotion_kwargs["promo_code"] in promo_codes
    assert second_promotion_kwargs["promo_code"] in promo_codes


def test_list_promotions_with_no_promotions_should_return_empty_list(
    client,
):
    response = client.get("/promotions")

    assert response.status_code == 200
    assert response.json() == []


# ==========================================
# READ SINGLE OPERATIONS
# ==========================================

# --------------------
# Successful Responses
# --------------------


def test_get_promotion_should_return_promotion(
    client,
    single_promotion,
    promotion_kwargs,
):
    response = client.get(
        f"/promotions/{single_promotion.id}",
    )

    assert response.status_code == 200

    promotion = PromotionRead(**response.json())

    expected = promotion_kwargs | {
        "id": single_promotion.id,
        "discount_percentage": (
            f"{Decimal(str(promotion_kwargs['discount_percentage'])):.2f}"
        ),
    }

    assert promotion.model_dump(mode="json") == expected


# --------------------
# Error / Invalid Responses
# --------------------


def test_get_promotion_with_nonexistent_id_should_return_404(
    client,
):
    response = client.get("/promotions/999999")

    assert response.status_code == 404


# ==========================================
# CREATE OPERATIONS
# ==========================================

# --------------------
# Successful Responses
# --------------------


def test_create_promotion_should_return_promotion(
    client,
    promotion_kwargs,
):
    response = client.post(
        "/promotions",
        json=promotion_kwargs,
    )

    assert response.status_code == 201

    promotion = PromotionRead(**response.json())

    expected = promotion_kwargs | {
        "id": promotion.id,
        "discount_percentage": (
            f"{Decimal(str(promotion_kwargs['discount_percentage'])):.2f}"
        ),
    }

    assert promotion.model_dump(mode="json") == expected


# --------------------
# Error / Invalid Responses
# --------------------


def test_create_promotion_with_missing_promo_code_should_return_422(
    client,
    promotion_missing_promo_code_kwargs,
):
    response = client.post(
        "/promotions",
        json=promotion_missing_promo_code_kwargs,
    )

    assert response.status_code == 422


def test_create_promotion_with_duplicate_promo_code_should_return_409(
    client,
    promotion_kwargs,
):
    first_response = client.post(
        "/promotions",
        json=promotion_kwargs,
    )

    assert first_response.status_code == 201

    duplicate_response = client.post(
        "/promotions",
        json=promotion_kwargs,
    )

    assert duplicate_response.status_code == 409


def test_create_promotion_with_blank_promo_code_should_return_422(
    client,
    promotion_blank_promo_code_kwargs,
):
    response = client.post(
        "/promotions",
        json=promotion_blank_promo_code_kwargs,
    )

    assert response.status_code == 422


def test_create_promotion_with_numeric_promo_code_should_return_422(
    client,
    promotion_numeric_promo_code_kwargs,
):
    response = client.post(
        "/promotions",
        json=promotion_numeric_promo_code_kwargs,
    )

    assert response.status_code == 422


def test_create_promotion_with_lowercase_promo_code_should_return_422(
    client,
    promotion_lowercase_promo_code_kwargs,
):
    response = client.post(
        "/promotions",
        json=promotion_lowercase_promo_code_kwargs,
    )

    assert response.status_code == 422


def test_create_promotion_with_invalid_promo_code_character_should_return_422(
    client,
    promotion_invalid_character_kwargs,
):
    response = client.post(
        "/promotions",
        json=promotion_invalid_character_kwargs,
    )

    assert response.status_code == 422


def test_create_promotion_with_invalid_start_date_should_return_422(
    client,
    promotion_invalid_start_date_kwargs,
):
    response = client.post(
        "/promotions",
        json=promotion_invalid_start_date_kwargs,
    )

    assert response.status_code == 422


def test_create_promotion_with_month_first_end_date_should_return_422(
    client,
    promotion_invalid_end_date_month_first_kwargs,
):
    response = client.post(
        "/promotions",
        json=promotion_invalid_end_date_month_first_kwargs,
    )

    assert response.status_code == 422


def test_create_promotion_with_invalid_end_date_day_order_should_return_422(
    client,
    promotion_invalid_end_date_day_middle_kwargs,
):
    response = client.post(
        "/promotions",
        json=promotion_invalid_end_date_day_middle_kwargs,
    )

    assert response.status_code == 422


def test_create_promotion_with_invalid_end_date_year_order_should_return_422(
    client,
    promotion_invalid_end_date_year_middle_kwargs,
):
    response = client.post(
        "/promotions",
        json=promotion_invalid_end_date_year_middle_kwargs,
    )

    assert response.status_code == 422


def test_create_promotion_with_start_date_after_end_date_should_return_422(
    client,
    promotion_start_date_after_end_date_kwargs,
):
    response = client.post(
        "/promotions",
        json=promotion_start_date_after_end_date_kwargs,
    )

    assert response.status_code == 422


def test_create_promotion_with_discount_too_high_should_return_422(
    client,
    promotion_discount_too_high_kwargs,
):
    response = client.post(
        "/promotions",
        json=promotion_discount_too_high_kwargs,
    )

    assert response.status_code == 422


def test_create_promotion_with_negative_discount_should_return_422(
    client,
    promotion_negative_discount_kwargs,
):
    response = client.post(
        "/promotions",
        json=promotion_negative_discount_kwargs,
    )

    assert response.status_code == 422


def test_create_promotion_with_non_numeric_discount_should_return_422(
    client,
    promotion_non_numeric_discount_kwargs,
):
    response = client.post(
        "/promotions",
        json=promotion_non_numeric_discount_kwargs,
    )

    assert response.status_code == 422


def test_create_promotion_with_symbol_discount_should_return_422(
    client,
    promotion_symbol_discount_kwargs,
):
    response = client.post(
        "/promotions",
        json=promotion_symbol_discount_kwargs,
    )

    assert response.status_code == 422


# --------------------
# Side Effects
# --------------------


def test_create_promotion_should_persist_to_db(
    db_session,
    client,
    promotion_kwargs,
):
    response = client.post(
        "/promotions",
        json=promotion_kwargs,
    )

    promotion = db_session.get(
        Promotion,
        response.json()["id"],
    )

    assert promotion is not None
    assert promotion.promo_code == promotion_kwargs["promo_code"]
    assert promotion.discount_percentage == Decimal("50.00")
    assert promotion.active == promotion_kwargs["active"]
