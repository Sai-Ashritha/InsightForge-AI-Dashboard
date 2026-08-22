import pandas as pd

from app.database.db import fetch_table


def get_live_kpis() -> dict:
    sales = fetch_table("sales")
    production = fetch_table("production")
    inventory = fetch_table("inventory")
    employees = fetch_table("employees")

    sales_frame = pd.DataFrame(sales)
    production_frame = pd.DataFrame(production)
    inventory_frame = pd.DataFrame(inventory)
    employees_frame = pd.DataFrame(employees)

    revenue = float(pd.to_numeric(sales_frame.get("revenue", pd.Series(dtype=float)), errors="coerce").sum())
    production_units = int(pd.to_numeric(production_frame.get("units_produced", pd.Series(dtype=float)), errors="coerce").sum())
    inventory_units = int(pd.to_numeric(inventory_frame.get("stock_available", pd.Series(dtype=float)), errors="coerce").sum())

    defective = pd.to_numeric(production_frame.get("defective_units", pd.Series(dtype=float)), errors="coerce").sum()
    defect_rate = round(float(defective / production_units * 100), 2) if production_units else 0.0

    efficiency = 0.0
    machine_hours = pd.to_numeric(production_frame.get("machine_hours", pd.Series(dtype=float)), errors="coerce").sum()
    downtime = pd.to_numeric(production_frame.get("downtime", pd.Series(dtype=float)), errors="coerce").sum()
    if machine_hours:
        efficiency = round(float((1 - downtime / machine_hours) * 100), 2)
    else:
        productivity = pd.to_numeric(employees_frame.get("productivity", pd.Series(dtype=float)), errors="coerce").dropna()
        efficiency = round(float(productivity.mean()), 2) if not productivity.empty else 0.0

    return {
        "revenue": revenue,
        "production": production_units,
        "inventory": inventory_units,
        "efficiency": efficiency,
        "defect_rate": defect_rate,
        "employees": len(employees),
        "orders": len(sales),
        "total_records": len(sales),
    }
