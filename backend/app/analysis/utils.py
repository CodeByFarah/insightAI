"""Small helpers shared by the analysis modules."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

BYTE_UNITS = ("B", "KB", "MB", "GB", "TB")


def to_native(value: Any) -> Any:
    """Convert numpy/pandas scalars to JSON-serialisable Python values.

    NaN and infinity become None: they are not valid JSON and a null reads
    correctly as "no value" on the client.
    """
    if value is None or value is pd.NaT:
        return None
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        number = float(value)
        return None if math.isnan(number) or math.isinf(number) else number
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()
    if isinstance(value, np.ndarray):
        return [to_native(item) for item in value.tolist()]
    if isinstance(value, dict):
        return {str(key): to_native(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_native(item) for item in value]
    if pd.isna(value) if np.isscalar(value) else False:
        return None
    return value


def jsonify(payload: Any) -> Any:
    """Recursively make a structure safe to store as JSON."""
    return to_native(payload)


def round_or_none(value: Any, digits: int = 4) -> float | None:
    native = to_native(value)
    if native is None or isinstance(native, bool):
        return None
    try:
        return round(float(native), digits)
    except (TypeError, ValueError):
        return None


def percentage(part: float, whole: float, digits: int = 2) -> float:
    """Percentage of ``part`` within ``whole``; 0.0 when ``whole`` is zero."""
    if not whole:
        return 0.0
    return round((part / whole) * 100, digits)


def human_bytes(num_bytes: float) -> str:
    size = float(num_bytes)
    for unit in BYTE_UNITS:
        if size < 1024 or unit == BYTE_UNITS[-1]:
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return f"{size:.1f} TB"


def stringify_value(value: Any) -> str:
    """Render a categorical value for display, keeping missing values explicit."""
    native = to_native(value)
    if native is None:
        return "(missing)"
    return str(native)
