from decimal import Decimal

from wyrmwood_coffee.models.purchase import PurchaseCreate, PurchaseItemCreateNested
from wyrmwood_coffee.services.purchases import process_purchase


def test_process_purchase_calculates_totals_and_taxes_correctly(
    db_session, sample_baked_good
):
    # Set a known price for the test
    sample_baked_good.retail_price = Decimal("10.00")
    db_session.commit()

    payload = PurchaseCreate(
        items=[PurchaseItemCreateNested(name=sample_baked_good.name, quantity=2)]
    )

    purchase = process_purchase(db_session, payload)

    # Subtotal: $20.00, Tax (7%): $1.40, Total: $21.40
    assert purchase.subtotal == Decimal("20.00")
    assert purchase.tax == Decimal("1.40")
    assert purchase.total == Decimal("21.40")


def test_process_purchase_calculates_loyalty_points(
    db_session, sample_baked_good, sample_customer
):
    sample_baked_good.retail_price = Decimal("10.50")
    db_session.commit()

    initial_points = sample_customer.loyalty_points

    payload = PurchaseCreate(
        customer_id=sample_customer.id,
        items=[PurchaseItemCreateNested(name=sample_baked_good.name, quantity=1)],
    )

    purchase = process_purchase(db_session, payload)

    # Subtotal: $10.50, Tax: $0.74, Total: $11.24
    # Points earned = floor(11.24) = 11
    assert purchase.total == Decimal("11.24")

    db_session.refresh(sample_customer)
    assert sample_customer.loyalty_points == initial_points + 11
    assert sample_customer.loyalty_expires_at is not None
