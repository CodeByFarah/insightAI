"""Reading uploaded CSVs into pandas DataFrames."""

from __future__ import annotations

import io
import logging
from pathlib import Path

import pandas as pd

from app.analysis.profiler import is_text_dtype
from app.core.config import get_settings
from app.core.errors import InvalidDatasetError, InvalidFileError

logger = logging.getLogger(__name__)

DATETIME_PARSE_THRESHOLD = 0.95
MIN_ROWS_FOR_ANALYSIS = 2


def load_csv_bytes(content: bytes) -> pd.DataFrame:
    """Parse raw upload bytes, raising a user-safe error when it is not a CSV."""
    if not content.strip():
        raise InvalidFileError("The uploaded file is empty.")
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            text = content.decode("latin-1")
        except UnicodeDecodeError as exc:
            raise InvalidFileError("The file is not readable as text.") from exc
    return _read_frame(io.StringIO(text))


def load_csv_file(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise InvalidDatasetError("The stored file for this dataset is missing.")
    return load_csv_bytes(path.read_bytes())


def _read_frame(buffer: io.StringIO) -> pd.DataFrame:
    settings = get_settings()
    try:
        df = pd.read_csv(buffer, nrows=settings.max_analysis_rows, skip_blank_lines=True)
    except pd.errors.EmptyDataError as exc:
        raise InvalidFileError("The CSV has no columns to read.") from exc
    except pd.errors.ParserError as exc:
        logger.info("CSV parse failure: %s", exc)
        raise InvalidFileError("The CSV could not be parsed. Check the delimiter and quoting.") from exc

    df = df.rename(columns=lambda name: str(name).strip())
    validate_dataframe(df)
    return infer_datetime_columns(df)


def validate_dataframe(df: pd.DataFrame) -> None:
    if df.shape[1] == 0:
        raise InvalidDatasetError("The CSV does not contain any columns.")
    if len(df) < MIN_ROWS_FOR_ANALYSIS:
        raise InvalidDatasetError(
            "The uploaded CSV does not contain enough valid data for analysis "
            f"(at least {MIN_ROWS_FOR_ANALYSIS} data rows are required)."
        )
    if len(set(df.columns)) != len(df.columns):
        raise InvalidDatasetError("The CSV contains duplicate column names.")


def infer_datetime_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Convert text columns to datetimes when nearly every value parses.

    pandas leaves dates as strings by default. Converting them here is what
    makes time-series analysis possible; the threshold keeps the conversion
    conservative so ordinary text is never silently reinterpreted.
    """
    for name in df.columns:
        series = df[name]
        if not is_text_dtype(series):
            continue
        non_null = series.dropna()
        if non_null.empty or pd.to_numeric(non_null, errors="coerce").notna().any():
            continue
        try:
            parsed = pd.to_datetime(series, errors="coerce", format="mixed")
        except (ValueError, TypeError):
            continue
        parsed_ratio = parsed.notna().sum() / max(len(non_null), 1)
        if parsed_ratio >= DATETIME_PARSE_THRESHOLD:
            df[name] = parsed
    return df
