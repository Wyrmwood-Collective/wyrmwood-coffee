from fastapi import APIRouter, status

from wyrmwood_coffee.dependencies import DbSession
from wyrmwood_coffee.models.vendor import (
    Vendor,
    VendorContact,
    VendorCreate,
    VendorRead,
)

router = APIRouter()


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=VendorRead,
    response_description="The newly created Vendor",
    responses={
        422: {"description": "The provided VendorCreate is malformed or invalid."}
    },
)
def create_vendor(session: DbSession, payload: VendorCreate):
    """
    Create a new vendor, along with its initial set of contacts.

    Returns the created vendor, including generated IDs for the vendor
    and each vendor contact.
    """
    new_vendor = Vendor(
        name=payload.name,
        active=payload.active,
        contacts=[
            VendorContact(**contact.model_dump(mode="json"))
            for contact in payload.contacts
        ],
    )
    session.add(new_vendor)
    session.commit()
    return new_vendor
