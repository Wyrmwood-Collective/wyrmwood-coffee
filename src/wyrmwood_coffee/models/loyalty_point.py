from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import DateTime, ForeignKey, Identity, Integer
from sqlalchemy.orm import Mapped, mapped_column

from wyrmwood_coffee.database import Base


class LoyaltyPointAudit(Base):
    __tablename__ = "loyalty_point_audit"

    id: Mapped[int] = mapped_column(
        Integer,
        Identity(always=True),
        primary_key=True,
    )
    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id"),
        nullable=False,
    )
    points_expired: Mapped[int] = mapped_column(Integer, nullable=False)
    expired_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class LoyaltyPointAuditCreate(BaseModel):
    """Request model used when creating a new loyalty point audit record."""

    model_config = ConfigDict(from_attributes=True)

    customer_id: int = Field(gt=0)
    points_expired: int = Field(gt=0)
    expired_at: datetime


class LoyaltyPointAuditRead(LoyaltyPointAuditCreate):
    """Response model used when reading a loyalty point audit record."""

    id: int = Field(gt=0)
