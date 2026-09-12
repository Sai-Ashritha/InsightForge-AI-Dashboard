from fastapi import APIRouter
import pandas as pd

from app.database.db import fetch_table
from app.services.alert_engine import detect_real_alerts_and_causes
from app.services.anomaly_detector import detect_anomalies, get_column_statistics
from app.services.dynamic_engine import compute_dynamic_analytics, get_active_dataset
from app.services.forecasting import train_and_forecast_dynamic
from app.services.recommendations import estimate_impact, generate_recommendations, prioritize_recommendations

router = APIRouter()


@router.get("/anomalies")
def get_anomalies():
    """Detect anomalies in the active dataset."""
    try:
        df = get_active_dataset()
        if df is None or df.empty:
            return {
                "status": "no_data",
                "anomalies": [],
                "statistics": {},
            }

        result = detect_anomalies(df, contamination=0.05)
        return {
            "status": "success",
            "anomalies": result.get("anomalies", []),
            "statistics": result.get("statistics", {}),
            "column_stats": get_column_statistics(df),
        }
    except Exception as exc:
        return {
            "status": "error",
            "message": str(exc),
        }


@router.get("/recommendations")
def get_recommendations():
    """Generate business recommendations strictly from real data conditions."""
    try:
        df = get_active_dataset()
        if df is None or df.empty:
            return {
                "status": "no_data",
                "recommendations": [],
                "prioritized": {},
                "estimated_impact": {"total_potential_improvement": 0, "top_priority_count": 0},
                "total_count": 0,
                "anomaly_count": 0,
                "sales_decline_count": 0,
            }

        anomaly_result = detect_anomalies(df, contamination=0.05)
        anomalies = anomaly_result.get("anomalies", [])

        alerts_res = detect_real_alerts_and_causes(df)
        sales_declines = alerts_res.get("declining_products", [])

        forecast_res = train_and_forecast_dynamic(df)
        kpi_data = compute_dynamic_analytics(df).get("kpis", [])
        kpi_dict = {k["key"]: k["raw_value"] for k in kpi_data if "key" in k and "raw_value" in k}

        recommendations = generate_recommendations(
            data=kpi_dict,
            anomalies=anomalies,
            sales_declines=sales_declines,
            forecast_data=forecast_res,
            inventory_data=[],
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
            "estimated_impact": {"total_potential_improvement": 0, "top_priority_count": 0},
            "total_count": 0,
            "anomaly_count": 0,
            "sales_decline_count": 0,
        }


@router.get("/analytics")
def get_analytics():
    """Get comprehensive analytics summary based on active dataset."""
    try:
        df = get_active_dataset()
        if df is None or df.empty:
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

        anomaly_result = detect_anomalies(df, contamination=0.05)
        column_stats = get_column_statistics(df)
        alerts_res = detect_real_alerts_and_causes(df)
        forecast_res = train_and_forecast_dynamic(df)

        kpi_data = compute_dynamic_analytics(df).get("kpis", [])
        kpi_dict = {k["key"]: k["raw_value"] for k in kpi_data if "key" in k and "raw_value" in k}

        recommendations = generate_recommendations(
            data=kpi_dict,
            anomalies=anomaly_result.get("anomalies", []),
            sales_declines=alerts_res.get("declining_products", []),
            forecast_data=forecast_res,
            inventory_data=[],
        )
        impact = estimate_impact(recommendations)

        return {
            "status": "success",
            "summary": {
                "total_records": len(df),
                "anomaly_count": anomaly_result.get("anomaly_count", 0),
                "anomaly_percentage": anomaly_result.get("statistics", {}).get("anomaly_percentage", 0),
                "recommendation_count": len(recommendations),
                "critical_recommendations": sum(1 for r in recommendations if r.get("priority") == "critical"),
                "total_potential_improvement": impact.get("total_potential_improvement", 0),
            },
            "column_statistics": column_stats,
            "top_anomalies": anomaly_result.get("anomalies", [])[:5],
            "top_recommendations": recommendations[:3],
            "sales_declines": alerts_res.get("declining_products", [])[:3],
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
