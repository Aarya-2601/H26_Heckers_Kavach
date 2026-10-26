"""
Tests for Dependency Whisperer Pydantic Schemas and Contracts.
"""

from dependency_whisperer.schemas import (
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


def test_tagged_field_observed_vs_ai():
    observed = TaggedField(
        tag=TagEnum.OBSERVED,
        value="0.10.2",
        source="requirements.txt",
    )
    assert observed.tag == TagEnum.OBSERVED
    assert observed.value == "0.10.2"

    ai = TaggedField(
        tag=TagEnum.AI_SUGGESTED,
        value=True,
        confidence=0.95,
        rationale="Unmaintained since 2020",
    )
    assert ai.tag == TagEnum.AI_SUGGESTED
    assert ai.confidence == 0.95


def test_triage_and_replacement_serialization():
    triage = DependencyRiskTriage(
        dependency_name="toml",
        current_version=TaggedField(tag=TagEnum.OBSERVED, value="0.10.2"),
        is_deprecated=TaggedField(tag=TagEnum.AI_SUGGESTED, value=True, confidence=0.98),
        is_unmaintained=TaggedField(tag=TagEnum.AI_SUGGESTED, value=True, confidence=0.95),
        known_vulnerabilities=TaggedField(tag=TagEnum.OBSERVED, value=[]),
        python_compatibility_risk=TaggedField(tag=TagEnum.AI_SUGGESTED, value="HIGH"),
        risk_level="HIGH",
        risk_summary="Old toml library deprecated in favor of tomllib.",
    )

    opt = ReplacementOption(
        library_name="tomllib",
        recommended_version_spec="standard-library",
        ecosystem_health="Python Standard Library",
        pros=["Zero dependencies", "TOML 1.0.0 compliant"],
        cons=["Read only"],
        migration_difficulty="TRIVIAL",
        breaking_changes=["Requires binary stream for load()"],
        api_mappings=[
            ApiMapping(
                old_symbol="toml.load",
                new_symbol="tomllib.load",
                transformation_type="signature_change",
            )
        ],
    )

    rec = ReplacementRecommendation(
        target_dependency="toml",
        observed_usage_count=1,
        triage=triage,
        options=[opt],
        recommended_choice="tomllib",
    )

    dumped = rec.model_dump()
    assert dumped["target_dependency"] == "toml"
    assert dumped["triage"]["is_deprecated"]["tag"] == "AI_SUGGESTED"

    reloaded = ReplacementRecommendation.model_validate(dumped)
    assert reloaded.recommended_choice == "tomllib"
