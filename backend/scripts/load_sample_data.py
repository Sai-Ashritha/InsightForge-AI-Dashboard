import os
import pandas as pd
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.db import (
    create_tables,
    insert_dataframe_to_table,
    normalize_dataframe_for_table,
)


def load_sample_data_to_db() -> None:
    """Load all sample CSV data into PostgreSQL."""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "sample")

    print("=" * 70)
    print("Manufacturing Dashboard - Data Loader")
    print("=" * 70)

    print("\n1️⃣  Creating database tables...")
    try:
        result = create_tables()
        print(f"✓ Tables created: {result}")
    except Exception as exc:
        print(f"✗ Error creating tables: {exc}")
        return

    tables = [
        ("sales.csv", "sales"),
        ("production.csv", "production"),
        ("inventory.csv", "inventory"),
        ("employees.csv", "employees"),
        ("finance.csv", "finance"),
    ]

    for csv_file, table_name in tables:
        csv_path = os.path.join(data_dir, csv_file)

        if not os.path.exists(csv_path):
            print(f"⚠️  {csv_file} not found at {csv_path}")
            continue

        print(f"\n2️⃣  Loading {csv_file} into '{table_name}' table...")

        try:
            df = pd.read_csv(csv_path)
            print(f"   - Read {len(df)} records")

            normalized_df = normalize_dataframe_for_table(df, table_name)
            print(f"   - Normalized to {len(normalized_df.columns)} columns")

            result = insert_dataframe_to_table(df, table_name)
            inserted = result.get("inserted_rows", 0)
            print(f"✓ Inserted {inserted} rows into {table_name} table")

        except Exception as exc:
            print(f"✗ Error loading {csv_file}: {exc}")

    print("\n" + "=" * 70)
    print("Data loading completed!")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Start the backend: python -m uvicorn app.main:app --reload")
    print("2. Access dashboard at: http://localhost:3000")
    print("3. Upload more data or query: GET http://localhost:8000/api/dashboard")


if __name__ == "__main__":
    load_sample_data_to_db()
