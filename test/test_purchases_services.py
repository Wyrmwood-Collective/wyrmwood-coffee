import calendar
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi import HTTPException

from wyrmwood_coffee.models.promotions import Promotion
from wyrmwood_coffee.models.purchase import PurchaseCreate, PurchaseItemCreateNested
from wyrmwood_coffee.services.purchases import (
    calculate_discount,
    calculate_loyalty_points_and_expiration,
    calculate_taxes_and_total,
    get_prices_and_subtotal,
    process_purchase,
)

# ---------------------------------------------------------
# 1. TAXES AND TOTAL (Pure Math)
# ---------------------------------------------------------


def test_calculate_taxes_and_total_happy():
    """Happy Path: Verifies the 7% tax and total math logic."""
    sub, tax, total = calculate_taxes_and_total(Decimal("100.00"), Decimal("20.00"))

    assert sub == Decimal("80.00")  # 100 - 20
    assert tax == Decimal("5.60")  # 80 * 0.07
    assert total == Decimal("85.60")  # 80 + 5.60


def test_calculate_taxes_and_total_sad_zero_subtotal():
    """Sad Path: Verifies zero subtotal doesn't break math or taxes."""
    sub, tax, total = calculate_taxes_and_total(Decimal("0.00"), Decimal("0.00"))

    assert sub == Decimal("0.00")
    assert tax == Decimal("0.00")
    assert total == Decimal("0.00")


# ---------------------------------------------------------
# 2. LOYALTY POINTS (Math & Dates)
# ---------------------------------------------------------


def test_calculate_loyalty_points_happy():
    """Happy Path: Verifies points are rounded down and expiration is set correctly."""
    points, expires_at = calculate_loyalty_points_and_expiration(Decimal("15.99"))

    assert points == 15

    current_date = date.today()
    exp_year = current_date.year + 1
    exp_month = current_date.month
    _, last_day = calendar.monthrange(exp_year, exp_month)
    expected_date = datetime(exp_year, exp_month, last_day, 23, 59, 59, tzinfo=UTC)

    assert expires_at == expected_date


def test_calculate_loyalty_points_sad_zero_total():
    """Sad Path: Verifies a total under $1.00 yields 0 points."""
    points, _ = calculate_loyalty_points_and_expiration(Decimal("0.99"))
    assert points == 0


# ---------------------------------------------------------
# 3. PRICES AND SUBTOTAL (Database)
# ---------------------------------------------------------


def test_get_prices_and_subtotal_happy(db_session, sample_baked_good):
    """Happy Path: Verifies the database price lookup and subtotal calculation."""
    item = PurchaseItemCreateNested(name="Test Muffin", quantity=2)

    subtotal, items = get_prices_and_subtotal(db_session, [item])

    assert subtotal == Decimal("10.00")  # 2 * 5.00
    assert len(items) == 1
    assert items[0].name == "Test Muffin"
    assert items[0].unit_price == Decimal("5.00")


def test_get_prices_and_subtotal_sad_invalid_item(db_session):
    """Sad Path: Verifies buying a non-existent item throws a 422 error."""
    item = PurchaseItemCreateNested(name="Nonexistent Item", quantity=1)

    with pytest.raises(HTTPException) as exc:
        get_prices_and_subtotal(db_session, [item])

    assert exc.value.status_code == 422
    assert "not a valid baked good or drink" in exc.value.detail


# ---------------------------------------------------------
# 4. DISCOUNTS
# ---------------------------------------------------------


def test_calculate_discount_happy(db_session):
    """Happy Path: Verifies a valid promotion calculates correctly."""
    today = date.today()
    promo = Promotion(
        promo_code="TEST20",
        discount_percentage=20,
        start_date=today - timedelta(days=1),
        end_date=today + timedelta(days=5),
        active=True,
    )
    db_session.add(promo)
    db_session.commit()

    discount = calculate_discount(db_session, promo.id, Decimal("100.00"))
    assert discount == Decimal("20.00")


def test_calculate_discount_sad_not_found(db_session):
    """Sad Path: Verifies a fake promo_id throws a 404 error."""
    with pytest.raises(HTTPException) as exc:
        calculate_discount(db_session, 9999, Decimal("100.00"))

    assert exc.value.status_code == 404
    assert "not found" in exc.value.detail


def test_calculate_discount_sad_inactive(db_session):
    """Sad Path: Verifies an inactive promotion throws a 422 error."""
    today = date.today()
    promo = Promotion(
        promo_code="INACTIVE",
        discount_percentage=20,
        start_date=today - timedelta(days=1),
        end_date=today + timedelta(days=5),
        active=False,
    )
    db_session.add(promo)
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        calculate_discount(db_session, promo.id, Decimal("100.00"))

    assert exc.value.status_code == 422
    assert "not active" in exc.value.detail


def test_calculate_discount_sad_expired(db_session):
    """Sad Path: Verifies an expired promotion throws a 422 error."""
    today = date.today()
    promo = Promotion(
        promo_code="EXPIRED",
        discount_percentage=20,
        start_date=today - timedelta(days=10),
        end_date=today - timedelta(days=5),  # Ended 5 days ago!
        active=True,
    )
    db_session.add(promo)
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        calculate_discount(db_session, promo.id, Decimal("100.00"))

    assert exc.value.status_code == 422
    assert "outside its valid dates" in exc.value.detail


# ---------------------------------------------------------
# 5. PROCESS PURCHASE INTEGRATION
# ---------------------------------------------------------


def test_process_purchase_happy(db_session, sample_customer, sample_baked_good):
    """Happy Path: Verifies all functions coordinate into a single transaction."""
    payload = PurchaseCreate(
        customer_id=sample_customer.id,
        items=[PurchaseItemCreateNested(name="Test Muffin", quantity=3)],
    )

    purchase = process_purchase(db_session, payload)

    assert purchase.subtotal == Decimal("15.00")
    assert purchase.tax == Decimal("1.05")
    assert purchase.total == Decimal("16.05")

    db_session.refresh(sample_customer)
    assert sample_customer.loyalty_points == 16


def test_process_purchase_sad_customer_not_found(db_session, sample_baked_good):
    """Sad Path: Verifies that passing a fake customer_id throws a 404."""
    payload = PurchaseCreate(
        customer_id=9999,  # Fake customer ID
        items=[PurchaseItemCreateNested(name="Test Muffin", quantity=1)],
    )

    with pytest.raises(HTTPException) as exc:
        process_purchase(db_session, payload)

    assert exc.value.status_code == 404
    assert "customer was not found" in exc.value.detail
