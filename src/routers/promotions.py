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
        422: {"description": "The provided Promotion is malformed or invalid."},
    },
)
def create_promotion(
    promotion_data: PromotionCreate,
    db: Annotated[Session, Depends(get_db)],
):
    existing_promotion = db.scalar(
        Select(Promotion).where(Promotion.promo_code == promotion_data.promo_code)
    )

    if existing_promotion:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A Promotion with that name already exists.",
        )

    promotion = Promotion(**promotion_data.model_dump())

    db.add(promotion)
    db.commit()
    db.refresh(promotion)

    return promotion
