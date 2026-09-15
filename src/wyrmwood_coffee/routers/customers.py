import logging

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from wyrmwood_coffee.dependencies import DbSession, require_auth
from wyrmwood_coffee.logging import ResourceLogger
from wyrmwood_coffee.models.customer import (
    Customer,
    CustomerCreate,
    CustomerFavoriteItemRead,
    CustomerFavoriteRead,
    CustomerId,
    CustomerRead,
)
from wyrmwood_coffee.models.purchase import Purchase, PurchaseItem

customer_logger = ResourceLogger(logging.getLogger(__name__), Customer)
router = APIRouter()

DUPLICATE_ATTRS = {
    "ix_customers_email": [Customer.email],
    "ix_customers_phone": [Customer.phone],
}


def get_active_customer_by_phone(session: DbSession, phone: str) -> Customer:
    """
    Retrieve an active customer by phone number.
    """
    customer = session.scalar(
        select(Customer).where(
            Customer.phone == phone,
            Customer.active.is_(True),
        )
    )

    if customer is None:
        customer_logger.log_resource_not_found(phone)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The customer was not found.",
        )

    return customer


def get_customer_item_quantities(
    session: DbSession, customer_id: int
) -> list[tuple[str, str, int]]:
    """
    Get the total quantity purchased for each item by a customer.
    """
    results = session.execute(
        select(
            PurchaseItem.item_type,
            PurchaseItem.name,
            func.sum(PurchaseItem.quantity).label("quantity"),
        )
        .join(Purchase, Purchase.id == PurchaseItem.purchase_id)
        .where(Purchase.customer_id == customer_id)
        .group_by(PurchaseItem.item_type, PurchaseItem.name)
    ).all()

    return [(item_type, name, quantity) for item_type, name, quantity in results]


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=list[CustomerRead],
    response_description="The list of all customers",
)
def list_customers(session: DbSession) -> list[CustomerRead]:
    """
    List all customer records in the system.
    """
    customers = session.scalars(select(Customer)).all()
    return [CustomerRead.model_validate(c) for c in customers]


def get_customer_favorite_item(
    item_quantities: list[tuple[str, str, int]],
    item_type: str,
) -> CustomerFavoriteItemRead:
    """
    Get the customer's most-purchased item for the requested category.
    """
    matching_items = [
        (name, quantity)
        for category, name, quantity in item_quantities
        if category == item_type
    ]

    if not matching_items:
        return CustomerFavoriteItemRead()

    name, quantity = max(matching_items, key=lambda item: item[1])

    return CustomerFavoriteItemRead(
        name=name,
        quantity=quantity,
        is_favorite=quantity >= 5,
    )


@router.get(
    "/favorites",
    status_code=status.HTTP_200_OK,
    response_model=CustomerFavoriteRead,
    response_description="The customer's favorite items",
    responses={
        404: {"description": "The customer was not found."},
        422: {"description": "The provided query parameter is malformed or invalid."},
    },
)
def get_customer_favorites(
    session: DbSession,
    phone: str = Query(pattern=r"\d{3}-\d{3}-\d{4}$"),
) -> CustomerFavoriteRead:
    """
    Retrieve an active customer's favorite drink and baked good by phone number.
    """
    customer = get_active_customer_by_phone(session, phone)
    item_quantities = get_customer_item_quantities(session, customer.id)

    drink = get_customer_favorite_item(item_quantities, "drink")
    baked_good = get_customer_favorite_item(item_quantities, "baked_good")

    return CustomerFavoriteRead(
        customer=CustomerRead.model_validate(customer),
        drink=drink,
        baked_good=baked_good,
    )


@router.get(
    "/{id}",
    status_code=status.HTTP_200_OK,
    response_model=CustomerRead,
    response_description="The requested customer",
    responses={
        404: {"description": "The customer was not found."},
        422: {"description": "The provided path parameter is malformed or invalid."},
    },
)
def get_customer(session: DbSession, id: CustomerId) -> CustomerRead:
    """
    Retrieve a single customer by ID.
    """
    customer = session.get(Customer, id)
    if customer is None:
        customer_logger.log_resource_not_found(id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The customer was not found.",
        )
    return CustomerRead.model_validate(customer)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=CustomerRead,
    response_description="The newly created customer",
    responses={
        401: {"description": "Could not validate credentials."},
        status.HTTP_409_CONFLICT: {
            "description": "A customer with the given email or phone already exists"
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Missing or invalid values",
        },
    },
    dependencies=[Depends(require_auth)],
)
def create_customer(session: DbSession, payload: CustomerCreate) -> CustomerRead:
    """
    Create a new customer record.

    Both email and phone must be unique.
    """
    new_customer = Customer(**payload.model_dump())
    try:
        session.add(new_customer)
        session.commit()
        session.refresh(new_customer)
        customer_logger.log_resource_created(new_customer.id)
        return CustomerRead.model_validate(new_customer)
    except IntegrityError as err:
        session.rollback()
        constraint_name = (
            (err.orig.diag.constraint_name or "")
            if isinstance(err.orig, psycopg.Error)
            else ""
        )
        customer_logger.log_attrs_not_unique(DUPLICATE_ATTRS.get(constraint_name, []))
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already registered in the system with phone or email",
        ) from None
