import numpy as np
import pandas as pd

from app.analysis.quality import (
    assess_quality,
    find_constant_columns,
    find_high_cardinality_columns,
    find_suspicious_types,
)


def test_missing_values_are_counted_per_column_and_overall():
    df = pd.DataFrame({"a": [1, np.nan, 3, np.nan], "b": [1, 2, 3, 4]})

    quality = assess_quality(df)
    by_name = {column["name"]: column for column in quality["columns"]}

    assert by_name["a"]["missing_count"] == 2
    assert by_name["a"]["missing_pct"] == 50.0
    assert by_name["b"]["missing_count"] == 0
    assert quality["total_missing"] == 2
    assert quality["missing_pct"] == 25.0


def test_duplicate_rows_are_detected():
    df = pd.DataFrame({"a": [1, 1, 2], "b": ["x", "x", "y"]})

    quality = assess_quality(df)

    assert quality["duplicate_rows"] == 1
    assert quality["duplicate_pct"] == round(100 / 3, 2)


def test_no_duplicates_reported_for_distinct_rows():
    df = pd.DataFrame({"a": [1, 2, 3]})

    assert assess_quality(df)["duplicate_rows"] == 0


def test_constant_columns_include_single_value_columns():
    df = pd.DataFrame({"constant": ["USD"] * 4, "varied": [1, 2, 3, 4]})

    assert find_constant_columns(df) == ["constant"]


def test_high_cardinality_detects_identifier_columns():
    df = pd.DataFrame(
        {"customer_id": [f"C{i}" for i in range(50)], "plan": ["basic"] * 25 + ["pro"] * 25}
    )

    flagged = [column["name"] for column in find_high_cardinality_columns(df)]

    assert flagged == ["customer_id"]


def test_suspicious_types_flags_numbers_stored_as_text():
    df = pd.DataFrame({"amount": ["1", "2", "3", "4"]})

    findings = find_suspicious_types(df)

    assert findings and findings[0]["suggested_type"] == "numeric"
