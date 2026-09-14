from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from wyrmwood_coffee.database import get_db
from wyrmwood_coffee.main import app


def test_root_should_redirect_to_app(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/app/"


def test_health_should_return_message(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"message": "The API is running and reachable."}


def test_ready_should_return_200_when_database_is_reachable(client):
    response = client.get("/ready")
    assert response.status_code == 200


def test_ready_should_return_non_200_when_database_is_unreachable():
    def broken_get_db():
        session = MagicMock()
        session.execute.side_effect = OperationalError(
            "select 1", None, Exception("connection refused")
        )
        yield session

    app.dependency_overrides[get_db] = broken_get_db
    try:
        response = TestClient(app, raise_server_exceptions=False).get("/ready")
    finally:
        del app.dependency_overrides[get_db]

    assert response.status_code != 200
