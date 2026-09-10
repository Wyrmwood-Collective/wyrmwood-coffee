import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError

from wyrmwood_coffee.dependencies import DbSession, require_manager
from wyrmwood_coffee.logging import ResourceLogger
from wyrmwood_coffee.models.drink import Drink, DrinkCreate, DrinkRead
from wyrmwood_coffee.services import drinks as drink_service

HTTP_422_DESCRIPTION = """
The provided DrinkCreate is malformed or invalid. This includes: 
- Invalid 'type'
- Invalid 'unit'
- Duplicate 'ingredient_id' values
- 'sale_price' is less than 'production_cost'
- Attempting to convert between incompatible unit categories
"""

drink_logger = ResourceLogger(logging.getLogger(__name__), Drink)
router = APIRouter()


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=DrinkRead,
    response_description="The newly created drink recipe",
    responses={
        401: {"description": "Could not validate credentials."},
        403: {"description": "Insufficient permissions."},
        404: {"description": "The ingredient was not found."},
        409: {"description": "A drink with that name already exists."},
        422: {"description": HTTP_422_DESCRIPTION},
    },
    dependencies=[Depends(require_manager)],
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
