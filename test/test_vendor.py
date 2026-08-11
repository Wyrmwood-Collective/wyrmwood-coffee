import pytest

from wyrmwood_coffee.models.vendor import Vendor, VendorRead


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


def test_create_vendor_should_persist_to_db(
    db_session, client, vendor_single_contact_kwargs
):
    response = client.post("/vendors", json=vendor_single_contact_kwargs)
    vendor = db_session.get(Vendor, response.json()["id"])
    assert vendor is not None


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


def test_create_vendor_with_active_false_should_return_inactive_vendor(
    client, vendor_inactive_kwargs
):
    response = client.post("/vendors", json=vendor_inactive_kwargs)
    assert response.status_code == 201
    assert response.json()["active"] is False
