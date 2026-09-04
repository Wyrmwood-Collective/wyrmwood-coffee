import logging

import psycopg
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from wyrmwood_coffee.dependencies import DbSession
from wyrmwood_coffee.logging import ResourceLogger
from wyrmwood_coffee.models.customer import (
    Customer,
    CustomerCreate,
    CustomerId,
    CustomerRead,
)

customer_logger = ResourceLogger(logging.getLogger(__name__), Customer)
router = APIRouter()

DUPLICATE_ATTRS = {
    "ix_customers_email": [Customer.email],
    "ix_customers_phone": [Customer.phone],
}


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
        status.HTTP_409_CONFLICT: {
            "description": "A customer with the given email or phone already exists"
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Missing or invalid values",
        },
    },
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
