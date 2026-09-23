import io

import pandas as pd
import pytest

from app.core.errors import InvalidDatasetError, InvalidFileError
from app.services.csv_loader import (
    infer_datetime_columns,
    load_csv_bytes,
    validate_dataframe,
)


def test_valid_csv_is_parsed():
    df = load_csv_bytes(b"a,b\n1,x\n2,y\n")

    assert list(df.columns) == ["a", "b"]
    assert len(df) == 2


def test_empty_file_is_rejected():
    with pytest.raises(InvalidFileError):
        load_csv_bytes(b"   \n")


def test_header_only_file_is_rejected_as_too_small():
    with pytest.raises(InvalidDatasetError):
        load_csv_bytes(b"a,b\n")


def test_duplicate_column_names_are_rejected():
    df = pd.DataFrame([[1, 2], [3, 4]], columns=["a", "a"])

    with pytest.raises(InvalidDatasetError):
        validate_dataframe(df)


def test_column_names_are_trimmed():
    df = load_csv_bytes(b" a , b \n1,2\n3,4\n")

    assert list(df.columns) == ["a", "b"]


def test_date_columns_are_converted():
    df = load_csv_bytes(b"day,value\n2024-01-01,1\n2024-02-01,2\n2024-03-01,3\n")

    assert pd.api.types.is_datetime64_any_dtype(df["day"])


def test_plain_text_columns_are_left_alone():
    df = pd.DataFrame({"name": ["alpha", "beta", "gamma"]})

    assert not pd.api.types.is_datetime64_any_dtype(infer_datetime_columns(df)["name"])


def test_numeric_looking_text_is_not_converted_to_dates():
    df = pd.DataFrame({"code": ["1", "2", "3"]})

    assert not pd.api.types.is_datetime64_any_dtype(infer_datetime_columns(df)["code"])
