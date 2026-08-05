import pytest
from fastapi.testclient import TestClient

from wyrmwood_coffee.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_main_should_return_message(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
