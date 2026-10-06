from fastapi import APIRouter
import pandas as pd

from app.database.db import fetch_table
from app.services.dynamic_engine import get_active_dataset, inspect_dataset_schema
from app.services.forecasting import generate_forecast, train_and_forecast_dynamic

router = APIRouter()


@router.get("/forecast")
def forecast_summary():
    try:
        active_df = get_active_dataset()
        source = "active_dataset"
        if active_df is None or active_df.empty:
            rows = fetch_table("sales")
            active_df = pd.DataFrame(rows) if rows else pd.DataFrame()
            source = "sales_database"

        if active_df.empty:
            return {
                "has_forecast": False,
                "message": "Upload a dataset with chronological observations and a numeric measure to generate a forecast.",
                "data_source": "no_data",
                "history": [],
                "forecast_values": [],
                "forecast_data": [],
                "history_points": 0,
                "expected_revenue": 0,
                "predicted_revenue": 0,
                "predicted_demand": 0,
                "product_forecasts": [],
                "model_performance": {},
            }

        schema = inspect_dataset_schema(active_df)
        date_col = schema["date_cols"][0] if schema["date_cols"] else None
        numeric_cols = schema["numeric_cols"]
        target_col = next(
            (column for column in numeric_cols if any(token in str(column).lower() for token in ["revenue", "sales", "amount", "quantity", "units", "output", "volume"])),
            numeric_cols[0] if numeric_cols else None,
        )
        if not date_col or not target_col:
            result = train_and_forecast_dynamic(active_df, date_col=date_col, target_col=target_col)
            result.update({
                "data_source": source,
                "history": [],
                "forecast_values": [],
                "history_points": len(active_df),
                "expected_revenue": 0,
            })
            return result

        frame = active_df[[date_col, target_col]].copy()
        frame[date_col] = pd.to_datetime(frame[date_col], errors="coerce")
        frame[target_col] = pd.to_numeric(frame[target_col], errors="coerce")
        frame = frame.dropna(subset=[date_col, target_col])
        history = frame.groupby(date_col)[target_col].sum().sort_index().tolist()
        result = generate_forecast(history)
        ml_result = train_and_forecast_dynamic(active_df, date_col=date_col, target_col=target_col)
        result.update({
            "has_forecast": ml_result.get("has_forecast", bool(history)),
            "message": ml_result.get("message", "Forecast generated from uploaded data."),
            "data_source": source,
            "history_points": len(history),
            "target_metric": target_col,
            "forecast_data": ml_result.get("forecast_data", []),
            "historical_actuals": ml_result.get("historical_actuals", []),
            "predicted_revenue": ml_result.get("predicted_revenue", result["expected_revenue"]),
            "predicted_demand": ml_result.get("predicted_demand", 0),
            "product_forecasts": ml_result.get("product_forecasts", []),
            "model_performance": ml_result.get("model_performance", result["model_performance"]),
            "model_limitations": ml_result.get("model_limitations"),
        })
        return result
    except Exception as exc:
        return {
            "has_forecast": False,
            "message": f"Forecast could not be generated from the active dataset: {exc}",
            "data_source": "error",
            "history": [],
            "forecast_values": [],
            "forecast_data": [],
            "history_points": 0,
            "expected_revenue": 0,
            "predicted_revenue": 0,
            "predicted_demand": 0,
            "product_forecasts": [],
            "model_performance": {},
        }

