from fastapi import APIRouter
import pandas as pd

from app.database.db import fetch_table
from app.services.forecasting import generate_forecast, train_and_forecast_sales

router = APIRouter()


@router.get("/forecast")
def forecast_summary():
    fallback_values = [120000, 135000, 140000, 155000, 170000, 185000, 200000]

    try:
        sales_data = fetch_table("sales")
        sales_df = pd.DataFrame(sales_data)
        if sales_df.empty or "revenue" not in sales_df.columns:
            result = generate_forecast(fallback_values)
            result["data_source"] = "fallback"
            result["history_points"] = len(fallback_values)
            return result

        sales_df["revenue"] = pd.to_numeric(sales_df["revenue"], errors="coerce")
        sales_df = sales_df.dropna(subset=["revenue"])

        if "date" in sales_df.columns:
            sales_df["date"] = pd.to_datetime(sales_df["date"], errors="coerce")
            dated_sales = sales_df.dropna(subset=["date"])
            if not dated_sales.empty:
                values = dated_sales.groupby("date")["revenue"].sum().sort_index().tolist()
            else:
                values = sales_df["revenue"].tolist()
        else:
            values = sales_df["revenue"].tolist()

        if not values:
            values = fallback_values
            source = "fallback"
        else:
            source = "sales_database"

        # Also get full ML forecast
        s_renamed = sales_df.rename(columns={"revenue": "total_revenue"})
        ml_res = train_and_forecast_sales(s_renamed, forecast_days=30)
        
        result = generate_forecast(values)
        result["data_source"] = source
        result["history_points"] = len(values)
        result["forecast_data"] = ml_res.get("forecast_data", [])
        result["predicted_revenue"] = ml_res.get("predicted_revenue", result.get("expected_revenue", 850000))
        result["predicted_demand"] = ml_res.get("predicted_demand", 12500)
        result["product_forecasts"] = ml_res.get("product_forecasts", [])
        result["model_performance"] = ml_res.get("model_performance", {})
        return result

    except Exception:
        result = generate_forecast(fallback_values)
        result["data_source"] = "fallback"
        result["history_points"] = len(fallback_values)
        return result

