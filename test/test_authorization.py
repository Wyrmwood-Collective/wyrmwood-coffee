import logging

import pytest


@pytest.fixture
def vendor_create_kwargs():
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
def customer_create_kwargs():
    return {
        "first_name": "SpongeBob",
        "last_name": "SquarePants",
        "email": "spongebob@bikinibottom.com",
        "phone": "555-010-0100",
    }


def test_create_vendor_without_token_should_return_401(
    unauthenticated_client, vendor_create_kwargs
):
    response = unauthenticated_client.post("/vendors", json=vendor_create_kwargs)
    assert response.status_code == 401


def test_create_vendor_with_employee_role_should_return_403(
    employee_client, vendor_create_kwargs, caplog
):
    caplog.set_level(logging.INFO, logger="wyrmwood_coffee.dependencies")

    response = employee_client.post("/vendors", json=vendor_create_kwargs)

    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions."
    records = [
        r
        for r in caplog.records
        if r.name == "wyrmwood_coffee.dependencies"
        and r.getMessage() == "Unauthorized role attempt"
    ]
    assert len(records) == 1
    assert records[0].employee_role == "employee"
    assert records[0].required_roles == ["admin", "manager"]


def test_create_vendor_with_admin_role_should_return_201(
    admin_client, vendor_create_kwargs
):
    response = admin_client.post("/vendors", json=vendor_create_kwargs)
    assert response.status_code == 201


def test_create_customer_without_token_should_return_401(
    unauthenticated_client, customer_create_kwargs
):
    response = unauthenticated_client.post("/customers", json=customer_create_kwargs)
    assert response.status_code == 401


def test_create_customer_with_employee_role_should_return_201(
    employee_client, customer_create_kwargs
):
    response = employee_client.post("/customers", json=customer_create_kwargs)
    assert response.status_code == 201


def test_create_employee_with_employee_role_should_return_403(
    employee_client, employee_kwargs
):
    response = employee_client.post("/employees", json=employee_kwargs)
    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions."


def test_create_ingredient_with_employee_role_should_return_403(
    employee_client, make_vendor
):
    vendor = make_vendor()
    response = employee_client.post(
        "/ingredients",
        json={
            "name": "Espresso Beans",
            "purchasing_cost": 12.5,
            "unit_amount": 1,
            "unit_of_measure": "kg",
            "allergens": [],
            "vendor_id": vendor.id,
            "active": True,
        },
    )
    assert response.status_code == 403


def test_create_baked_good_with_employee_role_should_return_403(employee_client):
    response = employee_client.post(
        "/baked-goods",
        json={
            "name": "Croissant",
            "description": "Buttery",
            "purchase_cost": "1.50",
            "retail_price": "3.50",
            "allergens": ["gluten"],
        },
    )
    assert response.status_code == 403


def test_create_promotion_with_employee_role_should_return_403(employee_client):
    response = employee_client.post(
        "/promotions",
        json={
            "active": True,
            "promo_code": "SPRING SALE",
            "discount_percentage": 10,
            "start_date": "2026-03-01",
            "end_date": "2026-03-31",
        },
    )
    assert response.status_code == 403
