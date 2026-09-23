"""Insight generation.

Every insight is derived from numbers already computed by the analysis modules.
This service never reads the raw DataFrame, which makes it impossible for a
finding to reference a statistic the application did not calculate.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

SEVERITY_ORDER = {"critical": 0, "warning": 1, "info": 2}

MISSING_WARNING_PCT = 5.0
MISSING_CRITICAL_PCT = 30.0
DUPLICATE_WARNING_PCT = 1.0
DOMINANT_CATEGORY_PCT = 80.0
SKEW_STD_RATIO = 0.25
OUTLIER_WARNING_PCT = 5.0
MAX_INSIGHTS_PER_RULE = 5


@dataclass(frozen=True)
class Insight:
    title: str
    description: str
    category: str
    severity: str
    metric: str
    column_name: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def generate_insights(summary: dict) -> list[dict]:
    """Run every rule over a computed analysis summary."""
    rules = (
        _missing_value_insights,
        _duplicate_insights,
        _constant_column_insights,
        _cardinality_insights,
        _suspicious_type_insights,
        _correlation_insights,
        _distribution_insights,
        _outlier_insights,
        _imbalance_insights,
        _anomaly_insights,
    )
    insights: list[Insight] = []
    for rule in rules:
        insights.extend(rule(summary))
    insights.sort(key=lambda item: SEVERITY_ORDER.get(item.severity, 3))
    return [item.to_dict() for item in insights]


def _missing_value_insights(summary: dict) -> list[Insight]:
    columns = summary.get("data_quality", {}).get("columns", [])
    flagged = sorted(
        (column for column in columns if column["missing_pct"] >= MISSING_WARNING_PCT),
        key=lambda column: column["missing_pct"],
        reverse=True,
    )
    return [
        Insight(
            title="High Missing Data",
            description=(
                f"{column['name']} contains missing values in {column['missing_pct']}% "
                f"of rows ({column['missing_count']} rows)."
            ),
            category="data_quality",
            severity="critical" if column["missing_pct"] >= MISSING_CRITICAL_PCT else "warning",
            metric=f"{column['missing_pct']}% missing",
            column_name=column["name"],
        )
        for column in flagged[:MAX_INSIGHTS_PER_RULE]
    ]


def _duplicate_insights(summary: dict) -> list[Insight]:
    quality = summary.get("data_quality", {})
    duplicates = quality.get("duplicate_rows", 0)
    if not duplicates:
        return []
    pct = quality.get("duplicate_pct", 0.0)
    return [
        Insight(
            title="Duplicate Rows",
            description=(
                f"{duplicates} rows ({pct}%) are exact duplicates of another row. "
                "Duplicates can inflate counts and bias aggregate statistics."
            ),
            category="data_quality",
            severity="warning" if pct >= DUPLICATE_WARNING_PCT else "info",
            metric=f"{duplicates} duplicate rows",
        )
    ]


def _constant_column_insights(summary: dict) -> list[Insight]:
    constants = summary.get("data_quality", {}).get("constant_columns", [])
    if not constants:
        return []
    listed = ", ".join(constants[:5])
    return [
        Insight(
            title="Constant Columns",
            description=(
                f"{len(constants)} column(s) hold a single value across every row: {listed}. "
                "They cannot explain variation in the data."
            ),
            category="data_quality",
            severity="warning",
            metric=f"{len(constants)} constant column(s)",
        )
    ]


def _cardinality_insights(summary: dict) -> list[Insight]:
    high_cardinality = summary.get("data_quality", {}).get("high_cardinality_columns", [])
    total_rows = summary.get("overview", {}).get("rows", 0)
    return [
        Insight(
            title="Very High Cardinality",
            description=(
                f"{column['name']} has {column['unique_count']} distinct values across "
                f"{total_rows} rows ({round(column['unique_ratio'] * 100, 1)}% unique), "
                "which is typical of an identifier rather than a variable to group by."
            ),
            category="cardinality",
            severity="info",
            metric=f"{column['unique_count']} unique values",
            column_name=column["name"],
        )
        for column in high_cardinality[:MAX_INSIGHTS_PER_RULE]
    ]


def _suspicious_type_insights(summary: dict) -> list[Insight]:
    suspicious = summary.get("data_quality", {}).get("suspicious_types", [])
    return [
        Insight(
            title="Column Type Looks Wrong",
            description=(
                f"{item['name']} is stored as {item['detected_type']}, but "
                f"{round(item['match_ratio'] * 100, 1)}% of its values parse as "
                f"{item['suggested_type']}. Converting it would enable "
                f"{item['suggested_type']} analysis."
            ),
            category="data_quality",
            severity="warning",
            metric=f"{round(item['match_ratio'] * 100, 1)}% parse as {item['suggested_type']}",
            column_name=item["name"],
        )
        for item in suspicious[:MAX_INSIGHTS_PER_RULE]
    ]


def _correlation_insights(summary: dict) -> list[Insight]:
    pairs = summary.get("correlation", {}).get("strong_pairs", [])
    return [
        Insight(
            title=f"Strong {pair['direction'].title()} Correlation",
            description=(
                f"{pair['column_a']} and {pair['column_b']} have a Pearson correlation of "
                f"{pair['correlation']}. They move together closely; this measures "
                "association only and does not show that one causes the other."
            ),
            category="correlation",
            severity="info",
            metric=f"r = {pair['correlation']}",
        )
        for pair in pairs[:MAX_INSIGHTS_PER_RULE]
    ]


def _distribution_insights(summary: dict) -> list[Insight]:
    """Flag numeric columns whose mean is pulled noticeably away from the median."""
    insights = []
    for name, stats in summary.get("numeric_statistics", {}).items():
        mean, median, std = stats.get("mean"), stats.get("median"), stats.get("std")
        if mean is None or median is None or not std:
            continue
        gap = abs(mean - median)
        if gap / std < SKEW_STD_RATIO:
            continue
        direction = "above" if mean > median else "below"
        insights.append(
            Insight(
                title="Skewed Distribution",
                description=(
                    f"The mean of {name} ({mean}) sits {direction} its median ({median}), "
                    f"a gap of {round(gap, 4)} against a standard deviation of {std}. "
                    "A few extreme values are pulling the average."
                ),
                category="distribution",
                severity="info",
                metric=f"mean {mean} vs median {median}",
                column_name=name,
            )
        )
    return insights[:MAX_INSIGHTS_PER_RULE]


def _outlier_insights(summary: dict) -> list[Insight]:
    flagged = sorted(
        (
            (name, stats)
            for name, stats in summary.get("outliers", {}).items()
            if stats.get("pct", 0) >= OUTLIER_WARNING_PCT
        ),
        key=lambda item: item[1]["pct"],
        reverse=True,
    )
    return [
        Insight(
            title="Potential Outliers",
            description=(
                f"{stats['count']} values in {name} ({stats['pct']}% of non-missing rows) "
                f"fall outside the {stats['method']} range "
                f"[{stats['lower_bound']}, {stats['upper_bound']}]."
            ),
            category="outlier",
            severity="warning",
            metric=f"{stats['pct']}% outside IQR fences",
            column_name=name,
        )
        for name, stats in flagged[:MAX_INSIGHTS_PER_RULE]
    ]


def _imbalance_insights(summary: dict) -> list[Insight]:
    insights = []
    for name, stats in summary.get("categorical_analysis", {}).items():
        dominant_pct = stats.get("dominant_pct", 0.0)
        if stats.get("unique_count", 0) < 2 or dominant_pct < DOMINANT_CATEGORY_PCT:
            continue
        insights.append(
            Insight(
                title="Dominant Category",
                description=(
                    f"{dominant_pct}% of rows in {name} share the single value "
                    f"{stats['dominant_value']!r} out of {stats['unique_count']} distinct "
                    "values. The distribution is heavily imbalanced."
                ),
                category="balance",
                severity="warning",
                metric=f"{dominant_pct}% in one category",
                column_name=name,
            )
        )
    return insights[:MAX_INSIGHTS_PER_RULE]


def _anomaly_insights(summary: dict) -> list[Insight]:
    anomalies = summary.get("anomalies", {})
    if not anomalies.get("applicable") or not anomalies.get("anomalous_rows"):
        return []
    columns = ", ".join(anomalies.get("columns", [])[:5])
    return [
        Insight(
            title="Unusual Row Combinations",
            description=(
                f"{anomalies['anomalous_rows']} of {anomalies['rows_considered']} complete rows "
                f"({anomalies['anomalous_pct']}%) are unusual when {columns} are considered "
                "together, even where each individual value looks ordinary."
            ),
            category="outlier",
            severity="info",
            metric=f"{anomalies['anomalous_pct']}% anomalous rows",
        )
    ]
