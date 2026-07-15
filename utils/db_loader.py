"""
Database Loader -- CSV -> SQLite
===============================
Reads Superstore CSV files and loads them into a normalized SQLite
database with proper types, indexes, and foreign-key constraints.

The resulting schema has four tables:
    * orders      – order line-items (sales, quantity, discount, profit)
    * customers   – customer demographics (segment, region, city)
    * products    – product catalogue (category, sub-category, price)
    * returns     – returned orders with reason

Usage (standalone):
    python utils/db_loader.py                     # uses defaults
    python utils/db_loader.py --data-dir data --db data/database.db

Programmatic:
    from utils.db_loader import load_csvs_to_sqlite
    engine = load_csvs_to_sqlite("data", "data/database.db")
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

import pandas as pd
from sqlalchemy import (
    Column,
    Date,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    inspect,
    text,
)
from sqlalchemy.engine import Engine


# -- Schema definition ------------------------------------------------------

METADATA = MetaData()

customers_table = Table(
    "customers",
    METADATA,
    Column("customer_id", String, primary_key=True),
    Column("customer_name", String, nullable=False),
    Column("segment", String, nullable=False),
    Column("region", String, nullable=False),
    Column("state", String, nullable=False),
    Column("city", String, nullable=False),
)

products_table = Table(
    "products",
    METADATA,
    Column("product_id", String, primary_key=True),
    Column("product_name", String, nullable=False),
    Column("category", String, nullable=False),
    Column("sub_category", String, nullable=False),
    Column("base_price", Float, nullable=False),
)

orders_table = Table(
    "orders",
    METADATA,
    Column("row_id", Integer, primary_key=True, autoincrement=True),
    Column("order_id", String, nullable=False, index=True),
    Column("order_date", Date, nullable=False),
    Column("ship_date", Date, nullable=False),
    Column("ship_mode", String, nullable=False),
    Column("customer_id", String, nullable=False, index=True),
    Column("customer_name", String, nullable=False),
    Column("segment", String, nullable=False),
    Column("region", String, nullable=False),
    Column("state", String, nullable=False),
    Column("city", String, nullable=False),
    Column("product_id", String, nullable=False, index=True),
    Column("product_name", String, nullable=False),
    Column("category", String, nullable=False),
    Column("sub_category", String, nullable=False),
    Column("sales", Float, nullable=False),
    Column("quantity", Integer, nullable=False),
    Column("discount", Float, nullable=False, default=0.0),
    Column("profit", Float, nullable=False),
)

returns_table = Table(
    "returns",
    METADATA,
    Column("return_id", String, primary_key=True),
    Column("order_id", String, nullable=False, index=True),
    Column("reason", String, nullable=False),
    Column("return_date", Date, nullable=False),
)


# -- Helpers ----------------------------------------------------------------

def _coerce_dates(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Convert string date columns to proper datetime objects.

    Args:
        df: Input DataFrame.
        columns: Column names to coerce.

    Returns:
        DataFrame with date columns converted.
    """
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], format="mixed", dayfirst=False)
    return df


def _validate_csv_exists(path: Path) -> None:
    """Raise FileNotFoundError with a helpful message if *path* is missing."""
    if not path.exists():
        raise FileNotFoundError(
            f"Expected CSV not found: {path}\n"
            f"Run `python utils/generate_data.py` first to create the dataset."
        )


# -- Public API -------------------------------------------------------------

def load_csvs_to_sqlite(
    data_dir: str | Path = "data",
    db_path: str | Path = "data/database.db",
    *,
    if_exists: str = "replace",
    echo: bool = False,
) -> Engine:
    """Read Superstore CSVs and load them into a SQLite database.

    This function:
      1. Validates that all required CSVs exist.
      2. Creates the SQLite database (and parent dirs) if needed.
      3. Creates tables with proper column types and indexes.
      4. Loads data using pandas ``to_sql`` with dtype mapping.

    Args:
        data_dir:   Directory containing orders.csv, customers.csv,
                    products.csv, returns.csv.
        db_path:    Path to the SQLite database file.
        if_exists:  Pandas ``to_sql`` strategy -- ``"replace"`` or ``"append"``.
        echo:       If True, SQLAlchemy logs all SQL statements.

    Returns:
        A SQLAlchemy ``Engine`` connected to the new database.

    Raises:
        FileNotFoundError: If any required CSV is missing.
    """
    data_dir = Path(data_dir)
    db_path = Path(db_path)

    # -- 1. Validate inputs ---------------------------------------------
    required_files = ["orders.csv", "customers.csv", "products.csv", "returns.csv"]
    for fname in required_files:
        _validate_csv_exists(data_dir / fname)

    # -- 2. Create engine -----------------------------------------------
    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{db_path}", echo=echo)

    # Enable WAL mode for better concurrent-read performance
    with engine.connect() as conn:
        conn.execute(text("PRAGMA journal_mode=WAL"))
        conn.execute(text("PRAGMA foreign_keys=ON"))
        conn.commit()

    # -- 3. Create tables ----------------------------------------------
    METADATA.create_all(engine)

    # -- 4. Load CSVs --------------------------------------------------
    # Customers
    df_customers = pd.read_csv(data_dir / "customers.csv")
    df_customers.to_sql("customers", engine, if_exists=if_exists, index=False)
    print(f"  [OK] Loaded {len(df_customers):,} rows -> customers")

    # Products
    df_products = pd.read_csv(data_dir / "products.csv")
    df_products.to_sql("products", engine, if_exists=if_exists, index=False)
    print(f"  [OK] Loaded {len(df_products):,} rows -> products")

    # Orders
    df_orders = pd.read_csv(data_dir / "orders.csv")
    df_orders = _coerce_dates(df_orders, ["order_date", "ship_date"])
    df_orders.to_sql("orders", engine, if_exists=if_exists, index=False)
    print(f"  [OK] Loaded {len(df_orders):,} rows -> orders")

    # Returns
    df_returns = pd.read_csv(data_dir / "returns.csv")
    df_returns = _coerce_dates(df_returns, ["return_date"])
    df_returns.to_sql("returns", engine, if_exists=if_exists, index=False)
    print(f"  [OK] Loaded {len(df_returns):,} rows -> returns")

    print(f"\n  Database ready -> {db_path.resolve()}")
    return engine


def load_custom_csv_to_sqlite(
    csv_path: str | Path,
    table_name: str,
    db_path: str | Path = "data/database.db",
) -> dict[str, str]:
    """Load an arbitrary user-uploaded CSV into the database.

    Automatically detects column types and creates the table.
    Returns a dict mapping column names to detected SQLite types
    (used by the Auto Schema Detection feature in Phase 6).

    Args:
        csv_path:    Path to the CSV file.
        table_name:  Name for the new SQLite table.
        db_path:     Path to the SQLite database.

    Returns:
        A dict of ``{column_name: detected_type}`` for schema context.

    Raises:
        FileNotFoundError: If *csv_path* does not exist.
        ValueError:        If the CSV is empty.
    """
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)
    if df.empty:
        raise ValueError(f"CSV is empty: {csv_path}")

    engine = create_engine(f"sqlite:///{db_path}")

    # Sanitize column names (lowercase, replace spaces/special chars with underscore)
    import re
    new_cols = {}
    for col in df.columns:
        c = str(col).strip().lower()
        c = re.sub(r"[^a-z0-9_]", "_", c)
        c = re.sub(r"_+", "_", c).strip("_")
        if not c:
            c = "column"
        base = c
        idx = 1
        while c in new_cols.values():
            c = f"{base}_{idx}"
            idx += 1
        new_cols[col] = c
    df = df.rename(columns=new_cols)

    # Auto-detect date columns
    for col in df.columns:
        if df[col].dtype == "object":
            try:
                df[col] = pd.to_datetime(df[col], format="mixed", dayfirst=False)
            except (ValueError, TypeError):
                pass

    df.to_sql(table_name, engine, if_exists="replace", index=False)

    # Build schema description
    type_map: dict[str, str] = {}
    for col in df.columns:
        dtype = df[col].dtype
        if pd.api.types.is_integer_dtype(dtype):
            type_map[col] = "INTEGER"
        elif pd.api.types.is_float_dtype(dtype):
            type_map[col] = "REAL"
        elif pd.api.types.is_datetime64_any_dtype(dtype):
            type_map[col] = "DATE"
        else:
            type_map[col] = "TEXT"

    print(f"  [OK] Loaded {len(df):,} rows -> {table_name} ({len(type_map)} columns)")
    return type_map


def get_schema_description(db_path: str | Path = "data/database.db") -> str:
    """Generate a human-readable schema description for LLM context.

    Inspects the SQLite database and returns a formatted string showing
    every table with its columns, types, and sample values.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        A multi-line string describing the full database schema.
    """
    db_path = Path(db_path)
    if not db_path.exists():
        return "Database not found. Please load data first."

    engine = create_engine(f"sqlite:///{db_path}")
    inspector = inspect(engine)
    lines: list[str] = ["DATABASE SCHEMA", "=" * 60]

    for table_name in inspector.get_table_names():
        lines.append(f"\nTable: {table_name}")
        lines.append("-" * 40)

        columns = inspector.get_columns(table_name)
        for col in columns:
            col_type = str(col["type"])
            nullable = "NULL" if col.get("nullable", True) else "NOT NULL"
            lines.append(f"  * {col['name']:25s}  {col_type:12s}  {nullable}")

        # Add sample data (first 3 rows)
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT * FROM {table_name} LIMIT 3"))
            sample_rows = result.fetchall()
            col_names = result.keys()

        if sample_rows:
            lines.append(f"\n  Sample data ({table_name}):")
            lines.append(f"  {' | '.join(str(c) for c in col_names)}")
            for row in sample_rows:
                lines.append(f"  {' | '.join(str(v) for v in row)}")

        # Row count
        with engine.connect() as conn:
            count = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
        lines.append(f"\n  Total rows: {count:,}")

    return "\n".join(lines)


# -- CLI entry point -------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load Superstore CSVs into SQLite")
    parser.add_argument("--data-dir", default="data", help="CSV directory")
    parser.add_argument("--db", default="data/database.db", help="SQLite path")
    args = parser.parse_args()

    print("Loading Superstore data into SQLite ...")
    load_csvs_to_sqlite(data_dir=args.data_dir, db_path=args.db)

    print("\n" + get_schema_description(args.db))
