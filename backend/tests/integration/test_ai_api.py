"""AI endpoint behaviour. No test here reaches the real Gemini API."""

from app.ai.mock_provider import MockAIProvider
from app.core.errors import AIUnavailableError


def analyzed(client, dataset):
    client.post(f"/api/datasets/{dataset['id']}/analyze")
    return dataset["id"]


def test_ai_status_reports_disabled_without_a_key(client):
    body = client.get("/api/ai/status").json()

    assert body["enabled"] is False
    assert "still available" in body["message"]


def test_chat_returns_an_answer_from_the_provider(client, uploaded_dataset, mock_provider):
    dataset_id = analyzed(client, uploaded_dataset)

    response = client.post(
        f"/api/datasets/{dataset_id}/ai/chat", json={"question": "What stands out?"}
    )

    assert response.status_code == 200
    assert response.json()["answer"]["content"] == mock_provider._response
    assert response.json()["answer"]["role"] == "assistant"


def test_chat_sends_the_analysis_context_not_the_raw_rows(
    client, uploaded_dataset, mock_provider
):
    dataset_id = analyzed(client, uploaded_dataset)

    client.post(f"/api/datasets/{dataset_id}/ai/chat", json={"question": "Summarise this"})

    context = mock_provider.requests[0].context
    assert "numeric_statistics" in context
    assert "C1" not in context  # no individual customer row reaches the model


def test_chat_system_prompt_forbids_invented_values(client, uploaded_dataset, mock_provider):
    dataset_id = analyzed(client, uploaded_dataset)

    client.post(f"/api/datasets/{dataset_id}/ai/chat", json={"question": "Summarise this"})

    assert "Never invent values" in mock_provider.requests[0].system_prompt


def test_conversation_history_is_persisted(client, uploaded_dataset, mock_provider):
    dataset_id = analyzed(client, uploaded_dataset)
    client.post(f"/api/datasets/{dataset_id}/ai/chat", json={"question": "First question"})

    messages = client.get(f"/api/datasets/{dataset_id}/ai/messages").json()["messages"]

    assert [message["role"] for message in messages] == ["user", "assistant"]
    assert messages[0]["content"] == "First question"


def test_chat_without_a_configured_key_returns_a_helpful_message(client, uploaded_dataset):
    dataset_id = analyzed(client, uploaded_dataset)

    response = client.post(
        f"/api/datasets/{dataset_id}/ai/chat", json={"question": "What stands out?"}
    )

    assert response.status_code == 503
    assert response.json()["error"] == "AI_UNAVAILABLE"
    assert "still available" in response.json()["message"]


def test_chat_before_analysis_is_refused(client, uploaded_dataset, mock_provider):
    response = client.post(
        f"/api/datasets/{uploaded_dataset['id']}/ai/chat", json={"question": "What stands out?"}
    )

    assert response.status_code == 404
    assert response.json()["error"] == "ANALYSIS_NOT_FOUND"


def test_a_provider_timeout_is_reported_as_unavailable(client, uploaded_dataset, use_provider):
    use_provider(MockAIProvider(error=AIUnavailableError("The AI assistant did not respond in time.")))
    dataset_id = analyzed(client, uploaded_dataset)

    response = client.post(
        f"/api/datasets/{dataset_id}/ai/chat", json={"question": "What stands out?"}
    )

    assert response.status_code == 503
    assert response.json()["message"] == "The AI assistant did not respond in time."


def test_an_empty_provider_response_is_reported_safely(client, uploaded_dataset, use_provider):
    use_provider(MockAIProvider(response="  "))
    dataset_id = analyzed(client, uploaded_dataset)

    response = client.post(
        f"/api/datasets/{dataset_id}/ai/chat", json={"question": "What stands out?"}
    )

    assert response.status_code == 503
    assert "empty response" in response.json()["message"]


def test_an_unexpected_provider_crash_does_not_leak_internals(
    client, uploaded_dataset, use_provider
):
    use_provider(MockAIProvider(error=RuntimeError("secret-token=abc123 blew up")))
    dataset_id = analyzed(client, uploaded_dataset)

    response = client.post(
        f"/api/datasets/{dataset_id}/ai/chat", json={"question": "What stands out?"}
    )

    assert response.status_code == 500
    assert "secret-token" not in response.text
    assert response.json()["error"] == "INTERNAL_ERROR"


def test_a_blank_question_is_rejected(client, uploaded_dataset, mock_provider):
    dataset_id = analyzed(client, uploaded_dataset)

    response = client.post(f"/api/datasets/{dataset_id}/ai/chat", json={"question": " "})

    assert response.status_code == 422
    assert response.json()["error"] == "VALIDATION_ERROR"
