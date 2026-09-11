from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from wyrmwood_coffee.database import Base

# ==========================================
# SQLAlchemy Models
# ==========================================


class Purchase(Base):
    __tablename__ = "purchases"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id"))
    promo_id: Mapped[int | None] = mapped_column(ForeignKey("promotions.id"))

    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    tax: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    items: Mapped[list["PurchaseItem"]] = relationship(
        back_populates="purchase", cascade="all, delete-orphan"
    )


class PurchaseItem(Base):
    __tablename__ = "purchase_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    purchase_id: Mapped[int] = mapped_column(ForeignKey("purchases.id"))

    name: Mapped[str]
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    purchase: Mapped[Purchase] = relationship(back_populates="items")


# ==========================================
# Pydantic Schemas
# ==========================================


class PurchaseItemCreateNested(BaseModel):
    """Input schema for an item nested inside a PurchaseCreate payload."""

    name: str = Field(min_length=1)
    quantity: int = Field(gt=0, default=1)


class PurchaseItemRead(BaseModel):
    id: int
    purchase_id: int
    name: str
    quantity: int
    unit_price: Decimal
    model_config = ConfigDict(from_attributes=True)


class PurchaseCreate(BaseModel):
    customer_id: int | None = None
    promo_id: int | None = None
    items: list[PurchaseItemCreateNested] = Field(min_length=1)


class PurchaseRead(BaseModel):
    id: int
    customer_id: int | None
    promo_id: int | None
    subtotal: Decimal
    tax: Decimal
    total: Decimal
    created_at: datetime
    items: list[PurchaseItemRead]
    model_config = ConfigDict(from_attributes=True)
