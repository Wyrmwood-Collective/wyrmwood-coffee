import logging

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from wyrmwood_coffee.dependencies import DbSession
from wyrmwood_coffee.logging import ResourceLogger
from wyrmwood_coffee.models.ingredient import Ingredient
from wyrmwood_coffee.models.vendor import (
    Vendor,
    VendorContact,
    VendorCreate,
    VendorRead,
)

vendor_logger = ResourceLogger(logging.getLogger(__name__), Vendor)
router = APIRouter()


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=list[VendorRead],
    response_description="A list of all vendors",
)
def list_vendors(session: DbSession) -> list[VendorRead]:
    """
    Retrieve a list of all vendors.
    """
    vendors = session.scalars(select(Vendor).where(~Vendor.is_deleted)).all()
    return [VendorRead.model_validate(v, from_attributes=True) for v in vendors]


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

    vendor_logger.log_resource_created(new_vendor.id)
    return new_vendor


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_description="The vendor was deleted successfully.",
    responses={
        404: {"description": "The vendor was not found."},
        409: {"description": "The vendor has associated ingredients."},
        422: {"description": "The provided path parameter is malformed or invalid."},
    },
)
def delete_vendor(session: DbSession, id: int):
    """Delete the vendor and its associated contacts."""
    vendor = session.get(Vendor, id)

    if not vendor or vendor.is_deleted:
        vendor_logger.log_resource_not_found(id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The vendor was not found.",
        )

    if any(not i.is_deleted for i in vendor.ingredients):
        vendor_logger.log_deletion_conflict(
            vendor.id,
            "vendor_has_ingredients",
            {Ingredient: [i.id for i in vendor.ingredients]},
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The vendor has associated ingredients.",
        )

    for contact in vendor.contacts:
        contact.is_deleted = True
    vendor.is_deleted = True
    session.commit()
    vendor_logger.log_resource_deleted(vendor.id)
