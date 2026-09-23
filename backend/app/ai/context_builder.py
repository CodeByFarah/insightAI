"""Builds the structured analysis context sent to the AI provider.

The raw dataset is never sent. The model receives dataset metadata, column
information, computed statistics, missing-value counts, correlations and the
generated insights: enough to explain the analysis, and nothing it could use
to fabricate row-level claims.
"""

from __future__ import annotations

import json

from app.models import Analysis, Dataset

MAX_CATEGORICAL_COLUMNS = 15
MAX_TOP_VALUES = 5
MAX_INSIGHTS = 20


def build_analysis_context(dataset: Dataset, analysis: Analysis) -> dict:
    summary = analysis.analysis_summary or {}
    return {
        "dataset": {
            "filename": dataset.filename,
            "rows": summary.get("overview", {}).get("rows", dataset.row_count),
            "columns": summary.get("overview", {}).get("columns", dataset.column_count),
            "uploaded_at": dataset.uploaded_at.isoformat() if dataset.uploaded_at else None,
        },
        "column_types": {
            "numeric": summary.get("overview", {}).get("numeric_columns", []),
            "categorical": summary.get("overview", {}).get("categorical_columns", []),
            "datetime": summary.get("overview", {}).get("datetime_columns", []),
            "boolean": summary.get("overview", {}).get("boolean_columns", []),
        },
        "columns": summary.get("columns", []),
        "numeric_statistics": summary.get("numeric_statistics", {}),
        "categorical_analysis": _trim_categorical(
            summary.get("categorical_analysis", {}),
            {
                column["name"]
                for column in summary.get("data_quality", {}).get(
                    "high_cardinality_columns", []
                )
            },
        ),
        "data_quality": _trim_quality(summary.get("data_quality", {})),
        "correlation": {
            "method": summary.get("correlation", {}).get("method", "pearson"),
            "strong_pairs": summary.get("correlation", {}).get("strong_pairs", []),
        },
        "outliers": summary.get("outliers", {}),
        "insights": [
            {
                "title": insight.title,
                "description": insight.description,
                "category": insight.category,
                "severity": insight.severity,
                "metric": insight.metric,
            }
            for insight in analysis.insights[:MAX_INSIGHTS]
        ],
    }


def render_context(context: dict) -> str:
    """Serialise the context compactly for the prompt."""
    return json.dumps(context, indent=None, separators=(",", ":"), default=str)


def _trim_categorical(categorical: dict, identifier_columns: set[str]) -> dict:
    """Keep the frequency distributions, minus identifier-like columns.

    Listing the values of a near-unique column would put raw row content in the
    prompt without telling the model anything it can reason about, so those
    columns are summarised by their cardinality alone.
    """
    trimmed = {}
    for name, stats in list(categorical.items())[:MAX_CATEGORICAL_COLUMNS]:
        if name in identifier_columns:
            trimmed[name] = {
                "unique_count": stats.get("unique_count"),
                "note": "Identifier-like column; individual values are not shared.",
            }
            continue
        trimmed[name] = {
            "unique_count": stats.get("unique_count"),
            "top_values": stats.get("top_values", [])[:MAX_TOP_VALUES],
            "dominant_value": stats.get("dominant_value"),
            "dominant_pct": stats.get("dominant_pct"),
        }
    return trimmed


def _trim_quality(quality: dict) -> dict:
    columns_with_gaps = [
        column for column in quality.get("columns", []) if column.get("missing_count")
    ]
    return {
        "total_missing": quality.get("total_missing"),
        "missing_pct": quality.get("missing_pct"),
        "duplicate_rows": quality.get("duplicate_rows"),
        "duplicate_pct": quality.get("duplicate_pct"),
        "constant_columns": quality.get("constant_columns", []),
        "high_cardinality_columns": quality.get("high_cardinality_columns", []),
        "suspicious_types": quality.get("suspicious_types", []),
        "columns_with_missing_values": columns_with_gaps,
    }
