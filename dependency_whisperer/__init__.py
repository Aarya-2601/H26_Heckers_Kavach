"""
Dependency Whisperer - AI Engine for Gemma 4 Dependency Resilience.
Person 3 Deliverable.
"""

from .gemma_client import GemmaClient, GemmaModelMetadata, GemmaBackendError
from .schemas import (
    ApiMapping,
    DependencyRiskTriage,
    DependencyUsageLocation,
    ExitCapsulePayload,
    MigrationPatch,
    RepairRequest,
    RepairResult,
    ReplacementOption,
    ReplacementRecommendation,
    TagEnum,
    TaggedField,
    TestCaseItem,
    TestSuitePlan,
)
from .whisperer import DependencyWhisperer

__version__ = "1.0.0"

__all__ = [
    "DependencyWhisperer",
    "GemmaClient",
    "GemmaBackendError",
    "GemmaModelMetadata",
    "ApiMapping",
    "DependencyRiskTriage",
    "DependencyUsageLocation",
    "ExitCapsulePayload",
    "MigrationPatch",
    "RepairRequest",
    "RepairResult",
    "ReplacementOption",
    "ReplacementRecommendation",
    "TagEnum",
    "TaggedField",
    "TestCaseItem",
    "TestSuitePlan",
]