import pandas as pd
import numpy as np
from typing import Dict, Any, List
from app.services.dynamic_engine import inspect_dataset_schema


def detect_real_alerts_and_causes(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate alerts and root causes strictly derived from actual data conditions.
    Never fabricates probabilities, departments, or inventory levels that do not exist.
    """
    if df is None or df.empty:
        return {
            "alerts": [],
            "declining_products": [],
            "root_causes": [],
            "status": "no_data",
            "message": "No active dataset available to analyze.",
        }

    schema = inspect_dataset_schema(df)
    date_cols = schema["date_cols"]
    numeric_cols = schema["numeric_cols"]
    categorical_cols = schema["categorical_cols"]

    alerts = []
    declining_items = []
    root_causes = []

    # 1. Check Data Quality Condition
    missing_count = int(df.isnull().sum().sum())
    duplicate_count = int(df.duplicated().sum())

    if missing_count > 0:
        pct = round((missing_count / (len(df) * len(df.columns))) * 100, 1)
        alerts.append({
            "id": "alert_data_missing",
            "type": "data_quality",
            "severity": "warning" if pct < 5 else "critical",
            "title": "Missing Values Detected",
            "product": "Dataset Quality",
            "actual_value": f"{missing_count} missing cells",
            "comparison_value": "0 missing cells",
            "change_pct": pct,
            "period": "Current Ingestion",
            "explanation": f"Dataset contains {missing_count} missing values ({pct}% of total cells) across {len(df.columns)} columns.",
            "recommended_action": "Review data source pipeline and verify missing value imputation in the cleaning step.",
        })

    if duplicate_count > 0:
        alerts.append({
            "id": "alert_data_duplicate",
            "type": "data_quality",
            "severity": "warning",
            "title": "Duplicate Records Detected",
            "product": "Dataset Integrity",
            "actual_value": f"{duplicate_count} duplicate rows",
            "comparison_value": "0 duplicate rows",
            "change_pct": round((duplicate_count / len(df)) * 100, 1),
            "period": "Current Ingestion",
            "explanation": f"Found {duplicate_count} duplicate rows in the uploaded dataset.",
            "recommended_action": "Deduplicate records to avoid inflated analytical metrics.",
        })

    # 2. Check Period-over-Period Metric Decline
    # Identify primary measure (sales, revenue, quantity, units_produced, etc.)
    primary_metric = next(
        (c for c in numeric_cols if any(k in str(c).lower() for k in ["sales", "revenue", "quantity", "units_sold", "units_produced", "output", "admissions"])),
        numeric_cols[0] if numeric_cols else None,
    )
    primary_cat = categorical_cols[0] if categorical_cols else None

    if primary_metric and len(df) >= 4:
        work_df = df.copy()
        work_df[primary_metric] = pd.to_numeric(work_df[primary_metric], errors="coerce").fillna(0)

        # Sort by date if available
        if date_cols and date_cols[0] in work_df.columns:
            work_df[date_cols[0]] = pd.to_datetime(work_df[date_cols[0]], errors="coerce")
            work_df = work_df.dropna(subset=[date_cols[0]]).sort_values(date_cols[0])

        half = len(work_df) // 2
        prev_slice = work_df.iloc[:half]
        curr_slice = work_df.iloc[half:]

        # Overall metric change
        prev_tot = float(prev_slice[primary_metric].sum())
        curr_tot = float(curr_slice[primary_metric].sum())
        if prev_tot > 0:
            tot_change = round(((curr_tot - prev_tot) / prev_tot) * 100, 1)
            if tot_change < -5.0:
                is_curr = any(k in str(primary_metric).lower() for k in ["sales", "revenue", "price", "income"])
                p_fmt = f"₹{prev_tot:,.2f}" if is_curr else f"{prev_tot:,.0f}"
                c_fmt = f"₹{curr_tot:,.2f}" if is_curr else f"{curr_tot:,.0f}"
                alerts.append({
                    "id": f"alert_overall_{primary_metric}",
                    "type": "metric_decline",
                    "severity": "critical" if tot_change <= -20 else "warning",
                    "title": f"Overall {primary_metric.replace('_', ' ').title()} Decline",
                    "product": "All Segments",
                    "actual_value": c_fmt,
                    "comparison_value": p_fmt,
                    "change_pct": tot_change,
                    "period": "Second Half vs First Half of Timeline",
                    "explanation": f"Overall {primary_metric.replace('_', ' ')} decreased by {abs(tot_change)}% (from {p_fmt} down to {c_fmt}).",
                    "recommended_action": f"Audit overall operational performance and review seasonal and channel variables.",
                })

        # By category / product if available
        if primary_cat and primary_cat in work_df.columns:
            prev_by_cat = prev_slice.groupby(primary_cat)[primary_metric].sum()
            curr_by_cat = curr_slice.groupby(primary_cat)[primary_metric].sum()
            all_cats = set(prev_by_cat.index).union(set(curr_by_cat.index))

            for cat in all_cats:
                p_val = float(prev_by_cat.get(cat, 0))
                c_val = float(curr_by_cat.get(cat, 0))

                if p_val > 0:
                    chg = round(((c_val - p_val) / p_val) * 100, 1)
                    if chg < -5.0:
                        decline_pct = abs(chg)
                        is_curr = any(k in str(primary_metric).lower() for k in ["sales", "revenue", "price", "income"])
                        p_fmt = f"₹{p_val:,.2f}" if is_curr else f"{p_val:,.0f}"
                        c_fmt = f"₹{c_val:,.2f}" if is_curr else f"{c_val:,.0f}"

                        dec_item = {
                            "product": str(cat),
                            "metric": primary_metric,
                            "decline_percentage": decline_pct,
                            "previous_sales": round(p_val, 2),
                            "current_sales": round(c_val, 2),
                            "difference": round(p_val - c_val, 2),
                            "severity": "critical" if decline_pct >= 25 else "warning",
                            "alert_message": f"{cat} {primary_metric} decreased by {decline_pct}% compared with the previous period.",
                        }
                        declining_items.append(dec_item)

                        alerts.append({
                            "id": f"alert_decline_{str(cat).replace(' ', '_')}",
                            "type": "metric_decline",
                            "severity": "critical" if decline_pct >= 25 else "warning",
                            "title": f"Performance Drop: {cat}",
                            "product": str(cat),
                            "actual_value": c_fmt,
                            "comparison_value": p_fmt,
                            "change_pct": -decline_pct,
                            "period": "Current vs Previous Period",
                            "explanation": f"{primary_metric.replace('_', ' ').title()} for {cat} decreased from {p_fmt} to {c_fmt} ({decline_pct}% drop).",
                            "recommended_action": f"Review pricing, distribution availability, and customer demand for {cat}.",
                        })

    declining_items = sorted(declining_items, key=lambda x: x["decline_percentage"], reverse=True)

    # 3. Check Inventory Below Reorder Level (if inventory columns exist)
    stock_col = next((c for c in numeric_cols if any(k in str(c).lower() for k in ["current_stock", "stock_available", "stock", "on_hand", "inventory"])), None)
    reorder_col = next((c for c in numeric_cols if any(k in str(c).lower() for k in ["reorder_level", "min_stock", "safety_stock"])), None)

    low_stock_items = []
    if stock_col and reorder_col and primary_cat:
        for _, row in df.iterrows():
            stk = pd.to_numeric(row.get(stock_col), errors="coerce")
            reord = pd.to_numeric(row.get(reorder_col), errors="coerce")
            if pd.notna(stk) and pd.notna(reord) and stk <= reord:
                p_name = str(row.get(primary_cat, "Item"))
                low_stock_items.append({
                    "product": p_name,
                    "stock": int(stk),
                    "reorder": int(reord),
                })
                alerts.append({
                    "id": f"alert_inv_{p_name.replace(' ', '_')}",
                    "type": "inventory_low",
                    "severity": "critical",
                    "title": f"Low Stock Alert: {p_name}",
                    "product": p_name,
                    "actual_value": f"{int(stk):,} units",
                    "comparison_value": f"{int(reord):,} units threshold",
                    "change_pct": round(((stk - reord) / reord) * 100, 1) if reord > 0 else 0,
                    "period": "Real-time Stock Count",
                    "explanation": f"Current stock ({int(stk):,}) is at or below the designated reorder level ({int(reord):,}).",
                    "recommended_action": f"Issue purchase or replenishment order immediately for {p_name} to prevent stockout.",
                })

    # 4. Check Defect Rate (if defect columns exist)
    defect_col = next((c for c in numeric_cols if any(k in str(c).lower() for k in ["defect", "defective_units", "scrap", "rejected"])), None)
    qty_col = next((c for c in numeric_cols if any(k in str(c).lower() for k in ["units_produced", "production", "quantity"])), None)
    if defect_col and qty_col:
        tot_d = float(pd.to_numeric(df[defect_col], errors="coerce").sum())
        tot_q = float(pd.to_numeric(df[qty_col], errors="coerce").sum())
        if tot_q > 0:
            d_rate = round((tot_d / tot_q * 100), 2)
            if d_rate > 2.5:
                alerts.append({
                    "id": "alert_defect_elevated",
                    "type": "defect_spike",
                    "severity": "critical" if d_rate > 5.0 else "warning",
                    "title": "Elevated Defect Rate",
                    "product": "Production Quality",
                    "actual_value": f"{d_rate}%",
                    "comparison_value": "2.0% benchmark",
                    "change_pct": round(((d_rate - 2.0) / 2.0) * 100, 1),
                    "period": "Cumulative Dataset",
                    "explanation": f"Defect rate is at {d_rate}% ({int(tot_d):,} defects across {int(tot_q):,} produced units), exceeding the 2.0% tolerance limit.",
                    "recommended_action": "Inspect calibration and assembly inspection stages to isolate scrap causes.",
                })

    # 5. Build Evidence-Based Root Cause Analysis (NO arbitrary percentages)
    if low_stock_items and declining_items:
        # Check if the same item is both low stock and declining
        overlapping = [d["product"] for d in declining_items if any(l["product"] == d["product"] for l in low_stock_items)]
        if overlapping:
            root_causes.append({
                "title": "Inventory Stockout Constraining Sales",
                "condition": f"Confirmed low inventory across {', '.join(overlapping[:3])}.",
                "finding": "Actual stock is below reorder thresholds, directly limiting order fulfillment velocity.",
                "action": "Expedite replenishment for low-stock SKUs.",
            })
        else:
            root_causes.append({
                "title": "Inventory Buffer Depletion",
                "condition": f"{len(low_stock_items)} items are below safety reorder levels.",
                "finding": "Stock depletion presents a high risk of fulfillment stockouts.",
                "action": "Issue warehouse replenishment purchase orders.",
            })

    if defect_col and qty_col:
        tot_d = float(pd.to_numeric(df[defect_col], errors="coerce").sum())
        tot_q = float(pd.to_numeric(df[qty_col], errors="coerce").sum())
        if tot_q > 0 and (tot_d / tot_q * 100) > 2.5:
            root_causes.append({
                "title": "Manufacturing Defect Rate Friction",
                "condition": f"Observed defect rate of {round(tot_d / tot_q * 100, 2)}% exceeds target threshold of 2.0%.",
                "finding": "Scrap and rework volume is reducing net salable production yield.",
                "action": "Implement quality gates and recalibrate fabrication equipment.",
            })

    if declining_items and not root_causes:
        top_dec = declining_items[0]
        root_causes.append({
            "title": f"Performance Decline in {top_dec['product']}",
            "condition": f"{top_dec['product']} decreased by {top_dec['decline_percentage']}% period-over-period.",
            "finding": "Possible cause cannot be determined from the available data. Further channel telemetry, customer feedback, and pricing logs are required.",
            "action": f"Review market demand, competitor pricing, and regional distribution for {top_dec['product']}.",
        })

    if not root_causes:
        if alerts:
            root_causes.append({
                "title": "Operational Condition Summary",
                "condition": f"{len(alerts)} alert condition(s) detected across quality and metric performance.",
                "finding": "Metrics reflect active variance within operational parameters.",
                "action": "Execute the recommended action listed under each alert.",
            })
        else:
            root_causes.append({
                "title": "Stable Baseline Performance",
                "condition": "No abnormal drops, inventory stockouts, or quality violations detected.",
                "finding": "All evaluated metrics are operating within normal baseline boundaries.",
                "action": "Continue regular monitoring and periodic data refreshes.",
            })

    return {
        "status": "success",
        "alerts": alerts,
        "declining_products": declining_items,
        "root_causes": root_causes,
        "total_alerts": len(alerts),
    }
