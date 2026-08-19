from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from wyrmwood_coffee.dependencies import DbSession
from wyrmwood_coffee.models.customer import Customer, CustomerCreate, CustomerRead

router = APIRouter()


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
        return CustomerRead.model_validate(new_customer)
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already registered in the system with phone or email",
        ) from None
