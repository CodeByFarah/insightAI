"""Descriptive statistics and outlier detection for numeric columns."""

from __future__ import annotations

import pandas as pd

from app.analysis.profiler import columns_of_type, NUMERIC
from app.analysis.utils import percentage, round_or_none

IQR_MULTIPLIER = 1.5


def numeric_statistics(df: pd.DataFrame) -> dict[str, dict]:
    """count / mean / median / std / min / max / quartiles per numeric column."""
    stats: dict[str, dict] = {}
    for name in columns_of_type(df, NUMERIC):
        series = df[name].dropna()
        if series.empty:
            stats[name] = _empty_stats()
            continue
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        stats[name] = {
            "count": int(series.count()),
            "mean": round_or_none(series.mean()),
            "median": round_or_none(series.median()),
            "std": round_or_none(series.std()),
            "min": round_or_none(series.min()),
            "max": round_or_none(series.max()),
            "q1": round_or_none(q1),
            "q3": round_or_none(q3),
            "iqr": round_or_none(q3 - q1),
            "skew": round_or_none(series.skew()) if series.count() > 2 else None,
        }
    return stats


def _empty_stats() -> dict:
    keys = ("mean", "median", "std", "min", "max", "q1", "q3", "iqr", "skew")
    return {"count": 0, **{key: None for key in keys}}


def outlier_summary(df: pd.DataFrame) -> dict[str, dict]:
    """Count values outside the 1.5 x IQR fences, the standard box-plot rule."""
    summary: dict[str, dict] = {}
    for name in columns_of_type(df, NUMERIC):
        series = df[name].dropna()
        if series.count() < 4:
            continue
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            continue
        lower = q1 - IQR_MULTIPLIER * iqr
        upper = q3 + IQR_MULTIPLIER * iqr
        count = int(((series < lower) | (series > upper)).sum())
        summary[name] = {
            "count": count,
            "pct": percentage(count, int(series.count())),
            "lower_bound": round_or_none(lower),
            "upper_bound": round_or_none(upper),
            "method": "1.5 x IQR",
        }
    return summary
