from fastapi import APIRouter, status

from wyrmwood_coffee.dependencies import DbSession  # <--- Fixed this line!
from wyrmwood_coffee.models.purchase import PurchaseCreate, PurchaseRead
from wyrmwood_coffee.services.purchases import process_purchase

router = APIRouter(tags=["purchases"])


@router.post(
    "/purchases",
    status_code=status.HTTP_201_CREATED,
    response_model=PurchaseRead,
    response_description="The newly created purchase",
    responses={
        404: {
            "description": "The customer was not found, or the promotion was not found."
        },
        422: {"description": "The provided PurchaseCreate is malformed or invalid."},
    },
)
def create_purchase(session: DbSession, payload: PurchaseCreate) -> PurchaseRead:
    """
    Process a new purchase.

    Looks up item prices, applies promotions, calculates taxes, and updates
    customer loyalty points.
    """
    purchase = process_purchase(session, payload)
    return PurchaseRead.model_validate(purchase)
