"""Add purchase histories

Revision ID: 69890016e1f4
Revises: 775e6fa11fa6
Create Date: 2026-09-09 11:32:17.889978

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "69890016e1f4"
down_revision: str | Sequence[str] | None = "775e6fa11fa6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "purchase_histories",
        sa.Column(
            "id",
            sa.Integer(),
            sa.Identity(always=True),
            nullable=False,
        ),
        sa.Column(
            "customer_id",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "item_type",
            sa.String(),
            nullable=False,
        ),
        sa.Column(
            "item_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "quantity",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "loyalty_points_earned",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "purchased_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.CheckConstraint(
            "item_type IN ('drink', 'baked_good')",
            name="ck_purchase_histories_item_type",
        ),
        sa.CheckConstraint(
            "item_id > 0",
            name="ck_purchase_histories_item_id_positive",
        ),
        sa.CheckConstraint(
            "loyalty_points_earned >= 0",
            name="ck_purchase_histories_loyalty_points_non_negative",
        ),
        sa.CheckConstraint(
            "quantity > 0",
            name="ck_purchase_histories_quantity_positive",
        ),
        sa.ForeignKeyConstraint(
            ["customer_id"],
            ["customers.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("purchase_histories")
    op.drop_table("loyalty_point_audits")
    # ### end Alembic commands ###
