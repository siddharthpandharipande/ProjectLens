from typing import Dict, Any, Optional

def get_evaluation_scores(project_id: str) -> Dict[str, Optional[float]]:
    """
    Evaluation Score Interface.
    
    IMPORTANT: Unimplemented evaluation modules MUST return None (JSON null).
    The frontend will render "Pending Evaluation" or "Not evaluated".
    Numerical scores MUST NOT be fabricated.
    """
    return {
        "overall_score": None,
        "technical_execution": None,
        "originality": None,
        "documentation_integrity": None,
        "development_process": None,
    }
