"""Dataset overview: shape, memory, column types."""

from __future__ import annotations

import pandas as pd
from pandas.api import types as ptypes

from app.analysis.utils import human_bytes, percentage

NUMERIC = "numeric"
CATEGORICAL = "categorical"
DATETIME = "datetime"
BOOLEAN = "boolean"


def is_text_dtype(series: pd.Series) -> bool:
    """True for free-text columns.

    pandas 2 stores strings as ``object``; pandas 3 uses a dedicated ``str``
    dtype. Both are the same thing for analysis purposes.
    """
    return ptypes.is_object_dtype(series) or ptypes.is_string_dtype(series)


def classify_column(series: pd.Series) -> str:
    """Map a pandas dtype onto the four types the product reasons about."""
    if ptypes.is_bool_dtype(series):
        return BOOLEAN
    if ptypes.is_datetime64_any_dtype(series):
        return DATETIME
    if ptypes.is_numeric_dtype(series):
        return NUMERIC
    return CATEGORICAL


def column_types(df: pd.DataFrame) -> dict[str, str]:
    return {str(name): classify_column(df[name]) for name in df.columns}


def columns_of_type(df: pd.DataFrame, wanted: str) -> list[str]:
    return [name for name, kind in column_types(df).items() if kind == wanted]


def build_column_profiles(df: pd.DataFrame) -> list[dict]:
    """Per-column metadata used by both the preview and the analysis views."""
    total_rows = len(df)
    types = column_types(df)
    profiles = []
    for name in df.columns:
        series = df[name]
        missing = int(series.isna().sum())
        profiles.append(
            {
                "name": str(name),
                "dtype": str(series.dtype),
                "inferred_type": types[str(name)],
                "non_null_count": int(total_rows - missing),
                "missing_count": missing,
                "missing_pct": percentage(missing, total_rows),
                "unique_count": int(series.nunique(dropna=True)),
            }
        )
    return profiles


def build_overview(df: pd.DataFrame) -> dict:
    types = column_types(df)
    memory_bytes = int(df.memory_usage(deep=True).sum())
    return {
        "rows": int(len(df)),
        "columns": int(df.shape[1]),
        "memory_usage_bytes": memory_bytes,
        "memory_usage_human": human_bytes(memory_bytes),
        "numeric_columns": [name for name, kind in types.items() if kind == NUMERIC],
        "categorical_columns": [name for name, kind in types.items() if kind == CATEGORICAL],
        "datetime_columns": [name for name, kind in types.items() if kind == DATETIME],
        "boolean_columns": [name for name, kind in types.items() if kind == BOOLEAN],
    }
