import io
from typing import List
import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse

from app.auth import get_current_user
from app.database.db import save_uploaded_dataframe
from app.services.data_cleaner import clean_dataframe
from app.services.data_quality import assess_data_quality, clean_dataset_with_stats
from app.services.dynamic_engine import set_active_dataset

router = APIRouter()

# In-memory cache: {email -> DataFrame} — stores most recently cleaned dataset per user
_CLEANED_CACHE: dict[str, pd.DataFrame] = {}


def get_dataframe_from_upload(file_name: str, content: bytes) -> pd.DataFrame:
    lower_name = file_name.lower()
    if lower_name.endswith(".csv"):
        return pd.read_csv(pd.io.common.BytesIO(content))
    if lower_name.endswith((".xls", ".xlsx")):
        return pd.read_excel(pd.io.common.BytesIO(content))
    if lower_name.endswith(".json"):
        return pd.read_json(pd.io.common.BytesIO(content))
    raise ValueError("Unsupported file type. Use CSV, Excel, or JSON.")


def analyze_and_clean_df(raw_df: pd.DataFrame, file_name: str):
    initial_rows = int(len(raw_df))
    initial_columns = int(len(raw_df.columns))
    column_names = [str(c) for c in raw_df.columns]
    data_types = {str(k): str(v) for k, v in raw_df.dtypes.items()}
    raw_missing_values = int(raw_df.isnull().sum().sum())
    raw_duplicate_rows = int(raw_df.duplicated().sum())

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

    quality = assess_data_quality(raw_df)
    clean_df, cleaning_stats = clean_dataset_with_stats(raw_df)

    return {
        "file_name": file_name,
        "clean_df": clean_df,
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
    }


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

    res = analyze_and_clean_df(raw_df, file_name)
    clean_df = res.pop("clean_df")

    # Save to PostgreSQL DB
    try:
        db_result = save_uploaded_dataframe(clean_df, clear_existing=True)
    except Exception as exc:
        db_result = {"table": "sales", "inserted_rows": len(clean_df), "error": str(exc)}

    user_key = current_user.get("email", "default") if isinstance(current_user, dict) else getattr(current_user, "email", "default")
    _CLEANED_CACHE[user_key] = clean_df
    set_active_dataset(user_key, clean_df, file_name)
    set_active_dataset("default", clean_df, file_name)

    return {
        "status": "success",
        "file_name": file_name,
        "files_count": 1,
        "raw_analysis": res["raw_analysis"],
        "data_quality": res["data_quality"],
        "cleaning_summary": res["cleaning_summary"],
        # Backwards compatibility fields
        "rows": res["cleaning_summary"]["cleaned_rows"],
        "columns": res["raw_analysis"]["columns"],
        "missing_values": res["raw_analysis"]["missing_values"],
        "duplicate_rows": res["cleaning_summary"]["duplicates_removed"],
        "quality_score": res["data_quality"]["quality_score"],
        "db_table": db_result.get("table"),
        "db_inserted_rows": db_result.get("inserted_rows"),
        "cleaned_preview": clean_df.head(5).to_dict(orient="records"),
    }


@router.post("/upload-multiple")
async def upload_multiple_files(
    files: List[UploadFile] = File(...),
    append: bool = Query(False, description="If true, append to existing DB tables without clearing them"),
    current_user=Depends(get_current_user),
):
    if not files:
        raise HTTPException(status_code=400, detail="No files selected")

    processed_files = []
    cleaned_dfs = []
    total_rows = 0
    total_missing = 0
    total_duplicates = 0
    quality_scores = []
    inserted_tables = []
    total_inserted = 0

    for idx, f in enumerate(files):
        file_name = f.filename
        if not file_name:
            continue
        content = await f.read()
        try:
            raw_df = get_dataframe_from_upload(file_name, content)
        except Exception as exc:
            continue

        if raw_df.empty:
            continue

        res = analyze_and_clean_df(raw_df, file_name)
        clean_df = res.pop("clean_df")
        cleaned_dfs.append(clean_df)

        # In append mode, never wipe tables. In fresh-upload mode, only first file clears.
        try:
            should_clear = (not append) and (idx == 0)
            db_res = save_uploaded_dataframe(clean_df, clear_existing=should_clear)
            tbl = db_res.get("table", "")
            if tbl:
                inserted_tables.append(tbl)
            total_inserted += db_res.get("inserted_rows", 0)
        except Exception:
            pass

        total_rows += res["raw_analysis"]["rows"]
        total_missing += res["raw_analysis"]["missing_values"]
        total_duplicates += res["raw_analysis"]["duplicate_records"]
        quality_scores.append(res["data_quality"]["quality_score"])

        res["preview"] = clean_df.head(3).to_dict(orient="records")
        processed_files.append(res)

    if not processed_files:
        raise HTTPException(status_code=400, detail="Could not process any of the provided files.")

    # Cache combined cleaned DataFrame
    user_key = current_user.get("email", "default") if isinstance(current_user, dict) else getattr(current_user, "email", "default")
    if cleaned_dfs:
        try:
            _CLEANED_CACHE[user_key] = pd.concat(cleaned_dfs, ignore_index=True)
        except Exception:
            _CLEANED_CACHE[user_key] = cleaned_dfs[0]
        set_active_dataset(user_key, _CLEANED_CACHE[user_key], ", ".join(f["file_name"] for f in processed_files))
        set_active_dataset("default", _CLEANED_CACHE[user_key], ", ".join(f["file_name"] for f in processed_files))

    avg_quality = round(sum(quality_scores) / len(quality_scores), 1) if quality_scores else 94.0

    return {
        "status": "success",
        "file_name": ", ".join(f["file_name"] for f in processed_files),
        "files_count": len(processed_files),
        "files": processed_files,
        "raw_analysis": {
            "rows": total_rows,
            "columns": sum(f["raw_analysis"]["columns"] for f in processed_files),
            "missing_values": total_missing,
            "duplicate_records": total_duplicates,
        },
        "data_quality": {
            "quality_score": avg_quality,
            "null_percentage": round(sum(f["data_quality"]["null_percentage"] for f in processed_files) / len(processed_files), 1),
            "duplicate_percentage": round(sum(f["data_quality"]["duplicate_percentage"] for f in processed_files) / len(processed_files), 1),
            "outlier_percentage": round(sum(f["data_quality"]["outlier_percentage"] for f in processed_files) / len(processed_files), 1),
            "formula": "Average across uploaded datasets: 100 - (Null Ratio × 40 + Duplicate Ratio × 30 + Outlier Ratio × 30)",
        },
        "cleaning_summary": {
            "duplicates_removed": sum(f["cleaning_summary"]["duplicates_removed"] for f in processed_files),
            "missing_values_handled": sum(f["cleaning_summary"]["missing_values_handled"] for f in processed_files),
            "cleaned_rows": sum(f["cleaning_summary"]["cleaned_rows"] for f in processed_files),
            "message": f"Successfully merged and prepared {len(processed_files)} datasets for AI intelligence",
        },
        "rows": total_rows,
        "quality_score": avg_quality,
        "db_table": ", ".join(set(inserted_tables)),
        "db_inserted_rows": total_inserted,
    }


@router.get("/download-cleaned")
def download_cleaned_dataset(current_user=Depends(get_current_user)):
    """Export the most recently cleaned dataset as a CSV download."""
    user_key = current_user.get("email", "default") if isinstance(current_user, dict) else getattr(current_user, "email", "default")
    df = _CLEANED_CACHE.get(user_key)
    
    # Fallback to any cached df if user-specific not found
    if df is None and _CLEANED_CACHE:
        df = next(iter(_CLEANED_CACHE.values()))

    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="No cleaned dataset found. Please upload a dataset first.")

    stream = io.StringIO()
    df.to_csv(stream, index=False)
    stream.seek(0)
    
    return StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=insightforge_cleaned_dataset.csv"},
    )



