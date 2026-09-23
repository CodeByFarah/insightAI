"""Pearson correlation between numeric columns.

Correlation describes how two columns move together. It does not establish
that one causes the other, and nothing in this module claims that it does.
"""

from __future__ import annotations

import pandas as pd

from app.analysis.profiler import NUMERIC, columns_of_type
from app.analysis.utils import round_or_none

STRONG_THRESHOLD = 0.7
MAX_PAIRS = 10


def correlation_analysis(df: pd.DataFrame, threshold: float = STRONG_THRESHOLD) -> dict:
    numeric_columns = [
        name for name in columns_of_type(df, NUMERIC) if df[name].nunique(dropna=True) > 1
    ]
    if len(numeric_columns) < 2:
        return {"columns": [], "matrix": [], "strong_pairs": [], "threshold": threshold}

    matrix = df[numeric_columns].corr(method="pearson", numeric_only=True)
    return {
        "columns": [str(name) for name in matrix.columns],
        "matrix": [[round_or_none(value) for value in row] for row in matrix.to_numpy()],
        "strong_pairs": find_strong_pairs(matrix, threshold),
        "threshold": threshold,
        "method": "pearson",
    }


def find_strong_pairs(matrix: pd.DataFrame, threshold: float = STRONG_THRESHOLD) -> list[dict]:
    """Unique column pairs whose absolute correlation reaches the threshold."""
    pairs = []
    names = list(matrix.columns)
    for i, left in enumerate(names):
        for right in names[i + 1 :]:
            value = matrix.at[left, right]
            if pd.isna(value) or abs(value) < threshold:
                continue
            pairs.append(
                {
                    "column_a": str(left),
                    "column_b": str(right),
                    "correlation": round_or_none(value),
                    "direction": "positive" if value > 0 else "negative",
                }
            )
    pairs.sort(key=lambda pair: abs(pair["correlation"] or 0), reverse=True)
    return pairs[:MAX_PAIRS]
