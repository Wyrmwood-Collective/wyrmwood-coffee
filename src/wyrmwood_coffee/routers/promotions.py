import logging

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from wyrmwood_coffee.dependencies import DbSession
from wyrmwood_coffee.logging import ResourceLogger
from wyrmwood_coffee.models.promotions import (
    Promotion,
    PromotionCreate,
    PromotionId,
    PromotionRead,
    PromotionUpdate,
)

promotion_logger = ResourceLogger(logging.getLogger(__name__), Promotion)
router = APIRouter(prefix="/promotions", tags=["promotions"])


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=list[PromotionRead],
    response_description="The list of Promotions",
)
def list_promotions(session: DbSession) -> list[PromotionRead]:
    """
    Return all non-deleted Promotions.

    Returns all Promotions currently stored in the system
    that have not been soft deleted.
    """
    promotions = session.scalars(
        select(Promotion).where(Promotion.deleted.is_(False))
    ).all()

    return [PromotionRead.model_validate(promotion) for promotion in promotions]


@router.get(
    "/{id}",
    status_code=status.HTTP_200_OK,
    response_model=PromotionRead,
    response_description="The requested Promotion",
    responses={
        404: {
            "description": "The promotion was not found.",
        },
        422: {
            "description": "The provided path parameter is malformed or invalid.",
        },
    },
)
def get_promotion(
    session: DbSession,
    id: PromotionId,
) -> PromotionRead:
    """
    Retrieve a single promotion by ID.

    Returns the requested promotion.
    """
    promotion = session.get(Promotion, id)

    if promotion is None or promotion.deleted:
        promotion_logger.log_resource_not_found(id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The promotion was not found.",
        )

    return PromotionRead.model_validate(promotion)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=PromotionRead,
    response_description="The newly created Promotion",
    responses={
        409: {
            "description": "A promotion with that promo code already exists.",
        },
        422: {
            "description": "The provided PromotionCreate is malformed or invalid.",
        },
    },
)
def create_promotion(session: DbSession, payload: PromotionCreate) -> PromotionRead:
    """
    Create a new promotion.

    Returns the created promotion with its generated ID.

    """
    promotion = Promotion(**payload.model_dump())

    session.add(promotion)

    try:
        session.commit()
        promotion_logger.log_resource_created(promotion.id)
    except IntegrityError:
        session.rollback()
        promotion_logger.log_attrs_not_unique([Promotion.promo_code])
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A promotion with that promo code already exists.",
        ) from None

    session.refresh(promotion)

    return PromotionRead.model_validate(promotion)


@router.put(
    "/{id}",
    status_code=status.HTTP_200_OK,
    response_model=PromotionRead,
    response_description="The updated Promotion",
    responses={
        404: {
            "description": "The promotion was not found.",
        },
        409: {
            "description": "A promotion with that promo code already exists.",
        },
        422: {
            "description": (
                "The provided PromotionUpdate is malformed or invalid, "
                "or the provided path parameter is malformed or invalid."
            ),
        },
    },
)
def update_promotion(
    session: DbSession,
    id: PromotionId,
    payload: PromotionUpdate,
) -> PromotionRead:
    """
    Update a promotion.

    Returns the updated promotion.
    """
    promotion = session.get(Promotion, id)

    if promotion is None or promotion.deleted:
        promotion_logger.log_resource_not_found(id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The promotion was not found.",
        )

    update_data = payload.model_dump()

    for key, value in update_data.items():
        setattr(promotion, key, value)

    try:
        session.commit()
        promotion_logger.log_resource_updated(id)
    except IntegrityError:
        session.rollback()
        promotion_logger.log_attrs_not_unique([Promotion.promo_code])
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A promotion with that promo code already exists.",
        ) from None

    session.refresh(promotion)

    return PromotionRead.model_validate(promotion)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_description="The Promotion was deleted successfully",
    responses={
        404: {
            "description": "The promotion was not found.",
        },
        422: {
            "description": "The provided path parameter is malformed or invalid.",
        },
    },
)
def delete_promotion(
    session: DbSession,
    id: PromotionId,
) -> Response:
    """
    Soft delete a Promotion.

    The Promotion remains in the database for historical records
    but is no longer visible or available for use.
    """
    promotion = session.get(Promotion, id)

    if promotion is None or promotion.deleted:
        promotion_logger.log_resource_not_found(id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The promotion was not found.",
        )

    promotion.active = False
    promotion.deleted = True
    promotion.promo_code = f"{promotion.promo_code}deleted{promotion.id}"
    session.commit()

    promotion_logger.log_resource_deleted(id)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
