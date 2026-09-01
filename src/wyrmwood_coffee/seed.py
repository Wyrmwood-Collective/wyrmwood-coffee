"""Loads sample data from data/sample_data.json into the database.

Run with `uv run seed`. By default this skips seeding if any of the
seeded tables already contain data; pass `--overwrite` to truncate those
tables (resetting their ID sequences back to 1) and reinsert from the
JSON file, so IDs are predictable across reseeds.
"""

import argparse
import json
import logging
import sys
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from sqlalchemy import text

from wyrmwood_coffee.database import get_session_local
from wyrmwood_coffee.logging import setup_logging
from wyrmwood_coffee.models import (
    BakedGood,
    Customer,
    Drink,
    Employee,
    Ingredient,
    Promotion,
    Vendor,
    VendorContact,
)
from wyrmwood_coffee.models.drink import DrinkIngredient
from wyrmwood_coffee.security import hash_password
from wyrmwood_coffee.settings import Environment, settings

logger = logging.getLogger(__name__)

DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "sample_data.json"

SEEDED_MODELS = [Vendor, Ingredient, Drink, BakedGood, Customer, Employee, Promotion]

# Tables truncated on --overwrite. Order doesn't matter here (CASCADE
# pulls in any dependents), but every seeded table is listed explicitly
# so RESTART IDENTITY resets each one's sequence back to 1.
_TRUNCATE_MODELS = [
    DrinkIngredient,
    VendorContact,
    Drink,
    Ingredient,
    Vendor,
    BakedGood,
    Customer,
    Employee,
    Promotion,
]


def _load_data() -> dict:
    with DATA_FILE.open(encoding="utf-8") as f:
        return json.load(f)


def _already_seeded(session) -> bool:
    return any(session.query(model).first() is not None for model in SEEDED_MODELS)


def _clear_existing(session) -> None:
    tables = ", ".join(model.__tablename__ for model in _TRUNCATE_MODELS)
    session.execute(text(f"TRUNCATE TABLE {tables} RESTART IDENTITY CASCADE"))


def _seed_vendors(session, entries: list[dict]) -> dict[str, int]:
    vendor_ids = {}
    for entry in entries:
        vendor = Vendor(
            active=entry.get("active", True),
            name=entry["name"],
            contacts=[
                VendorContact(
                    name=c["name"], role=c["role"], email=c["email"], phone=c["phone"]
                )
                for c in entry.get("contacts", [])
            ],
        )
        session.add(vendor)
        session.flush()
        vendor_ids[entry["key"]] = vendor.id
    return vendor_ids


def _seed_ingredients(
    session, entries: list[dict], vendor_ids: dict[str, int]
) -> dict[str, int]:
    ingredient_ids = {}
    for entry in entries:
        ingredient = Ingredient(
            active=entry.get("active", True),
            is_deleted=entry.get("is_deleted", False),
            name=entry["name"],
            purchasing_cost=Decimal(entry["purchasing_cost"]),
            unit_amount=Decimal(entry["unit_amount"]),
            unit_of_measure=entry["unit_of_measure"],
            allergens=entry.get("allergens", []),
            vendor_id=vendor_ids[entry["vendor_key"]],
        )
        session.add(ingredient)
        session.flush()
        ingredient_ids[entry["key"]] = ingredient.id
    return ingredient_ids


def _seed_drinks(session, entries: list[dict], ingredient_ids: dict[str, int]) -> None:
    for entry in entries:
        drink_ingredients = []
        production_cost = Decimal("0.00")
        for di in entry["ingredients"]:
            amount = Decimal(di["amount"])
            ingredient = session.get(Ingredient, ingredient_ids[di["ingredient_key"]])
            production_cost += (amount * ingredient.purchasing_cost).quantize(
                Decimal("0.01")
            )
            drink_ingredients.append(
                DrinkIngredient(
                    ingredient_id=ingredient.id, amount=amount, unit=di["unit"]
                )
            )
        markup = Decimal(entry["markup_percentage"])
        sale_price = (production_cost * markup).quantize(Decimal("0.01"))
        session.add(
            Drink(
                active=entry.get("active", True),
                name=entry["name"],
                description=entry["description"],
                type=entry["type"],
                production_cost=production_cost,
                markup_percentage=markup,
                sale_price=sale_price,
                ingredients=drink_ingredients,
            )
        )


def _seed_baked_goods(session, entries: list[dict]) -> None:
    for entry in entries:
        session.add(
            BakedGood(
                active=entry.get("active", True),
                name=entry["name"],
                description=entry["description"],
                purchase_cost=Decimal(entry["purchase_cost"]),
                retail_price=Decimal(entry["retail_price"]),
                allergens=entry.get("allergens", []),
            )
        )


def _seed_customers(session, entries: list[dict]) -> None:
    for entry in entries:
        session.add(
            Customer(
                active=entry.get("active", True),
                first_name=entry["first_name"],
                last_name=entry["last_name"],
                email=entry.get("email"),
                phone=entry.get("phone"),
                loyalty_points=entry.get("loyalty_points", 0),
                loyalty_expires_at=datetime.fromisoformat(entry["loyalty_expires_at"]),
            )
        )


def _seed_employees(session, entries: list[dict]) -> None:
    for entry in entries:
        session.add(
            Employee(
                active=entry.get("active", True),
                first_name=entry["first_name"],
                last_name=entry["last_name"],
                role=entry["role"],
                hourly_rate=Decimal(entry["hourly_rate"]),
                hire_date=date.fromisoformat(entry["hire_date"]),
                term_date=date.fromisoformat(entry["term_date"])
                if entry.get("term_date")
                else None,
                username=entry["username"],
                password=hash_password(entry["password"]),
            )
        )


def _seed_promotions(session, entries: list[dict]) -> None:
    for entry in entries:
        session.add(
            Promotion(
                active=entry.get("active", True),
                deleted=entry.get("deleted", False),
                promo_code=entry["promo_code"],
                discount_percentage=Decimal(entry["discount_percentage"]),
                start_date=date.fromisoformat(entry["start_date"]),
                end_date=date.fromisoformat(entry["end_date"]),
            )
        )


def seed(overwrite: bool = False) -> None:
    if settings.app_environment == Environment.STAGING:
        logger.critical("Refusing to seed sample data into the staging environment.")
        sys.exit(1)

    session = get_session_local()()
    try:
        if _already_seeded(session):
            if not overwrite:
                logger.info(
                    "Sample data already present; skipping. "
                    "Pass --overwrite to replace it."
                )
                return
            logger.info("Overwrite requested; clearing existing seeded data.")
            _clear_existing(session)
            session.commit()

        data = _load_data()

        vendor_ids = _seed_vendors(session, data["vendors"])
        ingredient_ids = _seed_ingredients(session, data["ingredients"], vendor_ids)
        _seed_drinks(session, data["drinks"], ingredient_ids)
        _seed_baked_goods(session, data["baked_goods"])
        _seed_customers(session, data["customers"])
        _seed_employees(session, data["employees"])
        _seed_promotions(session, data["promotions"])

        session.commit()
        logger.info("Sample data seeded successfully.")
    finally:
        session.close()


def main():
    setup_logging()
    parser = argparse.ArgumentParser(description="Load sample data into the database.")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Delete existing seeded data and reinsert from data/sample_data.json",
    )
    args = parser.parse_args()
    seed(overwrite=args.overwrite)


if __name__ == "__main__":
    main()
