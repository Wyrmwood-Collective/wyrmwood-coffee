import logging

from fastapi import APIRouter, Depends, status

from wyrmwood_coffee.dependencies import DbSession, require_manager
from wyrmwood_coffee.logging import ResourceLogger
from wyrmwood_coffee.models.baked_goods import BakedGood, BakedGoodCreate, BakedGoodRead

baked_good_logger = ResourceLogger(logging.getLogger(__name__), BakedGood)
router = APIRouter()


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=BakedGoodRead,
    response_description="The newly created baked good",
    responses={
        401: {"description": "Could not validate credentials."},
        403: {"description": "Insufficient permissions."},
        422: {"description": "The provided BakedGoodCreate is malformed or invalid."},
    },
    dependencies=[Depends(require_manager)],
)
def create_baked_good(session: DbSession, payload: BakedGoodCreate) -> BakedGoodRead:
    """
    Create a new baked good.

    Returns the created baked good, including its generated ID.
    """
    new_baked_good = BakedGood(**payload.model_dump(mode="json"))
    session.add(new_baked_good)
    session.commit()

    baked_good_logger.log_resource_created(new_baked_good.id)
    return BakedGoodRead.model_validate(new_baked_good)
