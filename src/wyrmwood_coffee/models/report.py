from datetime import date
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints

LOW_STOCK_ID_TITLE = "Item ID"
LOW_STOCK_ID_DESC = "The unique identifier of the item"
LOW_STOCK_NAME_TITLE = "Item Name"
LOW_STOCK_NAME_DESC = "The name of the ingredient or baked good"
LOW_STOCK_TYPE_TITLE = "Item Type"
LOW_STOCK_TYPE_DESC = "The item category as either an ingredient or baked good"
LOW_STOCK_QUANTITY_ON_HAND_TITLE = "Item Quantity on Hand"
LOW_STOCK_QUANTITY_ON_HAND_DESC = "The current stock level of the item"
LOW_STOCK_REORDER_THRESHOLD_TITLE = "Reorder Threshold"
LOW_STOCK_REORDER_THRESHOLD_DESC = (
    "The stock level at which a reorder should be triggered"
)
LOW_STOCK_REORDER_QUANTITY_TITLE = "Reorder Quantity"
LOW_STOCK_REORDER_QUANTITY_DESC = "The item amount for a reorder"

USAGE_REPORT_DATE_TITLE = "Usage Date"
USAGE_REPORT_DATE_DESC = "The usage date of the item"
USAGE_REPORT_ITEM_ID_TITLE = "Used Item ID"
USAGE_REPORT_ITEM_ID_DESC = "The unique identifier of the used item"
USAGE_REPORT_ITEM_TYPE_TITLE = "Used Item Type"
USAGE_REPORT_ITEM_TYPE_DESC = "The type of the reported used item"
USAGE_REPORT_USAGE_TOTAL_TITLE = "Item Usage Total"
USAGE_REPORT_USAGE_TOTAL_DESC = "The aggregate sum of the item used on a date"


class LowStockItemReport(BaseModel):
    """Base schema of a low stock item report provided by the system."""

    id: Annotated[int, Field(title=LOW_STOCK_ID_TITLE, description=LOW_STOCK_ID_DESC)]
    name: Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)] = (
        Field(title=LOW_STOCK_NAME_TITLE, description=LOW_STOCK_NAME_DESC)
    )
    item_type: Annotated[
        Literal["ingredient", "baked_good"],
        Field(title=LOW_STOCK_TYPE_TITLE, description=LOW_STOCK_TYPE_DESC),
    ]
    quantity_on_hand: Annotated[
        Decimal,
        Field(
            title=LOW_STOCK_QUANTITY_ON_HAND_TITLE,
            description=LOW_STOCK_QUANTITY_ON_HAND_DESC,
        ),
    ]
    reorder_threshold: Annotated[
        Decimal,
        Field(
            title=LOW_STOCK_REORDER_THRESHOLD_TITLE,
            description=LOW_STOCK_REORDER_THRESHOLD_DESC,
        ),
    ]
    reorder_quantity: Annotated[
        Decimal,
        Field(
            title=LOW_STOCK_REORDER_QUANTITY_TITLE,
            description=LOW_STOCK_REORDER_QUANTITY_DESC,
        ),
    ]


class UsageReport(BaseModel):
    """Base schema of an item usage report provided by the system."""

    date: Annotated[
        date, Field(title=USAGE_REPORT_DATE_TITLE, description=USAGE_REPORT_DATE_DESC)
    ]
    item_id: Annotated[
        int,
        Field(title=USAGE_REPORT_ITEM_ID_TITLE, description=USAGE_REPORT_ITEM_ID_DESC),
    ]
    item_type: Annotated[
        Literal["ingredient", "baked_good"],
        Field(
            title=USAGE_REPORT_ITEM_TYPE_TITLE, description=USAGE_REPORT_ITEM_TYPE_DESC
        ),
    ]
    usage_total: Annotated[
        Decimal,
        Field(
            title=USAGE_REPORT_USAGE_TOTAL_TITLE,
            description=USAGE_REPORT_USAGE_TOTAL_DESC,
        ),
    ]
