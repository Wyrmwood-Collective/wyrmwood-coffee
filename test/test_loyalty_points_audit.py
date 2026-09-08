from datetime import datetime

import pytest
from sqlalchemy import select

from wyrmwood_coffee.models import Customer
from wyrmwood_coffee.models.loyalty_point import LoyaltyPointAudit


@pytest.fixture
def expired_customer(db_session):
    customer = Customer(
        active=True,
        first_name="Isabella",
        last_name="Rossi",
        email="issabella.rossi@example.com",
        phone=None,
        loyalty_points=75,
        loyalty_expires_at=datetime(2023, 12, 1),
    )
    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)

    return customer


@pytest.fixture
def loyalty_point_audit(db_session, expired_customer):
    audit = LoyaltyPointAudit(
        customer_id=expired_customer.id,
        points_expired=expired_customer.loyalty_points,
        expired_at=expired_customer.loyalty_expires_at,
    )
    db_session.add(audit)
    db_session.commit()
    db_session.refresh(audit)

    return audit


def test_loyalty_point_audit_should_persist_to_db(db_session, loyalty_point_audit):
    persisted_audit = db_session.scalar(
        select(LoyaltyPointAudit).where(LoyaltyPointAudit.id == loyalty_point_audit.id)
    )

    assert persisted_audit is not None


def test_loyalty_point_audit_should_reference_customer(
    loyalty_point_audit, expired_customer
):
    assert loyalty_point_audit.customer_id == expired_customer.id


def test_loyalty_point_audit_should_record_expired_points(
    loyalty_point_audit, expired_customer
):
    assert loyalty_point_audit.points_expired == 75
    assert loyalty_point_audit.expired_at == expired_customer.loyalty_expires_at
