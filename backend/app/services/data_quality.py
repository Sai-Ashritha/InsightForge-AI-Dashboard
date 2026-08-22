import numpy as np
import pandas as pd


def _outlier_ratio(df: pd.DataFrame) -> float:
    numeric = df.select_dtypes(include=[np.number])
    if numeric.empty or len(numeric) < 4:
        return 0.0

    outlier_rows = pd.Series(False, index=df.index)
    for column in numeric.columns:
        values = numeric[column].dropna()
        if values.empty:
            continue
        first_quartile = values.quantile(0.25)
        third_quartile = values.quantile(0.75)
        spread = third_quartile - first_quartile
        if spread == 0:
            continue
        outlier_rows |= (numeric[column] < first_quartile - 1.5 * spread) | (
            numeric[column] > third_quartile + 1.5 * spread
        )
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
        "quality_score": round(quality_score, 1),
        "null_ratio": round(null_ratio, 4),
        "null_percentage": round(null_ratio * 100, 1),
        "duplicate_ratio": round(duplicate_ratio, 4),
        "duplicate_percentage": round(duplicate_ratio * 100, 1),
        "outlier_ratio": round(outlier_ratio, 4),
        "outlier_percentage": round(outlier_ratio * 100, 1),
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
    }


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
    cleaned.columns = [str(column).strip().lower().replace(" ", "_") for column in cleaned.columns]
    
    cleaned = cleaned.drop_duplicates().reset_index(drop=True)
    duplicates_removed = initial_len - len(cleaned)

    numeric_columns = cleaned.select_dtypes(include=[np.number]).columns
    missing_numeric_filled = 0
    for column in numeric_columns:
        num_missing = int(cleaned[column].isna().sum())
        if num_missing > 0:
            median_val = cleaned[column].median()
            cleaned[column] = cleaned[column].fillna(median_val if not pd.isna(median_val) else 0)
            missing_numeric_filled += num_missing

    non_numeric_columns = cleaned.columns.difference(numeric_columns)
    missing_categorical_filled = 0
    for column in non_numeric_columns:
        cat_missing = int(cleaned[column].isna().sum())
        if cat_missing > 0:
            mode = cleaned[column].mode(dropna=True)
            mode_val = mode.iloc[0] if not mode.empty else "Unknown"
            cleaned[column] = cleaned[column].fillna(mode_val)
            missing_categorical_filled += cat_missing

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