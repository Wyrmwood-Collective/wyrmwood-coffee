def test_create_promotion_valid_entry(client):
    """Verify that a valid promotion is successfully created."""

    response = client.post(
        "/promotions",
        json={
            "active": True,
            "promo_code": "SUMMER_SALE ",
            "discount_percentage": 50,
            "start_date": "2026-06-01",
            "end_date": "2026-06-30",
        },
    )

    # A valid promotion should be created successfully.
    assert response.status_code == 201

    data = response.json()

    # Verify that the returned promotion contains the expected values.
    assert data["promo_code"] == "SUMMER_SALE "
    assert data["discount_percentage"] == "50.00"
    assert data["active"] is True
    assert data["start_date"] == "2026-06-01"
    assert data["end_date"] == "2026-06-30"

    # The database should generate an ID for the new promotion.
    assert data["id"] is not None


def test_create_promotion_no_entry(client):
    """Verify that an empty promo code is rejected."""

    response = client.post(
        "/promotions",
        json={
            "active": True,
            "promo_code": "",
            "discount_percentage": 50,
            "start_date": "2026-06-01",
            "end_date": "2026-06-30",
        },
    )

    assert response.status_code == 422
    assert (
        "Promo code must contain at least one letter."
        in response.json()["detail"][0]["msg"]
    )


def test_create_promotion_duplicate_entry(client):
    """Verify that a duplicate promo code returns a conflict response."""

    promotion_data = {
        "active": True,
        "promo_code": "SUMMER_SALE",
        "discount_percentage": 50,
        "start_date": "2026-06-01",
        "end_date": "2026-06-30",
    }

    # Create the promotion for the first time.
    first_response = client.post(
        "/promotions",
        json=promotion_data,
    )

    assert first_response.status_code == 201

    # Attempt to create the same promo code again.
    duplicate_response = client.post(
        "/promotions",
        json=promotion_data,
    )

    assert duplicate_response.status_code == 409
    assert (
        duplicate_response.json()["detail"]
        == "A Promotion with that name already exists."
    )


def test_create_promotion_space_entry(client):
    """Verify that a promo code containing only spaces is rejected."""

    response = client.post(
        "/promotions",
        json={
            "active": True,
            "promo_code": " ",
            "discount_percentage": 50,
            "start_date": "2026-06-01",
            "end_date": "2026-06-30",
        },
    )

    assert response.status_code == 422
    assert (
        "Promo code must contain at least one letter."
        in response.json()["detail"][0]["msg"]
    )


def test_create_promotion_number_entry(client):
    """Verify that a promo code containing only numbers is rejected."""

    response = client.post(
        "/promotions",
        json={
            "active": True,
            "promo_code": "123",
            "discount_percentage": 50,
            "start_date": "2026-06-01",
            "end_date": "2026-06-30",
        },
    )

    assert response.status_code == 422
    assert (
        "Promo code may contain only letters, spaces, and underscores"
        in response.json()["detail"][0]["msg"]
    )


def test_create_promotion_lowercase_entry(client):
    """Verify that lowercase promo codes are rejected."""

    response = client.post(
        "/promotions",
        json={
            "active": True,
            "promo_code": "summersale",
            "discount_percentage": 50,
            "start_date": "2026-06-01",
            "end_date": "2026-06-30",
        },
    )

    assert response.status_code == 422
    assert "Promo code must be in uppercase." in response.json()["detail"][0]["msg"]


def test_create_promotion_invalid_character(client):
    """Verify that unsupported special characters in a promo code are rejected."""

    response = client.post(
        "/promotions",
        json={
            "active": True,
            "promo_code": "$#%",
            "discount_percentage": 50,
            "start_date": "2026-06-01",
            "end_date": "2026-06-30",
        },
    )

    assert response.status_code == 422
    assert (
        "Promo code may contain only letters, spaces, and underscores"
        in response.json()["detail"][0]["msg"]
    )


def test_create_promotion_invalid_start_date(client):
    """Verify that an unsupported start-date format is rejected."""

    response = client.post(
        "/promotions",
        json={
            "active": True,
            "promo_code": "SUMMERSALE_",
            "discount_percentage": 50,
            "start_date": "August 12, 2026",
            "end_date": "2026-06-30",
        },
    )

    assert response.status_code == 422
    assert (
        "Date must use YYYY-MM-DD, YYYY/MM/DD, MM-DD-YYYY, "
        "MM/DD/YYYY, YYYY/DD/MM, or YYYY-DD-MM." in response.json()["detail"][0]["msg"]
    )


def test_create_promotion_invalid_end_date(client):
    """Verify that an unsupported end-date format is rejected."""

    response = client.post(
        "/promotions",
        json={
            "active": True,
            "promo_code": "SUMMERSALE_",
            "discount_percentage": 50,
            "start_date": "08-09-2026",
            "end_date": "August, 30, 2026",
        },
    )

    assert response.status_code == 422
    assert (
        "Date must use YYYY-MM-DD, YYYY/MM/DD, MM-DD-YYYY, "
        "MM/DD/YYYY, YYYY/DD/MM, or YYYY-DD-MM." in response.json()["detail"][0]["msg"]
    )


def test_create_promotion_start_date_after_end_date(client):
    """Verify that an end date before the start date is rejected."""

    response = client.post(
        "/promotions",
        json={
            "active": True,
            "promo_code": "GOLIONS",
            "discount_percentage": 20,
            "start_date": "08-09-2026",
            "end_date": "08-08-2026",
        },
    )

    assert response.status_code == 422
    assert "End date must be after start date." in response.json()["detail"][0]["msg"]


def test_create_promotion_discount_percentage_out_of_bounds_low(client):
    """Verify that a discount below zero is rejected."""

    response = client.post(
        "/promotions",
        json={
            "active": True,
            "promo_code": "GOLIONS",
            "discount_percentage": -76,
            "start_date": "08-09-2026",
            "end_date": "08-10-2026",
        },
    )

    assert response.status_code == 422
    assert (
        "Discount percentage must be between 0 and 100."
        in response.json()["detail"][0]["msg"]
    )


def test_create_promotion_discount_percentage_out_of_bounds_high(client):
    """Verify that a discount above 100 is rejected."""

    response = client.post(
        "/promotions",
        json={
            "active": True,
            "promo_code": "GOLIONS",
            "discount_percentage": 101,
            "start_date": "08-09-2026",
            "end_date": "08-10-2026",
        },
    )

    assert response.status_code == 422
    assert (
        "Discount percentage must be between 0 and 100."
        in response.json()["detail"][0]["msg"]
    )


def test_create_promotion_discount_percentage_not_numeric(client):
    """Verify that a nonnumeric discount percentage is rejected."""

    response = client.post(
        "/promotions",
        json={
            "active": True,
            "promo_code": "GOLIONS",
            "discount_percentage": "POOH",
            "start_date": "08-09-2026",
            "end_date": "08-10-2026",
        },
    )

    assert response.status_code == 422
    assert (
        "Discount percentage must be between 0 and 100."
        in response.json()["detail"][0]["msg"]
    )
