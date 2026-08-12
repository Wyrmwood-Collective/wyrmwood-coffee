from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import Select
from sqlalchemy.orm import Session

from wyrmwood_coffee.database import get_db
from wyrmwood_coffee.models.promotions import (
    Promotion,
    PromotionCreate,
    PromotionRead,
)

# Create the promotions router.
# All routes in this file will begin with /promotions.
router = APIRouter(prefix="/promotions", tags=["promotions"])


@router.post(
    "",
    response_model=PromotionRead,
    status_code=status.HTTP_201_CREATED,
    response_description="The Promotion was created successfully.",
    responses={
        409: {
            "description": "A Promotion with that name already exists.",
        },
        422: {
            "description": "The provided Promotion is malformed or invalid.",
        },
    },
)
def create_promotion(
    promotion_data: PromotionCreate,
    db: Annotated[Session, Depends(get_db)],
):
    """
    Create a new Promotion.

    Validates the incoming PromotionCreate request and checks whether
    a Promotion with the same promo code already exists.

    Returns:
        PromotionRead: The newly created Promotion.

    Raises:
        HTTPException: 409 if the promo code already exists.
        422: Automatically returned when the PromotionCreate request
        is malformed or fails validation.
    """

    # Check the database for an existing Promotion with the same promo code.
    existing_promotion = db.scalar(
        Select(Promotion).where(Promotion.promo_code == promotion_data.promo_code)
    )

    # Prevent duplicate promo codes.
    if existing_promotion:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A Promotion with that name already exists.",
        )

    # Convert the validated Pydantic request model into a SQLAlchemy model.
    promotion = Promotion(**promotion_data.model_dump())

    # Add the new Promotion to the current database session.
    db.add(promotion)

    # Save the new Promotion to the database.
    db.commit()

    # Refresh the object to retrieve database-generated values,
    # such as the Promotion ID.
    db.refresh(promotion)

    # FastAPI converts this object to the PromotionRead response model
    # and returns it with HTTP status 201 Created.
    return promotion
