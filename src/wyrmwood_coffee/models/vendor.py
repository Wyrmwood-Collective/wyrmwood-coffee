from typing import TYPE_CHECKING, Annotated

from pydantic import BaseModel, Field, StringConstraints
from sqlalchemy import CheckConstraint, ForeignKey, String, true
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

    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"))
    vendor: Mapped["Vendor"] = relationship(back_populates="contacts")


class VendorContactCreate(BaseModel):
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
    vendor_id: int = Field(
        title="Vendor ID", description="The ID of this contact's vendor"
    )


class VendorContactCreateNested(BaseModel):
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


class VendorContactRead(BaseModel):
    id: int = Field(title="Vendor Contact ID", description="The vendor contact ID")
    name: str = Field(
        title="Vendor Contact Name", description="The vendor contact's name"
    )
    role: str = Field(
        title="Vendor Contact Role", description="The vendor contact's role"
    )
    email: str = Field(
        title="Vendor Contact Email", description="The vendor contact's email"
    )
    phone: str = Field(
        title="Vendor Contact Phone", description="The vendor contact's phone"
    )
    vendor_id: int = Field(
        title="Vendor ID", description="The ID of this contact's vendor"
    )


class Vendor(Base):
    __tablename__ = "vendors"

    id: Mapped[int] = mapped_column(primary_key=True)
    active: Mapped[bool] = mapped_column(server_default=true())
    name: Mapped[str] = mapped_column(String, nullable=False)

    contacts: Mapped[list["VendorContact"]] = relationship(back_populates="vendor")
    ingredients: Mapped[list["Ingredient"]] = relationship(back_populates="vendor")


class VendorCreate(BaseModel):
    active: bool = Field(
        default=True, title="Active", description="Whether or not the vendor is active"
    )
    name: Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)] = (
        Field(title="Vendor Name", description="The name of the vendor")
    )
    contacts: list[VendorContactCreateNested] = Field(
        min_length=1,
        title="Vendor Contacts",
        description="The vendor's contacts",
    )


class VendorRead(BaseModel):
    id: int = Field(title="Vendor ID", description="The vendor's ID")
    active: bool = Field(
        title="Active", description="Whether or not the vendor is active"
    )
    name: Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)] = (
        Field(title="Vendor Name", description="The name of the vendor")
    )
    contacts: list[VendorContactRead] = Field(
        title="Vendor Contacts", description="The list of this vendor's contacts"
    )
