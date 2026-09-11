"""Merge conflicting heads

Revision ID: e00843adab64
Revises: 011c4a6b3563, e44c8b475e6a
Create Date: 2026-09-14 09:23:58.249106

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "e00843adab64"
down_revision: str | Sequence[str] | None = ("011c4a6b3563", "e44c8b475e6a")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
