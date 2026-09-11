from wyrmwood_coffee.models.purchase import Purchase


def test_create_purchase_with_valid_payload_should_return_purchase(
    db_session, client, sample_baked_good
):
    payload = {"items": [{"name": sample_baked_good.name, "quantity": 1}]}
    response = client.post("/purchases", json=payload)

    assert response.status_code == 201
    assert response.json()["total"] is not None


def test_create_purchase_with_missing_items_should_return_422(db_session, client):
    payload = {"items": []}
    response = client.post("/purchases", json=payload)

    assert response.status_code == 422


def test_create_purchase_should_persist_to_db(db_session, client, sample_baked_good):
    payload = {"items": [{"name": sample_baked_good.name, "quantity": 1}]}
    response = client.post("/purchases", json=payload)

    assert response.status_code == 201

    purchase_id = response.json()["id"]
    db_purchase = db_session.get(Purchase, purchase_id)
    assert db_purchase is not None
