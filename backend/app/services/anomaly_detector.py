import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


def _generate_anomaly_description(row_dict: dict, col_stats: dict) -> tuple[str, str, str, str]:
    """Generate human-readable anomaly title, description, anomaly type, and metric."""
    date_str = str(row_dict.get("date", ""))[:10]
    date_suffix = f" on {date_str}" if date_str and date_str != "nan" and date_str != "None" else ""
    product_str = str(row_dict.get("product", ""))
    prod_prefix = f"{product_str}: " if product_str and product_str != "nan" else ""

    # Check revenue
    if "revenue" in row_dict and "revenue" in col_stats:
        rev = float(row_dict["revenue"]) if row_dict["revenue"] is not None else 0
        mean = col_stats["revenue"]["mean"]
        std = col_stats["revenue"]["std"] or 1
        if rev > mean + 1.8 * std:
            return (
                f"{prod_prefix}Unexpected Sales Spike",
                f"Revenue spiked to ₹{int(rev):,}{date_suffix}, exceeding the average by {int(((rev - mean) / mean) * 100)}%.",
                "spike",
                "revenue",
            )
        elif rev < mean - 1.2 * std and rev > 0:
            return (
                f"{prod_prefix}Sudden Sales Drop",
                f"Revenue dropped to ₹{int(rev):,}{date_suffix}, falling {abs(int(((rev - mean) / mean) * 100))}% below normal.",
                "drop",
                "revenue",
            )

    # Check units_produced / production
    prod_col = "units_produced" if "units_produced" in row_dict else "production" if "production" in row_dict else None
    if prod_col and prod_col in col_stats:
        units = float(row_dict[prod_col]) if row_dict[prod_col] is not None else 0
        mean = col_stats[prod_col]["mean"]
        if units < mean * 0.6:
            return (
                f"{prod_prefix}Abnormal Production Drop",
                f"Production dropped unexpectedly to {int(units):,} units{date_suffix}.",
                "drop",
                "production",
            )
        elif units > mean * 1.5:
            return (
                f"{prod_prefix}Unusual Production Surge",
                f"Production surged to {int(units):,} units{date_suffix}.",
                "spike",
                "production",
            )

    # Check inventory
    inv_col = "stock_available" if "stock_available" in row_dict else "inventory" if "inventory" in row_dict else None
    if inv_col and inv_col in col_stats:
        stock = float(row_dict[inv_col]) if row_dict[inv_col] is not None else 0
        mean = col_stats[inv_col]["mean"]
        if stock < mean * 0.4:
            return (
                f"{prod_prefix}Critical Stock Anomaly",
                f"Inventory level dropped to {int(stock):,} units{date_suffix}.",
                "drop",
                "inventory",
            )

    # Check quantity
    if "quantity" in row_dict and "quantity" in col_stats:
        qty = float(row_dict["quantity"]) if row_dict["quantity"] is not None else 0
        mean = col_stats["quantity"]["mean"]
        if qty > mean * 1.8:
            return (
                f"{prod_prefix}High Order Volume Anomaly",
                f"Order volume surged to {int(qty):,} units{date_suffix}.",
                "spike",
                "quantity",
            )

    return (
        f"{prod_prefix}Process Anomaly Detected",
        f"Unusual metric pattern detected in manufacturing record{date_suffix}.",
        "pattern",
        "general",
    )


def detect_anomalies(df: pd.DataFrame, contamination: float = 0.05) -> dict:
    """
    Detect anomalies in numeric columns using IsolationForest.
    Returns anomalies with structured descriptions and statistics.
    """
    if df is None or df.empty:
        return {"anomalies": [], "statistics": {}, "anomaly_count": 0}

    df_numeric = df.select_dtypes(include=[np.number])

    if df_numeric.empty:
        return {"anomalies": [], "statistics": {}, "anomaly_count": 0}

    col_stats = get_column_statistics(df)
    df_filled = df_numeric.fillna(df_numeric.mean())

    if len(df_filled) < 2:
        return {"anomalies": [], "statistics": {}, "anomaly_count": 0}

    scaler = StandardScaler()
    df_scaled = scaler.fit_transform(df_filled)

    iso_forest = IsolationForest(
        contamination=min(contamination, 0.5),
        random_state=42,
        n_estimators=100
    )
    predictions = iso_forest.fit_predict(df_scaled)
    scores = iso_forest.score_samples(df_scaled)

    anomaly_indices = np.where(predictions == -1)[0]
    anomalies = []

    for idx in anomaly_indices:
        row = df.iloc[idx]
        row_dict = row.to_dict()
        title, description, anomaly_type, metric = _generate_anomaly_description(row_dict, col_stats)
        score_val = round(float(scores[idx]), 4)
        severity = "critical" if score_val < -0.2 else "high" if score_val < -0.1 else "medium"

        anomalies.append({
            "index": int(idx),
            "date": str(row_dict.get("date", ""))[:10] if "date" in row_dict else None,
            "product": str(row_dict.get("product", "")) if "product" in row_dict else None,
            "title": title,
            "description": description,
            "type": anomaly_type,
            "metric": metric,
            "severity": severity,
            "row": {k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in row_dict.items()},
            "anomaly_score": score_val,
        })

    anomalies_sorted = sorted(anomalies, key=lambda x: x["anomaly_score"])

    statistics = {
        "total_rows": len(df),
        "anomaly_count": len(anomalies),
        "anomaly_percentage": round((len(anomalies) / len(df)) * 100, 1),
        "average_score": round(float(np.mean(scores)), 4),
        "min_score": round(float(np.min(scores)), 4),
        "max_score": round(float(np.max(scores)), 4),
    }

    return {
        "anomalies": anomalies_sorted,
        "statistics": statistics,
        "anomaly_count": len(anomalies)
    }


def get_column_statistics(df: pd.DataFrame) -> dict:
    """Compute statistics for numeric columns."""
    if df is None or df.empty:
        return {}

    df_numeric = df.select_dtypes(include=[np.number])
    stats = {}

    for col in df_numeric.columns:
        col_data = df_numeric[col].dropna()
        if len(col_data) > 0:
            stats[col] = {
                "mean": round(float(col_data.mean()), 2),
                "median": round(float(col_data.median()), 2),
                "std": round(float(col_data.std()), 2),
                "min": round(float(col_data.min()), 2),
                "max": round(float(col_data.max()), 2),
                "q25": round(float(col_data.quantile(0.25)), 2),
                "q75": round(float(col_data.quantile(0.75)), 2),
            }

    return stats

