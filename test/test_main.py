def test_main_should_return_message(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Wyrmwood Coffee!"}
