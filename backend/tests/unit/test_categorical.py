import pandas as pd

from app.analysis.categorical import categorical_analysis


def test_frequency_distribution_counts_and_percentages():
    df = pd.DataFrame({"plan": ["basic", "basic", "basic", "pro"]})

    stats = categorical_analysis(df)["plan"]

    assert stats["unique_count"] == 2
    assert stats["top_values"][0] == {"value": "basic", "count": 3, "pct": 75.0}
    assert stats["dominant_value"] == "basic"
    assert stats["dominant_pct"] == 75.0


def test_top_values_are_limited():
    df = pd.DataFrame({"code": [f"v{i}" for i in range(30)]})

    assert len(categorical_analysis(df, top_n=5)["code"]["top_values"]) == 5


def test_numeric_columns_are_not_treated_as_categorical():
    df = pd.DataFrame({"amount": [1.0, 2.0, 3.0]})

    assert categorical_analysis(df) == {}


def test_boolean_columns_are_summarised():
    df = pd.DataFrame({"active": [True, True, False]})

    stats = categorical_analysis(df)["active"]

    assert stats["unique_count"] == 2
    assert stats["dominant_value"] == "True"
