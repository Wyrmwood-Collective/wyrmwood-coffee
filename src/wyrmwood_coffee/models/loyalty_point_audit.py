from datetime import datetime

from pydantic import BaseModel, ConfigDict
from sqlalchemy import DateTime, ForeignKey, Identity, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from wyrmwood_coffee.database import Base


class LoyaltyPointAudit(Base):
    __tablename__ = "loyalty_point_audits"

    id: Mapped[int] = mapped_column(
        Integer,
        Identity(always=True),
        primary_key=True,
    )
    customer_id: Mapped[int | None] = mapped_column(
        ForeignKey("customers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    points_expired: Mapped[int] = mapped_column(Integer, nullable=False)

    reason: Mapped[str] = mapped_column(String, nullable=False)

    expired_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class LoyaltyPointAuditBase(BaseModel):
    """Base model for loyalty point audit records."""

    model_config = ConfigDict(from_attributes=True)

    points_expired: int
    reason: str
    expired_at: datetime


class LoyaltyPointAuditCreate(LoyaltyPointAuditBase):
    customer_id: int


class LoyaltyPointAuditRead(LoyaltyPointAuditBase):
    id: int
    customer_id: int | None
    created_at: datetime
