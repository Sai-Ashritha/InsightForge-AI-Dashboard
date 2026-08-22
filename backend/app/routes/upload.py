import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.auth import get_current_user
from app.database.db import save_uploaded_dataframe
from app.services.data_cleaner import clean_dataframe
from app.services.data_quality import assess_data_quality, clean_dataset_with_stats

router = APIRouter()


def get_dataframe_from_upload(file_name: str, content: bytes) -> pd.DataFrame:
    lower_name = file_name.lower()
    if lower_name.endswith(".csv"):
        return pd.read_csv(pd.io.common.BytesIO(content))
    if lower_name.endswith((".xls", ".xlsx")):
        return pd.read_excel(pd.io.common.BytesIO(content))
    if lower_name.endswith(".json"):
        return pd.read_json(pd.io.common.BytesIO(content))
    raise ValueError("Unsupported file type. Use CSV, Excel, or JSON.")


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
):
    file_name = file.filename
    if not file_name:
        raise HTTPException(status_code=400, detail="No file selected")

    content = await file.read()
    try:
        raw_df = get_dataframe_from_upload(file_name, content)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid file format: {str(exc)}")

    if raw_df.empty:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Step 3: Raw Dataset Analysis
    initial_rows = int(len(raw_df))
    initial_columns = int(len(raw_df.columns))
    column_names = [str(c) for c in raw_df.columns]
    data_types = {str(k): str(v) for k, v in raw_df.dtypes.items()}
    raw_missing_values = int(raw_df.isnull().sum().sum())
    raw_duplicate_rows = int(raw_df.duplicated().sum())

    # Basic statistics for numeric columns
    numeric_df = raw_df.select_dtypes(include=[np.number])
    basic_stats = {}
    for col in numeric_df.columns:
        s = numeric_df[col].dropna()
        if not s.empty:
            basic_stats[str(col)] = {
                "mean": round(float(s.mean()), 2),
                "median": round(float(s.median()), 2),
                "min": round(float(s.min()), 2),
                "max": round(float(s.max()), 2),
                "std": round(float(s.std()), 2) if len(s) > 1 else 0.0,
            }

    # Step 4: Assess Data Quality
    quality = assess_data_quality(raw_df)

    # Step 5: Automatically Clean Dataset
    clean_df, cleaning_stats = clean_dataset_with_stats(raw_df)

    # Save to PostgreSQL DB
    try:
        db_result = save_uploaded_dataframe(clean_df)
    except Exception as exc:
        db_result = {"table": "sales", "inserted_rows": len(clean_df), "error": str(exc)}

    return {
        "status": "success",
        "file_name": file_name,
        "raw_analysis": {
            "rows": initial_rows,
            "columns": initial_columns,
            "column_names": column_names,
            "data_types": data_types,
            "missing_values": raw_missing_values,
            "duplicate_records": raw_duplicate_rows,
            "basic_stats": basic_stats,
            "outlier_ratio": quality["outlier_ratio"],
        },
        "data_quality": {
            "quality_score": quality["quality_score"],
            "null_percentage": quality["null_percentage"],
            "duplicate_percentage": quality["duplicate_percentage"],
            "outlier_percentage": quality["outlier_percentage"],
            "formula": "100 - (Null Ratio × 40 + Duplicate Ratio × 30 + Outlier Ratio × 30)",
        },
        "cleaning_summary": {
            "duplicates_removed": cleaning_stats["duplicates_removed"],
            "missing_values_handled": cleaning_stats["missing_numeric_filled"] + cleaning_stats["missing_categorical_filled"],
            "missing_numeric_filled": cleaning_stats["missing_numeric_filled"],
            "missing_categorical_filled": cleaning_stats["missing_categorical_filled"],
            "cleaned_rows": int(len(clean_df)),
            "message": "Dataset prepared for analysis",
        },
        # Backwards compatibility fields
        "rows": int(len(clean_df)),
        "columns": int(len(clean_df.columns)),
        "missing_values": raw_missing_values,
        "duplicate_rows": cleaning_stats["duplicates_removed"],
        "quality_score": quality["quality_score"],
        "db_table": db_result.get("table"),
        "db_inserted_rows": db_result.get("inserted_rows"),
        "cleaned_preview": clean_df.head(5).to_dict(orient="records"),
    }

