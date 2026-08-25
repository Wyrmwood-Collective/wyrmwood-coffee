import pytest

from wyrmwood_coffee.models.vendor import Vendor, VendorRead

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


# ==========================================
# LIST OPERATIONS
# ==========================================

# --------------------
# Successful Responses
# --------------------


def test_list_vendors_with_multiple_vendors_should_return_all_vendors(
    client, vendor_single_contact_kwargs
):
    # 1. Create the first vendor
    response1 = client.post("/vendors", json=vendor_single_contact_kwargs)
    assert response1.status_code == 201
    vendor1 = response1.json()

    # 2. Create a second vendor
    second_vendor_kwargs = dict(vendor_single_contact_kwargs)
    second_vendor_kwargs["name"] = "Second Vendor LLC"
    response2 = client.post("/vendors", json=second_vendor_kwargs)
    assert response2.status_code == 201
    vendor2 = response2.json()

    # 3. Fetch the list
    response = client.get("/vendors")
    assert response.status_code == 200
    data = response.json()

    # 4. Assert the exact expected length
    assert isinstance(data, list)
    assert len(data) == 2

    # 5. Verify the ENTIRE schema matches (id, name, active, contacts, etc.)
    returned_vendor1 = next(v for v in data if v["id"] == vendor1["id"])
    assert returned_vendor1 == vendor1

    returned_vendor2 = next(v for v in data if v["id"] == vendor2["id"])
    assert returned_vendor2 == vendor2


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


def test_list_vendors_with_multiple_contacts_should_return_vendors(
    client, vendor_single_contact_kwargs
):
    # Create a vendor with multiple contacts
    multi_contact_kwargs = dict(vendor_single_contact_kwargs)
    multi_contact_kwargs["name"] = "Multi Contact Vendor LLC"
    multi_contact_kwargs["contacts"] = [
        {
            "name": "Alice Admin",
            "role": "Manager",
            "email": "alice@multicontact.com",
            "phone": "555-555-0101",
        },
        {
            "name": "Bob Buyer",
            "role": "Purchasing",
            "email": "bob@multicontact.com",
            "phone": "555-555-0102",
        },
    ]
    # Insert it
    post_response = client.post("/vendors", json=multi_contact_kwargs)
    assert post_response.status_code == 201
    created_vendor = post_response.json()

    # Fetch the list
    get_response = client.get("/vendors")
    assert get_response.status_code == 200
    data = get_response.json()

    # Find our vendor and assert the complete schema matches
    returned_vendor = next((v for v in data if v["id"] == created_vendor["id"]), None)
    assert returned_vendor is not None
    assert returned_vendor == created_vendor


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
