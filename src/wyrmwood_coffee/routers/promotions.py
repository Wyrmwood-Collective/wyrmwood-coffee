from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from wyrmwood_coffee.database import get_db
from wyrmwood_coffee.dependencies import DbSession
from wyrmwood_coffee.models.promotions import (
    Promotion,
    PromotionCreate,
    PromotionRead,
)

router = APIRouter(prefix="/promotions", tags=["promotions"])


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=list[PromotionRead],
    response_description="The list of Promotions",
)
def list_promotions(session: DbSession) -> list[PromotionRead]:
    """
    Return all Promotions.

    Returns all Promotions currently stored in the system.
    """
    promotions = session.query(Promotion).all()

    return [PromotionRead.model_validate(promotion) for promotion in promotions]


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=PromotionRead,
    response_description="The newly created Promotion",
    responses={
        409: {
            "description": "A Promotion with that promo code already exists.",
        },
        422: {
            "description": "The provided PromotionCreate is malformed or invalid.",
        },
    },
)
def create_promotion(
    session: Annotated[Session, Depends(get_db)],
    payload: PromotionCreate,
) -> PromotionRead:
    """
    Create a new Promotion.

    Returns the created Promotion with its generated ID.

    """

    promotion = Promotion(**payload.model_dump())

    session.add(promotion)

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A Promotion with that promo code already exists.",
        ) from None

    session.refresh(promotion)

    return PromotionRead.model_validate(promotion)
