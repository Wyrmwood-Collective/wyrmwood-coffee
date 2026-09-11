import calendar
from datetime import UTC, date, datetime
from decimal import Decimal
from math import floor

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from wyrmwood_coffee.models.baked_goods import (
    BakedGood,  # Make sure this matches your team's models
)
from wyrmwood_coffee.models.customer import Customer
from wyrmwood_coffee.models.drink import Drink
from wyrmwood_coffee.models.promotions import (
    Promotion,  # Make sure this matches your team's models
)
from wyrmwood_coffee.models.purchase import Purchase, PurchaseCreate, PurchaseItem


def process_purchase(session: Session, payload: PurchaseCreate) -> Purchase:
    """
    Process a purchase: lookup prices, calculate totals, apply promos,
    and award loyalty points.
    """
    subtotal = Decimal("0.00")
    purchase_items: list[PurchaseItem] = []

    # 1. OPTIMIZATION: Bulk look up all item prices at once
    requested_names = [item.name for item in payload.items]

    # Get all matching baked goods and drinks in just TWO database queries
    baked_goods = (
        session.query(BakedGood).filter(BakedGood.name.in_(requested_names)).all()
    )
    drinks = session.query(Drink).filter(Drink.name.in_(requested_names)).all()

    # Create fast-lookup dictionaries { "Muffin": 5.00 }
    bg_prices = {bg.name: bg.retail_price for bg in baked_goods}
    drink_prices = {drink.name: drink.sale_price for drink in drinks}

    # 2. Calculate subtotal and build items list
    for item_in in payload.items:
        # Instant dictionary lookups instead of database queries!
        if item_in.name in bg_prices:
            unit_price = bg_prices[item_in.name]
        elif item_in.name in drink_prices:
            unit_price = drink_prices[item_in.name]
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Item '{item_in.name}' is not a valid baked good or drink.",
            )

        line_total = unit_price * item_in.quantity
        subtotal += line_total

        purchase_items.append(
            PurchaseItem(
                name=item_in.name, quantity=item_in.quantity, unit_price=unit_price
            )
        )

    # 3. Apply Promotion (if provided)
    discount = Decimal("0.00")
    if payload.promo_id:
        promo = session.get(Promotion, payload.promo_id)
        if not promo:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The promotion was not found.",
            )

        today = date.today()
        if not promo.active or today < promo.start_date or today > promo.end_date:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "The provided promotion is not active or is outside its "
                    "valid dates."
                ),
            )

        # discount_percentage is typically stored as a whole number (e.g., 20 for 20%)
        discount = (promo.discount_percentage / Decimal("100")) * subtotal

    # 4. Calculate Tax and Total (rounded to nearest cent)
    discounted_subtotal = subtotal - discount
    tax = round(discounted_subtotal * Decimal("0.07"), 2)
    total = round(discounted_subtotal + tax, 2)

    # 5. Create the Purchase record
    purchase = Purchase(
        customer_id=payload.customer_id,
        promo_id=payload.promo_id,
        subtotal=discounted_subtotal,
        tax=tax,
        total=total,
        items=purchase_items,
    )
    session.add(purchase)

    # 6. Award Loyalty Points (if a customer is attached)
    if payload.customer_id:
        customer = session.get(Customer, payload.customer_id)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The customer was not found.",
            )

        points_earned = floor(total)
        customer.loyalty_points += points_earned

        # Points expire at the end of the month of the following year
        current_date = date.today()
        exp_year = current_date.year + 1
        exp_month = current_date.month
        _, last_day = calendar.monthrange(exp_year, exp_month)

        # Set expiration to the very end of that day
        customer.loyalty_expires_at = datetime(
            exp_year, exp_month, last_day, 23, 59, 59, tzinfo=UTC
        )

    # Commit all changes in a single transaction!
    session.commit()
    session.refresh(purchase)

    return purchase
