# test/test_reports_services.py

from datetime import date, datetime
from decimal import Decimal

import pytest

from wyrmwood_coffee.models.inventory_transaction import (
    InventoryChangeType,
    InventoryTransaction,
)
from wyrmwood_coffee.services.reports import (
    get_low_stock_report,
    get_usage_report,
)


@pytest.fixture()
def make_inventory_transaction(db_session):
    def _make_transaction(**kwargs):
        defaults = {
            "change_type": InventoryChangeType.SALE,
            "quantity_delta": Decimal("-1.00"),
            "reference_id": None,
            "created_at": datetime(2026, 6, 15, 12, 0, 0),
        }
        defaults.update(kwargs)
        txn = InventoryTransaction(**defaults)
        db_session.add(txn)
        db_session.commit()
        db_session.refresh(txn)
        return txn

    return _make_transaction


# ==========================================
# Get Low Stock Report
# ==========================================


def test_get_low_stock_report_with_ingredient_at_threshold_should_return_ingredient(
    db_session, make_ingredient
):
    ingredient = make_ingredient(quantity_on_hand=10, reorder_threshold=10)
    reports = get_low_stock_report(db_session)

    ids = [report.id for report in reports if report.item_type == "ingredient"]
    assert ingredient.id in ids


def test_get_low_stock_report_with_ingredient_above_threshold_should_exclude_ingredient(
    db_session, make_ingredient
):
    ingredient = make_ingredient(quantity_on_hand=50, reorder_threshold=10)
    reports = get_low_stock_report(db_session)

    ids = [report.id for report in reports if report.item_type == "ingredient"]
    assert ingredient.id not in ids


def test_get_low_stock_report_with_baked_good_at_threshold_should_return_baked_good(
    db_session, make_baked_good
):
    baked_good = make_baked_good(quantity_on_hand=5, reorder_threshold=5)
    reports = get_low_stock_report(db_session)

    ids = [report.id for report in reports if report.item_type == "baked_good"]
    assert baked_good.id in ids


def test_get_low_stock_report_with_baked_good_above_threshold_should_exclude_baked_good(
    db_session, make_baked_good
):
    baked_good = make_baked_good(quantity_on_hand=30, reorder_threshold=20)
    reports = get_low_stock_report(db_session)

    ids = [report.id for report in reports if report.item_type == "baked_good"]
    assert baked_good.id not in ids


def test_get_low_stock_report_with_inactive_ingredient_should_exclude_ingredient(
    db_session, make_ingredient
):
    ingredient = make_ingredient(active=False, quantity_on_hand=4, reorder_threshold=12)
    reports = get_low_stock_report(db_session)

    ids = [report.id for report in reports]
    assert ingredient.id not in ids


def test_get_low_stock_report_with_soft_deleted_ingredient_should_exclude_ingredient(
    db_session, make_ingredient
):
    ingredient = make_ingredient(quantity_on_hand=2, reorder_threshold=8)
    ingredient.is_deleted = True
    db_session.commit()

    reports = get_low_stock_report(db_session)
    ids = [report.id for report in reports]
    assert ingredient.id not in ids


def test_get_low_stock_report_with_inactive_baked_good_should_exclude_baked_good(
    db_session, make_baked_good
):
    baked_good = make_baked_good(active=False, quantity_on_hand=6, reorder_threshold=9)
    reports = get_low_stock_report(db_session)

    ids = [report.id for report in reports]
    assert baked_good.id not in ids


def test_get_low_stock_report_with_both_item_types_at_threshold_should_return_items(
    db_session, make_ingredient, make_baked_good
):
    ingredient = make_ingredient(quantity_on_hand=8, reorder_threshold=16)
    baked_good = make_baked_good(quantity_on_hand=1, reorder_threshold=2)
    reports = get_low_stock_report(db_session)

    ingredient_ids = [
        report.id for report in reports if report.item_type == "ingredient"
    ]
    baked_good_ids = [
        report.id for report in reports if report.item_type == "baked_good"
    ]

    assert ingredient.id in ingredient_ids
    assert baked_good.id in baked_good_ids


# ==========================================
# Get Usage Report
# ==========================================


def test_get_usage_report_should_return_sale_transaction(
    db_session, make_ingredient, make_inventory_transaction
):
    ingredient = make_ingredient()
    make_inventory_transaction(
        ingredient_id=ingredient.id,
        change_type="SALE",
        quantity_delta=Decimal("-5.00"),
        created_at=datetime(2026, 6, 23, 5, 0, 0),
    )

    reports = get_usage_report(
        session=db_session, start_date=date(2026, 6, 20), end_date=date(2026, 6, 26)
    )

    item_reports = [r for r in reports if r.item_id == ingredient.id]
    assert len(item_reports) == 1
    assert item_reports[0].usage_total == Decimal("5.00")
    assert item_reports[0].item_type == "ingredient"
    assert item_reports[0].date == date(2026, 6, 23)


@pytest.mark.parametrize("excluded_change_type", ["RECEIVE", "ADJUSTMENT", "WASTE"])
def test_get_usage_report_with_excluded_change_type_should_return_empty(
    db_session, make_ingredient, make_inventory_transaction, excluded_change_type
):
    ingredient = make_ingredient()
    make_inventory_transaction(
        ingredient_id=ingredient.id,
        change_type=excluded_change_type,
        quantity_delta=Decimal("10.00"),
        created_at=datetime(2026, 5, 2, 7, 0, 0),
    )

    reports = get_usage_report(
        session=db_session, start_date=date(2026, 5, 1), end_date=date(2026, 5, 7)
    )

    item_reports = [r for r in reports if r.item_id == ingredient.id]
    assert item_reports == []


def test_get_usage_report_with_multiple_sales_should_return_usage_aggregate(
    db_session, make_ingredient, make_inventory_transaction
):
    ingredient = make_ingredient()
    make_inventory_transaction(
        ingredient_id=ingredient.id,
        change_type="SALE",
        quantity_delta=Decimal("-4.00"),
        created_at=datetime(2026, 8, 15, 9, 0, 0),
    )
    make_inventory_transaction(
        ingredient_id=ingredient.id,
        change_type="SALE",
        quantity_delta=Decimal("-7.75"),
        created_at=datetime(2026, 8, 15, 21, 0, 0),
    )

    reports = get_usage_report(
        session=db_session, start_date=date(2026, 8, 12), end_date=date(2026, 8, 18)
    )

    item_reports = [r for r in reports if r.item_id == ingredient.id]
    assert len(item_reports) == 1
    assert item_reports[0].usage_total == Decimal("11.75")


def test_get_usage_report_with_sales_on_different_days_should_separate_sum_sales_by_day(
    db_session, make_ingredient, make_inventory_transaction
):
    ingredient = make_ingredient()
    # "2026-04-14" Transactions
    make_inventory_transaction(
        ingredient_id=ingredient.id,
        change_type="SALE",
        quantity_delta=Decimal("-2.00"),
        created_at=datetime(2026, 4, 14, 19, 0, 0),
    )
    make_inventory_transaction(
        ingredient_id=ingredient.id,
        change_type="SALE",
        quantity_delta=Decimal("-1.50"),
        created_at=datetime(2026, 4, 14, 10, 0, 0),
    )
    # "2026-04-16" Transactions
    make_inventory_transaction(
        ingredient_id=ingredient.id,
        change_type="SALE",
        quantity_delta=Decimal("-6.25"),
        created_at=datetime(2026, 4, 16, 12, 0, 0),
    )
    make_inventory_transaction(
        ingredient_id=ingredient.id,
        change_type="SALE",
        quantity_delta=Decimal("-5.75"),
        created_at=datetime(2026, 4, 16, 18, 0, 0),
    )

    reports = get_usage_report(
        session=db_session, start_date=date(2026, 4, 11), end_date=date(2026, 4, 17)
    )

    item_reports = sorted(
        (r for r in reports if r.item_id == ingredient.id),
        key=lambda r: r.date,
    )

    assert len(item_reports) == 2
    assert item_reports[0].date == date(2026, 4, 14)
    assert item_reports[0].usage_total == Decimal("3.50")
    assert item_reports[1].date == date(2026, 4, 16)
    assert item_reports[1].usage_total == Decimal("12.00")


def test_get_usage_report_should_include_start_date(
    db_session, make_ingredient, make_inventory_transaction
):
    ingredient = make_ingredient()
    make_inventory_transaction(
        ingredient_id=ingredient.id,
        change_type="SALE",
        quantity_delta=Decimal("-1.00"),
        created_at=datetime(2026, 9, 1, 0, 0, 0),
    )

    reports = get_usage_report(
        session=db_session, start_date=date(2026, 9, 1), end_date=date(2026, 9, 7)
    )

    item_reports = [r for r in reports if r.item_id == ingredient.id]
    assert len(item_reports) == 1


def test_get_usage_report_should_exclude_end_date(
    db_session, make_ingredient, make_inventory_transaction
):
    ingredient = make_ingredient()
    make_inventory_transaction(
        ingredient_id=ingredient.id,
        change_type="SALE",
        quantity_delta=Decimal("-1.11"),
        created_at=datetime(2026, 11, 11, 0, 0, 0),
    )

    reports = get_usage_report(
        session=db_session, start_date=date(2026, 11, 5), end_date=date(2026, 11, 11)
    )

    item_reports = [r for r in reports if r.item_id == ingredient.id]
    assert item_reports == []


def test_get_usage_report_with_both_item_types_should_include_items(
    db_session, make_ingredient, make_baked_good, make_inventory_transaction
):
    ingredient = make_ingredient()
    make_inventory_transaction(
        ingredient_id=ingredient.id,
        change_type="SALE",
        quantity_delta=Decimal("-4.50"),
        created_at=datetime(2026, 12, 11, 6, 0, 0),
    )
    baked_good = make_baked_good()
    make_inventory_transaction(
        baked_good_id=baked_good.id,
        change_type="SALE",
        quantity_delta=Decimal("-2.50"),
        created_at=datetime(2026, 12, 11, 12, 0, 0),
    )

    reports = get_usage_report(
        session=db_session, start_date=date(2026, 12, 8), end_date=date(2026, 12, 14)
    )

    ingredient_ids = [r.item_id for r in reports if r.item_type == "ingredient"]
    baked_good_ids = [r.item_id for r in reports if r.item_type == "baked_good"]

    assert ingredient.id in ingredient_ids
    assert baked_good.id in baked_good_ids


def test_get_usage_report_with_no_transactions_should_return_empty_list(db_session):
    reports = get_usage_report(
        session=db_session, start_date=date(2026, 1, 1), end_date=date(2026, 1, 6)
    )
    assert reports == []
