from datetime import datetime

import pytest
from sqlalchemy.exc import IntegrityError

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


def test_create_purchase_history_should_persist_to_db(
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

    assert purchase_history.id is not None
    assert purchase_history.customer_id == customer.id
    assert purchase_history.item_type == purchase_history_kwargs["item_type"]
    assert purchase_history.item_id == purchase_history_kwargs["item_id"]
    assert purchase_history.quantity == purchase_history_kwargs["quantity"]
    assert (
        purchase_history.loyalty_points_earned
        == purchase_history_kwargs["loyalty_points_earned"]
    )


def test_purchase_history_with_no_customer_should_create_guest_purchase(
    db_session,
    purchase_history_kwargs,
):
    purchase_history = PurchaseHistory(
        customer_id=None,
        **purchase_history_kwargs,
    )

    db_session.add(purchase_history)
    db_session.commit()
    db_session.refresh(purchase_history)

    assert purchase_history.id is not None
    assert purchase_history.customer_id is None


# --------------------
# Error / Invalid Responses
# --------------------


@pytest.mark.parametrize("item_type", ["food", "employee", ""])
def test_purchase_history_with_invalid_item_type_should_fail(
    db_session,
    purchase_history_kwargs,
    item_type,
):
    purchase_history = PurchaseHistory(
        customer_id=None,
        **(purchase_history_kwargs | {"item_type": item_type}),
    )

    db_session.add(purchase_history)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


@pytest.mark.parametrize("item_id", [0, -1])
def test_purchase_history_with_non_positive_item_id_should_fail(
    db_session,
    purchase_history_kwargs,
    item_id,
):
    purchase_history = PurchaseHistory(
        customer_id=None,
        **(purchase_history_kwargs | {"item_id": item_id}),
    )

    db_session.add(purchase_history)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


@pytest.mark.parametrize("quantity", [0, -1])
def test_purchase_history_with_non_positive_quantity_should_fail(
    db_session,
    purchase_history_kwargs,
    quantity,
):
    purchase_history = PurchaseHistory(
        customer_id=None,
        **(purchase_history_kwargs | {"quantity": quantity}),
    )

    db_session.add(purchase_history)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_purchase_history_with_negative_loyalty_points_should_fail(
    db_session,
    purchase_history_kwargs,
):
    purchase_history = PurchaseHistory(
        customer_id=None,
        **(purchase_history_kwargs | {"loyalty_points_earned": -1}),
    )

    db_session.add(purchase_history)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


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
    assert persisted_purchase_history.quantity == purchase_history_kwargs["quantity"]
