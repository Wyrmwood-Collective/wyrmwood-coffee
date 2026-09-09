def test_root_should_redirect_to_app(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/app/"


def test_health_should_return_message(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Wyrmwood Coffee!"}
