"""Multivariate anomaly detection.

The IQR check in ``statistics`` looks at one column at a time. A row can be
unremarkable in every single column yet still be an unusual *combination* --
an isolation forest is the standard way to find those, and it is the one place
in the engine where scikit-learn earns its place.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from app.analysis.profiler import NUMERIC, columns_of_type
from app.analysis.utils import percentage

logger = logging.getLogger(__name__)

MIN_ROWS = 50
MIN_COLUMNS = 2
CONTAMINATION = 0.02
RANDOM_STATE = 0


def anomaly_summary(df: pd.DataFrame) -> dict:
    """Flag rows that are unusual across the numeric columns taken together."""
    numeric_columns = [
        name for name in columns_of_type(df, NUMERIC) if df[name].nunique(dropna=True) > 1
    ]
    if len(df) < MIN_ROWS or len(numeric_columns) < MIN_COLUMNS:
        return _not_applicable(numeric_columns)

    subset = df[numeric_columns].dropna()
    if len(subset) < MIN_ROWS:
        return _not_applicable(numeric_columns)

    try:
        from sklearn.ensemble import IsolationForest
        from sklearn.preprocessing import StandardScaler
    except ImportError:  # pragma: no cover - depends on the environment
        logger.warning("scikit-learn is unavailable; skipping anomaly detection")
        return _not_applicable(numeric_columns)

    scaled = StandardScaler().fit_transform(subset.to_numpy(dtype=float))
    model = IsolationForest(
        contamination=CONTAMINATION, random_state=RANDOM_STATE, n_estimators=100
    )
    labels = model.fit_predict(scaled)
    flagged = int(np.sum(labels == -1))

    return {
        "applicable": True,
        "method": "isolation forest",
        "columns": numeric_columns,
        "rows_considered": int(len(subset)),
        "anomalous_rows": flagged,
        "anomalous_pct": percentage(flagged, int(len(subset))),
    }


def _not_applicable(numeric_columns: list[str]) -> dict:
    return {
        "applicable": False,
        "method": "isolation forest",
        "columns": numeric_columns,
        "reason": (
            f"Needs at least {MIN_ROWS} complete rows across {MIN_COLUMNS} numeric columns."
        ),
        "rows_considered": 0,
        "anomalous_rows": 0,
        "anomalous_pct": 0.0,
    }
