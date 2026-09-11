import calendar
from datetime import UTC, date, datetime
from decimal import Decimal
from math import floor

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from wyrmwood_coffee.models.baked_goods import BakedGood
from wyrmwood_coffee.models.customer import Customer
from wyrmwood_coffee.models.drink import Drink
from wyrmwood_coffee.models.promotions import Promotion
from wyrmwood_coffee.models.purchase import Purchase, PurchaseCreate, PurchaseItem


def get_prices_and_subtotal(
    session: Session, payload_items: list
) -> tuple[Decimal, list[PurchaseItem]]:
    """Looks up item prices in bulk and returns the subtotal and item models."""
    requested_names = [item.name for item in payload_items]

    baked_goods = (
        session.query(BakedGood).filter(BakedGood.name.in_(requested_names)).all()
    )
    drinks = session.query(Drink).filter(Drink.name.in_(requested_names)).all()

    bg_prices = {bg.name: bg.retail_price for bg in baked_goods}
    drink_prices = {drink.name: drink.sale_price for drink in drinks}

    subtotal = Decimal("0.00")
    purchase_items: list[PurchaseItem] = []

    for item_in in payload_items:
        if item_in.name in bg_prices:
            unit_price = bg_prices[item_in.name]
        elif item_in.name in drink_prices:
            unit_price = drink_prices[item_in.name]
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"Item '{item_in.name}' is not a valid baked good or drink.",
            )

        subtotal += unit_price * item_in.quantity
        purchase_items.append(
            PurchaseItem(
                name=item_in.name, quantity=item_in.quantity, unit_price=unit_price
            )
        )

    return subtotal, purchase_items


def calculate_discount(
    session: Session, promo_id: int | None, subtotal: Decimal
) -> Decimal:
    """Validates the promotion and calculates the discount amount."""
    if not promo_id:
        return Decimal("0.00")

    promo = session.get(Promotion, promo_id)
    if not promo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The promotion was not found.",
        )

    today = date.today()
    if not promo.active or today < promo.start_date or today > promo.end_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                "The provided promotion is not active or is outside its valid dates."
            ),
        )

    return (promo.discount_percentage / Decimal("100")) * subtotal


def calculate_taxes_and_total(
    subtotal: Decimal, discount: Decimal
) -> tuple[Decimal, Decimal, Decimal]:
    """
    Calculates the 7% tax and final total, returning discounted_subtotal,
    tax, and total.
    """
    discounted_subtotal = subtotal - discount
    tax = round(discounted_subtotal * Decimal("0.07"), 2)
    total = round(discounted_subtotal + tax, 2)

    return discounted_subtotal, tax, total


def calculate_loyalty_points_and_expiration(total: Decimal) -> tuple[int, datetime]:
    """Calculates points earned and their expiration date."""
    points_earned = floor(total)

    current_date = date.today()
    exp_year = current_date.year + 1
    exp_month = current_date.month
    _, last_day = calendar.monthrange(exp_year, exp_month)

    expires_at = datetime(exp_year, exp_month, last_day, 23, 59, 59, tzinfo=UTC)

    return points_earned, expires_at


def process_purchase(session: Session, payload: PurchaseCreate) -> Purchase:
    """
    Process a purchase by coordinating helper functions and committing the transaction.
    """
    # 1. Build items and get subtotal
    subtotal, purchase_items = get_prices_and_subtotal(session, payload.items)

    # 2. Get discount
    discount = calculate_discount(session, payload.promo_id, subtotal)

    # 3. Calculate taxes and final total
    discounted_subtotal, tax, total = calculate_taxes_and_total(subtotal, discount)

    # 4. Create the initial purchase object
    purchase = Purchase(
        customer_id=payload.customer_id,
        promo_id=payload.promo_id,
        subtotal=discounted_subtotal,
        tax=tax,
        total=total,
        items=purchase_items,
    )
    session.add(purchase)

    # 5. Handle loyalty points if a customer is attached
    if payload.customer_id:
        customer = session.get(Customer, payload.customer_id)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The customer was not found.",
            )

        points_earned, expires_at = calculate_loyalty_points_and_expiration(total)
        customer.loyalty_points += points_earned
        customer.loyalty_expires_at = expires_at

    # 6. Commit the atomic transaction
    session.commit()
    session.refresh(purchase)

    return purchase
