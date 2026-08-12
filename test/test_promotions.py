import pytest


@pytest.fixture
def promotion_data():
    """Return a valid promotion request payload."""
    return {
        "active": True,
        "promo_code": "SUMMER_SALE",
        "discount_percentage": 50,
        "start_date": "2026-06-01",
        "end_date": "2026-06-30",
    }


def test_create_promotion_valid_entry(client, promotion_data):
    """Verify that a valid promotion is successfully created."""

    response = client.post(
        "/promotions",
        json=promotion_data,
    )

    # A valid promotion should be created successfully.
    assert response.status_code == 201


def test_create_promotion_no_entry(
    client,
    promotion_data,
):
    """Verify that an empty promo code is rejected."""
    promotion_data["promo_code"] = ""

    response = client.post(
        "/promotions",
        json=promotion_data,
    )

    assert response.status_code == 422


def test_create_promotion_duplicate_entry(client, promotion_data):
    """Verify that a duplicate promo code returns a 409 conflict."""

    # Create the promotion.
    first_response = client.post(
        "/promotions",
        json=promotion_data,
    )

    assert first_response.status_code == 201

    # Attempt to create another promotion with the same promo code.
    duplicate_response = client.post(
        "/promotions",
        json=promotion_data,
    )

    assert duplicate_response.status_code == 409


def test_create_promotion_space_entry(
    client,
    promotion_data,
):
    """Verify that a promo code containing only spaces is rejected."""
    promotion_data["promo_code"] = " "

    response = client.post(
        "/promotions",
        json=promotion_data,
    )
    assert response.status_code == 422


def test_create_promotion_number_entry(
    client,
    promotion_data,
):
    """Verify that a numeric promo code is rejected."""
    promotion_data["promo_code"] = 101

    response = client.post(
        "/promotions",
        json=promotion_data,
    )

    assert response.status_code == 422


def test_create_promotion_lowercase_entry(
    client,
    promotion_data,
):
    """Verify that a lowercase promo code is rejected."""
    promotion_data["promo_code"] = "summersale"

    response = client.post(
        "/promotions",
        json=promotion_data,
    )

    assert response.status_code == 422


def test_create_promotion_invalid_character(
    client,
    promotion_data,
):
    """Verify that unsupported characters in a promo code are rejected."""
    promotion_data["promo_code"] = "!@$&*"

    response = client.post(
        "/promotions",
        json=promotion_data,
    )

    assert response.status_code == 422


def test_create_promotion_invalid_start_date_backslash(
    client,
    promotion_data,
):
    """Verify that a start date using slashes is rejected."""
    promotion_data["start_date"] = "2006/01/03"

    response = client.post(
        "/promotions",
        json=promotion_data,
    )

    assert response.status_code == 422


def test_create_promotion_invalid_end_date_start_with_month(
    client,
    promotion_data,
):
    """Verify that an end date beginning with the month is rejected."""
    promotion_data["end_date"] = "09-08-2003"

    response = client.post(
        "/promotions",
        json=promotion_data,
    )

    assert response.status_code == 422


def test_create_promotion_invalid_end_date_day_in_middle(
    client,
    promotion_data,
):
    """Verify that an end date with an invalid month/day order is rejected."""
    promotion_data["end_date"] = "2003-31-09"

    response = client.post(
        "/promotions",
        json=promotion_data,
    )

    assert response.status_code == 422


def test_create_promotion_invalid_end_date_year_in_middle(
    client,
    promotion_data,
):
    """Verify that an end date with the year in the middle is rejected."""
    promotion_data["end_date"] = "09-2009-04"

    response = client.post(
        "/promotions",
        json=promotion_data,
    )

    assert response.status_code == 422


def test_create_promotion_start_date_after_end_date(
    client,
    promotion_data,
):
    """Verify that an end date before the start date is rejected."""
    promotion_data["start_date"] = "2026-04-05"
    promotion_data["end_date"] = "2026-04-01"

    response = client.post(
        "/promotions",
        json=promotion_data,
    )

    assert response.status_code == 422


def test_create_promotion_discount_too_high(
    client,
    promotion_data,
):
    """Verify that a discount percentage greater than 100 is rejected."""
    promotion_data["discount_percentage"] = 101

    response = client.post(
        "/promotions",
        json=promotion_data,
    )

    assert response.status_code == 422


def test_create_promotion_discount_too_low(
    client,
    promotion_data,
):
    """Verify that a discount percentage below zero is rejected."""
    promotion_data["discount_percentage"] = -9

    response = client.post(
        "/promotions",
        json=promotion_data,
    )

    assert response.status_code == 422


def test_create_promotion_discount_percentage_not_numeric_letter(
    client,
    promotion_data,
):
    """Verify that a letter discount percentage is rejected."""
    promotion_data["discount_percentage"] = "RADIO!"

    response = client.post(
        "/promotions",
        json=promotion_data,
    )

    assert response.status_code == 422


def test_create_promotion_discount_percentage_not_numeric_symbol(
    client,
    promotion_data,
):
    """Verify that a symbolic discount percentage is rejected."""
    promotion_data["discount_percentage"] = "_"

    response = client.post(
        "/promotions",
        json=promotion_data,
    )

    assert response.status_code == 422
