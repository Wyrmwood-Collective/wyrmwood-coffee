"""Loads sample data from data/sample_data.json into the database.

Run with `uv run seed`. By default this skips seeding if any of the
seeded tables already contain data; pass `--overwrite` to truncate those
tables (resetting their ID sequences back to 1) and reinsert from the
JSON file, so IDs are predictable across reseeds.
"""

import argparse
import json
import logging
import os
import sys
from datetime import UTC, date, datetime
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
    InventoryTransaction,
    Promotion,
    Purchase,
    PurchaseItem,
    Vendor,
    VendorContact,
)
from wyrmwood_coffee.models.drink import DrinkIngredient
from wyrmwood_coffee.models.inventory import InventoryChangeType
from wyrmwood_coffee.security import hash_password
from wyrmwood_coffee.settings import Environment, script_settings

logger = logging.getLogger(__name__)

DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "sample_data.json"

SEEDED_MODELS = [
    Vendor,
    Ingredient,
    Drink,
    BakedGood,
    Customer,
    Employee,
    Promotion,
    Purchase,
]

# Tables truncated on --overwrite. Order doesn't matter here (CASCADE
# pulls in any dependents), but every seeded table is listed explicitly
# so RESTART IDENTITY resets each one's sequence back to 1.
_TRUNCATE_MODELS = [
    PurchaseItem,
    Purchase,
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
            quantity_on_hand=Decimal(entry["quantity_on_hand"]),
            reorder_threshold=Decimal(entry["reorder_threshold"]),
            reorder_quantity=Decimal(entry["reorder_quantity"]),
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

            unit_cost = ingredient.purchasing_cost / ingredient.unit_amount
            production_cost += (amount * unit_cost).quantize(Decimal("0.01"))

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


def _seed_baked_goods(session, entries: list[dict]) -> dict[str, int]:
    baked_good_ids = {}
    for entry in entries:
        baked_good = BakedGood(
            active=entry.get("active", True),
            name=entry["name"],
            description=entry["description"],
            purchase_cost=Decimal(entry["purchase_cost"]),
            retail_price=Decimal(entry["retail_price"]),
            allergens=entry.get("allergens", []),
            quantity_on_hand=entry["quantity_on_hand"],
            reorder_threshold=entry["reorder_threshold"],
            reorder_quantity=entry["reorder_quantity"],
        )
        session.add(baked_good)
        session.flush()
        baked_good_ids[entry["name"]] = baked_good.id
    return baked_good_ids


def _seed_customers(session, entries: list[dict]) -> dict[int, int]:
    customer_ids = {}
    for idx, entry in enumerate(entries, start=1):
        customer = Customer(
            active=entry.get("active", True),
            first_name=entry["first_name"],
            last_name=entry["last_name"],
            email=entry.get("email"),
            phone=entry.get("phone"),
            loyalty_points=entry.get("loyalty_points", 0),
            loyalty_expires_at=datetime.fromisoformat(entry["loyalty_expires_at"]),
        )
        session.add(customer)
        session.flush()
        json_id = entry.get("id", idx)
        customer_ids[json_id] = customer.id
    return customer_ids


def _seed_employees(session, entries: list[dict]) -> None:
    for entry in entries:
        session.add(
            Employee(
                active=entry.get("active", True),
                is_deleted=entry.get("is_deleted", False),
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


def _seed_promotions(session, entries: list[dict]) -> dict[int, int]:
    promo_ids = {}
    for idx, entry in enumerate(entries, start=1):
        promo = Promotion(
            active=entry.get("active", True),
            deleted=entry.get("deleted", False),
            promo_code=entry["promo_code"],
            discount_percentage=Decimal(entry["discount_percentage"]),
            start_date=date.fromisoformat(entry["start_date"]),
            end_date=date.fromisoformat(entry["end_date"]),
        )
        session.add(promo)
        session.flush()
        json_id = entry.get("id", idx)
        promo_ids[json_id] = promo.id
    return promo_ids


def _seed_inventory_transactions(
    session,
    entries: list[dict],
    ingredient_ids: dict[str, int],
    baked_good_ids: dict[str, int],
) -> None:
    for entry in entries:
        if "ingredient_key" in entry:
            item_kwargs = {"ingredient_id": ingredient_ids[entry["ingredient_key"]]}
        elif "baked_good_name" in entry:
            item_kwargs = {"baked_good_id": baked_good_ids[entry["baked_good_name"]]}
        else:
            raise ValueError(
                "inventory_transaction entry must have either "
                "'ingredient_key' or 'baked_good_name': "
                f"{entry}"
            )

        session.add(
            InventoryTransaction(
                change_type=InventoryChangeType(entry["change_type"]),
                quantity_delta=Decimal(entry["quantity_delta"]),
                reference_id=entry.get("reference_id"),
                created_at=datetime.fromisoformat(entry["created_at"]),
                **item_kwargs,
            )
        )

def _seed_purchases(
    session,
    entries: list[dict],
    customer_ids: dict[int, int],
    promo_ids: dict[int, int],
) -> None:
    baked_good_names = {bg.name for bg in session.query(BakedGood).all()}

    for entry in entries:
        items = []
        for item in entry["items"]:
            item_type = "baked_good" if item["name"] in baked_good_names else "drink"

            items.append(
                PurchaseItem(
                    name=item["name"],
                    item_type=item_type,
                    quantity=item["quantity"],
                    unit_price=Decimal(str(item["unit_price"])),
                )
            )

        created_at_str = entry.get("created_at")
        created_at = (
            datetime.fromisoformat(created_at_str)
            if created_at_str
            else datetime.now(UTC)
        )

        raw_customer_id = entry.get("customer_id")
        actual_customer_id = (
            customer_ids.get(raw_customer_id) if raw_customer_id is not None else None
        )

        raw_promo_id = entry.get("promo_id")
        actual_promo_id = (
            promo_ids.get(raw_promo_id) if raw_promo_id is not None else None
        )

        session.add(
            Purchase(
                customer_id=actual_customer_id,
                promo_id=actual_promo_id,
                subtotal=Decimal(str(entry["subtotal"])),
                tax=Decimal(str(entry["tax"])),
                total=Decimal(str(entry["total"])),
                created_at=created_at,
                items=items,
            )
        )


def _ensure_staging_seed_allowed(confirm_staging_seed: bool) -> None:
    if script_settings().core.app_environment != Environment.STAGING:
        return

    if not confirm_staging_seed:
        logger.critical(
            "Refusing to seed sample data into staging. Pass "
            "--confirm-staging-seed to seed staging from the seed-staging "
            "GitHub Actions workflow."
        )
        sys.exit(1)

    if os.environ.get("GITHUB_ACTIONS") != "true":
        logger.critical(
            "Refusing to seed sample data into staging outside of the "
            "seed-staging GitHub Actions workflow."
        )
        sys.exit(1)


def seed(overwrite: bool = False, confirm_staging_seed: bool = False) -> None:
    _ensure_staging_seed_allowed(confirm_staging_seed)

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
        baked_good_ids = _seed_baked_goods(session, data["baked_goods"])
        _seed_drinks(session, data["drinks"], ingredient_ids)
<<<<<<< HEAD
        _seed_baked_goods(session, data["baked_goods"])
        customer_ids = _seed_customers(session, data["customers"])
        _seed_employees(session, data["employees"])
        promo_ids = _seed_promotions(session, data["promotions"])
=======
        _seed_customers(session, data["customers"])
        _seed_employees(session, data["employees"])
        _seed_inventory_transactions(
            session, data["inventory_transactions"], ingredient_ids, baked_good_ids
        )
        _seed_promotions(session, data["promotions"])
>>>>>>> cacdacd (Add reporting endpoints, inventory repository, and report service)

        if "purchases" in data:
            _seed_purchases(session, data["purchases"], customer_ids, promo_ids)

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
    parser.add_argument(
        "--confirm-staging-seed",
        action="store_true",
        help=(
            "Required, in addition to running inside the seed-staging GitHub "
            "Actions workflow, to seed the staging environment."
        ),
    )
    args = parser.parse_args()
    seed(overwrite=args.overwrite, confirm_staging_seed=args.confirm_staging_seed)


if __name__ == "__main__":
    main()
