import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from wyrmwood_coffee.database import get_db
from wyrmwood_coffee.main import app
from wyrmwood_coffee.models.ingredient import Base

# ---------------------------------------------------------
# Create ONE shared in-memory SQLite database
# ---------------------------------------------------------
engine = create_engine(
    "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
)

TestingSessionLocal = sessionmaker(bind=engine)

# Create tables ONCE
Base.metadata.create_all(bind=engine)


# ---------------------------------------------------------
# Apply DB override BEFORE TestClient is created
# ---------------------------------------------------------
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


# ---------------------------------------------------------
# Your teammate’s fixture — unchanged
# ---------------------------------------------------------
@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------
# Tests
# ---------------------------------------------------------
def test_create_ingredient(client):
    payload = {
        "name": "Sugar",
        "vendor": "Domino",
        "purchasing_cost": 3.5,
        "unit_amount": 1000,
        "unit_of_measure": "g",
        "allergens": ["corn"],
    }

    response = client.post("/ingredients", json=payload)
    assert response.status_code == 200
    assert response.json()["name"] == "Sugar"
