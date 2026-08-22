import numpy as np
import pandas as pd


def detect_sales_declines(df: pd.DataFrame) -> dict:
    """
    Analyze sales trends across time and by product/category to detect declining segments.
    Compares the current period against the previous period.
    """
    if df is None or df.empty:
        return {
            "declining_products": [],
            "overall_decline": None,
            "alerts": ["No sales data available to analyze trends."],
            "trend_data": [],
        }

    sales_df = df.copy()
    if "revenue" not in sales_df.columns:
        return {
            "declining_products": [],
            "overall_decline": None,
            "alerts": [],
            "trend_data": [],
        }

    sales_df["revenue"] = pd.to_numeric(sales_df["revenue"], errors="coerce").fillna(0)
    
    if "date" in sales_df.columns:
        sales_df["date"] = pd.to_datetime(sales_df["date"], errors="coerce")
        sales_df = sales_df.dropna(subset=["date"]).sort_values("date")
    
    if sales_df.empty:
        return {
            "declining_products": [],
            "overall_decline": None,
            "alerts": [],
            "trend_data": [],
        }

    # Split dataset into previous period and current period (halves or date-based)
    mid_point = len(sales_df) // 2
    if mid_point < 2:
        return {
            "declining_products": [],
            "overall_decline": None,
            "alerts": ["Insufficient historical data points to calculate decline."],
            "trend_data": [],
        }

    prev_df = sales_df.iloc[:mid_point]
    curr_df = sales_df.iloc[mid_point:]

    prev_total = float(prev_df["revenue"].sum())
    curr_total = float(curr_df["revenue"].sum())
    overall_change_pct = round(((curr_total - prev_total) / prev_total) * 100, 1) if prev_total > 0 else 0.0

    declining_products = []
    alerts = []

    if "product" in sales_df.columns:
        prod_prev = prev_df.groupby("product")["revenue"].sum()
        prod_curr = curr_df.groupby("product")["revenue"].sum()

        all_products = set(prod_prev.index).union(set(prod_curr.index))
        for prod in all_products:
            p_val = float(prod_prev.get(prod, 0))
            c_val = float(prod_curr.get(prod, 0))

            if p_val > 0:
                decline_pct = round(((p_val - c_val) / p_val) * 100, 1)
                if decline_pct > 5.0:  # declining by more than 5%
                    declining_products.append({
                        "product": str(prod),
                        "decline_percentage": decline_pct,
                        "previous_sales": round(p_val, 2),
                        "current_sales": round(c_val, 2),
                        "difference": round(p_val - c_val, 2),
                        "severity": "critical" if decline_pct >= 20 else "warning",
                        "alert_message": f"{prod} sales decreased by {decline_pct}% compared to the previous period.",
                    })
                    alerts.append(f"⚠ Sales Alert: {prod} sales decreased by {decline_pct}% compared to the previous period.")
            elif c_val == 0 and p_val > 0:
                declining_products.append({
                    "product": str(prod),
                    "decline_percentage": 100.0,
                    "previous_sales": round(p_val, 2),
                    "current_sales": 0.0,
                    "difference": round(p_val, 2),
                    "severity": "critical",
                    "alert_message": f"{prod} had 0 sales in the recent period (100% decline).",
                })
                alerts.append(f"⚠ Sales Alert: {prod} had 0 sales in the recent period.")

    declining_products = sorted(declining_products, key=lambda x: x["decline_percentage"], reverse=True)

    if not alerts:
        if overall_change_pct < 0:
            alerts.append(f"⚠ Overall sales decreased by {abs(overall_change_pct)}% across all products.")
        else:
            alerts.append("Sales trajectory is healthy across product categories.")

    # Timeline buckets for trend comparison
    trend_buckets = []
    if len(sales_df) >= 4:
        chunk_size = max(1, len(sales_df) // 6)
        for i in range(0, len(sales_df), chunk_size):
            chunk = sales_df.iloc[i:i + chunk_size]
            if not chunk.empty:
                label = f"P{len(trend_buckets) + 1}"
                if "date" in chunk.columns and not chunk["date"].isna().all():
                    label = chunk["date"].iloc[0].strftime("%b %d")
                trend_buckets.append({
                    "period": label,
                    "revenue": round(float(chunk["revenue"].sum()), 2),
                })

    return {
        "declining_products": declining_products,
        "overall_decline_percentage": overall_change_pct if overall_change_pct < 0 else 0,
        "previous_total": round(prev_total, 2),
        "current_total": round(curr_total, 2),
        "alerts": alerts,
        "trend_data": trend_buckets,
    }
