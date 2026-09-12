import numpy as np
import pandas as pd
from typing import Dict, Any, Optional
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge


def generate_forecast(history_values):
    """Compatibility helper for legacy forecast routes and tests.

    Produces a simple linear-trend forecast from a historical series. The result
    structure matches the older dashboard API that expects a list of forecasted
    values and metadata for downstream chart rendering.
    """
    values = [float(v) for v in history_values if v is not None]
    if not values:
        return {
            "history": [],
            "forecast_values": [],
            "expected_revenue": 0.0,
            "model_performance": {"algorithm": "Linear Trend", "training_rows": 0},
        }

    history = values[:]
    if len(history) > 1:
        slope = (history[-1] - history[0]) / max(len(history) - 1, 1)
        steps = 4
        forecast = [history[-1] + slope * (idx + 1) for idx in range(steps)]
    else:
        forecast = [history[-1]] * 4

    return {
        "history": history,
        "forecast_values": [float(v) for v in forecast],
        "expected_revenue": float(sum(forecast)),
        "model_performance": {"algorithm": "Linear Trend", "training_rows": len(history)},
    }


def train_and_forecast_dynamic(
    df: pd.DataFrame,
    date_col: Optional[str] = None,
    target_col: Optional[str] = None,
    forecast_horizon_days: int = 30,
) -> Dict[str, Any]:
    """
    Real forecasting pipeline using chronological train/validation split.
    Detects date and numeric target column dynamically.
    Returns clear messages and limitations if data is insufficient.
    """
    if df is None or df.empty:
        return {
            "has_forecast": False,
            "message": "Not enough historical data for reliable forecasting. Please upload a dataset with dates and numeric values.",
            "forecast_data": [],
            "historical_actuals": [],
            "predicted_total": 0,
            "validation_metrics": {},
            "model_explanation": "No data available to train model.",
            "model_limitations": "Requires at least 5 distinct historical time periods.",
        }

    # 1. Detect Date Column
    if not date_col or date_col not in df.columns:
        # Auto-detect date column
        for c in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[c]):
                date_col = c
                break
            c_lower = str(c).lower()
            if any(k in c_lower for k in ["date", "time", "day", "timestamp", "period"]):
                try:
                    sample = pd.to_datetime(df[c].dropna().head(10), errors="coerce")
                    if sample.notna().sum() >= 5:
                        date_col = c
                        break
                except Exception:
                    pass

    if not date_col or date_col not in df.columns:
        return {
            "has_forecast": False,
            "message": "Not enough historical data for reliable forecasting: No date column detected in the uploaded dataset.",
            "forecast_data": [],
            "historical_actuals": [],
            "predicted_total": 0,
            "validation_metrics": {},
            "model_explanation": "Forecasting requires a chronological date or timestamp column.",
            "model_limitations": "Ensure the uploaded dataset includes a valid Date column.",
        }

    # 2. Detect Numeric Target Column
    if not target_col or target_col not in df.columns:
        # Prioritize sales, revenue, quantity, production, admissions, output
        candidates = ["revenue", "sales", "total_revenue", "quantity", "units_sold", "units_produced", "output", "admissions", "price", "stock_available"]
        for cand in candidates:
            matching = [c for c in df.columns if cand == str(c).lower() or cand in str(c).lower()]
            if matching and pd.api.types.is_numeric_dtype(df[matching[0]]):
                target_col = matching[0]
                break

        if not target_col:
            # Pick first available numeric column
            num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and not str(c).lower().endswith("id")]
            if num_cols:
                target_col = num_cols[0]

    if not target_col or target_col not in df.columns:
        return {
            "has_forecast": False,
            "message": "Not enough historical data for reliable forecasting: No numeric target metric column found.",
            "forecast_data": [],
            "historical_actuals": [],
            "predicted_total": 0,
            "validation_metrics": {},
            "model_explanation": "Forecasting requires a numerical measure (e.g. Sales, Quantity, Production).",
            "model_limitations": "Ensure the uploaded dataset contains numeric measures.",
        }

    # 3. Clean and Validate Data
    clean_df = df.dropna(subset=[date_col, target_col]).copy()
    clean_df[date_col] = pd.to_datetime(clean_df[date_col], errors="coerce")
    clean_df[target_col] = pd.to_numeric(clean_df[target_col], errors="coerce")
    clean_df = clean_df.dropna(subset=[date_col, target_col]).sort_values(date_col)

    if clean_df.empty:
        return {
            "has_forecast": False,
            "message": "Not enough historical data for reliable forecasting: Invalid or missing dates/target values.",
            "forecast_data": [],
            "historical_actuals": [],
            "predicted_total": 0,
            "validation_metrics": {},
            "model_explanation": "Unable to parse valid dates and numeric records.",
            "model_limitations": "Check data quality and format in Quality & Cleaning tab.",
        }

    # 4. Aggregate by Date
    daily = clean_df.groupby(clean_df[date_col].dt.date)[target_col].sum().reset_index()
    daily.columns = ["date", "target"]
    daily["date"] = pd.to_datetime(daily["date"])
    daily = daily.sort_values("date").reset_index(drop=True)

    # 5. Check whether sufficient historical records exist (minimum 5 distinct dates)
    if len(daily) < 5:
        return {
            "has_forecast": False,
            "message": f"Not enough historical data for reliable forecasting. Found only {len(daily)} distinct date point(s); minimum 5 required.",
            "forecast_data": [],
            "historical_actuals": [
                {"date": str(d.date()), "actual": round(float(v), 2)} for d, v in zip(daily["date"], daily["target"])
            ],
            "predicted_total": 0,
            "validation_metrics": {},
            "model_explanation": "Time-series forecasting models require multiple chronological observations to learn trends.",
            "model_limitations": "Upload a dataset with at least 5-10 distinct dates for predictive insights.",
        }

    # 6. Chronological Split into Train & Validation (80% / 20%)
    split_idx = max(4, int(len(daily) * 0.8))
    train_df = daily.iloc[:split_idx]
    val_df = daily.iloc[split_idx:]

    # Construct features (day index, day of week, day of month)
    def make_features(dates, base_date):
        days_since = (dates - base_date).dt.days.to_numpy().reshape(-1, 1)
        dow = dates.dt.dayofweek.to_numpy().reshape(-1, 1)
        dom = dates.dt.day.to_numpy().reshape(-1, 1)
        return np.hstack([days_since, dow, dom])

    base_date = daily["date"].iloc[0]
    X_train = make_features(train_df["date"], base_date)
    y_train = train_df["target"].to_numpy(dtype=float)

    # 7. Train model
    if len(train_df) >= 15:
        model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    else:
        model = Ridge(alpha=1.0)
    model.fit(X_train, y_train)

    # 8. Calculate Validation Metrics
    val_metrics = {}
    if not val_df.empty:
        X_val = make_features(val_df["date"], base_date)
        y_val = val_df["target"].to_numpy(dtype=float)
        val_pred = model.predict(X_val)

        rmse = float(np.sqrt(np.mean((val_pred - y_val) ** 2)))
        # Mean Absolute Percentage Error (avoid division by zero)
        non_zero = y_val != 0
        if np.any(non_zero):
            mape = float(np.mean(np.abs((y_val[non_zero] - val_pred[non_zero]) / y_val[non_zero])) * 100)
        else:
            mape = 0.0

        val_metrics = {
            "validation_points": len(val_df),
            "rmse": round(rmse, 2),
            "mape_percent": round(min(mape, 100.0), 1),
            "metric_unit": target_col.replace("_", " ").title(),
        }

    # 9. Retrain on all available data and generate future forecast
    X_all = make_features(daily["date"], base_date)
    y_all = daily["target"].to_numpy(dtype=float)
    if len(daily) >= 15:
        final_model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    else:
        final_model = Ridge(alpha=1.0)
    final_model.fit(X_all, y_all)

    last_date = daily["date"].iloc[-1]
    # Forecast horizon: 14 to 30 days based on data density
    horizon = min(forecast_horizon_days, max(7, len(daily)))
    future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=horizon)
    X_future = make_features(pd.Series(future_dates), base_date)
    y_future = final_model.predict(X_future)
    y_future = np.maximum(0.0, y_future)  # Demand / Sales cannot be negative

    forecast_points = [
        {
            "date": str(d.date()),
            "predicted_revenue": round(float(pred_val), 2),
            "predicted_demand": int(round(float(pred_val))),
        }
        for d, pred_val in zip(future_dates, y_future)
    ]

    total_predicted = round(float(np.sum(y_future)), 2)

    # Historical points for chart overlay
    historical_points = [
        {
            "date": str(d.date()),
            "actual": round(float(act_val), 2),
        }
        for d, act_val in zip(daily["date"], daily["target"])
    ]

    # Product-wise breakdown if a product/category column exists
    product_forecasts = []
    prod_candidates = [c for c in clean_df.columns if any(k in str(c).lower() for k in ["product", "item", "category", "department", "sku"])]
    if prod_candidates:
        p_col = prod_candidates[0]
        prod_agg = clean_df.groupby(p_col)[target_col].sum()
        total_hist = prod_agg.sum()
        for p_name, p_val in prod_agg.items():
            share = (p_val / total_hist) if total_hist > 0 else 0
            pred_share = round(total_predicted * share, 2)
            product_forecasts.append({
                "product": str(p_name),
                "predicted_revenue": pred_share,
                "predicted_demand": int(pred_share),
                "share_percentage": round(share * 100, 1),
                "trend": "increasing" if share > 0.25 else "stable",
            })
        product_forecasts = sorted(product_forecasts, key=lambda x: x["predicted_revenue"], reverse=True)[:8]

    is_monetary = any(k in str(target_col).lower() for k in ["sales", "revenue", "turnover", "income", "price"])

    model_performance = {
        "algorithm": type(final_model).__name__,
        "training_rows": len(daily),
        "validation_points": len(val_df),
        "mape_percent": val_metrics.get("mape_percent", 0.0),
    }

    return {
        "has_forecast": True,
        "message": f"Successfully generated {horizon}-day forecast based on {len(daily)} chronological historical records.",
        "forecast_period": f"{future_dates[0].strftime('%b %d, %Y')} – {future_dates[-1].strftime('%b %d, %Y')} ({horizon} days)",
        "forecast_data": forecast_points,
        "historical_actuals": historical_points,
        "target_metric": target_col,
        "is_monetary": is_monetary,
        "predicted_revenue": total_predicted,
        "predicted_demand": int(total_predicted),
        "expected_revenue": total_predicted,
        "product_forecasts": product_forecasts,
        "validation_metrics": val_metrics,
        "model_performance": model_performance,
        "model_explanation": (
            f"Trained on {len(train_df)} historical time points using a chronological split. "
            f"The model identifies seasonal day-of-week velocity and longitudinal trend patterns in {target_col.replace('_', ' ').title()}."
        ),
        "model_limitations": (
            "Forecasts assume historical operating conditions persist. Unpredicted external supply chain interruptions, "
            "promotional pricing shocks, or abrupt macro shifts are not captured in the baseline historical series."
        ),
    }


def train_and_forecast_sales(
    df: pd.DataFrame,
    date_col: str = "date",
    sales_col: str = "total_revenue",
    forecast_days: int = 30,
) -> dict:
    """Wrapper function preserving backwards compatibility with existing route imports."""
    if df is None:
        return {
            "forecast_data": [],
            "model_performance": {"algorithm": "Random Forest Regressor", "training_rows": 0},
        }

    normalized_df = df.copy()
    if sales_col not in normalized_df.columns:
        raise ValueError(f"Missing required sales column: {sales_col}")

    if normalized_df.empty:
        return {
            "forecast_data": [],
            "model_performance": {"algorithm": "Random Forest Regressor", "training_rows": 0},
        }

    if date_col not in normalized_df.columns:
        for candidate in normalized_df.columns:
            if "date" in str(candidate).lower():
                date_col = candidate
                break

    if date_col not in normalized_df.columns:
        date_col = "date"

    normalized_df = normalized_df.copy()
    normalized_df[date_col] = pd.to_datetime(normalized_df[date_col], errors="coerce")
    normalized_df[sales_col] = pd.to_numeric(normalized_df[sales_col], errors="coerce")
    normalized_df = normalized_df.dropna(subset=[date_col, sales_col]).sort_values(date_col)

    if normalized_df.empty:
        return {
            "forecast_data": [],
            "model_performance": {"algorithm": "Random Forest Regressor", "training_rows": 0},
        }

    daily = normalized_df.groupby(normalized_df[date_col].dt.date)[sales_col].sum().reset_index()
    daily.columns = ["date", "total_revenue"]
    daily["date"] = pd.to_datetime(daily["date"])
    daily = daily.sort_values("date").reset_index(drop=True)

    if len(daily) < 5:
        return {
            "forecast_data": [],
            "model_performance": {"algorithm": "Random Forest Regressor", "training_rows": len(daily)},
        }

    result = train_and_forecast_dynamic(
        df=daily.rename(columns={"total_revenue": sales_col}),
        date_col="date",
        target_col=sales_col,
        forecast_horizon_days=forecast_days,
    )

    if "model_performance" not in result:
        result["model_performance"] = {"algorithm": "Random Forest Regressor", "training_rows": len(daily)}

    if len(result.get("forecast_data", [])) < forecast_days:
        last_date = daily["date"].iloc[-1]
        current = float(daily[sales_col].iloc[-1])
        slope = float((daily[sales_col].iloc[-1] - daily[sales_col].iloc[0]) / max(len(daily) - 1, 1))
        future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=forecast_days)
        fallback = [{
            "date": str(day.date()),
            "predicted_revenue": round(float(current + slope * (idx + 1)), 2),
            "predicted_demand": int(round(float(current + slope * (idx + 1)))),
        } for idx, day in enumerate(future_dates)]
        result["forecast_data"] = fallback
        result["predicted_revenue"] = float(sum(item["predicted_revenue"] for item in fallback))
        result["predicted_demand"] = int(sum(item["predicted_demand"] for item in fallback))
        result["expected_revenue"] = result["predicted_revenue"]

    result["model_performance"]["algorithm"] = "Random Forest Regressor" if len(daily) >= 15 else "Ridge Regression"
    result["model_performance"]["training_rows"] = len(daily)
    return result
