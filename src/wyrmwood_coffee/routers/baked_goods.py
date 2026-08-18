from fastapi import APIRouter, status

from wyrmwood_coffee.dependencies import DbSession
from wyrmwood_coffee.models.baked_goods import BakedGood, BakedGoodCreate, BakedGoodRead

router = APIRouter()


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=BakedGoodRead,
    response_description="The newly created baked good",
    responses={
        422: {"description": "The provided BakedGoodCreate is malformed or invalid."}
    },
)
def create_baked_good(session: DbSession, payload: BakedGoodCreate) -> BakedGoodRead:
    """
    Create a new baked good.

    Returns the created baked good, including its generated ID.
    """
    new_baked_good = BakedGood(**payload.model_dump(mode="json"))
    session.add(new_baked_good)
    session.commit()
    return BakedGoodRead.model_validate(new_baked_good)
