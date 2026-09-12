import pandas as pd
from fastapi import APIRouter, Depends

from app.auth import get_current_user
from app.database.db import fetch_table
from app.services.alert_engine import detect_real_alerts_and_causes
from app.services.anomaly_detector import detect_anomalies
from app.services.dynamic_engine import get_active_dataset, inspect_dataset_schema
from app.services.forecasting import train_and_forecast_dynamic

router = APIRouter(prefix="/ml", tags=["machine-learning"])


@router.get("/forecast")
def ml_forecast(current_user=Depends(get_current_user)):
    df = None
    try:
        rows = fetch_table("sales")
        if rows:
            df = pd.DataFrame(rows)
    except Exception:
        pass

    if df is None or df.empty:
        cached_df = get_active_dataset()
        if cached_df is not None and not cached_df.empty:
            df = cached_df

    if df is None or df.empty:
        return {
            "has_forecast": False,
            "message": "Not enough historical data for reliable forecasting. Please upload a dataset in Quality & Cleaning.",
            "forecast_data": [],
            "historical_actuals": [],
            "predicted_revenue": 0,
            "predicted_demand": 0,
            "expected_revenue": 0,
            "product_forecasts": [],
            "validation_metrics": {},
        }
    return train_and_forecast_dynamic(df, forecast_horizon_days=30)


@router.get("/anomalies")
def ml_anomalies(current_user=Depends(get_current_user)):
    df = None
    try:
        rows = fetch_table("sales")
        if rows:
            df = pd.DataFrame(rows)
    except Exception:
        pass

    if df is None or df.empty:
        cached_df = get_active_dataset()
        if cached_df is not None and not cached_df.empty:
            df = cached_df

    if df is None or df.empty:
        return {
            "algorithm": "Isolation Forest",
            "anomalies": [],
            "statistics": {"total_rows": 0, "anomaly_count": 0, "anomaly_percentage": 0},
            "anomaly_count": 0,
        }

    result = detect_anomalies(df, contamination=0.05)
    return {
        "algorithm": "Isolation Forest",
        "anomalies": result.get("anomalies", []),
        "statistics": result.get("statistics", {}),
        "anomaly_count": result.get("anomaly_count", 0),
    }


@router.get("/sales-decline")
def ml_sales_decline(current_user=Depends(get_current_user)):
    df = None
    try:
        rows = fetch_table("sales")
        if rows:
            df = pd.DataFrame(rows)
    except Exception:
        pass

    if df is None or df.empty:
        cached_df = get_active_dataset()
        if cached_df is not None and not cached_df.empty:
            df = cached_df

    if df is None or df.empty:
        return {"declining_products": [], "alerts": []}
    alerts_res = detect_real_alerts_and_causes(df)
    return {
        "declining_products": alerts_res.get("declining_products", []),
        "alerts": [a["explanation"] for a in alerts_res.get("alerts", [])],
    }


@router.get("/inventory")
def inventory_status(current_user=Depends(get_current_user)):
    df = None
    try:
        rows = fetch_table("inventory")
        if rows:
            df = pd.DataFrame(rows)
    except Exception:
        pass

    if df is None or df.empty:
        cached_df = get_active_dataset()
        if cached_df is not None and not cached_df.empty:
            df = cached_df

    if df is None or df.empty:
        return {"has_inventory": False, "items": [], "low_stock_count": 0, "total_stock": 0, "alerts": []}

    schema = inspect_dataset_schema(df)
    numeric_cols = schema["numeric_cols"]
    categorical_cols = schema["categorical_cols"]

    stock_col = next((c for c in numeric_cols if any(k in str(c).lower() for k in ["stock_available", "current_stock", "stock", "on_hand", "inventory"])), None)
    reorder_col = next((c for c in numeric_cols if any(k in str(c).lower() for k in ["reorder_level", "min_stock", "safety_stock"])), None)
    prod_col = categorical_cols[0] if categorical_cols else None

    # If no stock column exists, do not fabricate synthetic stock
    if not stock_col:
        return {
            "has_inventory": False,
            "message": "The uploaded dataset does not contain inventory or stock columns.",
            "items": [],
            "low_stock_count": 0,
            "total_stock": 0,
            "alerts": [],
        }

    frame = df.copy()
    frame[stock_col] = pd.to_numeric(frame[stock_col], errors="coerce").fillna(0)

    if reorder_col:
        frame[reorder_col] = pd.to_numeric(frame[reorder_col], errors="coerce").fillna(0)
    else:
        # Benchmark median/quantile if no reorder level specified
        frame["reorder_level"] = int(frame[stock_col].quantile(0.25))
        reorder_col = "reorder_level"

    frame["low_stock"] = frame[stock_col] <= frame[reorder_col]
    items = []
    alerts = []

    for _, row in frame.iterrows():
        p_name = str(row[prod_col]) if prod_col else f"SKU-{_ + 1}"
        stk = int(row[stock_col])
        reord = int(row[reorder_col])
        is_low = stk <= reord
        items.append({
            "product": p_name,
            "stock_available": stk,
            "reorder_level": reord,
            "low_stock": is_low,
        })
        if is_low:
            alerts.append(f"⚠ Low Stock Alert: {p_name} is below the reorder level. Current Stock: {stk}, Reorder Level: {reord}")

    return {
        "has_inventory": True,
        "items": items[:50],
        "low_stock_count": sum(1 for i in items if i["low_stock"]),
        "total_stock": int(frame[stock_col].sum()),
        "alerts": alerts[:10],
    }
