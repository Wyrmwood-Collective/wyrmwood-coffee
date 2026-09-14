import logging

from fastapi import APIRouter, Depends, status

from wyrmwood_coffee.dependencies import DbSession, require_auth
from wyrmwood_coffee.logging import ResourceLogger
from wyrmwood_coffee.models.purchase import Purchase, PurchaseCreate, PurchaseRead
from wyrmwood_coffee.services.purchases import process_purchase

# Instantiate the logger just like in customers.py
purchase_logger = ResourceLogger(logging.getLogger(__name__), Purchase)
router = APIRouter(tags=["purchases"])


@router.post(
    "/purchases",
    status_code=status.HTTP_201_CREATED,
    response_model=PurchaseRead,
    response_description="The newly created purchase",
    responses={
        401: {"description": "Could not validate credentials."},
        403: {"description": "Insufficient permissions."},
        404: {
            "description": "The customer was not found, or the promotion was not found."
        },
        422: {
            "description": (
                "The provided PurchaseCreate is malformed or invalid, "
                "an unknown item name was provided, or the promotion "
                "is inactive/expired."
            )
        },
    },
    dependencies=[Depends(require_auth)],
)
def create_purchase(session: DbSession, payload: PurchaseCreate) -> PurchaseRead:
    """
    Process a new purchase.

    Looks up item prices, applies promotions, calculates taxes, and updates
    customer loyalty points.
    """
    purchase = process_purchase(session, payload)

    # Log the successful creation using your team's custom method
    purchase_logger.log_resource_created(purchase.id)

    return PurchaseRead.model_validate(purchase)
