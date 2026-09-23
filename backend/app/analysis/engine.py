"""Orchestrates the analysis modules into one result.

Everything the product reports about a dataset is computed here, in Python.
The AI layer consumes this output; it never produces it.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import pandas as pd

from app.analysis.anomalies import anomaly_summary
from app.analysis.categorical import categorical_analysis
from app.analysis.correlation import correlation_analysis
from app.analysis.insights import generate_insights
from app.analysis.profiler import build_column_profiles, build_overview
from app.analysis.quality import assess_quality
from app.analysis.statistics import numeric_statistics, outlier_summary
from app.analysis.utils import jsonify, stringify_value
from app.analysis.visualizations import build_visualizations

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    summary: dict = field(default_factory=dict)
    insights: list[dict] = field(default_factory=list)
    visualizations: list[dict] = field(default_factory=list)


def analyze_dataframe(df: pd.DataFrame) -> AnalysisResult:
    """Compute the full analysis for a dataframe."""
    summary = {
        "overview": build_overview(df),
        "columns": build_column_profiles(df),
        "numeric_statistics": numeric_statistics(df),
        "categorical_analysis": categorical_analysis(df),
        "data_quality": assess_quality(df),
        "correlation": correlation_analysis(df),
        "outliers": outlier_summary(df),
        "anomalies": anomaly_summary(df),
    }
    insights = generate_insights(summary)
    visualizations = build_visualizations(df, summary)
    logger.info(
        "Analyzed dataframe: %s rows, %s columns, %s insights",
        summary["overview"]["rows"],
        summary["overview"]["columns"],
        len(insights),
    )
    return AnalysisResult(
        summary=jsonify(summary),
        insights=jsonify(insights),
        visualizations=jsonify(visualizations),
    )


def build_preview(df: pd.DataFrame, row_limit: int = 20) -> dict:
    """A lightweight look at the data, computed without a full analysis run."""
    head = df.head(row_limit)
    rows = [
        {str(column): stringify_value(value) for column, value in record.items()}
        for record in head.to_dict(orient="records")
    ]
    return jsonify(
        {
            "row_count": int(len(df)),
            "column_count": int(df.shape[1]),
            "columns": build_column_profiles(df),
            "rows": rows,
            "total_missing": int(df.isna().sum().sum()),
            "duplicate_rows": int(df.duplicated().sum()),
        }
    )
