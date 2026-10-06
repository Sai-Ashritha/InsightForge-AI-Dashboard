import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional

# Active cached dataset: user_key -> DataFrame
_ACTIVE_DATASETS: Dict[str, pd.DataFrame] = {}
_ACTIVE_METADATA: Dict[str, Dict[str, Any]] = {}


def set_active_dataset(user_key: str, df: pd.DataFrame, file_name: str = "dataset"):
    """Store the most recently processed dataset in memory for live dynamic analytics."""
    if df is not None and not df.empty:
        stored_df = df.copy()
        stored_df.attrs["file_name"] = file_name
        _ACTIVE_DATASETS[user_key] = stored_df
        _ACTIVE_METADATA[user_key] = {
            "file_name": file_name,
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns),
        }


def get_active_dataset(user_key: str = "default") -> Optional[pd.DataFrame]:
    """Retrieve the active dataset for the user, falling back to any available or DB."""
    if user_key in _ACTIVE_DATASETS:
        return _ACTIVE_DATASETS[user_key]
    if _ACTIVE_DATASETS:
        return next(iter(_ACTIVE_DATASETS.values()))
    
    # Fallback: query database tables
    try:
        from app.database.db import fetch_table
        sales = fetch_table("sales")
        if sales:
            df = pd.DataFrame(sales)
            if not df.empty:
                return df
        prod = fetch_table("production")
        if prod:
            df = pd.DataFrame(prod)
            if not df.empty:
                return df
        inv = fetch_table("inventory")
        if inv:
            df = pd.DataFrame(inv)
            if not df.empty:
                return df
    except Exception:
        pass
    return None


def inspect_dataset_schema(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyze columns to detect temporal, numeric measures, and categorical dimensions."""
    if df is None or df.empty:
        return {
            "date_cols": [],
            "numeric_cols": [],
            "categorical_cols": [],
            "summary_stats": {},
            "domain": "Generic",
        }

    date_cols = []
    numeric_cols = []
    categorical_cols = []

    for col in df.columns:
        col_str = str(col).lower()
        col_series = df[col]

        # 1. Check if datetime
        is_date = False
        if pd.api.types.is_datetime64_any_dtype(col_series):
            is_date = True
        elif not pd.api.types.is_numeric_dtype(col_series) and any(k in col_str for k in ["date", "time", "day", "month", "year", "timestamp"]):
            try:
                parsed = pd.to_datetime(col_series.dropna().head(20), errors="coerce")
                if parsed.notna().sum() > len(parsed) * 0.7:
                    is_date = True
            except Exception:
                pass

        if is_date:
            date_cols.append(col)
            continue

        # 2. Check if numeric
        if pd.api.types.is_numeric_dtype(col_series):
            # Exclude id columns if purely sequential integers with unique = total
            if any(k in col_str for k in ["id", "index", "code", "pk"]) and col_series.nunique() == len(df):
                pass
            else:
                numeric_cols.append(col)
                continue

        # 3. Categorical / Dimension
        if col_series.dtype == "object" or pd.api.types.is_string_dtype(col_series) or pd.api.types.is_categorical_dtype(col_series):
            categorical_cols.append(col)

    # Infer business domain
    col_names_lower = [str(c).lower() for c in df.columns]
    domain = "General Business"
    if any(k in col_names_lower for k in ["sales", "revenue", "quantity", "unit_price", "order", "price"]):
        domain = "Sales & Revenue"
    elif any(k in col_names_lower for k in ["production", "units_produced", "defects", "defective_units", "machine_hours", "downtime"]):
        domain = "Manufacturing & Production"
    elif any(k in col_names_lower for k in ["current_stock", "stock_available", "reorder_level", "inventory", "warehouse"]):
        domain = "Inventory & Logistics"
    elif any(k in col_names_lower for k in ["admissions", "discharges", "patient", "doctor", "hospital"]):
        domain = "Healthcare & Admissions"
    elif any(k in col_names_lower for k in ["salary", "employee", "hours_worked", "productivity", "headcount"]):
        domain = "Human Resources & Workforce"

    return {
        "date_cols": date_cols,
        "numeric_cols": numeric_cols,
        "categorical_cols": categorical_cols,
        "domain": domain,
    }


def _is_rate_column(column: Any) -> bool:
    name = str(column).lower()
    return any(token in name for token in ["percent", "percentage", "_pct", "rate", "ratio", "margin"])


def _aggregate_metric(series: pd.Series, column: Any) -> float:
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.empty:
        return 0.0
    return float(values.mean() if _is_rate_column(column) else values.sum())


def compute_dynamic_analytics(
    df: pd.DataFrame,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category_col: Optional[str] = None,
    category_val: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate KPIs, dynamic chart specifications, filter options, and data preview
    strictly computed from the actual uploaded dataset.
    """
    if df is None or df.empty:
        return {
            "status": "empty",
            "domain": "No Data",
            "kpis": [],
            "charts": [],
            "available_filters": {},
            "total_records": 0,
            "filtered_records": 0,
            "preview": [],
        }

    schema = inspect_dataset_schema(df)
    date_cols = schema["date_cols"]
    numeric_cols = schema["numeric_cols"]
    categorical_cols = schema["categorical_cols"]
    domain = schema["domain"]

    # Work on a copy for filtering
    working_df = df.copy()

    # Apply date filtering if applicable
    primary_date_col = date_cols[0] if date_cols else None
    if primary_date_col and primary_date_col in working_df.columns:
        working_df[primary_date_col] = pd.to_datetime(working_df[primary_date_col], errors="coerce")
        if start_date:
            try:
                s_dt = pd.to_datetime(start_date)
                working_df = working_df[working_df[primary_date_col] >= s_dt]
            except Exception:
                pass
        if end_date:
            try:
                e_dt = pd.to_datetime(end_date)
                working_df = working_df[working_df[primary_date_col] <= e_dt]
            except Exception:
                pass

    # Apply category filtering if applicable
    if category_col and category_col in working_df.columns and category_val:
        working_df = working_df[working_df[category_col].astype(str) == str(category_val)]

    total_records = len(df)
    filtered_records = len(working_df)

    # 1. Build Available Filter Options
    available_filters = {
        "date_column": primary_date_col,
        "date_min": None,
        "date_max": None,
        "categories": {},
    }

    if primary_date_col and not df[primary_date_col].isna().all():
        d_series = pd.to_datetime(df[primary_date_col], errors="coerce").dropna()
        if not d_series.empty:
            available_filters["date_min"] = d_series.min().strftime("%Y-%m-%d")
            available_filters["date_max"] = d_series.max().strftime("%Y-%m-%d")

    for cat_col in categorical_cols[:3]:
        uniques = [str(x) for x in df[cat_col].dropna().unique() if str(x).strip()]
        if 0 < len(uniques) <= 60:
            available_filters["categories"][cat_col] = uniques[:30]

    # 2. Dynamic KPIs: only calculate what is supported by actual columns
    kpis = []

    # KPI: Total Records
    kpis.append({
        "key": "total_records",
        "title": "Total Records",
        "value": f"{filtered_records:,}",
        "raw_value": filtered_records,
        "unit": "records",
        "color": "indigo",
        "subtext": f"{filtered_records} of {total_records} records",
    })

    # Find primary monetary or high-value measure (e.g. Sales, Revenue)
    sales_col = next((c for c in numeric_cols if not _is_rate_column(c) and any(k in str(c).lower() for k in ["sales", "revenue", "turnover", "income", "price_total"])), None)
    if sales_col and sales_col in working_df.columns:
        tot_sales = float(pd.to_numeric(working_df[sales_col], errors="coerce").sum())
        formatted_sales = f"₹{tot_sales / 100000:.2f}L" if tot_sales >= 100000 else f"₹{tot_sales:,.2f}"
        kpis.append({
            "key": "total_sales",
            "title": f"Total {sales_col.replace('_', ' ').title()}",
            "value": formatted_sales,
            "raw_value": tot_sales,
            "unit": "₹",
            "color": "emerald",
            "subtext": "Sum of actual values",
        })

    # Quantity / Volume / Output / Produced measure
    qty_col = next((c for c in numeric_cols if not _is_rate_column(c) and any(k in str(c).lower() for k in ["quantity", "units_sold", "units_produced", "production", "admissions", "output", "qty"])), None)
    if qty_col and qty_col in working_df.columns:
        tot_qty = float(pd.to_numeric(working_df[qty_col], errors="coerce").sum())
        unit_label = "units"
        if "admission" in str(qty_col).lower():
            unit_label = "patients"
        elif "hour" in str(qty_col).lower():
            unit_label = "hours"
        kpis.append({
            "key": "total_quantity",
            "title": f"Total {qty_col.replace('_', ' ').title()}",
            "value": f"{int(tot_qty):,}",
            "raw_value": tot_qty,
            "unit": unit_label,
            "color": "blue",
            "subtext": f"Total across {filtered_records} records",
        })

    # Stock / Inventory measure
    stock_col = next((c for c in numeric_cols if not _is_rate_column(c) and any(k in str(c).lower() for k in ["current_stock", "stock_available", "inventory", "stock", "on_hand"])), None)
    if stock_col and stock_col in working_df.columns:
        tot_stock = float(pd.to_numeric(working_df[stock_col], errors="coerce").sum())
        kpis.append({
            "key": "current_inventory",
            "title": f"Total {stock_col.replace('_', ' ').title()}",
            "value": f"{int(tot_stock):,}",
            "raw_value": tot_stock,
            "unit": "units",
            "color": "amber",
            "subtext": "Current stock count",
        })

    # Count measures are distinct from rates and financial costs.
    defect_col = next((c for c in numeric_cols if not _is_rate_column(c) and any(k in str(c).lower() for k in ["defect", "scrap", "rejected"]) and not any(k in str(c).lower() for k in ["cost", "expense"])), None)
    if defect_col and defect_col in working_df.columns:
        paired = working_df[[defect_col, qty_col]].apply(pd.to_numeric, errors="coerce").dropna() if qty_col else pd.DataFrame()
        tot_def = float(paired[defect_col].sum()) if not paired.empty else float(pd.to_numeric(working_df[defect_col], errors="coerce").sum())
        if qty_col and qty_col in working_df.columns:
            tot_q = float(paired[qty_col].sum()) if not paired.empty else 0.0
            rate = round((tot_def / tot_q * 100), 2) if tot_q > 0 else 0.0
            if tot_q > 0 and rate <= 100:
                kpis.append({
                    "key": "defect_rate",
                    "title": "Defect Rate",
                    "value": f"{rate}%",
                    "raw_value": rate,
                    "unit": "%",
                    "color": "rose",
                    "subtext": f"{int(tot_def):,} flagged of {int(tot_q):,} records",
                })
            else:
                kpis.append({
                    "key": f"total_{defect_col}",
                    "title": f"Total {defect_col.replace('_', ' ').title()}",
                    "value": f"{int(tot_def):,}",
                    "raw_value": tot_def,
                    "unit": "records",
                    "color": "rose",
                    "subtext": "Sum of available count values",
                })
        else:
            kpis.append({
                "key": "total_defects",
                "title": f"Total {defect_col.replace('_', ' ').title()}",
                "value": f"{int(tot_def):,}",
                "raw_value": tot_def,
                "unit": "units",
                "color": "rose",
                "subtext": "Total recorded volume",
            })

    # Primary Categorical Count (e.g. Products or Departments)
    primary_cat_col = categorical_cols[0] if categorical_cols else None
    if primary_cat_col and primary_cat_col in working_df.columns:
        cat_count = working_df[primary_cat_col].dropna().nunique()
        kpis.append({
            "key": "unique_categories",
            "title": f"Active {primary_cat_col.replace('_', ' ').title()}s",
            "value": f"{cat_count}",
            "raw_value": cat_count,
            "unit": "items",
            "color": "cyan",
            "subtext": f"Distinct {primary_cat_col} items",
        })

    # If few KPIs generated, add basic numerical summary of first numeric column
    if len(kpis) < 4 and numeric_cols:
        col_to_use = [c for c in numeric_cols if c not in [sales_col, qty_col, stock_col, defect_col]][:1]
        if col_to_use:
            c = col_to_use[0]
            val = float(pd.to_numeric(working_df[c], errors="coerce").mean())
            kpis.append({
                "key": f"avg_{c}",
                "title": f"Average {c.replace('_', ' ').title()}",
                "value": f"{val:,.1f}",
                "raw_value": val,
                "unit": "avg",
                "color": "teal",
                "subtext": "Mean value across records",
            })

    rate_col = next((c for c in numeric_cols if _is_rate_column(c)), None)
    if rate_col and rate_col in working_df.columns and not any(k in str(rate_col).lower() for k in ["defect", "scrap", "reject"]):
        rate_values = pd.to_numeric(working_df[rate_col], errors="coerce").dropna()
        if not rate_values.empty:
            average_rate = float(rate_values.mean())
            kpis.append({
                "key": f"average_{rate_col}",
                "title": f"Average {str(rate_col).replace('_', ' ').title()}",
                "value": f"{average_rate:.2f}%",
                "raw_value": average_rate,
                "unit": "%",
                "color": "teal",
                "subtext": f"Average of {len(rate_values):,} populated values",
            })

    # Build charts only when the category and measure coexist on actual rows.
    charts = []
    metric_candidates = [c for c in numeric_cols if pd.to_numeric(working_df[c], errors="coerce").nunique(dropna=True) > 1]
    plot_metric = next((c for c in [sales_col, qty_col, *metric_candidates] if c is not None and c in working_df.columns), None)

    if primary_date_col and plot_metric:
        dated = working_df[[primary_date_col, plot_metric]].copy()
        dated[primary_date_col] = pd.to_datetime(dated[primary_date_col], errors="coerce")
        dated[plot_metric] = pd.to_numeric(dated[plot_metric], errors="coerce")
        dated = dated.dropna().sort_values(primary_date_col)
        if len(dated) >= 3 and dated[primary_date_col].nunique() >= 3:
            date_freq = "W" if dated[primary_date_col].dt.date.nunique() > 30 else "D"
            grouped = dated.set_index(primary_date_col)[plot_metric].resample(date_freq).agg("mean" if _is_rate_column(plot_metric) else "sum").dropna()
            if len(grouped) >= 2 and grouped.nunique() > 1:
                charts.append({
                    "id": "chart_trend",
                    "title": f"{str(plot_metric).replace('_', ' ').title()} Over Time",
                    "chart_type": "line",
                    "x_label": str(primary_date_col).replace('_', ' ').title(),
                    "y_label": str(plot_metric).replace('_', ' ').title(),
                    "x": [str(value.date()) for value in grouped.index],
                    "y": [round(float(value), 2) for value in grouped.values],
                    "color": "#6366f1",
                })

    category_candidates = []
    for category in categorical_cols:
        for metric in metric_candidates:
            paired = working_df[[category, metric]].copy()
            paired[metric] = pd.to_numeric(paired[metric], errors="coerce")
            paired = paired.dropna()
            group_count = paired[category].nunique()
            if len(paired) < 3 or group_count < 2 or group_count > 30 or paired[metric].nunique() < 2:
                continue
            grouped = paired.groupby(category, dropna=True)[metric].agg("mean" if _is_rate_column(metric) else "sum")
            grouped = grouped.replace([np.inf, -np.inf], np.nan).dropna().sort_values(ascending=False).head(10)
            if len(grouped) < 2 or grouped.nunique() < 2 or not (grouped.abs() > 0).any():
                continue
            category_candidates.append((len(paired), 1 if 2 <= group_count <= 12 else 0, category, metric, grouped))

    category_candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
    used_pairs = set()
    for _, _, category, metric, grouped in category_candidates:
        pair = (category, metric)
        if pair in used_pairs:
            continue
        chart_id = "chart_category_bar" if not charts or not any(chart["id"].startswith("chart_category") for chart in charts) else f"chart_category_{len(used_pairs)}"
        charts.append({
            "id": chart_id,
            "title": f"{str(metric).replace('_', ' ').title()} by {str(category).replace('_', ' ').title()}",
            "chart_type": "bar",
            "x_label": str(category).replace('_', ' ').title(),
            "y_label": str(metric).replace('_', ' ').title(),
            "x": [str(value) for value in grouped.index],
            "y": [round(float(value), 2) for value in grouped.values],
            "color": "#10b981" if len(used_pairs) % 2 == 0 else "#f59e0b",
        })
        used_pairs.add(pair)
        if len(used_pairs) >= 3:
            break

    scatter_candidates = []
    for index, first_metric in enumerate(metric_candidates):
        for second_metric in metric_candidates[index + 1:]:
            paired = working_df[[first_metric, second_metric]].apply(pd.to_numeric, errors="coerce").dropna()
            if len(paired) >= 3 and paired[first_metric].nunique() > 1 and paired[second_metric].nunique() > 1:
                scatter_candidates.append((len(paired), first_metric, second_metric, paired.head(100)))
    if scatter_candidates:
        _, first_metric, second_metric, paired = max(scatter_candidates, key=lambda item: item[0])
        charts.append({
            "id": "chart_scatter",
            "title": f"{str(first_metric).replace('_', ' ').title()} vs {str(second_metric).replace('_', ' ').title()}",
            "chart_type": "scatter",
            "x_label": str(first_metric).replace('_', ' ').title(),
            "y_label": str(second_metric).replace('_', ' ').title(),
            "x": [round(float(value), 2) for value in paired[first_metric]],
            "y": [round(float(value), 2) for value in paired[second_metric]],
            "color": "#8b5cf6",
        })

    # Preview Table (First 50 rows, formatted)
    preview_df = working_df.head(50).fillna("").copy()
    for d_col in date_cols:
        if d_col in preview_df.columns:
            preview_df[d_col] = preview_df[d_col].astype(str).str[:10]

    preview_records = preview_df.to_dict(orient="records")

    return {
        "status": "success",
        "domain": domain,
        "kpis": kpis,
        "charts": charts,
        "available_filters": available_filters,
        "total_records": total_records,
        "filtered_records": filtered_records,
        "columns": [str(c) for c in df.columns],
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols,
        "date_columns": date_cols,
        "preview": preview_records,
    }
