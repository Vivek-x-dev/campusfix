"""CampusFix AI — package init."""
try:  # load campusfix-ai/.env so GEMINI_API_KEY works without manual export
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

from .schemas import (
    CATEGORIES,
    SEVERITIES,
    AIAnalysisResult,
    DuplicateMatch,
    DuplicateCheckResult,
)

__all__ = [
    "CATEGORIES",
    "SEVERITIES",
    "AIAnalysisResult",
    "DuplicateMatch",
    "DuplicateCheckResult",
]

__version__ = "1.0.0"
