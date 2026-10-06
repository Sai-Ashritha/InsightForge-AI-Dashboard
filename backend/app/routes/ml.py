import pandas as pd
from fastapi import APIRouter, Depends

from app.auth import get_current_user
from app.database.db import fetch_table
from app.services.alert_engine import detect_real_alerts_and_causes
from app.services.anomaly_detector import detect_anomalies
from app.services.dynamic_engine import get_active_dataset, inspect_dataset_schema
from app.services.forecasting import train_and_forecast_dynamic

router = APIRouter(prefix="/ml", tags=["machine-learning"])


def _active_frame():
    frame = get_active_dataset()
    if frame is not None and not frame.empty:
        return frame
    rows = fetch_table("sales")
    return pd.DataFrame(rows) if rows else pd.DataFrame()


@router.get("/forecast")
def ml_forecast(current_user=Depends(get_current_user)):
    df = _active_frame()
    if df.empty:
        return {
            "has_forecast": False,
            "message": "Upload a dataset to generate predictive insights.",
            "forecast_data": [],
            "historical_actuals": [],
            "predicted_revenue": 0,
            "predicted_demand": 0,
            "expected_revenue": 0,
            "product_forecasts": [],
            "validation_metrics": {},
        }
    result = train_and_forecast_dynamic(df)
    result.setdefault("predicted_revenue", 0)
    result.setdefault("predicted_demand", 0)
    result.setdefault("expected_revenue", result["predicted_revenue"])
    result.setdefault("product_forecasts", [])
    result.setdefault("validation_metrics", {})
    return result


@router.get("/anomalies")
def ml_anomalies(current_user=Depends(get_current_user)):
    df = _active_frame()
    if df.empty:
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
    df = _active_frame()
    if df.empty:
        return {"declining_products": [], "alerts": []}
    alerts_res = detect_real_alerts_and_causes(df)
    return {
        "declining_products": alerts_res.get("declining_products", []),
        "alerts": [alert["explanation"] for alert in alerts_res.get("alerts", [])],
    }


@router.get("/inventory")
def inventory_status(current_user=Depends(get_current_user)):
    df = _active_frame()
    if df.empty:
        return {"has_inventory": False, "items": [], "low_stock_count": 0, "total_stock": 0, "alerts": []}

    schema = inspect_dataset_schema(df)
    numeric_cols = schema["numeric_cols"]
    categorical_cols = schema["categorical_cols"]
    stock_col = next((c for c in numeric_cols if any(k in str(c).lower() for k in ["stock_available", "current_stock", "stock", "on_hand", "inventory"])), None)
    reorder_col = next((c for c in numeric_cols if any(k in str(c).lower() for k in ["reorder_level", "min_stock", "safety_stock"])), None)

    if not stock_col:
        return {
            "has_inventory": False,
            "message": "The uploaded dataset does not contain an identifiable stock measure.",
            "items": [],
            "low_stock_count": 0,
            "total_stock": 0,
            "alerts": [],
        }

    frame = df.copy()
    frame[stock_col] = pd.to_numeric(frame[stock_col], errors="coerce")
    if not reorder_col:
        return {
            "has_inventory": True,
            "message": "A stock measure is present, but no reorder threshold was supplied; low-stock status was not inferred.",
            "items": [],
            "low_stock_count": 0,
            "total_stock": int(frame[stock_col].sum()),
            "alerts": [],
        }
    frame[reorder_col] = pd.to_numeric(frame[reorder_col], errors="coerce")
    valid_stock = frame.dropna(subset=[stock_col, reorder_col])
    valid_stock = valid_stock[(valid_stock[stock_col] >= 0) & (valid_stock[reorder_col] >= 0)]

    label_candidates = []
    for column in categorical_cols:
        paired = valid_stock[[column, stock_col, reorder_col]].dropna(subset=[column])
        unique_count = paired[column].nunique()
        if len(paired) and unique_count > 1:
            label_candidates.append((len(paired), unique_count, column))
    category_col = max(label_candidates, default=(0, 0, None))[2]

    items = []
    alerts = []
    for index, row in valid_stock.iterrows():
        stock = row[stock_col]
        threshold = row[reorder_col]
        label = str(row[category_col]) if category_col and pd.notna(row[category_col]) else f"Record {index + 1}"
        low_stock = stock <= threshold
        items.append({
            "product": label,
            "stock_available": int(stock),
            "reorder_level": int(threshold),
            "low_stock": low_stock,
        })
        if low_stock:
            alerts.append(f"{label} is at or below the supplied stock threshold.")

    return {
        "has_inventory": True,
        "items": items[:50],
        "low_stock_count": sum(item["low_stock"] for item in items),
        "total_stock": int(frame[stock_col].sum()),
        "alerts": alerts[:10],
    }
