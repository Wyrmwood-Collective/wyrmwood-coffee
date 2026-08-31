import logging

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from wyrmwood_coffee.dependencies import DbSession
from wyrmwood_coffee.logging import ResourceLogger
from wyrmwood_coffee.models.ingredient import (
    Ingredient,
    IngredientCreate,
    IngredientRead,
    IngredientUpdate,
)
from wyrmwood_coffee.models.vendor import Vendor

logger = logging.getLogger(__name__)
ingredient_logger = ResourceLogger(logger, Ingredient)
vendor_logger = ResourceLogger(logger, Vendor)
router = APIRouter(prefix="/ingredients", tags=["Ingredients"])


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=list[IngredientRead],
    response_description="The list of ingredients",
)
def list_ingredients(session: DbSession) -> list[IngredientRead]:
    """
    Returns a list of all ingredient records in the system.
    """
    ingredients = session.scalars(select(Ingredient)).all()
    return [IngredientRead.model_validate(ingredient) for ingredient in ingredients]


@router.get(
    "/{id}",
    status_code=status.HTTP_200_OK,
    response_model=IngredientRead,
    response_description="The requested ingredient",
    responses={
        404: {"description": "The ingredient was not found."},
        422: {"description": "The provided path parameter is malformed or invalid."},
    },
)
def get_ingredient(id: int, session: DbSession) -> IngredientRead:
    """
    Retrieve a single ingredient by ID.
    """
    ingredient = session.get(Ingredient, id)
    if not ingredient:
        ingredient_logger.log_resource_not_found(id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The ingredient was not found.",
        )

    return IngredientRead.model_validate(ingredient)


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
    if vendor is None or vendor.is_deleted:
        vendor_logger.log_resource_not_found(payload.vendor_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The vendor was not found.",
        )
    if not vendor.active:
        # log-level rationale (per WC-49 requirements):
        # warning, because this may indicate a problem with a client
        # we have written against our API
        ingredient_logger.logger.warning(
            "Ingredient linked to inactive vendor",
            extra={"resource_type": Ingredient.__name__, "vendor_id": vendor.id},
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
        ingredient_logger.log_resource_created(ingredient.id)
    except IntegrityError as err:
        session.rollback()
        ingredient_logger.log_attrs_not_unique([Ingredient.name, Ingredient.vendor_id])
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An ingredient with that name and vendor ID already exists.",
        ) from err
    session.refresh(ingredient)

    return IngredientRead.model_validate(ingredient)


@router.put(
    "/{id}",
    status_code=status.HTTP_200_OK,
    response_model=IngredientRead,
    response_description="The updated ingredient",
    responses={
        404: {
            "description": "The ingredient was not found.\n\nThe vendor was not found."
        },
        409: {
            "description": "An ingredient with that name and vendor ID already exists."
        },
        422: {
            "description": (
                "The provided path parameter is malformed or invalid.\n\n"
                "The provided IngredientUpdate is malformed or invalid."
            )
        },
    },
)
def update_ingredient(
    id: int, payload: IngredientUpdate, session: DbSession
) -> IngredientRead:
    """
    Update an existing ingredient.
    """
    ingredient = session.get(Ingredient, id)
    if not ingredient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The ingredient was not found.",
        )

    vendor = session.get(Vendor, payload.vendor_id)
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The vendor was not found.",
        )

    update_data = payload.model_dump()
    for key, value in update_data.items():
        setattr(ingredient, key, value)

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
