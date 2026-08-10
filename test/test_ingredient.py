from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from wyrmwood_coffee.database import get_db
from wyrmwood_coffee.main import app
from wyrmwood_coffee.models.ingredient import Base

# ---------------------------------------------------------
# TEST DATABASE (SQLite in-memory)
# ---------------------------------------------------------
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables for tests
Base.metadata.create_all(bind=engine)


# ---------------------------------------------------------
# Override get_db for tests
# ---------------------------------------------------------
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# ---------------------------------------------------------
# TESTS
# ---------------------------------------------------------


def test_api_create_ingredient():
    payload = {
        "name": "Sugar",
        "vendor": "Domino",
        "purchasing_cost": 3.5,
        "unit_amount": 1000,
        "unit_of_measure": "ml",
        "allergens": ["corn"],
    }

    response = client.post("/ingredients", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["name"] == "Sugar"
    assert data["vendor"] == "Domino"
    assert data["allergens"] == ["corn"]


def test_api_get_ingredient_by_id():
    # First create ingredient
    payload = {
        "name": "Salt",
        "vendor": "Morton",
        "purchasing_cost": 2.0,
        "unit_amount": 500,
        "unit_of_measure": "g",
        "allergens": [],
    }

    create_response = client.post("/ingredients", json=payload)
    ingredient_id = create_response.json()["id"]

    # Now fetch it
    response = client.get(f"/ingredients/{ingredient_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["name"] == "Salt"
    assert data["vendor"] == "Morton"


def test_api_get_all_ingredients():
    response = client.get("/ingredients")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
