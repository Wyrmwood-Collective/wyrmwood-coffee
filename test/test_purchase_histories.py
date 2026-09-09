from datetime import datetime

import pytest

from wyrmwood_coffee.models.customer import Customer
from wyrmwood_coffee.models.purchase_history import PurchaseHistory


@pytest.fixture()
def make_customer(db_session):
    def _make_customer():
        customer = Customer(
            active=True,
            first_name="SpongeBob",
            last_name="SquarePants",
            email="ilovegary@bikinibottom.com",
            phone="929-573-0156",
            loyalty_points=0,
            loyalty_expires_at=datetime.now(),
        )

        db_session.add(customer)
        db_session.commit()
        db_session.refresh(customer)

        return customer

    return _make_customer


@pytest.fixture()
def purchase_history_kwargs():
    return {
        "item_type": "drink",
        "item_id": 1,
        "quantity": 2,
        "loyalty_points_earned": 10,
        "purchased_at": datetime(2026, 9, 9, 10, 30),
    }


# ==========================================
# PURCHASE HISTORY
# ==========================================

# --------------------
# Successful Responses
# --------------------


def test_purchase_history_should_create_purchase_history(
    db_session,
    make_customer,
    purchase_history_kwargs,
): ...


def test_purchase_history_with_no_customer_should_create_guest_purchase(
    db_session,
    purchase_history_kwargs,
): ...


# --------------------
# Error / Invalid Responses
# --------------------

# --------------------
# Side Effects
# --------------------


def test_purchase_history_should_persist_to_db(
    db_session,
    make_customer,
    purchase_history_kwargs,
):
    customer = make_customer()

    purchase_history = PurchaseHistory(
        customer_id=customer.id,
        **purchase_history_kwargs,
    )

    db_session.add(purchase_history)
    db_session.commit()
    db_session.refresh(purchase_history)

    persisted_purchase_history = db_session.get(
        PurchaseHistory,
        purchase_history.id,
    )

    assert persisted_purchase_history is not None
    assert persisted_purchase_history.customer_id == customer.id
