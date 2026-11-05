"""OpenRouter LLM client package (Phase 7A).

Provides a reusable, OpenAI-compatible client for OpenRouter with typed error
handling and Pydantic response validation. The client is safely disabled when
LLM configuration or credentials are missing so the rest of the application
continues to work deterministically.
"""

from app.services.llm.client import OpenRouterClient, build_llm_error_payload
from app.services.llm.exceptions import (
    LLMConfigurationError,
    LLMError,
    LLMAuthenticationError,
    LLMQuotaExceededError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMConnectionError,
    LLMProviderUnavailableError,
    LLMModelUnavailableError,
    LLMInvalidResponseError,
    LLMInvalidReferenceError,
    LLMDiagnosticMetadata,
)
from app.services.llm.schemas import (
    EvidenceSignal,
    EvidenceSummary,
    EvidenceReference,
    FactVsInterpretation,
    AIAssistanceFinding,
    LLMInterpretation,
    InterpretationStatus,
    InnovationEvidenceReference,
    LLMInnovationInterpretation,
)

__all__ = [
    "OpenRouterClient",
    "build_llm_error_payload",
    "LLMConfigurationError",
    "LLMError",
    "LLMAuthenticationError",
    "LLMQuotaExceededError",
    "LLMRateLimitError",
    "LLMTimeoutError",
    "LLMConnectionError",
    "LLMProviderUnavailableError",
    "LLMModelUnavailableError",
    "LLMInvalidResponseError",
    "LLMInvalidReferenceError",
    "LLMDiagnosticMetadata",
    "EvidenceSignal",
    "EvidenceSummary",
    "EvidenceReference",
    "FactVsInterpretation",
    "AIAssistanceFinding",
    "LLMInterpretation",
    "InterpretationStatus",
    "InnovationEvidenceReference",
    "LLMInnovationInterpretation",
]
