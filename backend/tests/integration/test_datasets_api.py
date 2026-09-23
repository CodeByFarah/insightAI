from tests.conftest import SAMPLE_CSV


def test_upload_returns_dataset_metadata(client):
    response = client.post(
        "/api/datasets", files={"file": ("customers.csv", SAMPLE_CSV, "text/csv")}
    )

    assert response.status_code == 201
    body = response.json()
    assert body["filename"] == "customers.csv"
    assert body["row_count"] == 6
    assert body["column_count"] == 5


def test_upload_rejects_non_csv_files(client):
    response = client.post(
        "/api/datasets", files={"file": ("script.exe", b"MZ\x00binary", "application/octet-stream")}
    )

    assert response.status_code == 400
    assert response.json()["error"] == "INVALID_FILE"


def test_upload_rejects_a_file_above_the_size_limit(client):
    oversized = ("a,b\n" + "1,2\n" * 2_000_000).encode()

    response = client.post(
        "/api/datasets", files={"file": ("big.csv", oversized, "text/csv")}
    )

    assert response.status_code == 413
    assert response.json()["error"] == "FILE_TOO_LARGE"


def test_upload_rejects_a_csv_with_too_little_data(client):
    response = client.post(
        "/api/datasets", files={"file": ("tiny.csv", b"a,b\n", "text/csv")}
    )

    assert response.status_code == 400
    assert response.json()["error"] == "INVALID_DATASET"


def test_listing_returns_uploaded_datasets(client, uploaded_dataset):
    response = client.get("/api/datasets")

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [uploaded_dataset["id"]]


def test_dataset_detail_is_returned(client, uploaded_dataset):
    response = client.get(f"/api/datasets/{uploaded_dataset['id']}")

    assert response.status_code == 200
    assert response.json()["filename"] == "customers.csv"


def test_missing_dataset_returns_a_structured_error(client):
    response = client.get("/api/datasets/9999")

    assert response.status_code == 404
    assert response.json() == {
        "error": "NOT_FOUND",
        "message": "Dataset 9999 was not found.",
    }


def test_a_user_cannot_read_another_users_dataset(client, uploaded_dataset):
    response = client.get(
        f"/api/datasets/{uploaded_dataset['id']}", headers={"X-User-Email": "someone@else.test"}
    )

    assert response.status_code == 404


def test_preview_returns_rows_and_column_profiles(client, uploaded_dataset):
    response = client.get(f"/api/datasets/{uploaded_dataset['id']}/preview?rows=3")

    assert response.status_code == 200
    body = response.json()
    assert len(body["rows"]) == 3
    assert {column["name"] for column in body["columns"]} == {
        "customer_id",
        "age",
        "monthly_spend",
        "plan",
        "signup_date",
    }
    assert body["total_missing"] == 1


def test_delete_removes_the_dataset(client, uploaded_dataset):
    assert client.delete(f"/api/datasets/{uploaded_dataset['id']}").status_code == 204
    assert client.get(f"/api/datasets/{uploaded_dataset['id']}").status_code == 404


def test_dashboard_counts_datasets_and_analyses(client, uploaded_dataset):
    client.post(f"/api/datasets/{uploaded_dataset['id']}/analyze")

    body = client.get("/api/dashboard").json()

    assert body["dataset_count"] == 1
    assert body["analysis_count"] == 1
    assert body["most_recent_dataset"]["id"] == uploaded_dataset["id"]
    assert body["ai_enabled"] is False
