"""LLM client exceptions for Phase 7A OpenRouter integration.

All exceptions are raised by the OpenRouter client and translated into
appropriate HTTP responses by the API layer. Secret values are never
included in exception messages.
"""

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class LLMDiagnosticMetadata:
    """Whitelisted, sanitized metadata from an OpenAI-compatible response."""

    status_code: Optional[int] = None
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    provider_code: Optional[str] = None
    limit_source: Optional[str] = None
    retry_after: Optional[str] = None
    rate_limit_limit: Optional[str] = None
    rate_limit_remaining: Optional[str] = None
    rate_limit_reset: Optional[str] = None
    request_id: Optional[str] = None
    classification: Optional[str] = None
    user_message: Optional[str] = None
    recommended_action: Optional[str] = None

    def as_dict(self) -> dict[str, Any]:
        return {key: value for key, value in self.__dict__.items() if value is not None}


class LLMError(Exception):
    """Base exception for all LLM-related errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        diagnostic: Optional[LLMDiagnosticMetadata] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.diagnostic = diagnostic


class LLMConfigurationError(LLMError):
    """Raised when LLM is not configured (disabled or missing credentials)."""

    def __init__(self, message: str = "LLM integration is not configured."):
        super().__init__(message, status_code=400)


class LLMAuthenticationError(LLMError):
    """Raised when the provider rejects the API key (HTTP 401)."""

    def __init__(
        self,
        message: str = "LLM provider authentication failed (HTTP 401).",
        diagnostic: Optional[LLMDiagnosticMetadata] = None,
    ):
        super().__init__(message, status_code=401, diagnostic=diagnostic)


class LLMQuotaExceededError(LLMError):
    """Raised when account credits or payment is required (HTTP 402 or account limit)."""

    def __init__(
        self,
        message: str = "OpenRouter account quota exceeded or credits depleted (HTTP 402).",
        diagnostic: Optional[LLMDiagnosticMetadata] = None,
    ):
        super().__init__(message, status_code=402, diagnostic=diagnostic)


class LLMRateLimitError(LLMError):
    """Raised when the provider rate-limits the request (HTTP 429).

    No automatic retry is performed because free-tier requests are limited.
    """

    def __init__(
        self,
        message: str = "LLM provider rate limit reached (HTTP 429).",
        diagnostic: Optional[LLMDiagnosticMetadata] = None,
    ):
        super().__init__(message, status_code=429, diagnostic=diagnostic)


class LLMTimeoutError(LLMError):
    """Raised when the provider request times out."""

    def __init__(
        self,
        message: str = "LLM provider request timed out.",
        diagnostic: Optional[LLMDiagnosticMetadata] = None,
    ):
        super().__init__(message, status_code=504, diagnostic=diagnostic)


class LLMConnectionError(LLMError):
    """Raised when unable to connect to OpenRouter (network error)."""

    def __init__(
        self,
        message: str = "Unable to connect to OpenRouter network.",
        diagnostic: Optional[LLMDiagnosticMetadata] = None,
    ):
        super().__init__(message, status_code=503, diagnostic=diagnostic)


class LLMProviderUnavailableError(LLMError):
    """Raised when the provider is unavailable (HTTP 502/503/504 not due to timeout)."""

    def __init__(
        self,
        message: str = "LLM provider is unavailable.",
        diagnostic: Optional[LLMDiagnosticMetadata] = None,
    ):
        super().__init__(message, status_code=502, diagnostic=diagnostic)


class LLMModelUnavailableError(LLMError):
    """Raised when the configured model is not available."""

    def __init__(self, model: str, message: Optional[str] = None):
        msg = message or f"LLM model '{model}' is not available."
        super().__init__(msg, status_code=404)
        self.model = model


class LLMInvalidResponseError(LLMError):
    """Raised when the provider returns invalid JSON or missing/invalid content."""

    def __init__(self, message: str = "LLM provider returned an invalid response."):
        super().__init__(message, status_code=502)


class LLMInvalidReferenceError(LLMError):
    """Raised when the LLM references evidence IDs that were not supplied in input."""

    def __init__(self, message: str = "LLM referenced evidence IDs not present in input."):
        super().__init__(message, status_code=422)
