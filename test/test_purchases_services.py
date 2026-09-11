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


def test_calculate_taxes_and_total_pure_math():
    """Unit Test: Verifies the 7% tax and total math logic completely isolated."""
    sub, tax, total = calculate_taxes_and_total(Decimal("100.00"), Decimal("20.00"))

    assert sub == Decimal("80.00")  # 100 - 20
    assert tax == Decimal("5.60")  # 80 * 0.07
    assert total == Decimal("85.60")  # 80 + 5.60


def test_calculate_loyalty_points_and_expiration_logic():
    """
    Unit Test: Verifies points are rounded down and expiration is exactly
    end of next year's month.
    """
    points, expires_at = calculate_loyalty_points_and_expiration(Decimal("15.99"))

    # 15.99 should round down to 15 points
    assert points == 15

    # Calculate what the expected date should be
    current_date = date.today()
    exp_year = current_date.year + 1
    exp_month = current_date.month
    _, last_day = calendar.monthrange(exp_year, exp_month)
    expected_date = datetime(exp_year, exp_month, last_day, 23, 59, 59, tzinfo=UTC)

    assert expires_at == expected_date


def test_get_prices_and_subtotal_bulk_lookup(db_session, sample_baked_good):
    """Unit Test: Verifies the database price lookup and subtotal calculation."""
    item = PurchaseItemCreateNested(name="Test Muffin", quantity=2)

    subtotal, items = get_prices_and_subtotal(db_session, [item])

    assert subtotal == Decimal("10.00")  # 2 * 5.00
    assert len(items) == 1
    assert items[0].name == "Test Muffin"
    assert items[0].unit_price == Decimal("5.00")


def test_get_prices_and_subtotal_invalid_item_fails(db_session):
    """Unit Test: Verifies buying a non-existent item throws a 422 error."""
    item = PurchaseItemCreateNested(name="Nonexistent Item", quantity=1)

    with pytest.raises(HTTPException) as exc:
        get_prices_and_subtotal(db_session, [item])

    assert exc.value.status_code == 422
    assert "not a valid baked good or drink" in exc.value.detail


def test_calculate_discount_with_valid_promo(db_session):
    """
    Unit Test: Verifies a valid promotion correctly calculates percentage
    discounts.
    """
    today = date.today()
    promo = Promotion(
        promo_code="TEST20",  # <--- Add this!
        discount_percentage=20,
        start_date=today - timedelta(days=1),
        end_date=today + timedelta(days=5),
        active=True,
    )
    db_session.add(promo)
    db_session.commit()

    discount = calculate_discount(db_session, promo.id, Decimal("100.00"))
    assert discount == Decimal("20.00")  # 20% of 100


def test_calculate_discount_inactive_promo_fails(db_session):
    """Unit Test: Verifies an inactive promotion throws a 422 error."""
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


def test_process_purchase_full_integration(
    db_session, sample_customer, sample_baked_good
):
    """
    Integration Test: Verifies all helper functions coordinate correctly
    into a single transaction.
    """
    payload = PurchaseCreate(
        customer_id=sample_customer.id,
        items=[PurchaseItemCreateNested(name="Test Muffin", quantity=3)],
    )

    purchase = process_purchase(db_session, payload)

    # Math check: 3 * 5.00 = 15.00 subtotal. 15.00 * 0.07 = 1.05 tax. 16.05 total.
    assert purchase.subtotal == Decimal("15.00")
    assert purchase.tax == Decimal("1.05")
    assert purchase.total == Decimal("16.05")

    # Loyalty check: 16.05 -> 16 points added to the customer's balance
    db_session.refresh(sample_customer)
    assert sample_customer.loyalty_points == 16
