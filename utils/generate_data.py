"""
Superstore Sales Dataset Generator
====================================
Generates a realistic Superstore Sales CSV dataset with four tables:
orders, products, customers, and returns.

This avoids the need to download from Kaggle and gives us full control
over the schema, which makes Text-to-SQL demonstrations more reliable.

Usage:
    python utils/generate_data.py          # writes to data/superstore.csv (+ related CSVs)
    python utils/generate_data.py --rows 5000
"""

from __future__ import annotations

import argparse
import csv
import os
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Seed for reproducibility
# ---------------------------------------------------------------------------
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

# ---------------------------------------------------------------------------
# Reference data — realistic Superstore-like values
# ---------------------------------------------------------------------------

REGIONS: list[str] = ["East", "West", "Central", "South"]

STATES_BY_REGION: dict[str, list[str]] = {
    "East": ["New York", "Pennsylvania", "Massachusetts", "New Jersey", "Connecticut"],
    "West": ["California", "Washington", "Oregon", "Colorado", "Arizona"],
    "Central": ["Illinois", "Texas", "Ohio", "Michigan", "Minnesota"],
    "South": ["Florida", "Georgia", "Virginia", "North Carolina", "Tennessee"],
}

CITIES_BY_STATE: dict[str, list[str]] = {
    "New York": ["New York City", "Buffalo", "Rochester"],
    "Pennsylvania": ["Philadelphia", "Pittsburgh", "Allentown"],
    "Massachusetts": ["Boston", "Worcester", "Springfield"],
    "New Jersey": ["Newark", "Jersey City", "Trenton"],
    "Connecticut": ["Hartford", "New Haven", "Stamford"],
    "California": ["Los Angeles", "San Francisco", "San Diego", "Sacramento"],
    "Washington": ["Seattle", "Spokane", "Tacoma"],
    "Oregon": ["Portland", "Salem", "Eugene"],
    "Colorado": ["Denver", "Colorado Springs", "Aurora"],
    "Arizona": ["Phoenix", "Tucson", "Mesa"],
    "Illinois": ["Chicago", "Springfield", "Naperville"],
    "Texas": ["Houston", "Dallas", "Austin", "San Antonio"],
    "Ohio": ["Columbus", "Cleveland", "Cincinnati"],
    "Michigan": ["Detroit", "Grand Rapids", "Ann Arbor"],
    "Minnesota": ["Minneapolis", "Saint Paul", "Rochester"],
    "Florida": ["Miami", "Orlando", "Tampa", "Jacksonville"],
    "Georgia": ["Atlanta", "Savannah", "Augusta"],
    "Virginia": ["Richmond", "Virginia Beach", "Norfolk"],
    "North Carolina": ["Charlotte", "Raleigh", "Durham"],
    "Tennessee": ["Nashville", "Memphis", "Knoxville"],
}

SEGMENTS: list[str] = ["Consumer", "Corporate", "Home Office"]
SHIP_MODES: list[str] = ["Standard Class", "Second Class", "First Class", "Same Day"]

CATEGORIES: dict[str, dict[str, list[dict[str, Any]]]] = {
    "Technology": {
        "Phones": [
            {"name": "Apple iPhone 15 Pro", "base_price": 999.99},
            {"name": "Samsung Galaxy S24", "base_price": 849.99},
            {"name": "Google Pixel 8", "base_price": 699.99},
            {"name": "Cisco IP Phone 8845", "base_price": 349.99},
        ],
        "Laptops": [
            {"name": "Apple MacBook Pro 16-inch", "base_price": 2499.99},
            {"name": "Dell XPS 15", "base_price": 1799.99},
            {"name": "Lenovo ThinkPad X1 Carbon", "base_price": 1649.99},
            {"name": "HP Spectre x360", "base_price": 1399.99},
        ],
        "Accessories": [
            {"name": "Logitech MX Master 3S Mouse", "base_price": 99.99},
            {"name": "Anker USB-C Hub 7-in-1", "base_price": 45.99},
            {"name": "Samsung 27\" 4K Monitor", "base_price": 349.99},
            {"name": "SanDisk 1TB Portable SSD", "base_price": 89.99},
        ],
    },
    "Furniture": {
        "Chairs": [
            {"name": "Herman Miller Aeron Chair", "base_price": 1395.00},
            {"name": "Steelcase Leap V2", "base_price": 1089.00},
            {"name": "IKEA Markus Office Chair", "base_price": 229.00},
            {"name": "HON Ignition 2.0 Task Chair", "base_price": 389.00},
        ],
        "Tables": [
            {"name": "Autonomous SmartDesk Pro", "base_price": 699.00},
            {"name": "IKEA BEKANT Desk", "base_price": 349.00},
            {"name": "Bush Business Series C Desk", "base_price": 499.00},
            {"name": "Bretford Rectangular Conference Table", "base_price": 899.00},
        ],
        "Bookcases": [
            {"name": "Sauder Heritage Hill Bookcase", "base_price": 259.99},
            {"name": "IKEA KALLAX Shelf Unit", "base_price": 89.99},
            {"name": "Bush Furniture Cabot Bookshelf", "base_price": 199.99},
        ],
    },
    "Office Supplies": {
        "Paper": [
            {"name": "Hammermill Premium Copy Paper 5000ct", "base_price": 42.99},
            {"name": "HP Printer Paper 8.5x11 1500ct", "base_price": 24.99},
            {"name": "Southworth 25% Cotton Paper 500ct", "base_price": 34.99},
        ],
        "Binders": [
            {"name": "Avery Heavy-Duty 3-Ring Binder", "base_price": 12.99},
            {"name": "Cardinal XtraLife ClearVue Binder", "base_price": 9.99},
            {"name": "Wilson Jones 3-Ring Binder Set", "base_price": 18.99},
        ],
        "Storage": [
            {"name": "Bankers Box SmoothMove Boxes 12pk", "base_price": 29.99},
            {"name": "Fellowes Banker Box R-Kive", "base_price": 45.99},
            {"name": "Sterilite Storage Crate", "base_price": 8.99},
        ],
        "Art": [
            {"name": "Prismacolor Premier Colored Pencils 72ct", "base_price": 39.99},
            {"name": "Sharpie Permanent Markers 24pk", "base_price": 14.99},
            {"name": "Post-it Super Sticky Notes 24pk", "base_price": 22.99},
        ],
    },
}

FIRST_NAMES: list[str] = [
    "James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael",
    "Linda", "David", "Elizabeth", "William", "Barbara", "Richard", "Susan",
    "Joseph", "Jessica", "Thomas", "Sarah", "Christopher", "Karen",
    "Daniel", "Lisa", "Matthew", "Nancy", "Anthony", "Betty", "Mark",
    "Margaret", "Steven", "Sandra", "Andrew", "Ashley", "Paul", "Dorothy",
    "Joshua", "Kimberly", "Kenneth", "Emily", "Kevin", "Donna",
]

LAST_NAMES: list[str] = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
    "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King",
    "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
]

RETURN_REASONS: list[str] = [
    "Defective", "Wrong Item", "Not Needed", "Better Price Available",
    "Did Not Match Description",
]


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _generate_order_id(index: int) -> str:
    """Generate a Superstore-style order ID like US-2024-100001."""
    return f"US-2024-{100001 + index}"


def _generate_customer_id(index: int) -> str:
    """Generate a customer ID like CUST-0001."""
    return f"CUST-{index:04d}"


def _generate_product_id(cat_prefix: str, index: int) -> str:
    """Generate a product ID like TEC-PH-0001."""
    return f"{cat_prefix}-{index:04d}"


def _random_date(start: datetime, end: datetime) -> datetime:
    """Return a random datetime between *start* and *end*."""
    delta = end - start
    random_seconds = random.randint(0, int(delta.total_seconds()))
    return start + timedelta(seconds=random_seconds)


# ---------------------------------------------------------------------------
# Core generation logic
# ---------------------------------------------------------------------------

def generate_customers(n: int = 200) -> list[dict[str, Any]]:
    """Generate *n* unique customer records.

    Returns:
        A list of customer dicts with keys: customer_id, customer_name,
        segment, region, state, city.
    """
    customers: list[dict[str, Any]] = []
    used_names: set[str] = set()

    for i in range(n):
        # Ensure unique names
        while True:
            name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
            if name not in used_names:
                used_names.add(name)
                break

        region = random.choice(REGIONS)
        state = random.choice(STATES_BY_REGION[region])
        city = random.choice(CITIES_BY_STATE[state])
        segment = random.choice(SEGMENTS)

        customers.append({
            "customer_id": _generate_customer_id(i + 1),
            "customer_name": name,
            "segment": segment,
            "region": region,
            "state": state,
            "city": city,
        })

    return customers


def generate_products() -> list[dict[str, Any]]:
    """Build the product catalogue from the CATEGORIES reference data.

    Returns:
        A list of product dicts with keys: product_id, product_name,
        category, sub_category, base_price.
    """
    products: list[dict[str, Any]] = []
    cat_prefix_map = {"Technology": "TEC", "Furniture": "FUR", "Office Supplies": "OFF"}
    sub_prefix_map: dict[str, str] = {}
    idx = 0

    for category, sub_cats in CATEGORIES.items():
        for sub_category, items in sub_cats.items():
            sub_prefix = sub_category[:2].upper()
            prefix = f"{cat_prefix_map[category]}-{sub_prefix}"
            sub_prefix_map[sub_category] = prefix

            for item in items:
                idx += 1
                products.append({
                    "product_id": _generate_product_id(prefix, idx),
                    "product_name": item["name"],
                    "category": category,
                    "sub_category": sub_category,
                    "base_price": item["base_price"],
                })

    return products


def generate_orders(
    customers: list[dict[str, Any]],
    products: list[dict[str, Any]],
    n_orders: int = 2000,
) -> list[dict[str, Any]]:
    """Generate *n_orders* order line-item records.

    Each order can have 1-5 line items. The function generates enough
    distinct order IDs so that the total line-item count is approximately
    *n_orders*.

    Returns:
        A list of order-line dicts with all columns needed for the
        ``orders`` table.
    """
    order_start = datetime(2023, 1, 1)
    order_end = datetime(2024, 12, 31)

    rows: list[dict[str, Any]] = []
    order_idx = 0

    while len(rows) < n_orders:
        order_idx += 1
        order_id = _generate_order_id(order_idx)
        customer = random.choice(customers)
        order_date = _random_date(order_start, order_end)
        ship_mode = random.choice(SHIP_MODES)

        # Ship date is 1-7 days after order
        ship_delay = {"Same Day": 0, "First Class": 2, "Second Class": 4, "Standard Class": 6}
        ship_date = order_date + timedelta(days=ship_delay.get(ship_mode, 5) + random.randint(0, 1))

        n_items = random.randint(1, 5)
        chosen_products = random.sample(products, min(n_items, len(products)))

        for product in chosen_products:
            quantity = random.randint(1, 12)
            # Discount: 0%, 5%, 10%, 15%, 20%, 25%, 30%
            discount = random.choice([0.0, 0.0, 0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30])
            sales = round(product["base_price"] * quantity * (1 - discount), 2)
            # Profit margin varies: -10% to +40%
            profit_margin = random.uniform(-0.10, 0.40)
            profit = round(sales * profit_margin, 2)

            rows.append({
                "row_id": len(rows) + 1,
                "order_id": order_id,
                "order_date": order_date.strftime("%Y-%m-%d"),
                "ship_date": ship_date.strftime("%Y-%m-%d"),
                "ship_mode": ship_mode,
                "customer_id": customer["customer_id"],
                "customer_name": customer["customer_name"],
                "segment": customer["segment"],
                "region": customer["region"],
                "state": customer["state"],
                "city": customer["city"],
                "product_id": product["product_id"],
                "product_name": product["product_name"],
                "category": product["category"],
                "sub_category": product["sub_category"],
                "sales": sales,
                "quantity": quantity,
                "discount": discount,
                "profit": profit,
            })

    return rows[:n_orders]


def generate_returns(orders: list[dict[str, Any]], return_rate: float = 0.08) -> list[dict[str, Any]]:
    """Generate return records for a fraction of orders.

    Args:
        orders: The full order-line dataset.
        return_rate: Fraction of unique orders that have returns.

    Returns:
        A list of return dicts with keys: return_id, order_id, reason, return_date.
    """
    unique_orders = list({row["order_id"]: row for row in orders}.values())
    n_returns = max(1, int(len(unique_orders) * return_rate))
    returned_orders = random.sample(unique_orders, n_returns)

    returns: list[dict[str, Any]] = []
    for i, order in enumerate(returned_orders, start=1):
        order_date = datetime.strptime(order["order_date"], "%Y-%m-%d")
        return_date = order_date + timedelta(days=random.randint(7, 45))
        returns.append({
            "return_id": f"RET-{i:04d}",
            "order_id": order["order_id"],
            "reason": random.choice(RETURN_REASONS),
            "return_date": return_date.strftime("%Y-%m-%d"),
        })

    return returns


# ---------------------------------------------------------------------------
# CSV writers
# ---------------------------------------------------------------------------

def _write_csv(filepath: Path, rows: list[dict[str, Any]]) -> None:
    """Write a list of dicts to a CSV file."""
    if not rows:
        return
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"  [OK] Wrote {len(rows):,} rows -> {filepath}")


def generate_all(data_dir: str | Path = "data", n_orders: int = 2000) -> None:
    """Generate the full Superstore dataset and write CSVs.

    Creates:
        data/orders.csv
        data/customers.csv
        data/products.csv
        data/returns.csv

    Args:
        data_dir: Directory to write CSV files into.
        n_orders: Approximate number of order line-items to generate.
    """
    data_path = Path(data_dir)
    print("Generating Superstore Sales dataset ...")

    customers = generate_customers(n=200)
    products = generate_products()
    orders = generate_orders(customers, products, n_orders=n_orders)
    returns = generate_returns(orders, return_rate=0.08)

    _write_csv(data_path / "orders.csv", orders)
    _write_csv(data_path / "customers.csv", customers)
    _write_csv(data_path / "products.csv", products)
    _write_csv(data_path / "returns.csv", returns)

    print("Done [OK]")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Superstore Sales dataset")
    parser.add_argument("--rows", type=int, default=2000, help="Number of order rows")
    parser.add_argument("--outdir", type=str, default="data", help="Output directory")
    args = parser.parse_args()
    generate_all(data_dir=args.outdir, n_orders=args.rows)
