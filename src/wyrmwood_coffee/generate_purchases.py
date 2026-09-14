import json
import random
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Edge case strings to test UI truncation and special character encoding
EDGE_CASE_STRINGS = [
    "Extra Shot " * 50,  # Extremely long string for UI truncation
    "Café au Lait ☕✨ (Glitch Test: 𠜎𠜱𠝹𠱓)",  # Emojis and surrogate pairs
    "<script>alert('xss')</script> Muffin",  # XSS attempt injection
    "   Blank Space Latte   \n\t",  # Weird whitespace
    "Null\x00Byte Pastry",  # Null byte encoding test
]


def generate_mock_purchases():
    data_file = Path("data/sample_data.json")

    with data_file.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Figure out what valid data we have to work with
    num_customers = len(data.get("customers", []))
    num_promos = len(data.get("promotions", []))

    # Extract item names and fake prices for our mock data
    items_pool = []
    for drink in data.get("drinks", []):
        # Drinks lack a hardcoded JSON price, so we fake one
        mock_price = round(random.uniform(3.50, 7.50), 2)
        items_pool.append({"name": drink["name"], "price": mock_price})

    generated_purchases = []
    now = datetime.now(UTC)

    # Generate 500 purchases
    for _ in range(500):
        # 1. Date Range: Random date within the last 2 years (730 days)
        days_ago = random.randint(0, 730)
        purchase_date = now - timedelta(days=days_ago)

        # 2. Missing/Null Fields: 20% chance of guest checkout, 80% chance of no promo
        customer_id = (
            random.randint(1, num_customers) if random.random() > 0.2 else None
        )
        promo_id = random.randint(1, num_promos) if random.random() > 0.8 else None

        # Generate 1 to 4 items per purchase
        purchase_items = []
        subtotal = 0.0

        for _ in range(random.randint(1, 4)):
            base_item = random.choice(items_pool)
            qty = random.randint(1, 3)

            # 3. Special Characters / Long Text: 5% chance to inject an edge-case name
            item_name = base_item["name"]
            if random.random() < 0.05:
                item_name = random.choice(EDGE_CASE_STRINGS)

            purchase_items.append(
                {"name": item_name, "quantity": qty, "unit_price": base_item["price"]}
            )
            subtotal += base_item["price"] * qty

        # Apply a fake discount if promo exists
        discount = subtotal * 0.2 if promo_id else 0.0
        tax = (subtotal - discount) * 0.07
        total = (subtotal - discount) + tax

        generated_purchases.append(
            {
                "customer_id": customer_id,
                "promo_id": promo_id,
                "subtotal": round(subtotal, 2),
                "tax": round(tax, 2),
                "total": round(total, 2),
                "created_at": purchase_date.isoformat(),
                "items": purchase_items,
            }
        )

    # Overwrite the purchases array in the JSON file
    data["purchases"] = generated_purchases

    with data_file.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"✅ Generated {len(generated_purchases)} mock purchases!")


if __name__ == "__main__":
    generate_mock_purchases()
