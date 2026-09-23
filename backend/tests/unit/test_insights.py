"""Insights must always be traceable to a computed number."""

from app.analysis.insights import generate_insights


def base_summary(**overrides) -> dict:
    summary = {
        "overview": {"rows": 100, "columns": 3},
        "numeric_statistics": {},
        "categorical_analysis": {},
        "data_quality": {
            "total_missing": 0,
            "missing_pct": 0.0,
            "duplicate_rows": 0,
            "duplicate_pct": 0.0,
            "constant_columns": [],
            "high_cardinality_columns": [],
            "suspicious_types": [],
            "columns": [],
        },
        "correlation": {"strong_pairs": []},
        "outliers": {},
        "anomalies": {"applicable": False},
    }
    summary.update(overrides)
    return summary


def test_clean_dataset_produces_no_insights():
    assert generate_insights(base_summary()) == []


def test_high_missing_data_insight_quotes_the_percentage():
    summary = base_summary()
    summary["data_quality"]["columns"] = [
        {"name": "customer_age", "missing_count": 184, "missing_pct": 18.4, "unique_count": 40}
    ]

    insight = generate_insights(summary)[0]

    assert insight["title"] == "High Missing Data"
    assert "customer_age" in insight["description"]
    assert "18.4%" in insight["description"]
    assert insight["severity"] == "warning"
    assert insight["column_name"] == "customer_age"


def test_missing_data_above_thirty_percent_is_critical():
    summary = base_summary()
    summary["data_quality"]["columns"] = [
        {"name": "notes", "missing_count": 60, "missing_pct": 60.0, "unique_count": 5}
    ]

    assert generate_insights(summary)[0]["severity"] == "critical"


def test_small_missing_share_is_not_reported():
    summary = base_summary()
    summary["data_quality"]["columns"] = [
        {"name": "age", "missing_count": 1, "missing_pct": 1.0, "unique_count": 40}
    ]

    assert generate_insights(summary) == []


def test_duplicate_rows_insight_reports_the_count():
    summary = base_summary()
    summary["data_quality"]["duplicate_rows"] = 12
    summary["data_quality"]["duplicate_pct"] = 12.0

    insight = generate_insights(summary)[0]

    assert insight["title"] == "Duplicate Rows"
    assert "12 rows" in insight["description"]


def test_correlation_insight_refuses_to_claim_causation():
    summary = base_summary()
    summary["correlation"]["strong_pairs"] = [
        {"column_a": "tenure", "column_b": "spend", "correlation": 0.93, "direction": "positive"}
    ]

    insight = generate_insights(summary)[0]

    assert "0.93" in insight["description"]
    assert "does not show that one causes the other" in insight["description"]


def test_dominant_category_insight_is_generated():
    summary = base_summary()
    summary["categorical_analysis"] = {
        "status": {"unique_count": 3, "dominant_value": "active", "dominant_pct": 94.0}
    }

    insight = generate_insights(summary)[0]

    assert insight["title"] == "Dominant Category"
    assert "94.0%" in insight["description"]


def test_outlier_insight_uses_the_computed_fences():
    summary = base_summary()
    summary["outliers"] = {
        "spend": {
            "count": 9,
            "pct": 9.0,
            "lower_bound": -5.0,
            "upper_bound": 210.0,
            "method": "1.5 x IQR",
        }
    }

    insight = generate_insights(summary)[0]

    assert "9 values in spend" in insight["description"]
    assert "210.0" in insight["description"]


def test_constant_columns_insight_lists_the_columns():
    summary = base_summary()
    summary["data_quality"]["constant_columns"] = ["currency"]

    assert "currency" in generate_insights(summary)[0]["description"]


def test_insights_are_ordered_with_the_most_severe_first():
    summary = base_summary()
    summary["data_quality"]["columns"] = [
        {"name": "notes", "missing_count": 60, "missing_pct": 60.0, "unique_count": 5}
    ]
    summary["correlation"]["strong_pairs"] = [
        {"column_a": "a", "column_b": "b", "correlation": 0.9, "direction": "positive"}
    ]

    severities = [insight["severity"] for insight in generate_insights(summary)]

    assert severities == ["critical", "info"]
