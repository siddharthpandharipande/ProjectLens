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
    "2. Top-level JSON must contain these exact keys:\n"
    "   - interpretation_status: 'completed'\n"
    "   - innovation_summary: string\n"
    "   - problem_understanding: string\n"
    "   - proposed_solution_understanding: string\n"
    "   - potential_contributions: list of strings\n"
    "   - distinctive_elements: list of strings\n"
    "   - cohort_comparison_interpretation: string\n"
    "   - evidence_references: list of objects with evidence_id and observation\n"
    "   - alternative_explanations: list of strings\n"
    "   - faculty_follow_up_recommendations: list of strings\n"
    "   - innovation_strengths: list of strings\n"
    "   - missing_evidence: list of strings\n"
    "   - improvement_recommendations: list of strings\n"
    "   - confidence_classification: string ('Directly Verified', 'Strong Evidence', 'Moderate Evidence', 'Indirect Evidence', or 'Insufficient Evidence')\n"
    "   - confidence_rationale: string\n"
    "   - limitations: list of strings\n"
    "3. Every evidence reference you emit MUST use an evidence_id that appears in the input feature list. "
    "Do not invent or reference evidence IDs that were not supplied.\n"
    "4. Do not invent project descriptions, features, or similarity percentages not in the input.\n"
    "5. Do not output an arbitrary global novelty percentage. Assess qualitative distinctiveness and technical contribution.\n"
    "6. Clearly identify areas requiring faculty verification during oral viva.\n"
    "7. Include alternative explanations (e.g. standard framework boilerplate, open-source libraries) and limitations."
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
    provider_name = "Google Gemini" if settings.LLM_PROVIDER.lower() == "gemini" else "OpenRouter"

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
        user_message = f"Your {provider_name} API key is invalid."
        recommended_action = f"Your {provider_name} API key is invalid. Update the key in the backend configuration (.env)."
    elif error_type == "account_quota_exceeded" and not recommended_action:
        user_message = f"{provider_name} account quota exceeded or credits depleted."
        recommended_action = f"You can configure another authorized {provider_name} account or wait for quota reset."
    elif error_type == "upstream_provider_overloaded" and not recommended_action:
        user_message = "The selected model provider is temporarily overloaded."
        recommended_action = (
            "The selected model provider is temporarily overloaded. You can try again later "
            "or configure another available model/provider. Switching accounts may not resolve this issue."
        )
    elif error_type == "service_unavailable" and not recommended_action:
        user_message = f"{provider_name} or upstream provider is temporarily unavailable."
        recommended_action = f"{provider_name} or upstream provider is temporarily unavailable. Please try again later."
    elif error_type == "network_error" and not recommended_action:
        user_message = f"Unable to connect to {provider_name} network."
        recommended_action = f"Unable to connect to {provider_name}. Please check your internet connection or backend network settings."

    return {
        "error_type": error_type,
        "status_code": (
            diagnostic.status_code
            if diagnostic and diagnostic.status_code is not None
            else getattr(exc, "status_code", None)
        ),
        "title": f"{provider_name} AI Service Unavailable",
        "subtitle": "AI interpretation could not be completed. Your deterministic project analysis is still available.",
        "user_message": user_message,
        "recommended_action": recommended_action,
        "limit_source": diagnostic.limit_source if diagnostic else None,
        "provider_code": diagnostic.provider_code if diagnostic else None,
    }


class OpenRouterClient:
    """Unified LLM client supporting Google Gemini (Phase 8/9) and OpenRouter (Phase 7A)."""

    def __init__(self) -> None:
        self.enabled = settings.llm_configured
        self.client: Optional[OpenAI] = None
        self.gemini_client: Optional[Any] = None
        self.is_gemini: bool = settings.LLM_PROVIDER.lower() == "gemini" or (
            settings.gemini_configured and not settings.OPENROUTER_API_KEY
        )

        if self.enabled:
            if self.is_gemini:
                try:
                    from google import genai
                    self.gemini_client = genai.Client(api_key=settings.gemini_api_key)
                    logger.info(
                        "Google Gemini LLM client enabled (model=%s, provider=%s)",
                        settings.effective_gemini_model,
                        settings.LLM_PROVIDER,
                    )
                except Exception as exc:  # pragma: no cover - defensive
                    logger.warning("Failed to initialize Google Gemini client: %s", exc)
                    self.enabled = False
                    self.gemini_client = None
            else:
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
        if not self.enabled:
            return False
        if getattr(self, "is_gemini", False):
            return self.gemini_client is not None
        return self.client is not None

    def interpret_evidence(
        self,
        evidence: EvidenceSummary,
        valid_signal_ids: List[str],
        discard_invalid_references: bool = False,
    ) -> LLMInterpretation:
        """Send the evidence summary to the configured LLM provider and validate the response."""
        if not self.is_available():
            raise LLMConfigurationError(
                "LLM integration is not available. Enable LLM_ENABLED and provide an API key."
            )
        if getattr(self, "is_gemini", False) and getattr(self, "gemini_client", None) is not None:
            return self._interpret_evidence_gemini(
                evidence=evidence,
                valid_signal_ids=valid_signal_ids,
                discard_invalid_references=discard_invalid_references,
            )
        return self._interpret_evidence_openrouter(
            evidence=evidence,
            valid_signal_ids=valid_signal_ids,
            discard_invalid_references=discard_invalid_references,
        )

    def _interpret_evidence_gemini(
        self,
        evidence: EvidenceSummary,
        valid_signal_ids: List[str],
        discard_invalid_references: bool = False,
    ) -> LLMInterpretation:
        """Execute evidence interpretation via Google Gemini API."""
        try:
            from google.genai import types
        except ImportError:
            raise LLMConfigurationError("google-genai package is not installed.")

        user_prompt = build_user_prompt(evidence)
        max_chars = settings.LLM_MAX_INPUT_CHARS
        if len(user_prompt) > max_chars:
            user_prompt = user_prompt[:max_chars]
            logger.warning("Truncated LLM input to %d characters.", max_chars)

        model_name = settings.effective_gemini_model
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=settings.LLM_TEMPERATURE,
            response_mime_type="application/json",
        )

        max_retries = max(1, settings.GEMINI_MAX_RETRIES)
        last_exc: Optional[Exception] = None

        for attempt in range(max_retries + 1):
            try:
                logger.info(
                    "Generating evidence interpretation via Gemini (model=%s, attempt=%d)",
                    model_name,
                    attempt + 1,
                )
                response = self.gemini_client.models.generate_content(
                    model=model_name,
                    contents=user_prompt,
                    config=config,
                )
                raw_text = response.text or ""
                cleaned = re.sub(r"^```(?:json)?\s*", "", raw_text.strip(), flags=re.MULTILINE)
                cleaned = re.sub(r"\s*```$", "", cleaned.strip(), flags=re.MULTILINE)
                if not cleaned:
                    raise LLMInvalidResponseError("Gemini returned empty response text.")

                try:
                    data = json.loads(cleaned)
                except (json.JSONDecodeError, ValueError) as json_err:
                    logger.warning("Gemini returned invalid JSON: %s", json_err)
                    raise LLMInvalidResponseError("LLM returned invalid JSON.") from json_err

                try:
                    interpretation = LLMInterpretation.model_validate(data)
                except ValidationError as val_err:
                    logger.warning("Gemini response failed Pydantic validation: %s", val_err)
                    raise LLMInvalidResponseError("LLM response failed schema validation.") from val_err

                self._validate_references(
                    interpretation,
                    set(valid_signal_ids),
                    discard_invalid=discard_invalid_references,
                )
                return interpretation

            except (LLMInvalidResponseError, LLMInvalidReferenceError):
                raise
            except Exception as exc:
                last_exc = exc
                if attempt < max_retries:
                    import time
                    time.sleep(1.0 * (attempt + 1))
                else:
                    self._map_gemini_exception(exc)

        if last_exc:
            self._map_gemini_exception(last_exc)
        raise LLMProviderUnavailableError("Gemini generation failed after retries.")

    def _interpret_evidence_openrouter(
        self,
        evidence: EvidenceSummary,
        valid_signal_ids: List[str],
        discard_invalid_references: bool = False,
    ) -> LLMInterpretation:
        """Send the evidence summary to OpenRouter and validate the response."""
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
        """Send the structured innovation prompt to configured LLM and validate response.

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
        if getattr(self, "is_gemini", False) and getattr(self, "gemini_client", None) is not None:
            return self._interpret_innovation_gemini(
                user_prompt=user_prompt,
                valid_evidence_ids=valid_evidence_ids,
                discard_invalid_references=discard_invalid_references,
            )
        return self._interpret_innovation_openrouter(
            user_prompt=user_prompt,
            valid_evidence_ids=valid_evidence_ids,
            discard_invalid_references=discard_invalid_references,
        )

    def _interpret_innovation_gemini(
        self,
        user_prompt: str,
        valid_evidence_ids: List[str],
        discard_invalid_references: bool = False,
    ) -> LLMInnovationInterpretation:
        """Execute innovation interpretation via Google Gemini API."""
        try:
            from google.genai import types
        except ImportError:
            raise LLMConfigurationError("google-genai package is not installed.")

        max_chars = settings.LLM_MAX_INPUT_CHARS
        if len(user_prompt) > max_chars:
            user_prompt = user_prompt[:max_chars]
            logger.warning("Truncated LLM innovation input to %d characters.", max_chars)

        model_name = settings.effective_gemini_model
        config = types.GenerateContentConfig(
            system_instruction=INNOVATION_SYSTEM_PROMPT,
            temperature=settings.LLM_TEMPERATURE,
            response_mime_type="application/json",
        )

        max_retries = max(1, settings.GEMINI_MAX_RETRIES)
        last_exc: Optional[Exception] = None

        for attempt in range(max_retries + 1):
            try:
                logger.info(
                    "Generating innovation interpretation via Gemini (model=%s, attempt=%d)",
                    model_name,
                    attempt + 1,
                )
                response = self.gemini_client.models.generate_content(
                    model=model_name,
                    contents=user_prompt,
                    config=config,
                )
                raw_text = response.text or ""
                cleaned = re.sub(r"^```(?:json)?\s*", "", raw_text.strip(), flags=re.MULTILINE)
                cleaned = re.sub(r"\s*```$", "", cleaned.strip(), flags=re.MULTILINE)
                if not cleaned:
                    raise LLMInvalidResponseError("Gemini returned empty response text.")

                try:
                    data = json.loads(cleaned)
                except (json.JSONDecodeError, ValueError) as json_err:
                    logger.warning("Gemini returned invalid JSON: %s", json_err)
                    raise LLMInvalidResponseError("LLM returned invalid JSON.") from json_err

                try:
                    interpretation = LLMInnovationInterpretation.model_validate(data)
                except ValidationError as val_err:
                    logger.warning("Gemini innovation response failed Pydantic validation: %s", val_err)
                    raise LLMInvalidResponseError("LLM response failed schema validation.") from val_err

                self._validate_innovation_references(
                    interpretation,
                    set(valid_evidence_ids),
                    discard_invalid=discard_invalid_references,
                )
                return interpretation

            except (LLMInvalidResponseError, LLMInvalidReferenceError):
                raise
            except Exception as exc:
                last_exc = exc
                if attempt < max_retries:
                    import time
                    time.sleep(1.0 * (attempt + 1))
                else:
                    self._map_gemini_exception(exc)

        if last_exc:
            self._map_gemini_exception(last_exc)
        raise LLMProviderUnavailableError("Gemini innovation generation failed after retries.")

    def _interpret_innovation_openrouter(
        self,
        user_prompt: str,
        valid_evidence_ids: List[str],
        discard_invalid_references: bool = False,
    ) -> LLMInnovationInterpretation:
        """Send the structured innovation prompt to OpenRouter and validate response."""
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

    def _map_gemini_exception(self, exc: Exception) -> None:
        """Map Google Gemini API exceptions to typed LLM exceptions with diagnostics."""
        code = getattr(exc, "code", None)
        status_code = code if isinstance(code, int) else None
        msg = str(getattr(exc, "message", None) or str(exc))
        sanitized_msg = self._sanitize_text(msg, _MAX_DIAGNOSTIC_TEXT) or "Gemini API error."
        lower_msg = sanitized_msg.lower()

        classification = "unknown_error"
        user_message = sanitized_msg
        recommended_action = "Deterministic project analysis is still available."

        if (status_code in (401, 403)) or any(k in lower_msg for k in ("api_key_invalid", "unauthenticated", "permission_denied", "api key not valid")):
            classification = "auth_invalid_key"
            status_code = status_code or 401
            user_message = "Your Google Gemini API key is invalid or unauthorized."
            recommended_action = "Update the GEMINI_API_KEY in the backend configuration (.env)."
            diagnostic = LLMDiagnosticMetadata(
                status_code=status_code,
                error_message=sanitized_msg,
                classification=classification,
                user_message=user_message,
                recommended_action=recommended_action,
            )
            raise LLMAuthenticationError(user_message, diagnostic=diagnostic) from exc

        if (status_code == 429) or any(k in lower_msg for k in ("resource_exhausted", "quota", "rate limit", "too many requests")):
            classification = "account_quota_exceeded" if ("quota" in lower_msg or "credit" in lower_msg) else "upstream_provider_overloaded"
            status_code = status_code or 429
            user_message = "Google Gemini rate limit or quota reached."
            recommended_action = "The Google Gemini service is temporarily rate limited. Please try again in a few moments."
            diagnostic = LLMDiagnosticMetadata(
                status_code=status_code,
                error_message=sanitized_msg,
                classification=classification,
                user_message=user_message,
                recommended_action=recommended_action,
            )
            if classification == "account_quota_exceeded":
                raise LLMQuotaExceededError(user_message, diagnostic=diagnostic) from exc
            raise LLMRateLimitError(user_message, diagnostic=diagnostic) from exc

        if (status_code == 404) or "not found" in lower_msg:
            model_name = settings.effective_gemini_model
            raise LLMModelUnavailableError(model_name) from exc

        if (status_code in (408, 504)) or any(k in lower_msg for k in ("timeout", "deadline_exceeded", "timed out")):
            classification = "timeout"
            status_code = status_code or 504
            user_message = "Google Gemini request timed out."
            recommended_action = "The request to Google Gemini timed out. Please try again."
            diagnostic = LLMDiagnosticMetadata(
                status_code=status_code,
                error_message=sanitized_msg,
                classification=classification,
                user_message=user_message,
                recommended_action=recommended_action,
            )
            raise LLMTimeoutError(user_message, diagnostic=diagnostic) from exc

        if any(k in lower_msg for k in ("connection", "network", "failed to connect", "socket", "dns")):
            classification = "network_error"
            user_message = "Unable to connect to Google Gemini service."
            recommended_action = "Please check your internet connection or backend network settings."
            diagnostic = LLMDiagnosticMetadata(
                status_code=status_code,
                error_message=sanitized_msg,
                classification=classification,
                user_message=user_message,
                recommended_action=recommended_action,
            )
            raise LLMConnectionError(user_message, diagnostic=diagnostic) from exc

        classification = "service_unavailable"
        diagnostic = LLMDiagnosticMetadata(
            status_code=status_code or 503,
            error_message=sanitized_msg,
            classification=classification,
            user_message="Google Gemini AI service is temporarily unavailable.",
            recommended_action="Please try again later. Deterministic analysis remains available.",
        )
        raise LLMProviderUnavailableError("Google Gemini AI service is temporarily unavailable.", diagnostic=diagnostic) from exc

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
