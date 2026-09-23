import numpy as np
import pandas as pd

from app.analysis import analyze_dataframe, build_preview


def sample_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "customer_id": [f"C{i}" for i in range(20)],
            "age": [30 + i for i in range(19)] + [np.nan],
            "spend": [10 * (i + 1) for i in range(20)],
            "plan": ["basic"] * 18 + ["pro"] * 2,
        }
    )


def test_overview_reports_shape_and_column_types():
    result = analyze_dataframe(sample_frame())
    overview = result.summary["overview"]

    assert overview["rows"] == 20
    assert overview["columns"] == 4
    assert set(overview["numeric_columns"]) == {"age", "spend"}
    assert overview["categorical_columns"] == ["customer_id", "plan"]


def test_analysis_result_is_json_serialisable():
    import json

    result = analyze_dataframe(sample_frame())

    json.dumps({"s": result.summary, "i": result.insights, "v": result.visualizations})


def test_visualizations_are_generated_for_detected_types():
    charts = analyze_dataframe(sample_frame()).visualizations
    chart_types = {chart["type"] for chart in charts}

    assert "histogram" in chart_types
    assert "bar" in chart_types
    assert all(chart["title"] for chart in charts)


def test_insights_reference_real_columns():
    result = analyze_dataframe(sample_frame())
    column_names = {column["name"] for column in result.summary["columns"]}

    for insight in result.insights:
        if insight["column_name"]:
            assert insight["column_name"] in column_names


def test_preview_returns_requested_number_of_rows():
    preview = build_preview(sample_frame(), row_limit=5)

    assert len(preview["rows"]) == 5
    assert preview["row_count"] == 20
    assert preview["column_count"] == 4


def test_preview_renders_missing_values_explicitly():
    preview = build_preview(sample_frame(), row_limit=20)

    assert preview["rows"][-1]["age"] == "(missing)"
