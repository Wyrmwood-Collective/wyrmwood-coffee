import logging

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import IntegrityError

from wyrmwood_coffee.dependencies import DbSession
from wyrmwood_coffee.logging import ResourceLogger
from wyrmwood_coffee.models.drink import Drink, DrinkCreate, DrinkRead
from wyrmwood_coffee.services import drinks as drink_service

drink_logger = ResourceLogger(logging.getLogger(__name__), Drink)
router = APIRouter()


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=DrinkRead,
    response_description="The newly created drink recipe",
    responses={
        404: {"description": "The ingredient was not found."},
        409: {"description": "A drink with that name already exists."},
        422: {
            "description": (
                "The provided DrinkCreate is malformed or invalid. This includes: "
                "invalid 'type', invalid 'unit', duplicate 'ingredient_id' values, "
                "or 'production_cost' not less than 'sale_price'."
            )
        },
    },
)
def create_drink(session: DbSession, payload: DrinkCreate) -> DrinkRead:
    """Create a new drink recipe."""
    try:
        drink = drink_service.create_drink(session, payload)
        drink_logger.log_resource_created(drink.id)
        return DrinkRead.model_validate(drink)
    except IntegrityError:
        session.rollback()
        drink_logger.log_attrs_not_unique([Drink.name])
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A Drink with that name already exists.",
        ) from None
