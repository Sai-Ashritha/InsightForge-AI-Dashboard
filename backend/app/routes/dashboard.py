from typing import Optional
import numpy as np
import pandas as pd
from fastapi import APIRouter, Query

from app.database.db import fetch_table
from app.services.alert_engine import detect_real_alerts_and_causes
from app.services.data_quality import assess_data_quality
from app.services.dynamic_engine import compute_dynamic_analytics, get_active_dataset, inspect_dataset_schema
from app.services.sales_decline import detect_sales_declines

router = APIRouter()


@router.get("/dashboard/dynamic")
def get_dynamic_dashboard(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    category_col: Optional[str] = Query(None),
    category_val: Optional[str] = Query(None),
):
    """
    Generate dynamic KPIs, charts, and filter options strictly from the active uploaded dataset.
    Never fabricates values for missing domains.
    """
    df = get_active_dataset()
    if df is None or df.empty:
        return {
            "status": "no_data",
            "message": "No dataset uploaded yet. Please upload a CSV, Excel, or JSON dataset in Quality & Cleaning.",
            "kpis": [],
            "charts": [],
            "available_filters": {},
            "total_records": 0,
            "filtered_records": 0,
            "preview": [],
        }

    return compute_dynamic_analytics(
        df=df,
        start_date=start_date,
        end_date=end_date,
        category_col=category_col,
        category_val=category_val,
    )


@router.get("/alerts-and-causes")
def get_alerts_and_causes():
    """
    Derive alerts and root causes strictly from actual conditions in the active dataset.
    No arbitrary fake probability scores (e.g. 88%, 91%).
    """
    df = get_active_dataset()
    if df is None or df.empty:
        return {
            "status": "no_data",
            "alerts": [],
            "declining_products": [],
            "root_causes": [],
            "message": "Upload a dataset to generate real alerts and root cause analysis.",
        }

    return detect_real_alerts_and_causes(df)


@router.get("/dashboard")
def get_dashboard():
    """Return KPI values derived from the active uploaded dataset only."""
    try:
        active_df = get_active_dataset()

        if active_df is None or active_df.empty:
            return {
                "status": "no_data",
                "data_source": "no_data",
                "message": "Upload a CSV, Excel, or JSON dataset to generate real dashboard metrics.",
                "revenue": 0,
                "production": 0,
                "inventory": 0,
                "defect_rate": 0,
                "quality_score": 0,
                "employees": 0,
                "orders": 0,
                "forecast_next_month": 0,
                "trend": [],
                "trend_labels": [],
                "production_trend": [],
                "product_performance": [],
                "inventory_status": [],
                "sales_declines": [],
                "alerts": [],
                "dynamic_analytics": {"status": "empty", "charts": [], "kpis": [], "preview": []},
            }

        dynamic_result = compute_dynamic_analytics(active_df)
        alerts_res = detect_real_alerts_and_causes(active_df)
        quality_res = assess_data_quality(active_df)

        revenue = 0.0
        sales_col = next((c for c in active_df.columns if any(k in str(c).lower() for k in ["revenue", "sales", "price_total", "total_sales", "sales_value"])) , None)
        if sales_col:
            revenue = float(pd.to_numeric(active_df[sales_col], errors="coerce").sum())

        qty_col = next((c for c in active_df.columns if any(k in str(c).lower() for k in ["quantity", "units_sold", "units_produced", "production", "admissions", "output", "qty"])) , None)
        production_units = int(pd.to_numeric(active_df[qty_col], errors="coerce").sum()) if qty_col else 0

        stock_col = next((c for c in active_df.columns if any(k in str(c).lower() for k in ["current_stock", "stock_available", "inventory", "stock", "on_hand"])) , None)
        inventory_units = int(pd.to_numeric(active_df[stock_col], errors="coerce").sum()) if stock_col else 0

        defect_col = next((c for c in active_df.columns if any(k in str(c).lower() for k in ["defect", "scrap", "rejected"]) and not any(k in str(c).lower() for k in ["rate", "percent", "ratio", "cost", "expense"])) , None)
        defect_rate = 0.0
        if defect_col and qty_col and production_units > 0:
            paired_counts = active_df[[defect_col, qty_col]].apply(pd.to_numeric, errors="coerce").dropna()
            matched_quantity = float(paired_counts[qty_col].sum()) if not paired_counts.empty else 0.0
            matched_defects = float(paired_counts[defect_col].sum()) if not paired_counts.empty else 0.0
            if matched_quantity > 0 and 0 <= matched_defects <= matched_quantity:
                defect_rate = round(matched_defects / matched_quantity * 100, 2)

        quality_score = quality_res.get("quality_score", 0.0)
        date_col = next((c for c in active_df.columns if pd.api.types.is_datetime64_any_dtype(active_df[c]) or any(k in str(c).lower() for k in ["date", "time", "day"])) , None)
        metric_to_use = sales_col or qty_col

        product_performance = []
        cat_col = next((c for c in active_df.columns if any(k in str(c).lower() for k in ["product", "item", "category", "department", "sku", "region"])) , None)
        if cat_col and metric_to_use:
            prod_grp = active_df.groupby(cat_col)[metric_to_use].sum().reset_index()
            prod_grp = prod_grp.sort_values(by=metric_to_use, ascending=False).head(10)
            total_metric = float(prod_grp[metric_to_use].sum()) if not prod_grp.empty else 0.0
            for _, row in prod_grp.iterrows():
                metric_value = float(row[metric_to_use]) if pd.notna(row[metric_to_use]) else 0.0
                share = (metric_value / total_metric * 100) if total_metric > 0 else 0.0
                product_performance.append({
                    "name": str(row[cat_col]),
                    "revenue": metric_value,
                    "units": int(metric_value),
                    "share": round(float(share), 1),
                })

        trend = []
        trend_labels = []
        if date_col and metric_to_use:
            filtered = active_df.dropna(subset=[date_col, metric_to_use]).copy()
            filtered[date_col] = pd.to_datetime(filtered[date_col], errors="coerce")
            filtered = filtered.dropna(subset=[date_col]).sort_values(date_col)
            if len(filtered) >= 3:
                aggregated = filtered.groupby(filtered[date_col].dt.date)[metric_to_use].sum().head(15)
                trend = [round(float(v), 2) for v in aggregated.values]
                trend_labels = [d.strftime("%b %d") for d in aggregated.index]

        forecast_value = round(float(revenue), 2) if revenue > 0 else 0.0

        inventory_status = []
        if stock_col:
            stock_frame = active_df.copy()
            stock_frame[stock_col] = pd.to_numeric(stock_frame[stock_col], errors="coerce")
            valid_stock = stock_frame.dropna(subset=[stock_col])
            valid_stock = valid_stock[valid_stock[stock_col] >= 0]
            category_candidates = []
            categorical_columns = inspect_dataset_schema(active_df)["categorical_cols"]
            for column in categorical_columns:
                paired = valid_stock[[column, stock_col]].dropna()
                unique_count = paired[column].nunique()
                if len(paired) >= 2 and 2 <= unique_count <= 200:
                    category_candidates.append((len(paired), unique_count, column, paired))

            if category_candidates:
                _, _, stock_category, paired_stock = max(category_candidates, key=lambda item: (item[0], item[1]))
                grouped_stock = paired_stock.groupby(stock_category)[stock_col].sum().sort_values(ascending=False).head(8)
                maximum_stock = float(grouped_stock.max()) if not grouped_stock.empty else 0.0
                inventory_status = [
                    {
                        "name": str(name),
                        "units": int(value),
                        "value": round(float(value) / maximum_stock * 100) if maximum_stock > 0 else 0,
                    }
                    for name, value in grouped_stock.items()
                ]
            elif not valid_stock.empty:
                stock_total = float(valid_stock[stock_col].sum())
                inventory_status = [{"name": "All records", "units": int(stock_total), "value": 100 if stock_total > 0 else 0}]

        return {
            "status": "success",
            "data_source": "active_dataset",
            "revenue": revenue,
            "production": production_units,
            "inventory": inventory_units,
            "defect_rate": defect_rate,
            "quality_score": quality_score,
            "employees": len(active_df),
            "orders": len(active_df),
            "forecast_next_month": forecast_value,
            "trend": trend,
            "trend_labels": trend_labels,
            "production_trend": trend,
            "product_performance": product_performance,
            "inventory_status": inventory_status,
            "sales_declines": alerts_res.get("declining_products", []),
            "alerts": [a["explanation"] for a in alerts_res.get("alerts", [])],
            "dynamic_analytics": dynamic_result,
            "total_records": len(active_df),
            "filtered_records": len(active_df),
        }

    except Exception as exc:
        return {
            "status": "error",
            "data_source": "error",
            "message": str(exc),
            "revenue": 0,
            "production": 0,
            "inventory": 0,
            "defect_rate": 0,
            "quality_score": 0,
            "employees": 0,
            "orders": 0,
            "forecast_next_month": 0,
            "trend": [],
            "trend_labels": [],
            "production_trend": [],
            "product_performance": [],
            "inventory_status": [],
            "sales_declines": [],
            "alerts": [f"Status: {str(exc)}"],
            "dynamic_analytics": {"status": "error", "charts": [], "kpis": [], "preview": []},
        }
