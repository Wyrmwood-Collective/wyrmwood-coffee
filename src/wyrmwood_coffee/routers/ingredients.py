from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import IntegrityError

from wyrmwood_coffee.dependencies import DbSession
from wyrmwood_coffee.models.ingredient import (
    Ingredient,
    IngredientCreate,
    IngredientRead,
)
from wyrmwood_coffee.models.vendor import Vendor

router = APIRouter(prefix="/ingredients", tags=["Ingredients"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=IngredientRead,
    response_description="The newly created Ingredient",
    responses={
        404: {"description": "The vendor was not found."},
        409: {
            "description": "An ingredient with that name and vendor ID already exists."
        },
        422: {"description": "The provided IngredientCreate is malformed or invalid."},
    },
)
def create_ingredient(session: DbSession, payload: IngredientCreate) -> IngredientRead:
    """Create a new ingredient and link it to an existing vendor."""
    vendor = session.get(Vendor, payload.vendor_id)
    if vendor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The vendor was not found.",
        )

    ingredient = Ingredient(
        name=payload.name,
        purchasing_cost=payload.purchasing_cost,
        unit_amount=payload.unit_amount,
        unit_of_measure=payload.unit_of_measure,
        allergens=payload.allergens,
        vendor_id=payload.vendor_id,
        active=payload.active,
    )

    session.add(ingredient)

    try:
        session.commit()
    except IntegrityError as err:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An ingredient with that name and vendor ID already exists.",
        ) from err
    session.refresh(ingredient)

    return IngredientRead.model_validate(ingredient)
