def test_analysis_can_be_created(client, uploaded_dataset):
    response = client.post(f"/api/datasets/{uploaded_dataset['id']}/analyze")

    assert response.status_code == 201
    body = response.json()
    assert body["summary"]["overview"]["rows"] == 6
    assert body["summary"]["numeric_statistics"]["monthly_spend"]["count"] == 6


def test_repeat_analysis_reuses_the_stored_result(client, uploaded_dataset):
    first = client.post(f"/api/datasets/{uploaded_dataset['id']}/analyze").json()
    second = client.post(f"/api/datasets/{uploaded_dataset['id']}/analyze").json()

    assert first["id"] == second["id"]


def test_forced_analysis_creates_a_new_record(client, uploaded_dataset):
    first = client.post(f"/api/datasets/{uploaded_dataset['id']}/analyze").json()
    second = client.post(f"/api/datasets/{uploaded_dataset['id']}/analyze?force=true").json()

    assert second["id"] != first["id"]


def test_analysis_can_be_retrieved_after_creation(client, uploaded_dataset):
    client.post(f"/api/datasets/{uploaded_dataset['id']}/analyze")

    response = client.get(f"/api/datasets/{uploaded_dataset['id']}/analysis")

    assert response.status_code == 200
    assert response.json()["dataset_id"] == uploaded_dataset["id"]


def test_retrieving_analysis_before_running_it_returns_an_error(client, uploaded_dataset):
    response = client.get(f"/api/datasets/{uploaded_dataset['id']}/analysis")

    assert response.status_code == 404
    assert response.json()["error"] == "ANALYSIS_NOT_FOUND"


def test_insights_endpoint_returns_generated_findings(client, uploaded_dataset):
    client.post(f"/api/datasets/{uploaded_dataset['id']}/analyze")

    response = client.get(f"/api/datasets/{uploaded_dataset['id']}/insights")

    assert response.status_code == 200
    for insight in response.json():
        assert insight["title"] and insight["description"] and insight["metric"]


def test_visualizations_endpoint_returns_plottable_charts(client, uploaded_dataset):
    client.post(f"/api/datasets/{uploaded_dataset['id']}/analyze")

    charts = client.get(f"/api/datasets/{uploaded_dataset['id']}/visualizations").json()

    assert charts
    for chart in charts:
        assert chart["title"]
        assert isinstance(chart["data"], list)


def test_analysis_on_another_users_dataset_is_not_found(client, uploaded_dataset):
    response = client.post(
        f"/api/datasets/{uploaded_dataset['id']}/analyze",
        headers={"X-User-Email": "other@user.test"},
    )

    assert response.status_code == 404
