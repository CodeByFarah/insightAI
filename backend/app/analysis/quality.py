"""Data-quality checks: missing values, duplicates, constants, suspect types."""

from __future__ import annotations

import pandas as pd

from app.analysis.profiler import CATEGORICAL, classify_column, is_text_dtype
from app.analysis.utils import percentage

HIGH_CARDINALITY_RATIO = 0.9
NUMERIC_PARSE_THRESHOLD = 0.9
DATETIME_PARSE_THRESHOLD = 0.9


def assess_quality(df: pd.DataFrame) -> dict:
    total_rows = len(df)
    total_cells = total_rows * df.shape[1]
    missing_per_column = df.isna().sum()
    duplicate_rows = int(df.duplicated().sum())

    columns = [
        {
            "name": str(name),
            "missing_count": int(missing_per_column[name]),
            "missing_pct": percentage(int(missing_per_column[name]), total_rows),
            "unique_count": int(df[name].nunique(dropna=True)),
        }
        for name in df.columns
    ]

    return {
        "total_missing": int(missing_per_column.sum()),
        "missing_pct": percentage(int(missing_per_column.sum()), total_cells),
        "duplicate_rows": duplicate_rows,
        "duplicate_pct": percentage(duplicate_rows, total_rows),
        "constant_columns": find_constant_columns(df),
        "high_cardinality_columns": find_high_cardinality_columns(df),
        "suspicious_types": find_suspicious_types(df),
        "columns": columns,
    }


def find_constant_columns(df: pd.DataFrame) -> list[str]:
    """Columns holding a single value carry no information for analysis."""
    return [str(name) for name in df.columns if df[name].nunique(dropna=True) <= 1]


def find_high_cardinality_columns(df: pd.DataFrame) -> list[dict]:
    """Text columns that are nearly unique per row look like identifiers."""
    total_rows = len(df)
    if total_rows == 0:
        return []
    results = []
    for name in df.columns:
        if classify_column(df[name]) != CATEGORICAL:
            continue
        unique = int(df[name].nunique(dropna=True))
        ratio = unique / total_rows
        if ratio >= HIGH_CARDINALITY_RATIO and unique > 1:
            results.append(
                {
                    "name": str(name),
                    "unique_count": unique,
                    "unique_ratio": round(ratio, 4),
                }
            )
    return results


def find_suspicious_types(df: pd.DataFrame) -> list[dict]:
    """Text columns whose values almost all parse as numbers or dates."""
    findings = []
    for name in df.columns:
        series = df[name]
        if not is_text_dtype(series) and not isinstance(series.dtype, pd.CategoricalDtype):
            continue
        non_null = series.dropna().astype(str)
        if non_null.empty:
            continue
        numeric_ratio = pd.to_numeric(non_null, errors="coerce").notna().mean()
        if numeric_ratio >= NUMERIC_PARSE_THRESHOLD:
            findings.append(
                {
                    "name": str(name),
                    "detected_type": str(series.dtype),
                    "suggested_type": "numeric",
                    "match_ratio": round(float(numeric_ratio), 4),
                }
            )
            continue
        datetime_ratio = _datetime_parse_ratio(non_null)
        if datetime_ratio >= DATETIME_PARSE_THRESHOLD:
            findings.append(
                {
                    "name": str(name),
                    "detected_type": str(series.dtype),
                    "suggested_type": "datetime",
                    "match_ratio": round(float(datetime_ratio), 4),
                }
            )
    return findings


def _datetime_parse_ratio(values: pd.Series) -> float:
    try:
        parsed = pd.to_datetime(values, errors="coerce", format="mixed")
    except (ValueError, TypeError):
        return 0.0
    return float(parsed.notna().mean())
