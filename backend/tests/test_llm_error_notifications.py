"""Unit tests for OpenRouter error classification, diagnostics, and account switching.

Validates that OpenRouter errors are accurately classified into:
  - HTTP 401: Invalid API key (auth_invalid_key)
  - HTTP 402: Account quota/credits depleted (account_quota_exceeded)
  - HTTP 429 (Upstream): Model provider overloaded (upstream_provider_overloaded)
  - HTTP 429 (Platform): Account/platform rate or credit limit (account_quota_exceeded)
  - HTTP 502/503: Service/provider temporarily unavailable (service_unavailable)
  - Network error: Connection failure (network_error)
  - Timeout: Request timed out (timeout)
And that deterministic analysis data is never destroyed when LLM fails.
"""

import httpx
import pytest
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    RateLimitError,
)
from sqlalchemy.orm import Session

from app.config import Settings, settings
from app.services.llm.client import OpenRouterClient, build_llm_error_payload
from app.services.llm.exceptions import (
    LLMAuthenticationError,
    LLMConnectionError,
    LLMProviderUnavailableError,
    LLMQuotaExceededError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from app.services.llm.schemas import EvidenceSummary
from app.models.project import Project
from app.services.ai_assistance.service import AIAssistanceService
from app.services.innovation.service import InnovationService


def _dummy_evidence() -> EvidenceSummary:
    return EvidenceSummary(
        project_id="test-proj",
        rules_version="v1.0-deterministic",
        advisory_category="Deterministic Evidence Present",
        evidence_signals=[],
    )


def _client_with_chat_raising(error: Exception) -> OpenRouterClient:
    client = OpenRouterClient.__new__(OpenRouterClient)
    client.enabled = True

    class FakeCompletions:
        def create(self, *args, **kwargs):
            raise error

    class FakeChat:
        completions = FakeCompletions()

    class FakeOpenAI:
        chat = FakeChat()

    client.client = FakeOpenAI()
    return client


# ---------------------------------------------------------------------------
# 1. Config & Account Switching (OPENROUTER_API_KEY support)
# ---------------------------------------------------------------------------


def test_config_supports_openrouter_api_key_and_llm_api_key():
    """Verify OPENROUTER_API_KEY is recognized and takes precedence or falls back."""
    s1 = Settings(LLM_ENABLED=True, OPENROUTER_API_KEY="sk-or-new-key", LLM_API_KEY=None)
    assert s1.api_key == "sk-or-new-key"
    assert s1.llm_configured is True

    s2 = Settings(LLM_ENABLED=True, OPENROUTER_API_KEY=None, LLM_API_KEY="sk-legacy-key")
    assert s2.api_key == "sk-legacy-key"
    assert s2.llm_configured is True

    s3 = Settings(LLM_ENABLED=True, OPENROUTER_API_KEY="  ", LLM_API_KEY="sk-fallback-key")
    assert s3.api_key == "sk-fallback-key"

    s4 = Settings(LLM_ENABLED=False, OPENROUTER_API_KEY="sk-key")
    assert s4.llm_configured is False


# ---------------------------------------------------------------------------
# 2. HTTP 401 — Invalid or Unauthorized API Key
# ---------------------------------------------------------------------------


def test_classify_401_authentication_error():
    req = httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")
    resp = httpx.Response(401, request=req)
    error = AuthenticationError("User key invalid", response=resp, body={"error": {"message": "Invalid API key"}})

    client = _client_with_chat_raising(error)
    with pytest.raises(LLMAuthenticationError) as exc_info:
        client.interpret_evidence(_dummy_evidence(), [])

    payload = build_llm_error_payload(exc_info.value)
    assert payload["error_type"] == "auth_invalid_key"
    assert payload["status_code"] == 401
    assert "invalid" in payload["user_message"].lower()
    assert "update the key" in payload["recommended_action"].lower()


# ---------------------------------------------------------------------------
# 3. HTTP 402 — Account Quota Exceeded / Payment Required
# ---------------------------------------------------------------------------


def test_classify_402_quota_exceeded():
    req = httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")
    resp = httpx.Response(402, request=req)
    error = APIStatusError(
        "Payment required",
        response=resp,
        body={"error": {"message": "Insufficient credits or payment required", "metadata": {"error_type": "insufficient_quota"}}},
    )

    client = _client_with_chat_raising(error)
    with pytest.raises(LLMQuotaExceededError) as exc_info:
        client.interpret_evidence(_dummy_evidence(), [])

    payload = build_llm_error_payload(exc_info.value)
    assert payload["error_type"] == "account_quota_exceeded"
    assert payload["status_code"] == 402
    assert "configure another authorized openrouter account" in payload["recommended_action"].lower()


# ---------------------------------------------------------------------------
# 4. HTTP 429 — Upstream Provider Overload vs Account Quota Limit
# ---------------------------------------------------------------------------


def test_classify_429_upstream_provider_overloaded():
    req = httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")
    resp = httpx.Response(429, request=req)
    error = RateLimitError(
        "Rate limit",
        response=resp,
        body={
            "error": {
                "message": "Upstream provider rate limit reached for model google/gemma-4-26b-a4b-it:free",
                "metadata": {"limit_source": "provider", "provider_code": "529"},
            }
        },
    )

    client = _client_with_chat_raising(error)
    with pytest.raises(LLMRateLimitError) as exc_info:
        client.interpret_evidence(_dummy_evidence(), [])

    payload = build_llm_error_payload(exc_info.value)
    assert payload["error_type"] == "upstream_provider_overloaded"
    assert payload["status_code"] == 429
    assert "temporarily overloaded" in payload["user_message"].lower()
    assert "switching accounts may not resolve this issue" in payload["recommended_action"].lower()


def test_classify_429_account_quota_exceeded():
    req = httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")
    resp = httpx.Response(429, request=req)
    error = RateLimitError(
        "Rate limit",
        response=resp,
        body={
            "error": {
                "message": "Daily request limit reached for this free account key. Credit balance 0.",
                "metadata": {"limit_source": "platform", "error_type": "platform_rate_limit"},
            }
        },
    )

    client = _client_with_chat_raising(error)
    with pytest.raises(LLMRateLimitError) as exc_info:
        client.interpret_evidence(_dummy_evidence(), [])

    payload = build_llm_error_payload(exc_info.value)
    assert payload["error_type"] == "account_quota_exceeded"
    assert payload["status_code"] == 429
    assert "configure another authorized openrouter account" in payload["recommended_action"].lower()


# ---------------------------------------------------------------------------
# 5. HTTP 502 / 503 — Service Unavailable
# ---------------------------------------------------------------------------


def test_classify_502_503_service_unavailable():
    req = httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")
    resp = httpx.Response(503, request=req)
    error = APIStatusError(
        "Service Unavailable",
        response=resp,
        body={"error": {"message": "OpenRouter provider service unavailable"}},
    )

    client = _client_with_chat_raising(error)
    with pytest.raises(LLMProviderUnavailableError) as exc_info:
        client.interpret_evidence(_dummy_evidence(), [])

    payload = build_llm_error_payload(exc_info.value)
    assert payload["error_type"] == "service_unavailable"
    assert payload["status_code"] == 503
    assert "temporarily unavailable" in payload["user_message"].lower()


# ---------------------------------------------------------------------------
# 6. Network Connection Error & Timeout
# ---------------------------------------------------------------------------


def test_classify_network_connection_error():
    req = httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")
    error = APIConnectionError(request=req, message="Connection refused to openrouter.ai")

    client = _client_with_chat_raising(error)
    with pytest.raises(LLMConnectionError) as exc_info:
        client.interpret_evidence(_dummy_evidence(), [])

    payload = build_llm_error_payload(exc_info.value)
    assert payload["error_type"] == "network_error"
    assert "unable to connect" in payload["user_message"].lower()
    assert "internet connection" in payload["recommended_action"].lower()


def test_classify_timeout_error():
    req = httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")
    error = APITimeoutError(request=req)

    client = _client_with_chat_raising(error)
    with pytest.raises(LLMTimeoutError) as exc_info:
        client.interpret_evidence(_dummy_evidence(), [])

    payload = build_llm_error_payload(exc_info.value)
    assert payload["error_type"] == "timeout"
    assert "timed out" in payload["user_message"].lower()


# ---------------------------------------------------------------------------
# 7. Integration: Error Payload Stored in Analysis Results
# ---------------------------------------------------------------------------


from tests.test_innovation import _create_test_project


def test_innovation_analyzer_stores_llm_error_payload(db_session: Session, monkeypatch):
    monkeypatch.setattr(settings, "LLM_ENABLED", True)
    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "sk-test-key")

    _create_test_project(
        db_session,
        "p-err-test",
        title="Error Test Project",
        has_readme=True,
        file_names=["main.py", "README.md"],
        sections=[{"title": "Overview", "content": "Solves real problems with features"}],
    )

    req = httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")
    resp = httpx.Response(402, request=req)
    error = APIStatusError(
        "Payment required",
        response=resp,
        body={"error": {"message": "Credit exhausted"}},
    )

    client = _client_with_chat_raising(error)
    res = InnovationService.analyze_project(db_session, "p-err-test", client=client, call_llm=True)

    assert res.llm_interpretation_status == "error"
    assert "llm_error" in res.structured_interpretation
    llm_err = res.structured_interpretation["llm_error"]
    assert llm_err["error_type"] == "account_quota_exceeded"
    assert llm_err["status_code"] == 402
    assert "configure another authorized openrouter account" in llm_err["recommended_action"].lower()
    # Confirm deterministic profile and scores remain completely intact:
    assert res.profile is not None
    assert res.dimension_scores is not None
