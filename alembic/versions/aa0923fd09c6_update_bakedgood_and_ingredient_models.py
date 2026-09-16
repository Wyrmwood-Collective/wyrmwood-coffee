"""Update BakedGood and Ingredient models

Revision ID: aa0923fd09c6
Revises: 9511d0dd4bf0
Create Date: 2026-09-14 14:42:31.901521

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "aa0923fd09c6"
down_revision: str | Sequence[str] | None = "9511d0dd4bf0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "baked_goods", sa.Column("quantity_on_hand", sa.Integer(), nullable=True)
    )
    op.add_column(
        "baked_goods", sa.Column("reorder_threshold", sa.Integer(), nullable=True)
    )
    op.add_column(
        "baked_goods", sa.Column("reorder_quantity", sa.Integer(), nullable=True)
    )
    op.add_column(
        "ingredients",
        sa.Column("quantity_on_hand", sa.Numeric(precision=10, scale=2), nullable=True),
    )
    op.add_column(
        "ingredients",
        sa.Column(
            "reorder_threshold", sa.Numeric(precision=10, scale=2), nullable=True
        ),
    )
    op.add_column(
        "ingredients",
        sa.Column("reorder_quantity", sa.Numeric(precision=10, scale=2), nullable=True),
    )

    op.execute(
        "UPDATE baked_goods SET quantity_on_hand = 0, "
        "reorder_threshold = 0, reorder_quantity = 0"
    )
    op.execute(
        "UPDATE ingredients SET quantity_on_hand = 0, "
        "reorder_threshold = 0, reorder_quantity = 0"
    )

    op.alter_column("baked_goods", "quantity_on_hand", nullable=False)
    op.alter_column("baked_goods", "reorder_threshold", nullable=False)
    op.alter_column("baked_goods", "reorder_quantity", nullable=False)
    op.alter_column("ingredients", "quantity_on_hand", nullable=False)
    op.alter_column("ingredients", "reorder_threshold", nullable=False)
    op.alter_column("ingredients", "reorder_quantity", nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("ingredients", "reorder_quantity")
    op.drop_column("ingredients", "reorder_threshold")
    op.drop_column("ingredients", "quantity_on_hand")
    op.drop_column("baked_goods", "reorder_quantity")
    op.drop_column("baked_goods", "reorder_threshold")
    op.drop_column("baked_goods", "quantity_on_hand")
