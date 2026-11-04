"""OpenRouter LLM client (Phase 7A).

Thin wrapper around the OpenAI-compatible Python SDK pointed at OpenRouter.
Responsibilities:
  * Build and send a single chat completion with JSON mode.
  * Truncate input to the configured character limit.
  * Parse and Pydantic-validate the LLM response.
  * Translate provider errors into typed, user-safe exceptions (no secrets).

The client is *disabled* when LLM is not configured; the rest of the
application continues to work deterministically without it.
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional

from openai import OpenAI
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
)
from pydantic import ValidationError

from app.config import settings
from app.services.ai_assistance.prompts import SYSTEM_PROMPT, build_user_prompt
from app.services.llm.exceptions import (
    LLMAuthenticationError,
    LLMConfigurationError,
    LLMConnectionError,
    LLMDiagnosticMetadata,
    LLMInvalidReferenceError,
    LLMInvalidResponseError,
    LLMModelUnavailableError,
    LLMProviderUnavailableError,
    LLMQuotaExceededError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from app.services.llm.schemas import (
    EvidenceSummary,
    LLMInterpretation,
    LLMInnovationInterpretation,
)

INNOVATION_SYSTEM_PROMPT = (
    "You are an academic project evaluation assistant for a college project system called ProjectLens. "
    "You receive a compact, PII-free structured project profile and cohort comparison summary. "
    "Your role is to assess the project's problem understanding, proposed solution, distinctive "
    "features, and potential technical contribution compared to peer submissions.\n\n"
    "STRICT RULES:\n"
    "1. Return ONLY valid JSON matching the requested schema. No markdown fences, no explanatory text outside JSON.\n"
    "2. Every evidence reference you emit MUST use an evidence_id that appears in the input feature list. "
    "Do not invent or reference evidence IDs that were not supplied.\n"
    "3. Do not invent project descriptions, features, or similarity percentages not in the input.\n"
    "4. Do not output an arbitrary global novelty percentage. Assess qualitative distinctiveness and technical contribution.\n"
    "5. Clearly identify areas requiring faculty verification during oral viva.\n"
    "6. Include alternative explanations (e.g. standard framework boilerplate, open-source libraries) and limitations."
)

logger = logging.getLogger(__name__)

_MAX_DIAGNOSTIC_TEXT = 512
_MAX_DIAGNOSTIC_HEADER = 128
_SENSITIVE_VALUE = re.compile(
    r"(?i)(bearer\s+|authorization\s*[:=]\s*|api[_ -]?key\s*[:=]\s*)\S+"
)
_TOKEN_VALUE = re.compile(r"(?i)\b(?:sk|or|key)-[A-Za-z0-9_-]{12,}\b")


def build_llm_error_payload(exc: Exception) -> Dict[str, Any]:
    """Build standardized, safe error dictionary for UI serialization and database storage."""
    diagnostic: Optional[LLMDiagnosticMetadata] = getattr(exc, "diagnostic", None)

    error_type = diagnostic.classification if diagnostic and diagnostic.classification else None
    if not error_type:
        if isinstance(exc, LLMAuthenticationError):
            error_type = "auth_invalid_key"
        elif isinstance(exc, LLMQuotaExceededError):
            error_type = "account_quota_exceeded"
        elif isinstance(exc, LLMRateLimitError):
            error_type = "upstream_provider_overloaded"
        elif isinstance(exc, LLMConnectionError):
            error_type = "network_error"
        elif isinstance(exc, LLMTimeoutError):
            error_type = "timeout"
        elif isinstance(exc, LLMProviderUnavailableError):
            error_type = "service_unavailable"
        elif isinstance(exc, LLMConfigurationError):
            error_type = "configuration_missing"
        else:
            error_type = "unknown_error"

    user_message = (
        (diagnostic.user_message if diagnostic and diagnostic.user_message else None)
        or getattr(exc, "message", None)
        or str(exc)
    )
    recommended_action = (
        diagnostic.recommended_action if diagnostic and diagnostic.recommended_action else None
    ) or ""

    if error_type == "auth_invalid_key" and not recommended_action:
        user_message = "Your OpenRouter API key is invalid."
        recommended_action = "Your OpenRouter API key is invalid. Update the key in the backend configuration."
    elif error_type == "account_quota_exceeded" and not recommended_action:
        user_message = "OpenRouter account quota exceeded or credits depleted."
        recommended_action = "You can configure another authorized OpenRouter account by updating your API key."
    elif error_type == "upstream_provider_overloaded" and not recommended_action:
        user_message = "The selected model provider is temporarily overloaded."
        recommended_action = (
            "The selected model provider is temporarily overloaded. You can try again later "
            "or configure another available model/provider. Switching accounts may not resolve this issue."
        )
    elif error_type == "service_unavailable" and not recommended_action:
        user_message = "OpenRouter or upstream provider is temporarily unavailable."
        recommended_action = "OpenRouter or upstream provider is temporarily unavailable. Please try again later."
    elif error_type == "network_error" and not recommended_action:
        user_message = "Unable to connect to OpenRouter network."
        recommended_action = "Unable to connect to OpenRouter. Please check your internet connection or backend network settings."

    return {
        "error_type": error_type,
        "status_code": (
            diagnostic.status_code
            if diagnostic and diagnostic.status_code is not None
            else getattr(exc, "status_code", None)
        ),
        "title": "OpenRouter AI Service Unavailable",
        "subtitle": "AI interpretation could not be completed. Your deterministic project analysis is still available.",
        "user_message": user_message,
        "recommended_action": recommended_action,
        "limit_source": diagnostic.limit_source if diagnostic else None,
        "provider_code": diagnostic.provider_code if diagnostic else None,
    }


class OpenRouterClient:
    """OpenAI-compatible client for OpenRouter."""

    def __init__(self) -> None:
        self.enabled = settings.llm_configured
        self.client: Optional[OpenAI] = None
        if self.enabled:
            try:
                self.client = OpenAI(
                    base_url=settings.LLM_BASE_URL,
                    api_key=settings.api_key or "",
                    timeout=settings.LLM_TIMEOUT_SECONDS,
                    default_headers={
                        "HTTP-Referer": "https://projectlens.local",
                        "X-Title": "ProjectLens Academic Evaluation",
                    },
                )
                logger.info(
                    "OpenRouter LLM client enabled (model=%s, base_url=%s)",
                    settings.LLM_MODEL,
                    settings.LLM_BASE_URL,
                )
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Failed to initialise OpenRouter client: %s", exc)
                self.enabled = False
                self.client = None

    def is_available(self) -> bool:
        """Return True when the client is enabled and initialised."""
        return self.enabled and self.client is not None

    def interpret_evidence(
        self,
        evidence: EvidenceSummary,
        valid_signal_ids: List[str],
        discard_invalid_references: bool = False,
    ) -> LLMInterpretation:
        """Send the evidence summary to OpenRouter and validate the response.

        Args:
            evidence: Compact deterministic evidence summary.
            valid_signal_ids: Signal IDs that the LLM is allowed to reference.

        Returns:
            A validated LLMInterpretation.

        Raises:
            LLMConfigurationError: if LLM is not configured.
            LLMAuthenticationError: on provider 401.
            LLMQuotaExceededError: on provider 402 or platform quota limit.
            LLMRateLimitError: on provider 429.
            LLMTimeoutError: on provider timeout.
            LLMModelUnavailableError: on provider 404 for the model.
            LLMConnectionError: on provider network connection failure.
            LLMProviderUnavailableError: on other provider errors.
            LLMInvalidResponseError: on invalid JSON / missing content.
            LLMInvalidReferenceError: if LLM references unknown signal IDs.
        """
        if not self.is_available():
            raise LLMConfigurationError(
                "LLM integration is not available. Enable LLM_ENABLED and provide an API key."
            )

        user_prompt = build_user_prompt(evidence)
        # Enforce the input character limit deterministically.
        max_chars = settings.LLM_MAX_INPUT_CHARS
        if len(user_prompt) > max_chars:
            user_prompt = user_prompt[:max_chars]
            logger.warning("Truncated LLM input to %d characters.", max_chars)

        try:
            response = self.client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                max_tokens=settings.LLM_MAX_OUTPUT_TOKENS,
                temperature=settings.LLM_TEMPERATURE,
            )
        except AuthenticationError as exc:
            logger.warning("OpenRouter authentication failed.")
            diagnostic = self._diagnostic_from_exception(exc, default_status=401)
            raise LLMAuthenticationError("OpenRouter authentication failed.", diagnostic=diagnostic) from exc
        except RateLimitError as exc:
            diagnostic = self._diagnostic_from_exception(exc, default_status=429)
            cause = self._rate_limit_cause(diagnostic)
            logger.warning(
                "OpenRouter rate limit reached (cause=%s, status=%s).",
                cause,
                diagnostic.status_code,
            )
            raise LLMRateLimitError(
                f"OpenRouter rate limit reached (HTTP {diagnostic.status_code or 429}; "
                f"cause={cause}).",
                diagnostic=diagnostic,
            ) from exc
        except APITimeoutError as exc:
            logger.warning("OpenRouter request timed out.")
            diagnostic = self._diagnostic_from_exception(exc, default_status=504)
            raise LLMTimeoutError("OpenRouter request timed out.", diagnostic=diagnostic) from exc
        except NotFoundError as exc:
            logger.warning("OpenRouter model not found: %s", settings.LLM_MODEL)
            raise LLMModelUnavailableError(settings.LLM_MODEL) from exc
        except APIConnectionError as exc:
            logger.warning("OpenRouter connection error.")
            diagnostic = self._diagnostic_from_exception(exc)
            raise LLMConnectionError(
                "Unable to connect to the LLM provider.",
                diagnostic=diagnostic,
            ) from exc
        except APIStatusError as exc:
            diagnostic = self._diagnostic_from_exception(exc)
            logger.warning("OpenRouter returned HTTP %s.", diagnostic.status_code)
            if diagnostic.status_code == 401:
                raise LLMAuthenticationError(
                    "OpenRouter authentication failed.", diagnostic=diagnostic
                ) from exc
            if diagnostic.status_code == 402:
                raise LLMQuotaExceededError(
                    "OpenRouter account credits depleted.", diagnostic=diagnostic
                ) from exc
            if diagnostic.status_code == 429:
                cause = self._rate_limit_cause(diagnostic)
                raise LLMRateLimitError(
                    f"OpenRouter rate limit reached (HTTP 429; cause={cause}).",
                    diagnostic=diagnostic,
                ) from exc
            raise LLMProviderUnavailableError(
                f"LLM provider returned HTTP {diagnostic.status_code or 502}.",
                diagnostic=diagnostic,
            ) from exc

        # Extract content defensively; JSON mode does not guarantee valid JSON.
        content = self._extract_content(response)
        if content is None:
            raise LLMInvalidResponseError("LLM provider returned no content.")

        # Parse JSON (may fail even in JSON mode).
        try:
            data = json.loads(content)
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning("LLM returned invalid JSON: %s", exc)
            raise LLMInvalidResponseError("LLM returned invalid JSON.") from exc

        # Pydantic validation (structure, types, lengths).
        try:
            interpretation = LLMInterpretation.model_validate(data)
        except ValidationError as exc:
            logger.warning("LLM response failed Pydantic validation: %s", exc)
            raise LLMInvalidResponseError("LLM response failed schema validation.") from exc

        # Reject or discard evidence references that do not exist in the input.
        self._validate_references(
            interpretation,
            set(valid_signal_ids),
            discard_invalid=discard_invalid_references,
        )

        return interpretation

    def interpret_innovation(
        self,
        user_prompt: str,
        valid_evidence_ids: List[str],
        discard_invalid_references: bool = False,
    ) -> LLMInnovationInterpretation:
        """Send the structured innovation prompt to OpenRouter and validate response.

        Args:
            user_prompt: Compact, PII-free innovation summary.
            valid_evidence_ids: Feature/evidence IDs that the LLM is allowed to reference.

        Returns:
            A validated LLMInnovationInterpretation.
        """
        if not self.is_available():
            raise LLMConfigurationError(
                "LLM integration is not available. Enable LLM_ENABLED and provide an API key."
            )

        max_chars = settings.LLM_MAX_INPUT_CHARS
        if len(user_prompt) > max_chars:
            user_prompt = user_prompt[:max_chars]
            logger.warning("Truncated LLM innovation input to %d characters.", max_chars)

        try:
            response = self.client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {"role": "system", "content": INNOVATION_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                max_tokens=settings.LLM_MAX_OUTPUT_TOKENS,
                temperature=settings.LLM_TEMPERATURE,
            )
        except AuthenticationError as exc:
            logger.warning("OpenRouter authentication failed.")
            diagnostic = self._diagnostic_from_exception(exc, default_status=401)
            raise LLMAuthenticationError("OpenRouter authentication failed.", diagnostic=diagnostic) from exc
        except RateLimitError as exc:
            diagnostic = self._diagnostic_from_exception(exc, default_status=429)
            cause = self._rate_limit_cause(diagnostic)
            logger.warning(
                "OpenRouter rate limit reached (cause=%s, status=%s).",
                cause,
                diagnostic.status_code,
            )
            raise LLMRateLimitError(
                f"OpenRouter rate limit reached (HTTP {diagnostic.status_code or 429}; "
                f"cause={cause}).",
                diagnostic=diagnostic,
            ) from exc
        except APITimeoutError as exc:
            logger.warning("OpenRouter request timed out.")
            diagnostic = self._diagnostic_from_exception(exc, default_status=504)
            raise LLMTimeoutError("OpenRouter request timed out.", diagnostic=diagnostic) from exc
        except NotFoundError as exc:
            logger.warning("OpenRouter model not found: %s", settings.LLM_MODEL)
            raise LLMModelUnavailableError(settings.LLM_MODEL) from exc
        except APIConnectionError as exc:
            logger.warning("OpenRouter connection error.")
            diagnostic = self._diagnostic_from_exception(exc)
            raise LLMConnectionError(
                "Unable to connect to the LLM provider.",
                diagnostic=diagnostic,
            ) from exc
        except APIStatusError as exc:
            diagnostic = self._diagnostic_from_exception(exc)
            logger.warning("OpenRouter returned HTTP %s.", diagnostic.status_code)
            if diagnostic.status_code == 401:
                raise LLMAuthenticationError(
                    "OpenRouter authentication failed.", diagnostic=diagnostic
                ) from exc
            if diagnostic.status_code == 402:
                raise LLMQuotaExceededError(
                    "OpenRouter account credits depleted.", diagnostic=diagnostic
                ) from exc
            if diagnostic.status_code == 429:
                cause = self._rate_limit_cause(diagnostic)
                raise LLMRateLimitError(
                    f"OpenRouter rate limit reached (HTTP 429; cause={cause}).",
                    diagnostic=diagnostic,
                ) from exc
            raise LLMProviderUnavailableError(
                f"LLM provider returned HTTP {diagnostic.status_code or 502}.",
                diagnostic=diagnostic,
            ) from exc

        content = self._extract_content(response)
        if content is None:
            raise LLMInvalidResponseError("LLM provider returned no content.")

        try:
            data = json.loads(content)
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning("LLM returned invalid JSON: %s", exc)
            raise LLMInvalidResponseError("LLM returned invalid JSON.") from exc

        try:
            interpretation = LLMInnovationInterpretation.model_validate(data)
        except ValidationError as exc:
            logger.warning("LLM response failed Pydantic validation: %s", exc)
            raise LLMInvalidResponseError("LLM response failed schema validation.") from exc

        self._validate_innovation_references(
            interpretation,
            set(valid_evidence_ids),
            discard_invalid=discard_invalid_references,
        )

        return interpretation

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _sanitize_text(value: object, limit: int) -> Optional[str]:
        """Bound and redact diagnostic text before retaining or logging it."""
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None
        text = _SENSITIVE_VALUE.sub(r"\1[REDACTED]", text)
        text = _TOKEN_VALUE.sub("[REDACTED]", text)
        return text[:limit]

    @classmethod
    def _diagnostic_from_exception(
        cls, exc: Exception, default_status: Optional[int] = None
    ) -> LLMDiagnosticMetadata:
        """Extract only whitelisted fields from the SDK response and body, classifying cause."""
        response = getattr(exc, "response", None)
        headers = getattr(response, "headers", {}) or {}
        body = getattr(exc, "body", None)
        if (body is None or not isinstance(body, dict)) and response is not None:
            try:
                body = response.json()
            except Exception:
                body = None
        if not isinstance(body, dict):
            body = {}
        error = body.get("error") if isinstance(body.get("error"), dict) else body
        metadata = error.get("metadata", {}) or body.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}

        def header(name: str) -> Optional[str]:
            return cls._sanitize_text(headers.get(name), _MAX_DIAGNOSTIC_HEADER)

        msg = error.get("message") if isinstance(error, dict) else None
        raw_detail = metadata.get("raw") if isinstance(metadata, dict) else None
        if raw_detail and isinstance(raw_detail, str):
            msg = f"{msg}: {raw_detail}" if msg else raw_detail

        status_code = getattr(exc, "status_code", None) or default_status
        error_type = cls._sanitize_text(
            metadata.get("error_type") or (error.get("type") if isinstance(error, dict) else None),
            _MAX_DIAGNOSTIC_HEADER,
        )
        provider_code = cls._sanitize_text(
            metadata.get("provider_code") or (error.get("code") if isinstance(error, dict) else None),
            _MAX_DIAGNOSTIC_HEADER,
        )
        limit_source = cls._sanitize_text(metadata.get("limit_source"), _MAX_DIAGNOSTIC_HEADER)

        # Classification and recommendations
        classification: str
        user_message: str
        recommended_action: str

        if status_code == 401 or isinstance(exc, AuthenticationError):
            classification = "auth_invalid_key"
            user_message = "Your OpenRouter API key is invalid."
            recommended_action = "Your OpenRouter API key is invalid. Update the key in the backend configuration."
        elif status_code == 402:
            classification = "account_quota_exceeded"
            user_message = "Insufficient OpenRouter account credits or payment required."
            recommended_action = "You can configure another authorized OpenRouter account by updating your API key."
        elif status_code == 429 or isinstance(exc, RateLimitError):
            rate_cause = cls._rate_limit_cause_from_values(limit_source, error_type, msg)
            if rate_cause == "platform":
                classification = "account_quota_exceeded"
                user_message = "OpenRouter account quota or rate limit exceeded."
                recommended_action = "You can configure another authorized OpenRouter account by updating your API key."
            else:
                classification = "upstream_provider_overloaded"
                user_message = "The selected model provider is temporarily overloaded."
                recommended_action = (
                    "The selected model provider is temporarily overloaded. You can try again later "
                    "or configure another available model/provider. Switching accounts may not resolve this issue."
                )
        elif isinstance(exc, APITimeoutError) or status_code == 504:
            classification = "timeout"
            user_message = "OpenRouter request timed out."
            recommended_action = "OpenRouter request timed out. Please try again later."
        elif isinstance(exc, APIConnectionError):
            classification = "network_error"
            user_message = "Unable to connect to OpenRouter network."
            recommended_action = "Unable to connect to OpenRouter. Please check your internet connection or backend network settings."
        elif status_code in (502, 503) or (
            isinstance(exc, APIStatusError) and status_code and 500 <= status_code < 600
        ):
            classification = "service_unavailable"
            user_message = "OpenRouter or upstream provider is temporarily unavailable."
            recommended_action = "OpenRouter or upstream provider is temporarily unavailable. Please try again later."
        else:
            classification = "unknown_error"
            user_message = cls._sanitize_text(msg, _MAX_DIAGNOSTIC_TEXT) or "An error occurred during LLM communication."
            recommended_action = "Deterministic project analysis is still available."

        return LLMDiagnosticMetadata(
            status_code=status_code,
            error_message=cls._sanitize_text(msg, _MAX_DIAGNOSTIC_TEXT),
            error_type=error_type,
            provider_code=provider_code,
            limit_source=limit_source,
            retry_after=header("Retry-After"),
            rate_limit_limit=header("X-RateLimit-Limit"),
            rate_limit_remaining=header("X-RateLimit-Remaining"),
            rate_limit_reset=header("X-RateLimit-Reset"),
            request_id=cls._sanitize_text(
                getattr(exc, "request_id", None)
                or headers.get("x-request-id")
                or headers.get("X-Request-Id"),
                _MAX_DIAGNOSTIC_HEADER,
            ),
            classification=classification,
            user_message=user_message,
            recommended_action=recommended_action,
        )

    @classmethod
    def _rate_limit_cause_from_values(
        cls,
        limit_source: Optional[str],
        error_type: Optional[str],
        error_message: Optional[str],
    ) -> str:
        """Classify 429 into 'platform' (account quota/credits) vs 'upstream_provider' vs 'unknown'."""
        source = (limit_source or "").lower()
        err_type = (error_type or "").lower()
        msg = (error_message or "").lower()

        # Check explicit platform/account quota indicators first
        if any(token in source for token in ("platform", "account", "key", "user")):
            return "platform"
        if any(token in err_type for token in ("platform", "account", "credit")):
            return "platform"
        if any(
            token in msg
            for token in (
                "insufficient credit",
                "credit balance",
                "purchase credits",
                "exceeded your quota",
                "quota exceeded",
                "monthly quota",
                "daily quota",
                "billing",
            )
        ):
            return "platform"

        # Explicit upstream/provider overload indicators
        if any(token in source for token in ("provider", "upstream")):
            return "upstream_provider"
        if any(token in err_type for token in ("provider", "upstream")):
            return "upstream_provider"
        if any(token in msg for token in ("upstream", "provider", "temporarily")):
            return "upstream_provider"

        return "unknown"

    @classmethod
    def _rate_limit_cause(cls, diagnostic: LLMDiagnosticMetadata) -> str:
        """Classify only when the provider supplied an explicit useful signal."""
        return cls._rate_limit_cause_from_values(
            diagnostic.limit_source, diagnostic.error_type, diagnostic.error_message
        )

    @staticmethod
    def _extract_content(response) -> Optional[str]:
        """Safely extract text content from the provider response."""
        try:
            choices = getattr(response, "choices", None)
            if not choices:
                return None
            message = choices[0].message
            content = getattr(message, "content", None)
            return content
        except Exception:
            return None

    @staticmethod
    def _validate_references(
        interpretation: LLMInterpretation,
        valid_signal_ids: set,
        discard_invalid: bool = False,
    ) -> None:
        """Ensure every referenced signal_id was supplied in the input."""
        valid_refs = []
        unknown: List[str] = []
        for ref in interpretation.evidence_references:
            if ref.signal_id not in valid_signal_ids:
                unknown.append(ref.signal_id)
            else:
                valid_refs.append(ref)
        if unknown:
            if discard_invalid:
                interpretation.evidence_references = valid_refs
                interpretation.limitations.append(
                    f"Discarded invalid evidence reference(s) not in input: {', '.join(unknown)}."
                )
            else:
                raise LLMInvalidReferenceError(
                    f"LLM referenced unknown signal IDs: {', '.join(unknown)}."
                )

    @staticmethod
    def _validate_innovation_references(
        interpretation: LLMInnovationInterpretation,
        valid_ids: set,
        discard_invalid: bool = False,
    ) -> None:
        """Ensure every referenced evidence_id was supplied in the input."""
        valid_refs = []
        unknown: List[str] = []
        for ref in interpretation.evidence_references:
            if ref.evidence_id not in valid_ids:
                unknown.append(ref.evidence_id)
            else:
                valid_refs.append(ref)
        if unknown:
            if discard_invalid:
                interpretation.evidence_references = valid_refs
                interpretation.limitations.append(
                    f"Discarded invalid evidence reference(s) not in input: {', '.join(unknown)}."
                )
            else:
                raise LLMInvalidReferenceError(
                    f"LLM referenced unknown evidence IDs: {', '.join(unknown)}."
                )
