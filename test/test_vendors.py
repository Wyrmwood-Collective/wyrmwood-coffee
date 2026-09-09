import pytest
from sqlalchemy import func, select

from wyrmwood_coffee.models.vendor import Vendor, VendorContact, VendorRead

# ==========================================
# FIXTURES
# ==========================================


@pytest.fixture
def vendor_single_contact_kwargs():
    return {
        "name": "Cornerstone Wholesale",
        "contacts": [
            {
                "name": "Burton Daniels",
                "role": "Account Manager",
                "email": "burton@cornerstonewholesale.com",
                "phone": "517-555-1277",
            }
        ],
    }


@pytest.fixture
def vendor_multiple_contacts_kwargs(vendor_single_contact_kwargs):
    return vendor_single_contact_kwargs | {
        "contacts": vendor_single_contact_kwargs["contacts"]
        + [
            {
                "name": "Amelia Vasquez",
                "role": "Delivery Manager",
                "email": "amelia@cornerstonewholesale.com",
                "phone": "517-555-1278",
            }
        ]
    }


@pytest.fixture
def vendor_no_contacts_kwargs(vendor_single_contact_kwargs):
    return vendor_single_contact_kwargs | {"contacts": []}


@pytest.fixture
def vendor_invalid_name_kwargs(vendor_single_contact_kwargs):
    return vendor_single_contact_kwargs | {"name": 42}


@pytest.fixture
def vendor_missing_name_kwargs(vendor_single_contact_kwargs):
    kwargs = dict(vendor_single_contact_kwargs)
    del kwargs["name"]
    return kwargs


@pytest.fixture
def vendor_whitespace_name_kwargs(vendor_single_contact_kwargs):
    return vendor_single_contact_kwargs | {"name": "   "}


@pytest.fixture
def vendor_missing_contacts_kwargs(vendor_single_contact_kwargs):
    kwargs = dict(vendor_single_contact_kwargs)
    del kwargs["contacts"]
    return kwargs


@pytest.fixture
def vendor_invalid_contact_email_kwargs(vendor_single_contact_kwargs):
    contact = vendor_single_contact_kwargs["contacts"][0]
    return vendor_single_contact_kwargs | {
        "contacts": [contact | {"email": "not-an-email"}]
    }


@pytest.fixture
def vendor_invalid_contact_phone_kwargs(vendor_single_contact_kwargs):
    contact = vendor_single_contact_kwargs["contacts"][0]
    return vendor_single_contact_kwargs | {
        "contacts": [contact | {"phone": "5175551277"}]
    }


@pytest.fixture
def vendor_contact_missing_role_kwargs(vendor_single_contact_kwargs):
    contact = dict(vendor_single_contact_kwargs["contacts"][0])
    del contact["role"]
    return vendor_single_contact_kwargs | {"contacts": [contact]}


@pytest.fixture
def vendor_whitespace_contact_name_kwargs(vendor_single_contact_kwargs):
    contact = vendor_single_contact_kwargs["contacts"][0]
    return vendor_single_contact_kwargs | {"contacts": [contact | {"name": "   "}]}


@pytest.fixture
def vendor_inactive_kwargs(vendor_single_contact_kwargs):
    return vendor_single_contact_kwargs | {"active": False}


@pytest.fixture()
def unused_vendor_id(db_session):
    def _unused_vendor_id():
        max_id = db_session.scalar(select(func.max(Vendor.id))) or 0
        return max_id + 1

    return _unused_vendor_id


@pytest.fixture()
def vendor_single_contact(db_session, client, vendor_single_contact_kwargs):
    response = client.post("/vendors", json=vendor_single_contact_kwargs)
    return db_session.get(Vendor, response.json()["id"])


@pytest.fixture()
def vendor_multiple_contacts(db_session, client, vendor_multiple_contacts_kwargs):
    response = client.post("/vendors", json=vendor_multiple_contacts_kwargs)
    return db_session.get(Vendor, response.json()["id"])


@pytest.fixture()
def deleted_vendor(db_session, client, vendor_single_contact):
    client.delete(f"/vendors/{vendor_single_contact.id}")
    vendor = db_session.get(Vendor, vendor_single_contact.id)
    return vendor


@pytest.fixture()
def vendor_with_ingredient(client, vendor_single_contact):
    client.post(
        "/ingredients",
        json={
            "name": "Sugar",
            "purchasing_cost": 3.5,
            "unit_amount": 1000,
            "unit_of_measure": "g",
            "vendor_id": vendor_single_contact.id,
        },
    )
    return vendor_single_contact


@pytest.fixture()
def unused_contact_id(db_session):
    def _unused_contact_id():
        max_id = db_session.scalar(select(func.max(VendorContact.id))) or 0
        return max_id + 1

    return _unused_contact_id


@pytest.fixture()
def other_vendor(db_session, client, vendor_single_contact_kwargs):
    kwargs = vendor_single_contact_kwargs | {"name": "Other Vendor LLC"}
    response = client.post("/vendors", json=kwargs)
    return db_session.get(Vendor, response.json()["id"])


@pytest.fixture
def vendor_update_kwargs(vendor_single_contact):
    contact = vendor_single_contact.contacts[0]
    return {
        "name": "Cornerstone Wholesale Updated",
        "active": True,
        "contacts": [
            {
                "id": contact.id,
                "name": contact.name,
                "role": "Regional Manager",
                "email": contact.email,
                "phone": contact.phone,
            }
        ],
    }


@pytest.fixture
def vendor_update_new_contact_kwargs(vendor_single_contact):
    contact = vendor_single_contact.contacts[0]
    return {
        "name": vendor_single_contact.name,
        "active": vendor_single_contact.active,
        "contacts": [
            {
                "id": contact.id,
                "name": contact.name,
                "role": contact.role,
                "email": contact.email,
                "phone": contact.phone,
            },
            {
                "name": "New Contact",
                "role": "Sales Rep",
                "email": "newcontact@cornerstonewholesale.com",
                "phone": "517-555-1279",
            },
        ],
    }


@pytest.fixture
def vendor_update_remove_contact_kwargs(vendor_multiple_contacts):
    contact = vendor_multiple_contacts.contacts[0]
    return {
        "name": vendor_multiple_contacts.name,
        "active": vendor_multiple_contacts.active,
        "contacts": [
            {
                "id": contact.id,
                "name": contact.name,
                "role": contact.role,
                "email": contact.email,
                "phone": contact.phone,
            }
        ],
    }


@pytest.fixture
def vendor_update_invalid_name_kwargs(vendor_update_kwargs):
    return vendor_update_kwargs | {"name": 42}


@pytest.fixture
def vendor_update_missing_name_kwargs(vendor_update_kwargs):
    kwargs = dict(vendor_update_kwargs)
    del kwargs["name"]
    return kwargs


@pytest.fixture
def vendor_update_whitespace_name_kwargs(vendor_update_kwargs):
    return vendor_update_kwargs | {"name": "   "}


@pytest.fixture
def vendor_update_zero_contacts_kwargs(vendor_update_kwargs):
    return vendor_update_kwargs | {"contacts": []}


@pytest.fixture
def vendor_update_missing_contacts_kwargs(vendor_update_kwargs):
    kwargs = dict(vendor_update_kwargs)
    del kwargs["contacts"]
    return kwargs


@pytest.fixture
def vendor_update_invalid_contact_email_kwargs(vendor_update_kwargs):
    contact = vendor_update_kwargs["contacts"][0]
    return vendor_update_kwargs | {"contacts": [contact | {"email": "not-an-email"}]}


@pytest.fixture
def vendor_update_invalid_contact_phone_kwargs(vendor_update_kwargs):
    contact = vendor_update_kwargs["contacts"][0]
    return vendor_update_kwargs | {"contacts": [contact | {"phone": "5175551277"}]}


@pytest.fixture
def vendor_update_contact_missing_role_kwargs(vendor_update_kwargs):
    contact = dict(vendor_update_kwargs["contacts"][0])
    del contact["role"]
    return vendor_update_kwargs | {"contacts": [contact]}


@pytest.fixture
def vendor_update_whitespace_contact_name_kwargs(vendor_update_kwargs):
    contact = vendor_update_kwargs["contacts"][0]
    return vendor_update_kwargs | {"contacts": [contact | {"name": "   "}]}


@pytest.fixture
def vendor_update_nonexistent_contact_id_kwargs(
    vendor_update_kwargs, unused_contact_id
):
    contact = vendor_update_kwargs["contacts"][0]
    return vendor_update_kwargs | {"contacts": [contact | {"id": unused_contact_id()}]}


@pytest.fixture
def vendor_update_contact_belongs_to_other_vendor_kwargs(
    vendor_single_contact, other_vendor
):
    other_contact = other_vendor.contacts[0]
    return {
        "name": vendor_single_contact.name,
        "active": vendor_single_contact.active,
        "contacts": [
            {
                "id": other_contact.id,
                "name": other_contact.name,
                "role": other_contact.role,
                "email": other_contact.email,
                "phone": other_contact.phone,
            }
        ],
    }


@pytest.fixture
def vendor_with_soft_deleted_contact(db_session, vendor_multiple_contacts):
    contact = vendor_multiple_contacts.contacts[0]
    contact.is_deleted = True
    db_session.commit()
    db_session.refresh(vendor_multiple_contacts)
    return vendor_multiple_contacts


@pytest.fixture
def vendor_update_soft_deleted_contact_id_kwargs(vendor_with_soft_deleted_contact):
    deleted_contact = next(
        c for c in vendor_with_soft_deleted_contact.contacts if c.is_deleted
    )
    return {
        "name": vendor_with_soft_deleted_contact.name,
        "active": vendor_with_soft_deleted_contact.active,
        "contacts": [
            {
                "id": deleted_contact.id,
                "name": deleted_contact.name,
                "role": deleted_contact.role,
                "email": deleted_contact.email,
                "phone": deleted_contact.phone,
            }
        ],
    }


@pytest.fixture
def vendor_update_duplicate_contact_ids_kwargs(vendor_update_kwargs):
    contact = vendor_update_kwargs["contacts"][0]
    return vendor_update_kwargs | {"contacts": [contact, contact]}


# ==========================================
# LIST OPERATIONS
# ==========================================

# --------------------
# Successful Responses
# --------------------


def test_list_vendors_with_multiple_vendors_should_return_all_vendors(
    client, vendor_single_contact_kwargs
):
    # 1. Create the first vendor and assert success
    response1 = client.post("/vendors", json=vendor_single_contact_kwargs)
    assert response1.status_code == 201
    vendor1 = response1.json()

    # 2. Create a second vendor and assert success
    second_vendor_kwargs = dict(vendor_single_contact_kwargs)
    second_vendor_kwargs["name"] = "Second Vendor LLC"
    response2 = client.post("/vendors", json=second_vendor_kwargs)
    assert response2.status_code == 201
    vendor2 = response2.json()

    # 3. Fetch the list
    response = client.get("/vendors")
    assert response.status_code == 200
    data = response.json()

    # 4. Assert the exact expected length (assuming an isolated test database)
    assert isinstance(data, list)
    assert len(data) == 2

    # 5. Verify the exact data returned matches what we created
    # Check first vendor
    returned_vendor1 = next(v for v in data if v["id"] == vendor1["id"])
    assert returned_vendor1["name"] == vendor1["name"]
    assert returned_vendor1["contacts"] == vendor1["contacts"]

    # Check second vendor
    returned_vendor2 = next(v for v in data if v["id"] == vendor2["id"])
    assert returned_vendor2["name"] == vendor2["name"]
    assert returned_vendor2["contacts"] == vendor2["contacts"]


def test_list_vendors_with_inactive_vendor_should_return_vendors(
    client, vendor_single_contact_kwargs
):
    # Create an inactive vendor
    inactive_vendor_kwargs = dict(vendor_single_contact_kwargs)
    inactive_vendor_kwargs["name"] = "Defunct Suppliers Inc"
    inactive_vendor_kwargs["active"] = False

    post_response = client.post("/vendors", json=inactive_vendor_kwargs)
    assert post_response.status_code == 201
    inactive_vendor_id = post_response.json()["id"]

    # Fetch the list
    get_response = client.get("/vendors")
    assert get_response.status_code == 200
    data = get_response.json()

    # Verify the inactive vendor is present and data is correct
    returned_vendor = next((v for v in data if v["id"] == inactive_vendor_id), None)
    assert returned_vendor is not None
    assert returned_vendor["name"] == "Defunct Suppliers Inc"
    assert returned_vendor["active"] is False


def test_list_vendors_with_deleted_vendor_should_return_vendors_excluding_deleted_vendor(  # noqa: E501
    client, deleted_vendor
):
    list_response = client.get("/vendors")
    assert all(v["id"] != deleted_vendor.id for v in list_response.json())


def test_list_vendors_with_no_vendors_should_return_empty_list(client):
    response = client.get("/vendors")

    assert response.status_code == 200
    assert response.json() == []


# ==========================================
# CREATE OPERATIONS
# ==========================================

# --------------------
# Successful Responses
# --------------------


def test_create_vendor_with_one_contact_should_return_vendor(
    client, vendor_single_contact_kwargs
):
    response = client.post("/vendors", json=vendor_single_contact_kwargs)
    assert response.status_code == 201

    vendor = VendorRead(**response.json())
    expected = vendor_single_contact_kwargs | {
        "id": vendor.id,
        "active": True,
        "contacts": [
            vendor_single_contact_kwargs["contacts"][0]
            | {"id": vendor.contacts[0].id, "vendor_id": vendor.contacts[0].vendor_id}
        ],
    }
    assert vendor.model_dump(mode="json") == expected


def test_create_vendor_with_multiple_contacts_should_return_vendor(
    client, vendor_multiple_contacts_kwargs
):
    response = client.post("/vendors", json=vendor_multiple_contacts_kwargs)
    assert response.status_code == 201

    vendor = VendorRead(**response.json())
    expected = vendor_multiple_contacts_kwargs | {
        "id": vendor.id,
        "active": True,
        "contacts": [
            vendor_multiple_contacts_kwargs["contacts"][0]
            | {"id": vendor.contacts[0].id, "vendor_id": vendor.contacts[0].vendor_id},
            vendor_multiple_contacts_kwargs["contacts"][1]
            | {"id": vendor.contacts[1].id, "vendor_id": vendor.contacts[1].vendor_id},
        ],
    }
    assert vendor.model_dump(mode="json") == expected


def test_create_vendor_with_active_false_should_return_inactive_vendor(
    client, vendor_inactive_kwargs
):
    response = client.post("/vendors", json=vendor_inactive_kwargs)
    assert response.status_code == 201
    assert response.json()["active"] is False


# --------------------
# Error Responses
# --------------------


def test_create_vendor_with_invalid_name_should_return_422(
    client, vendor_invalid_name_kwargs
):
    response = client.post("/vendors", json=vendor_invalid_name_kwargs)
    assert response.status_code == 422


def test_create_vendor_with_zero_contacts_should_return_422(
    client, vendor_no_contacts_kwargs
):
    response = client.post("/vendors", json=vendor_no_contacts_kwargs)
    assert response.status_code == 422


def test_create_vendor_with_missing_name_should_return_422(
    client, vendor_missing_name_kwargs
):
    response = client.post("/vendors", json=vendor_missing_name_kwargs)
    assert response.status_code == 422


def test_create_vendor_with_whitespace_name_should_return_422(
    client, vendor_whitespace_name_kwargs
):
    response = client.post("/vendors", json=vendor_whitespace_name_kwargs)
    assert response.status_code == 422


def test_create_vendor_with_missing_contacts_should_return_422(
    client, vendor_missing_contacts_kwargs
):
    response = client.post("/vendors", json=vendor_missing_contacts_kwargs)
    assert response.status_code == 422


def test_create_vendor_with_invalid_contact_email_should_return_422(
    client, vendor_invalid_contact_email_kwargs
):
    response = client.post("/vendors", json=vendor_invalid_contact_email_kwargs)
    assert response.status_code == 422


def test_create_vendor_with_invalid_contact_phone_should_return_422(
    client, vendor_invalid_contact_phone_kwargs
):
    response = client.post("/vendors", json=vendor_invalid_contact_phone_kwargs)
    assert response.status_code == 422


def test_create_vendor_with_contact_missing_role_should_return_422(
    client, vendor_contact_missing_role_kwargs
):
    response = client.post("/vendors", json=vendor_contact_missing_role_kwargs)
    assert response.status_code == 422


def test_create_vendor_with_whitespace_contact_name_should_return_422(
    client, vendor_whitespace_contact_name_kwargs
):
    response = client.post("/vendors", json=vendor_whitespace_contact_name_kwargs)
    assert response.status_code == 422


# --------------------
# Side-Effect Tests
# --------------------


def test_create_vendor_should_persist_to_db(
    db_session, client, vendor_single_contact_kwargs
):
    response = client.post("/vendors", json=vendor_single_contact_kwargs)
    vendor = db_session.get(Vendor, response.json()["id"])
    assert vendor is not None


# ==========================================
# UPDATE OPERATIONS
# ==========================================

# --------------------
# Successful Responses
# --------------------


def test_update_vendor_should_return_vendor(
    client, vendor_single_contact, vendor_update_kwargs
):
    response = client.put(
        f"/vendors/{vendor_single_contact.id}", json=vendor_update_kwargs
    )
    assert response.status_code == 200

    vendor = VendorRead(**response.json())
    expected = vendor_update_kwargs | {
        "id": vendor_single_contact.id,
        "contacts": [
            vendor_update_kwargs["contacts"][0]
            | {"vendor_id": vendor_single_contact.id}
        ],
    }
    assert vendor.model_dump(mode="json") == expected


def test_update_vendor_with_new_contact_should_return_vendor_with_new_contact(
    client, vendor_single_contact, vendor_update_new_contact_kwargs
):
    response = client.put(
        f"/vendors/{vendor_single_contact.id}", json=vendor_update_new_contact_kwargs
    )
    assert response.status_code == 200

    contacts = response.json()["contacts"]
    assert len(contacts) == 2
    new_contact = next(c for c in contacts if c["name"] == "New Contact")
    assert new_contact["role"] == "Sales Rep"
    assert new_contact["vendor_id"] == vendor_single_contact.id


def test_update_vendor_with_removed_contact_should_return_vendor_without_removed_contact(  # noqa: E501
    client, vendor_multiple_contacts, vendor_update_remove_contact_kwargs
):
    remaining_contact_id = vendor_update_remove_contact_kwargs["contacts"][0]["id"]
    removed_contact_id = next(
        c.id for c in vendor_multiple_contacts.contacts if c.id != remaining_contact_id
    )

    response = client.put(
        f"/vendors/{vendor_multiple_contacts.id}",
        json=vendor_update_remove_contact_kwargs,
    )
    assert response.status_code == 200

    contact_ids = [c["id"] for c in response.json()["contacts"]]
    assert removed_contact_id not in contact_ids
    assert remaining_contact_id in contact_ids


# --------------------
# Error Responses
# --------------------


def test_update_vendor_with_nonexistent_vendor_id_should_return_404(
    client, unused_vendor_id, vendor_update_kwargs
):
    response = client.put(f"/vendors/{unused_vendor_id()}", json=vendor_update_kwargs)
    assert response.status_code == 404


def test_update_vendor_with_already_deleted_vendor_should_return_404(
    client, deleted_vendor, vendor_update_kwargs
):
    response = client.put(f"/vendors/{deleted_vendor.id}", json=vendor_update_kwargs)
    assert response.status_code == 404


def test_update_vendor_with_nonexistent_contact_id_should_return_404(
    client, vendor_single_contact, vendor_update_nonexistent_contact_id_kwargs
):
    response = client.put(
        f"/vendors/{vendor_single_contact.id}",
        json=vendor_update_nonexistent_contact_id_kwargs,
    )
    assert response.status_code == 404


def test_update_vendor_with_soft_deleted_contact_id_should_return_404(
    client,
    vendor_with_soft_deleted_contact,
    vendor_update_soft_deleted_contact_id_kwargs,
):
    response = client.put(
        f"/vendors/{vendor_with_soft_deleted_contact.id}",
        json=vendor_update_soft_deleted_contact_id_kwargs,
    )
    assert response.status_code == 404


def test_update_vendor_with_invalid_id_should_return_422(client, vendor_update_kwargs):
    response = client.put("/vendors/not-an-id", json=vendor_update_kwargs)
    assert response.status_code == 422


def test_update_vendor_with_invalid_name_should_return_422(
    client, vendor_single_contact, vendor_update_invalid_name_kwargs
):
    response = client.put(
        f"/vendors/{vendor_single_contact.id}", json=vendor_update_invalid_name_kwargs
    )
    assert response.status_code == 422


def test_update_vendor_with_missing_name_should_return_422(
    client, vendor_single_contact, vendor_update_missing_name_kwargs
):
    response = client.put(
        f"/vendors/{vendor_single_contact.id}", json=vendor_update_missing_name_kwargs
    )
    assert response.status_code == 422


def test_update_vendor_with_whitespace_name_should_return_422(
    client, vendor_single_contact, vendor_update_whitespace_name_kwargs
):
    response = client.put(
        f"/vendors/{vendor_single_contact.id}",
        json=vendor_update_whitespace_name_kwargs,
    )
    assert response.status_code == 422


def test_update_vendor_with_zero_contacts_should_return_422(
    client, vendor_single_contact, vendor_update_zero_contacts_kwargs
):
    response = client.put(
        f"/vendors/{vendor_single_contact.id}",
        json=vendor_update_zero_contacts_kwargs,
    )
    assert response.status_code == 422


def test_update_vendor_with_missing_contacts_should_return_422(
    client, vendor_single_contact, vendor_update_missing_contacts_kwargs
):
    response = client.put(
        f"/vendors/{vendor_single_contact.id}",
        json=vendor_update_missing_contacts_kwargs,
    )
    assert response.status_code == 422


def test_update_vendor_with_invalid_contact_email_should_return_422(
    client, vendor_single_contact, vendor_update_invalid_contact_email_kwargs
):
    response = client.put(
        f"/vendors/{vendor_single_contact.id}",
        json=vendor_update_invalid_contact_email_kwargs,
    )
    assert response.status_code == 422


def test_update_vendor_with_invalid_contact_phone_should_return_422(
    client, vendor_single_contact, vendor_update_invalid_contact_phone_kwargs
):
    response = client.put(
        f"/vendors/{vendor_single_contact.id}",
        json=vendor_update_invalid_contact_phone_kwargs,
    )
    assert response.status_code == 422


def test_update_vendor_with_contact_missing_role_should_return_422(
    client, vendor_single_contact, vendor_update_contact_missing_role_kwargs
):
    response = client.put(
        f"/vendors/{vendor_single_contact.id}",
        json=vendor_update_contact_missing_role_kwargs,
    )
    assert response.status_code == 422


def test_update_vendor_with_whitespace_contact_name_should_return_422(
    client, vendor_single_contact, vendor_update_whitespace_contact_name_kwargs
):
    response = client.put(
        f"/vendors/{vendor_single_contact.id}",
        json=vendor_update_whitespace_contact_name_kwargs,
    )
    assert response.status_code == 422


def test_update_vendor_with_contact_belonging_to_another_vendor_should_return_422(
    client,
    vendor_single_contact,
    vendor_update_contact_belongs_to_other_vendor_kwargs,
):
    response = client.put(
        f"/vendors/{vendor_single_contact.id}",
        json=vendor_update_contact_belongs_to_other_vendor_kwargs,
    )
    assert response.status_code == 422


def test_update_vendor_with_duplicate_contact_ids_should_return_422(
    client, vendor_single_contact, vendor_update_duplicate_contact_ids_kwargs
):
    response = client.put(
        f"/vendors/{vendor_single_contact.id}",
        json=vendor_update_duplicate_contact_ids_kwargs,
    )
    assert response.status_code == 422


# --------------------
# Side-Effect Tests
# --------------------


def test_update_vendor_should_persist_updated_name_to_db(
    db_session, client, vendor_single_contact, vendor_update_kwargs
):
    client.put(f"/vendors/{vendor_single_contact.id}", json=vendor_update_kwargs)

    db_session.refresh(vendor_single_contact)
    assert vendor_single_contact.name == vendor_update_kwargs["name"]


def test_update_vendor_with_new_contact_should_persist_new_contact_to_db(
    db_session, client, vendor_single_contact, vendor_update_new_contact_kwargs
):
    client.put(
        f"/vendors/{vendor_single_contact.id}", json=vendor_update_new_contact_kwargs
    )

    db_session.refresh(vendor_single_contact)
    assert any(c.name == "New Contact" for c in vendor_single_contact.contacts)


def test_update_vendor_with_removed_contact_should_mark_contact_as_deleted(
    db_session, client, vendor_multiple_contacts, vendor_update_remove_contact_kwargs
):
    remaining_contact_id = vendor_update_remove_contact_kwargs["contacts"][0]["id"]
    removed_contact_id = next(
        c.id for c in vendor_multiple_contacts.contacts if c.id != remaining_contact_id
    )

    client.put(
        f"/vendors/{vendor_multiple_contacts.id}",
        json=vendor_update_remove_contact_kwargs,
    )

    contact = db_session.get(VendorContact, removed_contact_id)
    assert contact is not None
    assert contact.is_deleted is True


# ==========================================
# DELETE OPERATIONS
# ==========================================

# --------------------
# Successful Responses
# --------------------


def test_delete_vendor_should_return_no_content(client, vendor_single_contact):
    response = client.delete(f"/vendors/{vendor_single_contact.id}")
    assert response.status_code == 204


# --------------------
# Error Responses
# --------------------


def test_delete_vendor_with_nonexistent_id_should_return_404(client, unused_vendor_id):
    response = client.delete(f"/vendors/{unused_vendor_id()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "The vendor was not found."


def test_delete_vendor_with_already_deleted_vendor_should_return_404(
    client, deleted_vendor
):
    response = client.delete(f"/vendors/{deleted_vendor.id}")
    assert response.status_code == 404


def test_delete_vendor_with_invalid_id_should_return_422(client):
    response = client.delete("/vendors/not-an-id")
    assert response.status_code == 422


def test_delete_vendor_with_associated_ingredient_should_return_409(
    client, vendor_with_ingredient
):
    response = client.delete(f"/vendors/{vendor_with_ingredient.id}")

    assert response.status_code == 409
    assert response.json()["detail"] == "The vendor has associated ingredients."


# --------------------
# Side-Effect Tests
# --------------------


def test_delete_vendor_should_mark_vendor_as_deleted(
    db_session, client, vendor_single_contact
):
    client.delete(f"/vendors/{vendor_single_contact.id}")
    vendor = db_session.get(Vendor, vendor_single_contact.id)
    assert vendor.is_deleted is True


def test_delete_vendor_with_single_contact_should_mark_contacts_as_deleted(
    db_session, client, vendor_single_contact
):
    client.delete(f"/vendors/{vendor_single_contact.id}")

    vendor = db_session.get(Vendor, vendor_single_contact.id)
    assert len(vendor.contacts) > 0
    assert all(contact.is_deleted for contact in vendor.contacts)


def test_delete_vendor_with_multiple_contacts_should_mark_contacts_as_deleted(
    db_session, client, vendor_multiple_contacts
):
    client.delete(f"/vendors/{vendor_multiple_contacts.id}")

    vendor = db_session.get(Vendor, vendor_multiple_contacts.id)
    assert len(vendor.contacts) > 0
    assert all(contact.is_deleted for contact in vendor.contacts)


def test_delete_vendor_with_associated_ingredient_should_not_mark_vendor_as_deleted(
    db_session, client, vendor_with_ingredient
):
    client.delete(f"/vendors/{vendor_with_ingredient.id}")

    vendor = db_session.get(Vendor, vendor_with_ingredient.id)
    assert vendor.is_deleted is False
