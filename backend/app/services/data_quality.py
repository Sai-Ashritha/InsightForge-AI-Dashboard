import numpy as np
import pandas as pd


def clamp_percentage(value) -> float:
    """Keep all percentages in a safe output range for UI and analytics."""
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return 0.0

    if pd.isna(numeric_value) or np.isinf(numeric_value):
        return 0.0
    return max(0.0, min(100.0, numeric_value))


def infer_column_types(df: pd.DataFrame) -> dict:
    """Detect columns as dates, numerics, or categories without assuming a specific business domain."""
    if df is None or df.empty:
        return {"date_cols": [], "numeric_cols": [], "categorical_cols": [], "summary_stats": {}}

    date_cols = []
    numeric_cols = []
    categorical_cols = []
    summary_stats = {}

    for column in df.columns:
        series = df[column]
        col_name = str(column).lower()

        is_datetime_like = pd.api.types.is_datetime64_any_dtype(series)
        if not is_datetime_like and any(token in col_name for token in ["date", "time", "day", "month", "year", "timestamp", "created", "updated", "period"]):
            parsed = pd.to_datetime(series.dropna().head(50), errors="coerce")
            is_datetime_like = parsed.notna().sum() >= max(1, int(len(parsed) * 0.7))

        if is_datetime_like:
            date_cols.append(column)
            continue

        if pd.api.types.is_numeric_dtype(series):
            numeric_cols.append(column)
            series_no_na = pd.to_numeric(series, errors="coerce").dropna()
            if not series_no_na.empty:
                summary_stats[str(column)] = {
                    "mean": round(float(series_no_na.mean()), 2),
                    "median": round(float(series_no_na.median()), 2),
                    "min": round(float(series_no_na.min()), 2),
                    "max": round(float(series_no_na.max()), 2),
                }
            continue

        categorical_cols.append(column)

    return {
        "date_cols": list(date_cols),
        "numeric_cols": list(numeric_cols),
        "categorical_cols": list(categorical_cols),
        "summary_stats": summary_stats,
    }


def _outlier_ratio(df: pd.DataFrame) -> float:
    numeric = df.select_dtypes(include=[np.number])
    if numeric.empty or len(numeric) < 4:
        return 0.0

    outlier_rows = pd.Series(False, index=df.index)
    for column in numeric.columns:
        values = pd.to_numeric(numeric[column], errors="coerce").dropna()
        if values.empty:
            continue
        first_quartile = values.quantile(0.25)
        third_quartile = values.quantile(0.75)
        spread = third_quartile - first_quartile
        if pd.isna(spread) or spread == 0:
            continue
        lower_bound = first_quartile - 1.5 * spread
        upper_bound = third_quartile + 1.5 * spread
        outlier_rows |= (numeric[column] < lower_bound) | (numeric[column] > upper_bound)
    return float(outlier_rows.mean()) if len(df) else 0.0


def assess_data_quality(df: pd.DataFrame) -> dict:
    if df is None or df.empty:
        return {
            "quality_score": 0.0,
            "null_ratio": 0.0,
            "null_percentage": 0.0,
            "duplicate_ratio": 0.0,
            "duplicate_percentage": 0.0,
            "outlier_ratio": 0.0,
            "outlier_percentage": 0.0,
            "row_count": 0,
            "column_count": 0,
        }

    null_ratio = float(df.isna().mean().mean())
    duplicate_ratio = float(df.duplicated().mean())
    outlier_ratio = _outlier_ratio(df)
    quality_score = max(0.0, 100.0 - (
        null_ratio * 40.0 + duplicate_ratio * 30.0 + outlier_ratio * 30.0
    ))
    return {
        "quality_score": round(clamp_percentage(quality_score), 1),
        "null_ratio": round(float(np.clip(null_ratio, 0, 1)), 4),
        "null_percentage": round(clamp_percentage(null_ratio * 100), 1),
        "duplicate_ratio": round(float(np.clip(duplicate_ratio, 0, 1)), 4),
        "duplicate_percentage": round(clamp_percentage(duplicate_ratio * 100), 1),
        "outlier_ratio": round(float(np.clip(outlier_ratio, 0, 1)), 4),
        "outlier_percentage": round(clamp_percentage(outlier_ratio * 100), 1),
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
    }


def _safe_numeric_fill(column: pd.Series) -> pd.Series:
    values = pd.to_numeric(column, errors="coerce")
    if values.dropna().empty:
        return pd.Series(0, index=column.index)

    median_value = values.median()
    values = values.fillna(median_value if pd.notna(median_value) else 0.0)
    values = values.replace([np.inf, -np.inf], np.nan)
    if values.notna().any():
        q1 = values.quantile(0.25)
        q3 = values.quantile(0.75)
        iqr = q3 - q1
        if pd.notna(iqr) and iqr != 0:
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            values = values.mask((values < lower_bound) | (values > upper_bound), median_value)
    return values


def clean_dataset_with_stats(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    if df is None or df.empty:
        return pd.DataFrame(), {
            "duplicates_removed": 0,
            "missing_numeric_filled": 0,
            "missing_categorical_filled": 0,
            "total_cleaned_values": 0,
        }

    initial_len = len(df)
    cleaned = df.copy()
    cleaned = cleaned.replace([np.inf, -np.inf], np.nan)
    cleaned.columns = [str(column).strip().lower().replace(" ", "_") for column in cleaned.columns]
    cleaned = cleaned.drop_duplicates().reset_index(drop=True)
    duplicates_removed = initial_len - len(cleaned)

    numeric_columns = cleaned.select_dtypes(include=[np.number]).columns
    missing_numeric_filled = 0
    missing_categorical_filled = 0
    for column in numeric_columns:
        missing_count = int(cleaned[column].isna().sum())
        if missing_count > 0:
            cleaned[column] = _safe_numeric_fill(cleaned[column])
            missing_numeric_filled += missing_count

    for column in cleaned.columns:
        if column in numeric_columns:
            continue
        missing_count = int(cleaned[column].isna().sum())
        if missing_count > 0:
            mode_value = cleaned[column].mode(dropna=True)
            fill_value = mode_value.iloc[0] if not mode_value.empty else "Unknown"
            cleaned[column] = cleaned[column].fillna(fill_value).astype(str).str.strip().replace("", "Unknown")
            missing_categorical_filled += missing_count

    stats = {
        "duplicates_removed": duplicates_removed,
        "missing_numeric_filled": missing_numeric_filled,
        "missing_categorical_filled": missing_categorical_filled,
        "total_cleaned_values": duplicates_removed + missing_numeric_filled + missing_categorical_filled,
    }
    return cleaned, stats


def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    cleaned, _ = clean_dataset_with_stats(df)
    return cleaned
