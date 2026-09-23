"""Frequency analysis for categorical and boolean columns."""

from __future__ import annotations

import pandas as pd

from app.analysis.profiler import BOOLEAN, CATEGORICAL, columns_of_type
from app.analysis.utils import percentage, stringify_value

TOP_VALUES = 10


def categorical_analysis(df: pd.DataFrame, top_n: int = TOP_VALUES) -> dict[str, dict]:
    total_rows = len(df)
    results: dict[str, dict] = {}
    targets = columns_of_type(df, CATEGORICAL) + columns_of_type(df, BOOLEAN)
    for name in targets:
        series = df[name].dropna()
        counts = series.value_counts()
        top_values = [
            {
                "value": stringify_value(value),
                "count": int(count),
                "pct": percentage(int(count), total_rows),
            }
            for value, count in counts.head(top_n).items()
        ]
        results[name] = {
            "unique_count": int(counts.size),
            "top_values": top_values,
            "dominant_value": top_values[0]["value"] if top_values else None,
            "dominant_pct": top_values[0]["pct"] if top_values else 0.0,
            "covered_pct": round(sum(item["pct"] for item in top_values), 2),
        }
    return results
