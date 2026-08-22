import pandas as pd
import pytest

from app.services.anomaly_detector import detect_anomalies
from app.services.forecasting import train_and_forecast_sales
from app.routes import forecast as forecast_route


def test_forecast_training_success():
    data = {
        "date": pd.date_range(start="2026-01-01", periods=20, freq="D"),
        "total_revenue": [100 + i * 5 for i in range(20)],
    }
    df = pd.DataFrame(data)

    result = train_and_forecast_sales(df, forecast_days=7)

    assert "forecast_data" in result
    assert len(result["forecast_data"]) == 7
    assert result["model_performance"]["algorithm"] == "Random Forest Regressor"
    assert result["forecast_data"][0]["date"] == "2026-01-21"


def test_forecast_rejects_missing_columns():
    df = pd.DataFrame({"date": pd.date_range("2026-01-01", periods=3)})

    with pytest.raises(ValueError, match="total_revenue"):
        train_and_forecast_sales(df)


def test_forecast_handles_empty_dataframe():
    result = train_and_forecast_sales(pd.DataFrame(columns=["date", "total_revenue"]))

    assert result["forecast_data"] == []
    assert result["model_performance"]["training_rows"] == 0


def test_anomaly_detector_handles_empty_and_non_numeric_data():
    assert detect_anomalies(pd.DataFrame()) == {
        "anomalies": [],
        "statistics": {},
        "anomaly_count": 0,
    }
    assert detect_anomalies(pd.DataFrame({"product": ["A", "B"]}))["anomalies"] == []


def test_forecast_endpoint_uses_sales_database(monkeypatch):
    monkeypatch.setattr(
        forecast_route,
        "fetch_table",
        lambda table_name: [
            {"date": "2026-02-01", "revenue": 1000},
            {"date": "2026-02-02", "revenue": 2000},
            {"date": "2026-02-03", "revenue": 3000},
        ],
    )

    result = forecast_route.forecast_summary()

    assert result["data_source"] == "sales_database"
    assert result["history_points"] == 3
    assert result["history"] == [1000, 2000, 3000]
    assert result["forecast_values"] == [4000.0, 5000.0, 6000.0, 7000.0]
