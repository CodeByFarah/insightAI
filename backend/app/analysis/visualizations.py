"""Chart specifications derived from the dataset.

The backend decides *which* charts are meaningful and ships ready-to-plot data
points; the frontend only renders them. Charts are deliberately few: one per
question worth asking, rather than one per column.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.analysis.profiler import CATEGORICAL, DATETIME, NUMERIC, columns_of_type
from app.analysis.utils import percentage, round_or_none, stringify_value

MAX_HISTOGRAMS = 3
MAX_BAR_CHARTS = 3
MAX_BINS = 20
TOP_CATEGORIES = 8
MAX_SCATTER_POINTS = 500
MAX_HEATMAP_COLUMNS = 12


def build_visualizations(df: pd.DataFrame, summary: dict) -> list[dict]:
    charts: list[dict] = []
    charts.extend(_histograms(df))
    charts.extend(_bar_charts(df))
    box = _box_plot(df, summary)
    if box:
        charts.append(box)
    scatter = _scatter_for_top_correlation(df, summary)
    if scatter:
        charts.append(scatter)
    heatmap = _correlation_heatmap(summary)
    if heatmap:
        charts.append(heatmap)
    timeseries = _time_series(df)
    if timeseries:
        charts.append(timeseries)
    return charts


def _numeric_columns_by_variation(df: pd.DataFrame) -> list[str]:
    """Numeric columns ordered by how much they vary, most interesting first."""
    candidates = [
        name for name in columns_of_type(df, NUMERIC) if df[name].nunique(dropna=True) > 1
    ]
    return sorted(candidates, key=lambda name: -float(df[name].std(skipna=True) or 0))


def _histograms(df: pd.DataFrame) -> list[dict]:
    charts = []
    for name in _numeric_columns_by_variation(df)[:MAX_HISTOGRAMS]:
        series = df[name].dropna()
        if series.empty:
            continue
        bin_count = _bin_count(series)
        counts, edges = np.histogram(series.to_numpy(dtype=float), bins=bin_count)
        data = [
            {
                "bin": f"{round(float(edges[i]), 2)} - {round(float(edges[i + 1]), 2)}",
                "bin_start": round(float(edges[i]), 4),
                "count": int(counts[i]),
            }
            for i in range(len(counts))
        ]
        charts.append(
            {
                "id": f"histogram-{name}",
                "type": "histogram",
                "title": f"Distribution of {name}",
                "description": f"How the {int(series.count())} recorded values of {name} spread out.",
                "x_label": name,
                "y_label": "Rows",
                "column": name,
                "data": data,
            }
        )
    return charts


def _bin_count(series: pd.Series) -> int:
    """Freedman-Diaconis bin width, capped so charts stay readable."""
    values = series.to_numpy(dtype=float)
    count = values.size
    if count < 2:
        return 1
    iqr = float(np.subtract(*np.percentile(values, [75, 25])))
    if iqr <= 0:
        return min(MAX_BINS, max(1, int(np.sqrt(count))))
    width = 2 * iqr / (count ** (1 / 3))
    span = float(values.max() - values.min())
    if width <= 0 or span <= 0:
        return 1
    return int(min(MAX_BINS, max(5, round(span / width))))


def _bar_charts(df: pd.DataFrame) -> list[dict]:
    charts = []
    total_rows = len(df)
    candidates = [
        name
        for name in columns_of_type(df, CATEGORICAL)
        if 1 < df[name].nunique(dropna=True) <= 50
    ]
    candidates.sort(key=lambda name: df[name].nunique(dropna=True))
    for name in candidates[:MAX_BAR_CHARTS]:
        counts = df[name].value_counts().head(TOP_CATEGORIES)
        if counts.empty:
            continue
        charts.append(
            {
                "id": f"bar-{name}",
                "type": "bar",
                "title": f"Most common values in {name}",
                "description": f"Row counts for the top {len(counts)} values of {name}.",
                "x_label": name,
                "y_label": "Rows",
                "column": name,
                "data": [
                    {
                        "category": stringify_value(value),
                        "count": int(count),
                        "pct": percentage(int(count), total_rows),
                    }
                    for value, count in counts.items()
                ],
            }
        )
    return charts


def _box_plot(df: pd.DataFrame, summary: dict) -> dict | None:
    """One box-plot summary row per numeric column, from the computed quartiles."""
    stats = summary.get("numeric_statistics", {})
    data = [
        {
            "column": name,
            "min": values["min"],
            "q1": values["q1"],
            "median": values["median"],
            "q3": values["q3"],
            "max": values["max"],
        }
        for name, values in stats.items()
        if values.get("count") and values.get("q1") is not None
    ]
    if not data:
        return None
    return {
        "id": "box-numeric",
        "type": "box",
        "title": "Spread of numeric columns",
        "description": "Minimum, quartiles, median and maximum for each numeric column.",
        "x_label": "Column",
        "y_label": "Value",
        "column": None,
        "data": data,
    }


def _scatter_for_top_correlation(df: pd.DataFrame, summary: dict) -> dict | None:
    pairs = summary.get("correlation", {}).get("strong_pairs", [])
    if not pairs:
        return None
    pair = pairs[0]
    left, right = pair["column_a"], pair["column_b"]
    if left not in df.columns or right not in df.columns:
        return None
    subset = df[[left, right]].dropna()
    if subset.empty:
        return None
    if len(subset) > MAX_SCATTER_POINTS:
        # Deterministic sample so repeated analyses of the same data agree.
        subset = subset.sample(MAX_SCATTER_POINTS, random_state=0)
    return {
        "id": f"scatter-{left}-{right}",
        "type": "scatter",
        "title": f"{left} vs {right}",
        "description": (
            f"The most strongly correlated numeric pair (r = {pair['correlation']}). "
            "Association only; this does not show causation."
        ),
        "x_label": left,
        "y_label": right,
        "column": None,
        "data": [
            {"x": round_or_none(x), "y": round_or_none(y)}
            for x, y in zip(subset[left], subset[right])
        ],
    }


def _correlation_heatmap(summary: dict) -> dict | None:
    correlation = summary.get("correlation", {})
    columns = correlation.get("columns", [])[:MAX_HEATMAP_COLUMNS]
    if len(columns) < 2:
        return None
    matrix = correlation.get("matrix", [])
    cells = [
        {"x": columns[col], "y": columns[row], "value": matrix[row][col]}
        for row in range(len(columns))
        for col in range(len(columns))
    ]
    return {
        "id": "heatmap-correlation",
        "type": "heatmap",
        "title": "Correlation between numeric columns",
        "description": "Pearson correlation, from -1 (opposite) through 0 (unrelated) to 1 (aligned).",
        "x_label": "Column",
        "y_label": "Column",
        "column": None,
        "data": cells,
        "meta": {"columns": columns},
    }


def _time_series(df: pd.DataFrame) -> dict | None:
    """Row volume over time, when the dataset has a usable date column."""
    datetime_columns = columns_of_type(df, DATETIME)
    numeric_columns = _numeric_columns_by_variation(df)
    if not datetime_columns:
        return None
    time_column = datetime_columns[0]
    subset = df[[time_column]].dropna()
    if subset.empty:
        return None
    freq = _time_frequency(subset[time_column])
    grouped = subset.set_index(time_column).resample(freq).size()
    value_column = None
    if numeric_columns:
        value_column = numeric_columns[0]
        averaged = (
            df[[time_column, value_column]]
            .dropna()
            .set_index(time_column)
            .resample(freq)[value_column]
            .mean()
        )
    data = []
    for period, count in grouped.items():
        point = {"period": pd.Timestamp(period).date().isoformat(), "rows": int(count)}
        if value_column is not None:
            point["value"] = round_or_none(averaged.get(period))
        data.append(point)
    return {
        "id": f"timeseries-{time_column}",
        "type": "timeseries",
        "title": f"Records over time by {time_column}",
        "description": (
            f"Rows per {freq.lower()} period"
            + (f", with the mean of {value_column}." if value_column else ".")
        ),
        "x_label": time_column,
        "y_label": "Rows",
        "column": time_column,
        "data": data,
        "meta": {"value_column": value_column},
    }


def _time_frequency(series: pd.Series) -> str:
    span_days = (series.max() - series.min()).days
    if span_days <= 31:
        return "D"
    if span_days <= 400:
        return "ME"
    return "YE"
