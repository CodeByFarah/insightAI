import pytest

from app.core.errors import InvalidFileError
from app.services.storage import build_storage_key, sanitize_filename, storage_path, validate_upload


def test_path_traversal_is_stripped_from_filenames():
    assert sanitize_filename("../../etc/passwd") == "passwd"


def test_filename_keeps_only_safe_characters():
    assert sanitize_filename("my report (final).csv") == "my_report__final_.csv"


def test_blank_filename_falls_back_to_a_default():
    assert sanitize_filename("") == "upload.csv"


def test_non_csv_extension_is_rejected():
    with pytest.raises(InvalidFileError):
        validate_upload("payload.exe", "application/octet-stream")


def test_csv_upload_is_accepted():
    assert validate_upload("customers.csv", "text/csv") == "customers.csv"


def test_unexpected_content_type_is_rejected():
    with pytest.raises(InvalidFileError):
        validate_upload("customers.csv", "image/png")


def test_storage_key_is_generated_not_taken_from_the_client():
    key = build_storage_key("customers.csv")

    assert key.endswith(".csv")
    assert "customers" not in key


def test_storage_path_stays_inside_the_storage_directory():
    root = storage_path("abc.csv").parent

    assert storage_path("../../abc.csv").parent == root
