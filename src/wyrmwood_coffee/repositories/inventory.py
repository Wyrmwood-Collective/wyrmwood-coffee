from collections.abc import Sequence
from datetime import date

from sqlalchemy import Row, func, select
from sqlalchemy.orm import Session

from wyrmwood_coffee.models.baked_goods import BakedGood
from wyrmwood_coffee.models.ingredient import Ingredient
from wyrmwood_coffee.models.inventory_transaction import (
    InventoryChangeType,
    InventoryTransaction,
)


def get_low_stock_baked_goods(session: Session) -> Sequence[BakedGood]:
    """Active baked goods at or below their reorder threshold"""
    stmt = select(BakedGood).where(
        BakedGood.active.is_(True),
        BakedGood.quantity_on_hand <= BakedGood.reorder_threshold,
    )
    return session.scalars(stmt).all()


def get_low_stock_ingredients(session: Session) -> Sequence[Ingredient]:
    """Active, non-deleted ingredients at or below their reorder threshold"""
    stmt = select(Ingredient).where(
        Ingredient.active.is_(True),
        Ingredient.is_deleted.is_(False),
        Ingredient.quantity_on_hand <= Ingredient.reorder_threshold,
    )
    return session.scalars(stmt).all()


def get_baked_good_usage(
    session: Session, start_date: date, end_date: date
) -> Sequence[Row]:
    """Sale totals for baked goods per day"""
    day = func.date(InventoryTransaction.created_at)
    stmt = (
        select(
            InventoryTransaction.baked_good_id,
            day.label("usage_date"),
            func.sum(-InventoryTransaction.quantity_delta).label("usage_total"),
        )
        .where(
            InventoryTransaction.change_type == InventoryChangeType.SALE,
            InventoryTransaction.baked_good_id.is_not(None),
            InventoryTransaction.created_at >= start_date,
            InventoryTransaction.created_at < end_date,
        )
        .group_by(InventoryTransaction.baked_good_id, day)
        .order_by(day)
    )
    return session.execute(stmt).all()


def get_ingredient_usage(
    session: Session, start_date: date, end_date: date
) -> Sequence[Row]:
    """Sale totals for ingredients per day"""
    day = func.date(InventoryTransaction.created_at)
    stmt = (
        select(
            InventoryTransaction.ingredient_id,
            day.label("usage_date"),
            func.sum(-InventoryTransaction.quantity_delta).label("usage_total"),
        )
        .where(
            InventoryTransaction.change_type == InventoryChangeType.SALE,
            InventoryTransaction.ingredient_id.is_not(None),
            InventoryTransaction.created_at >= start_date,
            InventoryTransaction.created_at < end_date,
        )
        .group_by(InventoryTransaction.ingredient_id, day)
        .order_by(day)
    )
    return session.execute(stmt).all()
