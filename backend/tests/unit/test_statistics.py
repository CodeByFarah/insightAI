import numpy as np
import pandas as pd

from app.analysis.statistics import numeric_statistics, outlier_summary


def test_numeric_statistics_match_known_values():
    df = pd.DataFrame({"value": [1, 2, 3, 4, 5], "label": list("abcde")})

    stats = numeric_statistics(df)["value"]

    assert stats["count"] == 5
    assert stats["mean"] == 3.0
    assert stats["median"] == 3.0
    assert stats["min"] == 1.0
    assert stats["max"] == 5.0
    assert stats["q1"] == 2.0
    assert stats["q3"] == 4.0
    assert stats["iqr"] == 2.0
    assert stats["std"] == round(float(np.std([1, 2, 3, 4, 5], ddof=1)), 4)


def test_numeric_statistics_ignore_non_numeric_columns():
    df = pd.DataFrame({"value": [1.0, 2.0], "label": ["x", "y"]})

    assert set(numeric_statistics(df)) == {"value"}


def test_numeric_statistics_handle_all_missing_column():
    df = pd.DataFrame({"value": [np.nan, np.nan, np.nan]})

    stats = numeric_statistics(df)["value"]

    assert stats["count"] == 0
    assert stats["mean"] is None


def test_numeric_statistics_exclude_missing_values_from_mean():
    df = pd.DataFrame({"value": [2.0, 4.0, np.nan]})

    stats = numeric_statistics(df)["value"]

    assert stats["count"] == 2
    assert stats["mean"] == 3.0


def test_outlier_summary_flags_extreme_value():
    df = pd.DataFrame({"value": [10, 11, 12, 13, 12, 11, 10, 12, 500]})

    summary = outlier_summary(df)["value"]

    assert summary["count"] == 1
    assert summary["upper_bound"] < 500


def test_outlier_summary_skips_constant_column():
    df = pd.DataFrame({"value": [5] * 20})

    assert "value" not in outlier_summary(df)
