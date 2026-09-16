from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from wyrmwood_coffee.models.report import LowStockItemReport, UsageReport
from wyrmwood_coffee.repositories import inventory


def get_low_stock_report(session: Session) -> list[LowStockItemReport]:
    """Combined low-stock report across baked goods and ingredients"""
    baked_goods = inventory.get_low_stock_baked_goods(session)
    ingredients = inventory.get_low_stock_ingredients(session)

    reports = [
        LowStockItemReport(
            id=bg.id,
            name=bg.name,
            item_type="baked_good",
            quantity_on_hand=Decimal(bg.quantity_on_hand),
            reorder_threshold=Decimal(bg.reorder_threshold),
            reorder_quantity=Decimal(bg.reorder_quantity),
        )
        for bg in baked_goods
    ]
    reports += [
        LowStockItemReport(
            id=ingredient.id,
            name=ingredient.name,
            item_type="ingredient",
            quantity_on_hand=ingredient.quantity_on_hand,
            reorder_threshold=ingredient.reorder_threshold,
            reorder_quantity=ingredient.reorder_quantity,
        )
        for ingredient in ingredients
    ]
    return reports


def get_usage_report(
    session: Session, start_date: date, end_date: date
) -> list[UsageReport]:
    """Combined per-day usage report across baked goods and ingredients"""
    baked_good_rows = inventory.get_baked_good_usage(session, start_date, end_date)
    ingredient_rows = inventory.get_ingredient_usage(session, start_date, end_date)

    reports = [
        UsageReport(
            date=row.usage_date,
            item_id=row.baked_good_id,
            item_type="baked_good",
            usage_total=row.usage_total,
        )
        for row in baked_good_rows
    ]
    reports += [
        UsageReport(
            date=row.usage_date,
            item_id=row.ingredient_id,
            item_type="ingredient",
            usage_total=row.usage_total,
        )
        for row in ingredient_rows
    ]
    return reports
