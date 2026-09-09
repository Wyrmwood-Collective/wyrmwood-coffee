from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Identity, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from wyrmwood_coffee.database import Base


class PurchaseHistory(Base):
    __tablename__ = "purchase_histories"

    __table_args__ = (
        CheckConstraint(
            "item_type IN ('drink', 'baked_good')",
            name="ck_purchase_histories_item_type",
        ),
        CheckConstraint(
            "item_id > 0",
            name="ck_purchase_histories_item_id_positive",
        ),
        CheckConstraint(
            "quantity > 0",
            name="ck_purchase_histories_quantity_positive",
        ),
        CheckConstraint(
            "loyalty_points_earned >= 0",
            name="ck_purchase_histories_loyalty_points_non_negative",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        Identity(always=True),
        primary_key=True,
    )
    customer_id: Mapped[int | None] = mapped_column(
        ForeignKey("customers.id"),
        nullable=True,
    )
    item_type: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    item_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    loyalty_points_earned: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    purchased_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
