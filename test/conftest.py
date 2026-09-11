import itertools
import os
import subprocess
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import cast

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from wyrmwood_coffee.database import Base, get_db
from wyrmwood_coffee.main import app
from wyrmwood_coffee.models.baked_goods import BakedGood
from wyrmwood_coffee.models.customer import Customer
from wyrmwood_coffee.models.employee import Employee
from wyrmwood_coffee.models.ingredient import Ingredient
from wyrmwood_coffee.models.vendor import Vendor, VendorContact
from wyrmwood_coffee.security import hash_password
from wyrmwood_coffee.settings import settings


def create_test_database(db_url: str) -> None:
    url = make_url(cast(str, settings.test_database_url))

    env = os.environ.copy()
    if url.password:
        env["PGPASSWORD"] = url.password

    args = ["createdb"]
    if url.username:
        args.extend(["-U", url.username])
    if url.host:
        args.extend(["-h", url.host])
    if url.port:
        args.extend(["-p", str(url.port)])
    if url.database:
        args.append(url.database)

    subprocess.run(args, env=env, check=True)


def destroy_test_database(db_name: str) -> None:
    url = make_url(cast(str, settings.test_database_url))

    env = os.environ.copy()
    if url.password:
        env["PGPASSWORD"] = url.password

    args = ["dropdb"]
    if url.username:
        args.extend(["-U", url.username])
    if url.host:
        args.extend(["-h", url.host])
    if url.port:
        args.extend(["-p", str(url.port)])
    if url.database:
        args.append(url.database)

    subprocess.run(args, env=env, check=True)


@pytest.fixture(scope="session")
def db_engine(request):
    db_name = cast(str, settings.test_database_url).split("/")[-1]
    db_url = cast(str, settings.test_database_url)
    create_test_database(db_name)
    request.addfinalizer(lambda: destroy_test_database(db_name))

    engine = create_engine(db_url)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()

    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session, transaction):
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    yield TestClient(app)
    del app.dependency_overrides[get_db]


@pytest.fixture
def employee_kwargs():
    return {
        "active": True,
        "first_name": "Ada",
        "last_name": "Lovelace",
        "role": "employee",
        "hourly_rate": 18.5,
        "hire_date": "2024-01-15",
        "username": "alovelace",
        "password": "Password1!",
    }


@pytest.fixture
def employee_inactive_kwargs(employee_kwargs):
    return employee_kwargs | {"active": False}


def _persist_employee(db_session, kwargs):
    term_date = kwargs.get("term_date")
    employee = Employee(
        active=kwargs["active"],
        first_name=kwargs["first_name"],
        last_name=kwargs["last_name"],
        role=kwargs["role"],
        hourly_rate=Decimal(str(kwargs["hourly_rate"])),
        hire_date=date.fromisoformat(kwargs["hire_date"]),
        term_date=date.fromisoformat(term_date) if term_date else None,
        username=kwargs["username"],
        password=hash_password(kwargs["password"]),
    )
    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)
    return employee


@pytest.fixture
def persist_employee(db_session):
    def persist(kwargs):
        return _persist_employee(db_session, kwargs)

    return persist


@pytest.fixture()
def make_vendor(db_session):
    counter = itertools.count(1)

    def _make_vendor(**kwargs):
        n = next(counter)
        contact_data = kwargs.pop(
            "contact",
            {
                "name": "Eugene Krabs",
                "role": "Owner",
                "email": f"moneymoneymoney+{n}@bikinibottom.com",
                "phone": f"810-337-{n:04d}",
            },
        )
        defaults = {
            "name": f"Krusty Krab Supply Co {n}",
            "contacts": [VendorContact(**contact_data)],
        }
        defaults.update(kwargs)
        vendor = Vendor(**defaults)
        db_session.add(vendor)
        db_session.commit()
        db_session.refresh(vendor)
        return vendor

    return _make_vendor


@pytest.fixture()
def make_ingredient(db_session, make_vendor):
    counter = itertools.count(1)

    def _make_ingredient(**kwargs):
        n = next(counter)
        defaults = {
            "name": f"Jellyfish Jelly {n}",
            "purchasing_cost": 3.0,
            "unit_amount": 5,
            "unit_of_measure": "L",
            "allergens": ["seafood"],
            "vendor_id": kwargs.get("vendor_id") or make_vendor().id,
        }
        defaults.update(kwargs)
        ingredient = Ingredient(**defaults)
        db_session.add(ingredient)
        db_session.commit()
        db_session.refresh(ingredient)
        return ingredient

    return _make_ingredient


@pytest.fixture
def sample_baked_good(db_session):
    """Creates a fake baked good to use in purchase tests."""
    bg = BakedGood(
        name="Test Muffin",
        description="A delicious test muffin.",
        purchase_cost=Decimal("2.00"),
        retail_price=Decimal("5.00"),
    )
    db_session.add(bg)
    db_session.commit()
    db_session.refresh(bg)
    return bg


@pytest.fixture
def sample_customer(db_session):
    """Creates a fake customer to test loyalty points."""
    customer = Customer(
        active=True,  # Required by your DB
        first_name="Test",
        last_name="Customer",
        email="test.customer@example.com",
        phone="555-555-5555",  # Changed from phone_number to phone!
        loyalty_points=0,
        loyalty_expires_at=datetime.now(UTC),  # Required by your DB
    )
    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)
    return customer
