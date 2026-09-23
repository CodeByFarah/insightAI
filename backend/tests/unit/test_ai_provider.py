"""Provider behaviour, exercised through the mock so no network is touched."""

import pytest

from app.ai.mock_provider import MockAIProvider
from app.ai.provider import AIRequest, NullProvider
from app.core.errors import AIUnavailableError
from app.ai.gemini_provider import GeminiProvider


def make_request() -> AIRequest:
    return AIRequest(system_prompt="sys", context="ctx", history=(), question="What stands out?")


def test_mock_provider_returns_configured_answer():
    provider = MockAIProvider(response="Spend correlates with tenure.")

    assert provider.generate(make_request()) == "Spend correlates with tenure."


def test_mock_provider_records_the_request_it_received():
    provider = MockAIProvider()
    provider.generate(make_request())

    assert provider.requests[0].question == "What stands out?"


def test_mock_provider_can_simulate_a_timeout():
    provider = MockAIProvider(error=TimeoutError("deadline exceeded"))

    with pytest.raises(TimeoutError):
        provider.generate(make_request())


def test_mock_provider_rejects_an_empty_response():
    provider = MockAIProvider(response="   ")

    with pytest.raises(AIUnavailableError):
        provider.generate(make_request())


def test_null_provider_is_never_available():
    assert NullProvider().is_available() is False


def test_gemini_provider_without_a_key_is_unavailable():
    assert GeminiProvider(api_key="", model="gemini-2.0-flash").is_available() is False


def test_gemini_provider_without_a_key_raises_a_safe_error():
    with pytest.raises(AIUnavailableError) as error:
        GeminiProvider(api_key="", model="gemini-2.0-flash").generate(make_request())

    assert "GEMINI_API_KEY" in str(error.value)


@pytest.mark.parametrize(
    ("message", "expected_fragment"),
    [
        ("Request timed out", "did not respond in time"),
        ("429 rate limit exceeded", "request limit"),
        ("Invalid API key provided", "not configured correctly"),
        ("upstream exploded", "currently unavailable"),
    ],
)
def test_gemini_errors_become_safe_user_messages(message, expected_fragment):
    translated = GeminiProvider._translate(RuntimeError(message))

    assert expected_fragment in translated.message
    assert message not in translated.message
