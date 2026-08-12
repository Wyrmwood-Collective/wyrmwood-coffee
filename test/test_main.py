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
    assert response.status_code == 201
    assert response.json()["name"] == "Sugar"
