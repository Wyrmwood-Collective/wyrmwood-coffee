import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from wyrmwood_coffee.database import Base
from wyrmwood_coffee.models.baked_goods import BakedGood
from wyrmwood_coffee.models.ingredient import Ingredient


class InventoryChangeType(enum.StrEnum):
    RECEIVE = "RECEIVE"
    SALE = "SALE"
    ADJUSTMENT = "ADJUSTMENT"
    WASTE = "WASTE"


class InventoryTransaction(Base):
    """The audit record of a single stock change."""

    __tablename__ = "inventory_transactions"

    __table_args__ = (
        CheckConstraint(
            "(baked_good_id IS NOT NULL AND ingredient_id IS NULL) OR "
            "(baked_good_id IS NULL AND ingredient_id IS NOT NULL)",
            name="ck_inventory_transaction_exclusive_item",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    baked_good_id: Mapped[int | None] = mapped_column(
        ForeignKey("baked_goods.id"), nullable=True, index=True
    )
    ingredient_id: Mapped[int | None] = mapped_column(
        ForeignKey("ingredients.id"), nullable=True, index=True
    )
    change_type: Mapped[InventoryChangeType] = mapped_column(String, nullable=False)
    quantity_delta: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2), nullable=False
    )
    reference_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    baked_good: Mapped["BakedGood | None"] = relationship()
    ingredient: Mapped["Ingredient | None"] = relationship()
