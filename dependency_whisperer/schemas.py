"""
Strict Data Schemas and Contracts for Person 3 (The AI Whisperer).

Defines the JSON contract between:
- Person 2 (Detective) -> Person 3 (Whisperer): Usage locations, AST call sites, dependency metadata.
- Person 3 (Whisperer) -> Person 1 (Referee): Set A & Set B test suites, migrated code patches.
- Person 3 (Whisperer) -> Person 4 (Presenter): Exit Capsule structured data with strict
  [OBSERVED] vs [AI-SUGGESTED] separation.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

# Pydantic v1 / v2 bidirectional compatibility shim
if not hasattr(BaseModel, "model_validate"):
    BaseModel.model_validate = classmethod(lambda cls, obj: cls.parse_obj(obj))  # type: ignore[attr-defined]
if not hasattr(BaseModel, "model_validate_json"):
    BaseModel.model_validate_json = classmethod(lambda cls, json_data: cls.parse_raw(json_data))  # type: ignore[attr-defined]
if not hasattr(BaseModel, "model_dump"):
    BaseModel.model_dump = lambda self, **kwargs: self.dict(**kwargs)  # type: ignore[attr-defined]
if not hasattr(BaseModel, "model_dump_json"):
    BaseModel.model_dump_json = lambda self, **kwargs: self.json(**kwargs)  # type: ignore[attr-defined]


class TagEnum(str, Enum):
    OBSERVED = "OBSERVED"
    AI_SUGGESTED = "AI_SUGGESTED"


class TaggedField(BaseModel):
    """
    Guarantees strict separation between verified/observed facts
    and AI-suggested recommendations as mandated by the challenge.
    """
    tag: TagEnum
    value: Any
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    source: Optional[str] = None  # e.g. "AST Scanner", "PyPI Metadata", "Gemma 4"
    rationale: Optional[str] = None


class DependencyUsageLocation(BaseModel):
    """Observed usage location supplied by Person 2 (Detective)."""
    file_path: str
    line_number: int
    code_snippet: str
    call_symbol: Optional[str] = None


class DependencyRiskTriage(BaseModel):
    """Risk analysis and classification for a single dependency."""
    dependency_name: str
    current_version: TaggedField  # OBSERVED
    is_deprecated: TaggedField  # OBSERVED / AI_SUGGESTED
    is_unmaintained: TaggedField  # OBSERVED / AI_SUGGESTED
    known_vulnerabilities: TaggedField  # OBSERVED
    python_compatibility_risk: TaggedField  # AI_SUGGESTED
    risk_level: str = Field(description="CRITICAL, HIGH, MEDIUM, LOW")  # AI_SUGGESTED
    risk_summary: str = Field(description="Plain text rationale of why this dependency is at risk")


class ApiMapping(BaseModel):
    """Exact mapping of an old symbol/call to its new equivalent."""
    old_symbol: str
    new_symbol: str
    transformation_type: str = Field(
        description="'direct_rename', 'signature_change', 'context_manager', 'structural_rewrite'"
    )
    notes: Optional[str] = None


class ReplacementOption(BaseModel):
    """One candidate replacement library suggested by Blue Team."""
    library_name: str
    recommended_version_spec: str
    ecosystem_health: str = Field(description="e.g. 'Active (Release in last 3 months)', 'Standard Library'")
    pros: List[str]
    cons: List[str]
    migration_difficulty: str = Field(description="'TRIVIAL', 'LOW', 'MEDIUM', 'HIGH'")
    breaking_changes: List[str]
    api_mappings: List[ApiMapping]


class ReplacementRecommendation(BaseModel):
    """Triage + Top 3 suggested replacements for an at-risk dependency."""
    target_dependency: str
    observed_usage_count: int
    triage: DependencyRiskTriage
    options: List[ReplacementOption] = Field(description="Top 3 modern replacement libraries")
    recommended_choice: str = Field(description="Primary suggested library name")


class TestCaseItem(BaseModel):
    """Individual test case in Set A or Set B."""
    __test__ = False
    test_id: str
    name: str
    category: str = Field(description="'SET_A_COMPATIBILITY_GATE' or 'SET_B_DIFFERENTIAL'")
    description: str
    test_code: str
    expected_behavior: str
    validity_gate_passed: Optional[bool] = Field(
        default=None,
        description="Must be True on original dependency for Set A before gating migrated code"
    )


class TestSuitePlan(BaseModel):
    """Red Team: Set A (Compatibility Gate) + Set B (Differential) test plan."""
    __test__ = False
    target_dependency: str
    replacement_library: str
    set_a_tests: List[TestCaseItem] = Field(
        description="Set A: Must pass on OLD library first, then on NEW library to detect regressions"
    )
    set_b_tests: List[TestCaseItem] = Field(
        description="Set B: Probes new features, edge cases, strict errors, and differential behavior"
    )
    full_pytest_file_content: str = Field(
        description="Complete, ready-to-run pytest file combining setup and both test sets"
    )


class MigrationPatch(BaseModel):
    """Blue Team: Generated code migration patch for target/hero file."""
    target_file: str
    target_dependency: str
    replacement_library: str
    original_code: str
    migrated_code: str
    unified_diff: str
    import_changes: List[str]
    call_site_transformations: List[str]
    confidence_score: float = Field(ge=0.0, le=1.0)
    limitations_and_assumptions: List[str]


class RepairRequest(BaseModel):
    """Input payload from Person 1 (Referee) when execution tests fail."""
    target_file: str
    target_dependency: str
    replacement_library: str
    original_code: str
    current_migrated_code: str
    test_stdout: str
    test_stderr: str
    failure_traceback: str
    attempt_number: int = 1


class RepairResult(BaseModel):
    """Self-healing output patch addressing test failures."""
    success: bool
    repaired_code: str
    unified_diff: Optional[str] = ""
    root_cause_diagnosis: str
    changes_applied: List[str]
    confidence_score: float = Field(ge=0.0, le=1.0)


class ExitCapsulePayload(BaseModel):
    """
    Standard schema for Person 4 (Presenter) to render the final Dependency Exit Capsule.
    """
    dependency_name: str
    target_file: str
    risk_triage: DependencyRiskTriage
    recommended_replacement: ReplacementOption
    alternative_options: List[ReplacementOption]
    test_suite_plan: TestSuitePlan
    migration_patch: MigrationPatch
    observed_evidence: Dict[str, Any] = Field(description="All strictly OBSERVED execution results")
    ai_recommendations: Dict[str, Any] = Field(description="All strictly AI-SUGGESTED guidance")
