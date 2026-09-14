import calendar
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi import HTTPException

from wyrmwood_coffee.models.customer import Customer
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


@pytest.fixture
def sample_customer(db_session):
    """Creates a fake customer to test loyalty points."""
    customer = Customer(
        active=True,
        first_name="Test",
        last_name="Customer",
        email="test.customer@example.com",
        phone="555-555-5555",
        loyalty_points=0,
        loyalty_expires_at=datetime.now(UTC),
    )
    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)
    return customer


def test_calculate_taxes_and_total_with_valid_amounts_should_return_calculated_totals():
    sub, tax, total = calculate_taxes_and_total(Decimal("100.00"), Decimal("20.00"))

    assert sub == Decimal("80.00")
    assert tax == Decimal("5.60")
    assert total == Decimal("85.60")


def test_calculate_taxes_and_total_with_zero_subtotal_should_return_zeros():
    sub, tax, total = calculate_taxes_and_total(Decimal("0.00"), Decimal("0.00"))

    assert sub == Decimal("0.00")
    assert tax == Decimal("0.00")
    assert total == Decimal("0.00")


# ---------------------------------------------------------
# 2. LOYALTY POINTS (Math & Dates)
# ---------------------------------------------------------


def test_calculate_loyalty_points_and_expiration_with_valid_should_return_points():
    points, expires_at = calculate_loyalty_points_and_expiration(Decimal("15.99"))

    assert points == 15

    current_date = date.today()
    exp_year = current_date.year + 1
    exp_month = current_date.month
    _, last_day = calendar.monthrange(exp_year, exp_month)
    expected_date = datetime(exp_year, exp_month, last_day, 23, 59, 59, tzinfo=UTC)

    assert expires_at == expected_date


def test_calculate_loyalty_points_and_expiration_with_small_should_return_zero():
    points, _ = calculate_loyalty_points_and_expiration(Decimal("0.99"))
    assert points == 0


# ---------------------------------------------------------
# 3. PRICES AND SUBTOTAL (Database)
# ---------------------------------------------------------


def test_get_prices_and_subtotal_with_valid_item_should_return_subtotal(
    db_session, sample_baked_good
):
    item = PurchaseItemCreateNested(name="Test Muffin", quantity=2)

    subtotal, items = get_prices_and_subtotal(db_session, [item])

    assert subtotal == Decimal("10.00")
    assert len(items) == 1
    assert items[0].name == "Test Muffin"
    assert items[0].unit_price == Decimal("5.00")


def test_get_prices_and_subtotal_with_invalid_item_should_return_422(db_session):
    item = PurchaseItemCreateNested(name="Nonexistent Item", quantity=1)

    with pytest.raises(HTTPException) as exc:
        get_prices_and_subtotal(db_session, [item])

    assert exc.value.status_code == 422
    assert "not a valid baked good or drink" in exc.value.detail


# ---------------------------------------------------------
# 4. DISCOUNTS
# ---------------------------------------------------------


def test_calculate_discount_with_valid_promo_should_return_discount(db_session):
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


def test_calculate_discount_with_invalid_promo_should_return_404(db_session):
    with pytest.raises(HTTPException) as exc:
        calculate_discount(db_session, 9999, Decimal("100.00"))

    assert exc.value.status_code == 404
    assert "not found" in exc.value.detail


def test_calculate_discount_with_inactive_promo_should_return_422(db_session):
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


def test_calculate_discount_with_expired_promo_should_return_422(db_session):
    today = date.today()
    promo = Promotion(
        promo_code="EXPIRED",
        discount_percentage=20,
        start_date=today - timedelta(days=10),
        end_date=today - timedelta(days=5),
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


def test_process_purchase_with_valid_payload_should_return_purchase(
    db_session, sample_customer, sample_baked_good
):
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


def test_process_purchase_with_guest_customer_should_return_purchase(
    db_session, sample_baked_good
):
    payload = PurchaseCreate(
        customer_id=None,
        items=[PurchaseItemCreateNested(name=sample_baked_good.name, quantity=1)],
    )

    purchase = process_purchase(db_session, payload)

    assert purchase.customer_id is None
    assert purchase.total > 0


def test_process_purchase_with_inactive_customer_should_return_purchase(
    db_session, sample_baked_good
):
    inactive_customer = Customer(
        active=False,
        first_name="Inactive",
        last_name="User",
        email="inactive@example.com",
        phone="555-555-5556",
        loyalty_points=0,
        loyalty_expires_at=datetime.now(UTC),
    )
    db_session.add(inactive_customer)
    db_session.commit()
    db_session.refresh(inactive_customer)

    payload = PurchaseCreate(
        customer_id=inactive_customer.id,
        items=[PurchaseItemCreateNested(name=sample_baked_good.name, quantity=1)],
    )

    purchase = process_purchase(db_session, payload)

    assert purchase.customer_id == inactive_customer.id
    assert inactive_customer.loyalty_points == 0


def test_process_purchase_with_invalid_customer_should_return_404(
    db_session, sample_baked_good
):
    payload = PurchaseCreate(
        customer_id=9999,
        items=[PurchaseItemCreateNested(name="Test Muffin", quantity=1)],
    )

    with pytest.raises(HTTPException) as exc:
        process_purchase(db_session, payload)

    assert exc.value.status_code == 404
    assert "customer was not found" in exc.value.detail
