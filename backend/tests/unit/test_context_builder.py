"""The AI context must carry the analysis, and nothing but the analysis."""

import json
from datetime import datetime, timezone

from app.ai.context_builder import build_analysis_context, render_context
from app.models import Analysis, AnalysisInsight, Dataset


def make_analysis() -> tuple[Dataset, Analysis]:
    dataset = Dataset(
        id=1,
        user_id=1,
        filename="customers.csv",
        storage_key="abc.csv",
        row_count=100,
        column_count=2,
        uploaded_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    analysis = Analysis(
        id=1,
        dataset_id=1,
        analysis_summary={
            "overview": {
                "rows": 100,
                "columns": 2,
                "numeric_columns": ["spend"],
                "categorical_columns": ["plan"],
                "datetime_columns": [],
                "boolean_columns": [],
            },
            "columns": [{"name": "spend", "missing_count": 4}],
            "numeric_statistics": {"spend": {"mean": 50.0, "median": 48.0}},
            "categorical_analysis": {
                "plan": {
                    "unique_count": 2,
                    "top_values": [{"value": "basic", "count": 70, "pct": 70.0}],
                    "dominant_value": "basic",
                    "dominant_pct": 70.0,
                }
            },
            "data_quality": {
                "total_missing": 4,
                "duplicate_rows": 1,
                "columns": [{"name": "spend", "missing_count": 4, "missing_pct": 4.0}],
            },
            "correlation": {"method": "pearson", "strong_pairs": []},
            "outliers": {},
        },
        visualizations=[],
    )
    analysis.insights = [
        AnalysisInsight(
            id=1,
            analysis_id=1,
            title="Duplicate Rows",
            description="1 row is a duplicate.",
            category="data_quality",
            severity="info",
            metric="1 duplicate row",
        )
    ]
    return dataset, analysis


def test_context_includes_dataset_metadata():
    context = build_analysis_context(*make_analysis())

    assert context["dataset"]["filename"] == "customers.csv"
    assert context["dataset"]["rows"] == 100


def test_context_includes_computed_statistics():
    context = build_analysis_context(*make_analysis())

    assert context["numeric_statistics"]["spend"]["mean"] == 50.0


def test_context_includes_generated_insights():
    context = build_analysis_context(*make_analysis())

    assert context["insights"][0]["title"] == "Duplicate Rows"


def test_context_reports_columns_with_missing_values():
    context = build_analysis_context(*make_analysis())

    assert context["data_quality"]["columns_with_missing_values"][0]["name"] == "spend"


def test_context_contains_no_raw_rows():
    context = build_analysis_context(*make_analysis())

    assert "rows" not in context
    assert "data" not in context


def test_rendered_context_is_valid_json():
    context = build_analysis_context(*make_analysis())

    assert json.loads(render_context(context))["dataset"]["rows"] == 100
