import pandas as pd

from app.routes.upload import merge_uploaded_dataframes
from app.routes import dashboard as dashboard_route, ml as ml_route
from app.services.data_quality import clamp_percentage, infer_column_types
from app.services.dynamic_engine import compute_dynamic_analytics, inspect_dataset_schema
from app.services.insight_generator import InsightGenerator
from app.services.recommendations import generate_recommendations


def test_infer_column_types_handles_generic_business_data():
    df = pd.DataFrame(
        {
            "Order Date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "Customer": ["A", "B", "A"],
            "Region": ["North", "South", "North"],
            "Sales Amount": [1200.0, 1400.0, 1100.0],
            "Units": [10, 16, 9],
        }
    )

    schema = infer_column_types(df)

    assert "Order Date" in schema["date_cols"]
    assert "Sales Amount" in schema["numeric_cols"]
    assert "Customer" in schema["categorical_cols"]
    assert "Region" in schema["categorical_cols"]


def test_percentage_values_are_clamped_to_safe_range():
    assert clamp_percentage(150) == 100.0
    assert clamp_percentage(-5) == 0.0
    assert clamp_percentage(42.5) == 42.5
    assert clamp_percentage(float("nan")) == 0.0


def test_multiple_uploads_are_merged_on_common_keys_when_possible():
    df_a = pd.DataFrame({"Customer": ["A", "B"], "Region": ["North", "South"], "Sales": [100, 200]})
    df_b = pd.DataFrame({"Customer": ["A", "B"], "Discount": [10, 5]})

    merged = merge_uploaded_dataframes([df_a, df_b])

    assert not merged.empty
    assert "Customer" in merged.columns
    assert merged.shape[0] == 2
    assert merged["Discount"].tolist() == [10, 5]


def test_cleaning_counts_filled_generic_categories():
    from app.services.data_quality import clean_dataset_with_stats

    cleaned, stats = clean_dataset_with_stats(pd.DataFrame({"Segment": ["A", None, "A"]}))

    assert cleaned["segment"].isna().sum() == 0
    assert stats["missing_categorical_filled"] == 1
    assert stats["total_cleaned_values"] == 2


def test_ai_summary_uses_dataset_metadata_and_actual_metrics():
    summary = InsightGenerator().generate_kpi_summary({
        "dataset_name": "customer_metrics.csv",
        "total_records": 2,
        "columns": ["customer", "spend"],
        "total_spend": 125.5,
    })

    assert "customer_metrics.csv" in summary
    assert "customer, spend" in summary
    assert "total spend: 125.50" in summary


def test_recommendations_do_not_invent_actions_without_evidence():
    assert generate_recommendations(data={"total_records": 10}) == []


def test_numeric_month_measure_is_not_inferred_as_a_date():
    schema = inspect_dataset_schema(pd.DataFrame({"hours_worked_month": [120, 135, 142]}))

    assert "hours_worked_month" in schema["numeric_cols"]
    assert "hours_worked_month" not in schema["date_cols"]


def test_dynamic_charts_skip_non_overlapping_and_zero_value_pairs():
    df = pd.DataFrame({
        "employee_id": ["E1", "E2", "E3", None, None, None],
        "department": ["A", "B", "A", "A", "B", "A"],
        "productivity_percent": [70, 85, 75, None, None, None],
        "revenue": [None, None, None, 100, 200, 150],
    })

    result = compute_dynamic_analytics(df)
    chart_titles = [chart["title"] for chart in result["charts"]]

    assert all(chart.get("x") and chart.get("y") for chart in result["charts"])
    assert all(any(value != 0 for value in chart["y"]) for chart in result["charts"] if chart["chart_type"] != "scatter")
    assert "Revenue by Employee Id" not in chart_titles
    assert any("Revenue by Department" == title for title in chart_titles)


def test_defect_rate_uses_matched_count_columns_not_cost_or_percent_sum():
    result = compute_dynamic_analytics(pd.DataFrame({
        "units_produced": [10, 20],
        "defective_units": [1, 2],
        "operating_cost": [1000, 2000],
        "productivity_percent": [80, 90],
    }))
    defect_kpi = next(kpi for kpi in result["kpis"] if kpi["key"] == "defect_rate")

    assert defect_kpi["raw_value"] == 10.0


def test_dashboard_stock_bars_use_inventory_rows_not_revenue_shares(monkeypatch):
    df = pd.DataFrame({
        "department": ["North", "South", "North", "South"],
        "revenue": [None, None, 100, 200],
        "stock_available": [100, 300, None, None],
    })
    monkeypatch.setattr(dashboard_route, "get_active_dataset", lambda: df)

    result = dashboard_route.get_dashboard()
    inventory = {item["name"]: item for item in result["inventory_status"]}

    assert inventory["North"]["units"] == 100
    assert inventory["South"]["units"] == 300
    assert inventory["South"]["value"] == 100


def test_inventory_alerts_label_rows_from_columns_present_with_stock(monkeypatch):
    df = pd.DataFrame({
        "employee_id": [None, None],
        "product_name": ["Item A", "Item B"],
        "stock_available": [2, 20],
        "reorder_level": [5, 10],
    })
    monkeypatch.setattr(ml_route, "_active_frame", lambda: df)

    result = ml_route.inventory_status()

    assert result["items"][0]["product"] == "Item A"
    assert result["items"][0]["low_stock"] is True
    assert "supplied stock threshold" in result["alerts"][0]
