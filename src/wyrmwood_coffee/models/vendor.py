from typing import TYPE_CHECKING, Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator
from sqlalchemy import Boolean, CheckConstraint, ForeignKey, String, false, true
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from wyrmwood_coffee.database import Base

if TYPE_CHECKING:
    from wyrmwood_coffee.models.ingredient import Ingredient


class VendorContact(Base):
    __tablename__ = "vendor_contacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        String, CheckConstraint("length(name) >= 1"), nullable=False
    )
    role: Mapped[str] = mapped_column(
        String, CheckConstraint("length(role) >= 1"), nullable=False
    )
    email: Mapped[str] = mapped_column(
        String, CheckConstraint("email ~ '.+@.+'"), nullable=False
    )
    phone: Mapped[str] = mapped_column(
        String, CheckConstraint("phone ~ '\\d{3}-\\d{3}-\\d{4}'"), nullable=False
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=false())

    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"))
    vendor: Mapped["Vendor"] = relationship(back_populates="contacts")


class VendorContactBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)] = (
        Field(title="Vendor Contact Name", description="The vendor contact's name")
    )
    role: Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)] = (
        Field(title="Vendor Contact Role", description="The vendor contact's role")
    )
    email: Annotated[str, StringConstraints(pattern=r".+@.+")] = Field(
        title="Vendor Contact Email", description="The vendor contact's email"
    )
    phone: Annotated[str, StringConstraints(pattern=r"\d{3}-\d{3}-\d{4}")] = Field(
        title="Vendor Contact Phone", description="The vendor contact's phone"
    )


class VendorContactCreate(VendorContactBase):
    vendor_id: int = Field(
        title="Vendor ID", description="The ID of this contact's vendor"
    )


class VendorContactCreateNested(VendorContactBase):
    """Does not include vendor_id"""


class VendorContactUpdateNested(VendorContactBase):
    id: int | None = Field(
        title="Vendor Contact ID", description="The vendor contact ID", default=None
    )


class VendorContactRead(VendorContactCreate):
    id: int = Field(title="Vendor Contact ID", description="The vendor contact ID")


class Vendor(Base):
    __tablename__ = "vendors"

    id: Mapped[int] = mapped_column(primary_key=True)
    active: Mapped[bool] = mapped_column(server_default=true())
    name: Mapped[str] = mapped_column(String, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=false())

    contacts: Mapped[list["VendorContact"]] = relationship(back_populates="vendor")
    ingredients: Mapped[list["Ingredient"]] = relationship(back_populates="vendor")


class VendorBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    active: bool = Field(
        default=True, title="Active", description="Whether or not the vendor is active"
    )
    name: Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)] = (
        Field(title="Vendor Name", description="The name of the vendor")
    )


class VendorCreate(VendorBase):
    contacts: list[VendorContactCreateNested] = Field(
        min_length=1,
        title="Vendor Contacts",
        description="The vendor's contacts",
    )


class VendorUpdate(VendorBase):
    contacts: list[VendorContactUpdateNested] = Field(
        min_length=1,
        title="Vendor Contacts",
        description="The vendor's contacts",
    )

    @model_validator(mode="after")
    def check_no_duplicate_ids(self) -> Self:
        seen_ids = set()
        duplicate_ids = set()

        for contact in self.contacts:
            if contact.id in seen_ids:
                duplicate_ids.add(contact.id)
            else:
                seen_ids.add(contact.id)

        if duplicate_ids:
            raise ValueError(
                f"Contacts list contains duplicate contact IDs: {duplicate_ids}"
            )
        return self


class VendorRead(VendorBase):
    id: int = Field(title="Vendor ID", description="The vendor's ID")
    contacts: list[VendorContactRead] = Field(
        min_length=1,
        title="Vendor Contacts",
        description="The vendor's contacts",
    )
