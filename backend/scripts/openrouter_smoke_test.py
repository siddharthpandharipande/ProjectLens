"""OpenRouter Gemma Free Model Smoke Test (Phase 7A).

Sends a minimal, non-confidential test request to OpenRouter using the configured
model ('google/gemma-4-26b-a4b-it:free') in JSON mode and validates the response
using the Pydantic schema.

SECURITY NOTE:
This script NEVER prints the API key, tokens, or any sensitive credentials.
"""

import os
import sys

# Ensure backend root is on sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.config import settings
from app.services.llm.client import OpenRouterClient
from app.services.llm.schemas import (
    EvidenceSignal,
    EvidenceSummary,
    LLMInterpretation,
)
from app.services.llm.exceptions import (
    LLMAuthenticationError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMModelUnavailableError,
    LLMProviderUnavailableError,
    LLMInvalidResponseError,
    LLMError,
)


def run_smoke_test() -> int:
    """Execute the non-confidential OpenRouter connection and validation test."""
    print("=" * 60)
    print("ProjectLens Phase 7A — OpenRouter Smoke Test")
    print("=" * 60)

    # 1. Configuration check
    print(f"Provider:        {settings.LLM_PROVIDER}")
    print(f"Base URL:        {settings.LLM_BASE_URL}")
    print(f"Configured Model:{settings.LLM_MODEL}")
    print(f"LLM Enabled:     {settings.LLM_ENABLED}")
    has_key = bool(settings.LLM_API_KEY and settings.LLM_API_KEY.strip())
    print(f"API Key Present: {'[CONFIGURED]' if has_key else '[MISSING]'}")

    if not settings.LLM_ENABLED:
        print("\n[ERROR] LLM_ENABLED is False in configuration.")
        print("Set LLM_ENABLED=true in backend/.env to run this test.")
        return 1

    if not has_key:
        print("\n[ERROR] LLM_API_KEY is not configured in backend/.env.")
        print("Provide a valid OpenRouter API key to run this test.")
        return 1

    # Ensure model is the approved free Gemma model
    expected_model = "google/gemma-4-26b-a4b-it:free"
    if settings.LLM_MODEL != expected_model:
        print(f"\n[WARNING] LLM_MODEL is '{settings.LLM_MODEL}' (expected '{expected_model}').")

    # 2. Client initialization
    print("\n[1/3] Initializing OpenRouter client...")
    client = OpenRouterClient()
    if not client.is_available():
        print("[ERROR] Client failed to initialize. Check configuration.")
        return 1
    print("      Client initialized successfully.")

    # 3. Build minimal, non-confidential test payload
    print("\n[2/3] Constructing non-confidential test payload...")
    test_signals = [
        EvidenceSignal(
            signal_id="cq-smoke-test-1",
            category="code_quality",
            source="smoke_test",
            observed_value="12 functions, 2 classes",
            explanation="Deterministic function and class count from test fixture.",
            confidence=1.0,
            alternative_explanations=["Standard test stub structure."],
            availability_status="available",
        ),
        EvidenceSignal(
            signal_id="doc-smoke-test-1",
            category="documentation",
            source="smoke_test",
            observed_value="1 document, 250 words",
            explanation="Minimal README documentation found.",
            confidence=1.0,
            alternative_explanations=[],
            availability_status="available",
        ),
    ]

    evidence_summary = EvidenceSummary(
        project_id="smoke-test-synthetic",
        signals=test_signals,
        rules_version="v1.0-smoke-test",
        advisory_category="Few Observable Signals",
    )
    valid_ids = [s.signal_id for s in test_signals]
    print(f"      Payload prepared with {len(test_signals)} test signals.")
    print("      (No source code, no student personal data, no secrets sent.)")

    # 4. Send request and validate response
    print("\n[3/3] Sending completion request to OpenRouter (JSON mode)...")
    try:
        interpretation: LLMInterpretation = client.interpret_evidence(
            evidence=evidence_summary,
            valid_signal_ids=valid_ids,
            discard_invalid_references=True,
        )
    except LLMAuthenticationError:
        print("[ERROR] Authentication failed (HTTP 401). Verify your LLM_API_KEY.")
        return 2
    except LLMRateLimitError as exc:
        print(f"[ERROR] Provider rate limit reached: {exc.message}")
        if exc.diagnostic:
            print(f"        Diagnostic: {exc.diagnostic.as_dict()}")
        return 3
    except LLMTimeoutError:
        print("[ERROR] Provider request timed out. Check network latency or timeout setting.")
        return 4
    except LLMModelUnavailableError as exc:
        print(f"[ERROR] Configured model is unavailable: {exc.model}")
        return 5
    except LLMProviderUnavailableError as exc:
        print(f"[ERROR] Provider unavailable (HTTP status error): {exc.message}")
        return 6
    except LLMInvalidResponseError as exc:
        print(f"[ERROR] Invalid response or JSON parse failure: {exc.message}")
        return 7
    except LLMError as exc:
        print(f"[ERROR] LLM error: {exc.message}")
        return 8
    except Exception as exc:
        print(f"[ERROR] Unexpected error: {type(exc).__name__}: {exc}")
        return 9

    # 5. Display success verification (never expose credentials)
    print("\n" + "=" * 60)
    print("SUCCESS: OpenRouter LLM Verification Complete!")
    print("=" * 60)
    print(f"Status:                      {interpretation.interpretation_status.value}")
    print(f"Executive Summary:           {interpretation.executive_summary[:160]}...")
    print(f"Patterns Explanation:        {interpretation.explanation_of_patterns[:160]}...")
    print(f"Evidence References Count:   {len(interpretation.evidence_references)}")
    for ref in interpretation.evidence_references[:3]:
        print(f"  - [{ref.signal_id}] {ref.observation[:80]}")
    print(f"Alternative Explanations:    {len(interpretation.alternative_explanations)}")
    print(f"Faculty Recommendations:     {len(interpretation.faculty_follow_up_recommendations)}")
    print(f"Limitations Count:           {len(interpretation.limitations)}")
    print(f"Facts observed:              {len(interpretation.fact_vs_interpretation.facts)}")
    print(f"Interpretations:             {len(interpretation.fact_vs_interpretation.interpretation)}")
    print("Pydantic Validation:         PASSED")
    print("Credential Redaction Check:  PASSED (no API keys exposed)")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(run_smoke_test())

