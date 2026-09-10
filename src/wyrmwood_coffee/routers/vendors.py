import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from wyrmwood_coffee.dependencies import DbSession, require_manager
from wyrmwood_coffee.logging import ResourceLogger
from wyrmwood_coffee.models.ingredient import Ingredient
from wyrmwood_coffee.models.vendor import (
    Vendor,
    VendorContact,
    VendorContactRead,
    VendorCreate,
    VendorRead,
    VendorUpdate,
)

vendor_logger = ResourceLogger(logging.getLogger(__name__), Vendor)
vendor_contact_logger = ResourceLogger(logging.getLogger(__name__), VendorContact)
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
    vendors = session.scalars(
        select(Vendor)
        .where(~Vendor.is_deleted)
        .options(selectinload(Vendor.contacts.and_(~VendorContact.is_deleted)))
    ).all()

    return [VendorRead.model_validate(v, from_attributes=True) for v in vendors]


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=VendorRead,
    response_description="The newly created Vendor",
    responses={
        401: {"description": "Could not validate credentials."},
        403: {"description": "Insufficient permissions."},
        422: {"description": "The provided VendorCreate is malformed or invalid."},
    },
    dependencies=[Depends(require_manager)],
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


@router.put(
    "/{id}",
    status_code=status.HTTP_200_OK,
    response_model=VendorRead,
    response_description="The updated vendor",
    responses={
        401: {"description": "Could not validate credentials."},
        403: {"description": "Insufficient permissions."},
        404: {
            "description": "The Vendor was not found, "
            "or the VendorContact was not found."
        },
        422: {
            "description": "The provided VendorUpdate is malformed or invalid, "
            "or the provided path parameter is malformed or invalid, "
            "or the VendorContact belongs to another Vendor."
        },
    },
    dependencies=[Depends(require_manager)],
)
def update_vendor(session: DbSession, id: int, payload: VendorUpdate) -> VendorRead:
    """
    Update an existing vendor and its contacts.

    The list of contacts is processed in the following way:
    - If the contact has an ID, the existing contact with that ID will be updated.
    - If the contact does not have an ID, a new contact will be created.
    - Any of the vendor's existing contacts without a corresponding contact in
      the request will be deleted.
    """

    vendor = session.get(Vendor, id)
    if not vendor or vendor.is_deleted:
        vendor_logger.log_resource_not_found(id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not find vendor with ID {id}",
        )

    # save for deferred logging calls
    deleted_contact_ids = []
    created_contacts = []

    # delete existing contacts not present in the payload
    for contact in [c for c in vendor.contacts if not c.is_deleted]:
        if contact.id not in [c.id for c in payload.contacts]:
            deleted_contact_ids.append(contact.id)
            contact.is_deleted = True

    for contact in payload.contacts:
        # if the payload contact has an ID, update
        if contact.id:
            updated_contact = session.get(VendorContact, contact.id)
            if not updated_contact or updated_contact.is_deleted:
                vendor_contact_logger.log_resource_not_found(contact.id)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Could not find contact with ID {contact.id}",
                )
            elif updated_contact.vendor != vendor:
                vendor_contact_logger.log_resource_belongs_to_another(
                    contact.id, Vendor, vendor.id, updated_contact.vendor.id
                )
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail=f"Contact {contact.id} does not belong to vendor {vendor.id}",  # noqa: E501
                )

            for field, value in contact.model_dump().items():
                setattr(updated_contact, field, value)

        # if the payload contact does not have an ID, create
        else:
            new_contact = VendorContact(**contact.model_dump())
            new_contact.vendor_id = vendor.id
            session.add(new_contact)
            created_contacts.append(new_contact)

    for field, value in payload.model_dump().items():
        if field == "contacts":
            continue
        setattr(vendor, field, value)

    session.commit()
    session.refresh(vendor)

    for cid in deleted_contact_ids:
        vendor_contact_logger.log_resource_deleted(cid)
    for c in created_contacts:
        vendor_contact_logger.log_resource_created(c.id)
    vendor_logger.log_resource_updated(vendor.id)

    return VendorRead.model_validate(vendor).model_copy(
        update={
            "contacts": [
                VendorContactRead.model_validate(contact)
                for contact in vendor.contacts
                if not contact.is_deleted
            ]
        }
    )


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_description="The vendor was deleted successfully.",
    responses={
        401: {"description": "Could not validate credentials."},
        403: {"description": "Insufficient permissions."},
        404: {"description": "The vendor was not found."},
        409: {"description": "The vendor has associated ingredients."},
        422: {"description": "The provided path parameter is malformed or invalid."},
    },
    dependencies=[Depends(require_manager)],
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
