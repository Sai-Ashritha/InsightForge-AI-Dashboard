import pandas as pd

from app.services.data_quality import assess_data_quality, clean_dataset


def test_quality_score_uses_null_duplicate_and_outlier_ratios():
    frame = pd.DataFrame({"revenue": [100, 100, 100, 1000], "product": ["A", "B", "C", "D"]})

    result = assess_data_quality(frame)

    assert 0 <= result["quality_score"] <= 100
    assert result["duplicate_ratio"] == 0.0
    assert result["outlier_ratio"] > 0


def test_clean_dataset_drops_duplicates_and_imputes_numeric_values():
    frame = pd.DataFrame({"revenue": [100.0, None, 100.0], "product": ["A", None, "A"]})

    cleaned = clean_dataset(frame)

    assert len(cleaned) == 2
    assert cleaned["revenue"].isna().sum() == 0
    assert cleaned["product"].isna().sum() == 0
