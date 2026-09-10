from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints
from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from wyrmwood_coffee.database import Base

TOKEN_ACCESS_TOKEN_TITLE = "Access Token"
TOKEN_ACCESS_TOKEN_DESC = "The JWT access token for the authenticated employee"

TOKEN_TYPE_TITLE = "Token Type"
TOKEN_TYPE_DESC = "The type of the access token"


class BlacklistedToken(Base):
    __tablename__ = "blacklisted_tokens"

    jti: Mapped[str] = mapped_column(String, primary_key=True)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    blacklisted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class Token(BaseModel):
    """Token schema returned from the system."""

    access_token: Annotated[str, StringConstraints(min_length=1)] = Field(
        title=TOKEN_ACCESS_TOKEN_TITLE,
        description=TOKEN_ACCESS_TOKEN_DESC,
    )
    token_type: Annotated[str, StringConstraints(min_length=1)] = Field(
        title=TOKEN_TYPE_TITLE,
        description=TOKEN_TYPE_DESC,
    )
