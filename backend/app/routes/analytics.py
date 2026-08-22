from fastapi import APIRouter
import pandas as pd

from app.database.db import fetch_table
from app.services.anomaly_detector import detect_anomalies, get_column_statistics
from app.services.forecasting import train_and_forecast_sales
from app.services.recommendations import generate_recommendations, prioritize_recommendations, estimate_impact
from app.services.sales_decline import detect_sales_declines
from app.services.kpi_calculator import get_live_kpis

router = APIRouter()


@router.get("/anomalies")
def get_anomalies():
    """Detect anomalies in the sales table."""
    try:
        sales_data = fetch_table("sales")
        if not sales_data:
            return {
                "status": "no_data",
                "anomalies": [],
                "statistics": {}
            }

        df = pd.DataFrame(sales_data)
        result = detect_anomalies(df, contamination=0.05)

        return {
            "status": "success",
            "table": "sales",
            "anomalies": result.get("anomalies", []),
            "statistics": result.get("statistics", {}),
            "column_stats": get_column_statistics(df)
        }
    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc)
        }


@router.get("/recommendations")
def get_recommendations():
    """Generate business recommendations based on current KPIs, anomalies, declines, and forecasts."""
    try:
        sales_data = fetch_table("sales")
        inventory_data = fetch_table("inventory")
        kpi_data = get_live_kpis()

        df_sales = pd.DataFrame(sales_data) if sales_data else pd.DataFrame()
        df_inv = pd.DataFrame(inventory_data) if inventory_data else pd.DataFrame()

        anomalies = []
        sales_declines = []
        forecast_res = {}

        if not df_sales.empty:
            anomaly_result = detect_anomalies(df_sales, contamination=0.05)
            anomalies = anomaly_result.get("anomalies", [])
            decline_result = detect_sales_declines(df_sales)
            sales_declines = decline_result.get("declining_products", [])
            if "revenue" in df_sales.columns:
                s_renamed = df_sales.rename(columns={"revenue": "total_revenue"})
                forecast_res = train_and_forecast_sales(s_renamed, forecast_days=30)

        inv_items = df_inv.to_dict(orient="records") if not df_inv.empty else []
        recommendations = generate_recommendations(
            data=kpi_data,
            anomalies=anomalies,
            sales_declines=sales_declines,
            forecast_data=forecast_res,
            inventory_data=inv_items,
        )
        prioritized = prioritize_recommendations(recommendations)
        impact = estimate_impact(recommendations)

        return {
            "status": "success",
            "recommendations": recommendations,
            "prioritized": prioritized,
            "estimated_impact": impact,
            "total_count": len(recommendations),
            "anomaly_count": len(anomalies),
            "sales_decline_count": len(sales_declines),
        }
    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc),
            "recommendations": [],
            "prioritized": {},
            "estimated_impact": {
                "total_potential_improvement": 0,
                "top_priority_count": 0,
            },
            "total_count": 0,
            "anomaly_count": 0,
            "sales_decline_count": 0,
        }


@router.get("/analytics")
def get_analytics():
    """Get comprehensive analytics summary."""
    try:
        sales_data = fetch_table("sales")
        inventory_data = fetch_table("inventory")

        if not sales_data:
            return {
                "status": "no_data",
                "summary": {
                    "total_records": 0,
                    "anomaly_count": 0,
                    "anomaly_percentage": 0,
                    "recommendation_count": 0,
                    "critical_recommendations": 0,
                    "total_potential_improvement": 0,
                },
                "column_statistics": {},
                "top_anomalies": [],
                "top_recommendations": [],
            }

        df_sales = pd.DataFrame(sales_data)
        df_inv = pd.DataFrame(inventory_data) if inventory_data else pd.DataFrame()

        anomaly_result = detect_anomalies(df_sales, contamination=0.05)
        column_stats = get_column_statistics(df_sales)
        kpi_data = get_live_kpis()
        decline_result = detect_sales_declines(df_sales)

        forecast_res = {}
        if "revenue" in df_sales.columns:
            s_renamed = df_sales.rename(columns={"revenue": "total_revenue"})
            forecast_res = train_and_forecast_sales(s_renamed, forecast_days=30)

        inv_items = df_inv.to_dict(orient="records") if not df_inv.empty else []
        recommendations = generate_recommendations(
            data=kpi_data,
            anomalies=anomaly_result.get("anomalies", []),
            sales_declines=decline_result.get("declining_products", []),
            forecast_data=forecast_res,
            inventory_data=inv_items,
        )
        impact = estimate_impact(recommendations)

        return {
            "status": "success",
            "summary": {
                "total_records": len(df_sales),
                "anomaly_count": anomaly_result.get("anomaly_count", 0),
                "anomaly_percentage": anomaly_result.get("statistics", {}).get("anomaly_percentage", 0),
                "recommendation_count": len(recommendations),
                "critical_recommendations": sum(1 for r in recommendations if r.get("priority") == "critical"),
                "total_potential_improvement": impact.get("total_potential_improvement", 0),
            },
            "column_statistics": column_stats,
            "top_anomalies": anomaly_result.get("anomalies", [])[:5],
            "top_recommendations": recommendations[:3],
            "sales_declines": decline_result.get("declining_products", [])[:3],
        }
    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc),
            "summary": {
                "total_records": 0,
                "anomaly_count": 0,
                "anomaly_percentage": 0,
                "recommendation_count": 0,
                "critical_recommendations": 0,
                "total_potential_improvement": 0,
            },
            "column_statistics": {},
            "top_anomalies": [],
            "top_recommendations": [],
        }

