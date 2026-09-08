from datetime import datetime

import pytest
from sqlalchemy.exc import IntegrityError

from wyrmwood_coffee.models.customer import Customer
from wyrmwood_coffee.models.loyalty_point_audit import LoyaltyPointAudit


@pytest.fixture
def loyalty_point_audit_customer(db_session):
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


@pytest.fixture
def loyalty_point_audit_kwargs(loyalty_point_audit_customer):
    return {
        "customer_id": loyalty_point_audit_customer.id,
        "points_expired": 10,
        "reason": "Points expired",
        "expired_at": datetime.now(),
    }


@pytest.fixture
def single_loyalty_point_audit(
    db_session,
    loyalty_point_audit_kwargs,
):
    audit = LoyaltyPointAudit(**loyalty_point_audit_kwargs)

    db_session.add(audit)
    db_session.commit()
    db_session.refresh(audit)

    return audit


# ==========================================
# MODEL CONSTRAINTS
# ==========================================

# --------------------
# Successful Responses
# --------------------


def test_create_loyalty_point_audit_should_persist_to_db(
    db_session,
    loyalty_point_audit_kwargs,
):
    audit = LoyaltyPointAudit(**loyalty_point_audit_kwargs)

    db_session.add(audit)
    db_session.commit()
    db_session.refresh(audit)

    assert audit.id is not None
    assert audit.customer_id == loyalty_point_audit_kwargs["customer_id"]
    assert audit.points_expired == loyalty_point_audit_kwargs["points_expired"]
    assert audit.reason == loyalty_point_audit_kwargs["reason"]


# --------------------
# Error / Invalid Responses
# --------------------


def test_create_loyalty_point_audit_without_points_expired_should_fail(
    db_session,
    loyalty_point_audit_kwargs,
):
    kwargs = loyalty_point_audit_kwargs | {"points_expired": None}
    audit = LoyaltyPointAudit(**kwargs)

    db_session.add(audit)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_create_loyalty_point_audit_without_reason_should_fail(
    db_session,
    loyalty_point_audit_kwargs,
):
    kwargs = loyalty_point_audit_kwargs | {"reason": None}
    audit = LoyaltyPointAudit(**kwargs)

    db_session.add(audit)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_create_loyalty_point_audit_without_expired_at_should_fail(
    db_session,
    loyalty_point_audit_kwargs,
):
    kwargs = loyalty_point_audit_kwargs | {"expired_at": None}
    audit = LoyaltyPointAudit(**kwargs)

    db_session.add(audit)

    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


# --------------------
# Side Effects
# --------------------


def test_delete_customer_should_preserve_loyalty_point_audit(
    db_session,
    loyalty_point_audit_customer,
    single_loyalty_point_audit,
):
    audit_id = single_loyalty_point_audit.id

    db_session.delete(loyalty_point_audit_customer)
    db_session.commit()

    db_session.expire_all()

    audit = db_session.get(
        LoyaltyPointAudit,
        audit_id,
    )

    assert audit is not None
    assert audit.customer_id is None


def test_loyalty_point_audit_should_use_timezone_aware_timestamps(
    single_loyalty_point_audit,
):
    assert single_loyalty_point_audit.expired_at.tzinfo is not None
    assert single_loyalty_point_audit.created_at.tzinfo is not None
