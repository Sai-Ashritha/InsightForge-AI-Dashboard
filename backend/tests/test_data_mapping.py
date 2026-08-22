import pandas as pd

import app.database.db as database
from app.database.db import infer_table_for_dataframe, normalize_dataframe_for_table


def test_infer_sales_table_from_dataframe():
    df = pd.DataFrame([
        {
            "date": "2024-01-01",
            "product": "Widget A",
            "category": "Electronics",
            "region": "North",
            "quantity": 120,
            "unit_price": 50,
            "revenue": 6000,
        }
    ])

    assert infer_table_for_dataframe(df) == "sales"


def test_normalize_dataframe_for_sales_table():
    df = pd.DataFrame([
        {
            "date": "2024-01-01",
            "product": "Widget A",
            "category": "Electronics",
            "region": "North",
            "quantity": 120,
            "unit_price": 50,
            "revenue": 6000,
        }
    ])

    normalized = normalize_dataframe_for_table(df, "sales")

    assert list(normalized.columns) == [
        "date",
        "product",
        "category",
        "region",
        "quantity",
        "unit_price",
        "revenue",
    ]
    assert normalized.iloc[0]["quantity"] == 120


def test_combined_manufacturing_upload_populates_kpi_tables(monkeypatch):
    inserted = []
    cleared = []

    def fake_insert(dataframe, table_name):
        inserted.append((table_name, list(dataframe.columns), len(dataframe)))
        return {"table": table_name, "inserted_rows": len(dataframe)}

    monkeypatch.setattr(database, "insert_dataframe_to_table", fake_insert)
    monkeypatch.setattr(database, "clear_table", lambda table_name: cleared.append(table_name))
    result = database.save_uploaded_dataframe(pd.DataFrame([{
        "date": "2026-01-01",
        "product": "Product A",
        "quantity": 10,
        "revenue": 1000,
        "production": 500,
        "inventory": 200,
        "employees": 4,
        "efficiency": 91,
        "defect_rate": 2,
    }]))

    assert result["tables"] == ["sales", "production", "inventory", "employees"]
    assert [item[0] for item in inserted] == ["sales", "production", "inventory", "employees"]
    assert cleared == ["sales", "production", "inventory", "employees"]
