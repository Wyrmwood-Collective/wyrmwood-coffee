from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

TOKEN_ACCESS_TOKEN_TITLE = "Access Token"
TOKEN_ACCESS_TOKEN_DESC = "The JWT access token for the authenticated employee"

TOKEN_TYPE_TITLE = "Token Type"
TOKEN_TYPE_DESC = "The type of the access token"


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
