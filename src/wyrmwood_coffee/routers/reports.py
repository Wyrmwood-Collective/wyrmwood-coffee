from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from wyrmwood_coffee.dependencies import DbSession, require_manager
from wyrmwood_coffee.models.report import LowStockItemReport, UsageReport
from wyrmwood_coffee.services import reports

router = APIRouter()


@router.get(
    "/low-stock",
    status_code=status.HTTP_200_OK,
    response_model=list[LowStockItemReport],
    response_description=(
        "The report of all active inventory items meeting their reorder threshold"
    ),
    responses={
        401: {"description": "Could not validate credentials."},
        403: {"description": "Insufficient permissions."},
    },
    dependencies=[Depends(require_manager)],
)
def get_low_stock_report(session: DbSession) -> list[LowStockItemReport]:
    """List active ingredients and baked goods at or below their reorder threshold"""
    return reports.get_low_stock_report(session)


@router.get(
    "/usage",
    status_code=status.HTTP_200_OK,
    response_model=list[UsageReport],
    response_description="The report of per-day usage totals for all inventory items",
    responses={
        401: {"description": "Could not validate credentials."},
        403: {"description": "Insufficient permissions."},
        422: {"description": "start_date or end_date is malformed or invalid."},
    },
    dependencies=[Depends(require_manager)],
)
def get_usage_report(
    session: DbSession,
    start_date: Annotated[
        date, Query(description="Inclusive start of the reporting window")
    ],
    end_date: Annotated[
        date, Query(description="Exclusive end of the reporting window")
    ],
) -> list[UsageReport]:
    """List per-day usage totals of ingredients and baked goods for sales"""
    return reports.get_usage_report(session, start_date, end_date)
