"""
API schemas for experiments.

Pydantic schemas for experiment API request/response handling.
Supports embedded scorecard data (1:1 relationship).

References:
    - OpenAPI: specs/019-experiment-refactor/contracts/experiment-api.yaml
    - Data model: specs/019-experiment-refactor/data-model.md
"""

from datetime import datetime

from pydantic import BaseModel, Field

from synth_lab.domain.entities.synth_group import DEFAULT_SYNTH_GROUP_ID
from synth_lab.models.pagination import PaginationMeta

# =============================================================================
# Feature Mechanisms Schemas (new in 038-mechanism-based-simulation)
# =============================================================================


class FeatureMechanismsInput(BaseModel):
    """Input schema for feature mechanisms (all optional, default 0.0)."""

    irreversibility: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Degree to which actions are permanent/irreversible.",
        examples=[0.9],
    )

    network_effect: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Degree to which value depends on others using it.",
        examples=[0.7],
    )

    institutional_trust: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Degree to which feature requires trust in institution.",
        examples=[0.8],
    )

    habit_displacement: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Degree to which feature replaces existing habits.",
        examples=[0.4],
    )

    learning_curve: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Degree to which feature requires learning new skills.",
        examples=[0.5],
    )

    social_visibility: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Degree to which usage is visible to others.",
        examples=[0.3],
    )

    valor_intrinseco: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Intrinsic value perceived by the user.",
        examples=[0.7],
    )

    friccao_operacional: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Operational friction to use the feature.",
        examples=[0.4],
    )

    frequencia_de_uso: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Expected frequency of use.",
        examples=[0.6],
    )


class FeatureMechanismsOutput(BaseModel):
    """Output schema for feature mechanisms."""

    irreversibility: float = Field(description="Degree to which actions are permanent/irreversible.")
    network_effect: float = Field(description="Degree to which value depends on others using it.")
    institutional_trust: float = Field(
        description="Degree to which feature requires trust in institution."
    )
    habit_displacement: float = Field(description="Degree to which feature replaces existing habits.")
    learning_curve: float = Field(
        description="Degree to which feature requires learning new skills."
    )
    social_visibility: float = Field(description="Degree to which usage is visible to others.")
    valor_intrinseco: float = Field(description="Intrinsic value perceived by the user.")
    friccao_operacional: float = Field(description="Operational friction to use the feature.")
    frequencia_de_uso: float = Field(description="Expected frequency of use.")


# =============================================================================
# Scorecard Schemas (Embedded in Experiment)
# =============================================================================


class ScorecardDataSchema(BaseModel):
    """Schema for embedded scorecard data.

    Legacy dimensions (complexity, initial_effort, perceived_risk, time_to_value)
    were removed in 040 — simulation uses only mechanisms.
    """

    feature_name: str = Field(
        description="Name of the feature being scored.",
        examples=["Novo Fluxo de Checkout"])

    scenario: str = Field(
        default="baseline",
        description="Scenario identifier.",
        examples=["baseline", "optimistic", "pessimistic"])

    description_text: str = Field(
        description="Detailed description of the feature.",
        examples=["Sistema de checkout simplificado com menos etapas"])

    description_media_urls: list[str] = Field(
        default_factory=list,
        description="URLs to media files describing the feature.")

    justification: str | None = Field(
        default=None,
        description="LLM justification for the scores.")

    impact_hypotheses: list[str] = Field(
        default_factory=list,
        description="Impact hypotheses from LLM analysis.")

    # Feature mechanisms (new in 038-mechanism-based-simulation)
    mechanisms: FeatureMechanismsInput | None = Field(
        default=None,
        description="Structural mechanisms of the feature for simulation.",
    )

    feature_types: list[str] = Field(
        default_factory=list,
        description="Category tags for the feature (e.g., 'financial', 'social', 'utility').",
    )


# =============================================================================
# Experiment Request Schemas
# =============================================================================


class ExperimentCreate(BaseModel):
    """Schema for creating a new experiment."""

    name: str = Field(
        max_length=100,
        description="Short name of the feature.",
        examples=["Novo Fluxo de Checkout"])

    hypothesis: str = Field(
        max_length=500,
        description="Description of the hypothesis to test.",
        examples=["Reduzir etapas do checkout aumentará conversão em 15%"])

    description: str | None = Field(
        default=None,
        max_length=2000,
        description="Additional context, links, references.",
        examples=["Baseado em feedback de usuários e análise de abandono"])

    synth_group_id: str = Field(
        default=DEFAULT_SYNTH_GROUP_ID,
        min_length=1,
        max_length=50,
        description="ID of the synth group to use for this experiment. Defaults to the default group.",
        examples=["grp_00000001", "grp_abc123"])

    scorecard_data: ScorecardDataSchema | None = Field(
        default=None,
        description="Optional embedded scorecard data.")

    # Feature mechanisms (new in 038-mechanism-based-simulation)
    mechanisms: FeatureMechanismsInput | None = Field(
        default=None,
        description="Optional feature mechanisms. If provided alongside scorecard_data, "
        "will be merged into scorecard_data.mechanisms.",
    )

    feature_types: list[str] = Field(
        default_factory=list,
        description="Category tags for the feature (e.g., 'financial', 'social', 'utility').",
    )


class ExperimentUpdate(BaseModel):
    """Schema for updating an experiment."""

    name: str | None = Field(
        default=None,
        max_length=100,
        description="Short name of the feature.")

    hypothesis: str | None = Field(
        default=None,
        max_length=500,
        description="Description of the hypothesis to test.")

    description: str | None = Field(
        default=None,
        max_length=2000,
        description="Additional context, links, references.")

    synth_group_id: str | None = Field(
        default=None,
        description="ID of the synth group to use for this experiment.")

    # Feature mechanisms (new in 038-mechanism-based-simulation)
    mechanisms: FeatureMechanismsInput | None = Field(
        default=None,
        description="Feature mechanisms to update. Merges with existing scorecard_data.",
    )

    feature_types: list[str] | None = Field(
        default=None,
        description="Category tags for the feature.",
    )


# =============================================================================
# Related Entity Summaries (for ExperimentDetail)
# =============================================================================


class AggregatedOutcomesSchema(BaseModel):
    """Schema for aggregated analysis outcomes (2-outcome model)."""

    adopted_rate: float = Field(
        ge=0.0,
        le=1.0,
        description="Proportion that adopted the feature.")

    not_adopted_rate: float = Field(
        ge=0.0,
        le=1.0,
        description="Proportion that did not adopt the feature.")


class AnalysisSummary(BaseModel):
    """Summary of analysis linked to an experiment (1:1 relationship)."""

    id: str = Field(description="Analysis run ID.")
    simulation_id: str = Field(description="Simulation ID for chart endpoints.")
    status: str = Field(description="Analysis status (pending, running, completed, failed).")
    started_at: datetime = Field(description="Start timestamp.")
    completed_at: datetime | None = Field(default=None, description="Completion timestamp.")
    total_synths: int = Field(default=0, description="Number of synths analyzed.")
    n_executions: int = Field(default=100, description="Monte Carlo executions per synth.")
    execution_time_seconds: float | None = Field(
        default=None, description="Time taken to run the analysis in seconds."
    )
    aggregated_outcomes: AggregatedOutcomesSchema | None = Field(
        default=None,
        description="Aggregated outcomes from analysis.")


class InterviewSummary(BaseModel):
    """Summary of an interview linked to an experiment."""

    exec_id: str = Field(description="Execution ID.")
    topic_name: str = Field(description="Research topic name.")
    status: str = Field(description="Interview status.")
    synth_count: int = Field(description="Number of synths interviewed.")
    total_turns: int = Field(default=0, description="Total turns across all transcripts.")
    has_summary: bool = Field(default=False, description="Whether summary is available.")
    has_prfaq: bool = Field(default=False, description="Whether PR-FAQ is available.")
    additional_context: str | None = Field(
        default=None, description="Additional context text (if provided)."
    )
    started_at: datetime = Field(description="Start timestamp.")
    completed_at: datetime | None = Field(default=None, description="Completion timestamp.")


# =============================================================================
# Experiment Response Schemas
# =============================================================================


class ExperimentResponse(BaseModel):
    """Response schema for experiment data."""

    id: str = Field(description="Experiment ID.", examples=["exp_a1b2c3d4"])
    name: str = Field(description="Short name of the feature.")
    hypothesis: str = Field(description="Hypothesis description.")
    description: str | None = Field(default=None, description="Additional context.")
    synth_group_id: str = Field(description="ID of the synth group used for this experiment.")
    synth_group_name: str = Field(description="Name of the synth group used for this experiment.")
    scorecard_data: ScorecardDataSchema | None = Field(
        default=None,
        description="Embedded scorecard data.")
    # Feature mechanisms (new in 038-mechanism-based-simulation)
    mechanisms: FeatureMechanismsOutput | None = Field(
        default=None,
        description="Feature mechanisms extracted from scorecard_data for convenience.",
    )
    feature_types: list[str] = Field(
        default_factory=list,
        description="Category tags for the feature.",
    )
    has_scorecard: bool = Field(default=False, description="Whether scorecard is filled.")
    has_interview_guide: bool = Field(
        default=False, description="Whether interview guide is configured."
    )
    tags: list[str] = Field(default_factory=list, description="Tag names associated with this experiment.")
    created_at: datetime = Field(description="Creation timestamp.")
    updated_at: datetime | None = Field(default=None, description="Last update timestamp.")


class ExperimentSummary(BaseModel):
    """Summary of an experiment for list display."""

    id: str = Field(description="Experiment ID.", examples=["exp_a1b2c3d4"])
    name: str = Field(description="Short name of the feature.")
    hypothesis: str = Field(description="Hypothesis description.")
    description: str | None = Field(default=None, description="Additional context.")
    synth_group_id: str = Field(description="ID of the synth group used for this experiment.")
    synth_group_name: str = Field(description="Name of the synth group used for this experiment.")
    has_scorecard: bool = Field(default=False, description="Whether scorecard is filled.")
    has_analysis: bool = Field(default=False, description="Whether analysis exists.")
    has_interview_guide: bool = Field(
        default=False, description="Whether interview guide is configured."
    )
    # Feature mechanisms (new in 038-mechanism-based-simulation)
    has_mechanisms: bool = Field(
        default=False, description="Whether feature mechanisms are defined."
    )
    interview_count: int = Field(default=0, description="Number of linked interviews.")
    tags: list[str] = Field(default_factory=list, description="Tag names associated with this experiment.")
    created_at: datetime = Field(description="Creation timestamp.")
    updated_at: datetime | None = Field(default=None, description="Last update timestamp.")


class ExperimentDetail(ExperimentResponse):
    """Full experiment details including linked analysis and interviews."""

    analysis: AnalysisSummary | None = Field(
        default=None,
        description="Linked analysis (1:1 relationship).")
    interviews: list[InterviewSummary] = Field(
        default_factory=list,
        description="Linked interviews (N:1 relationship).")
    interview_count: int = Field(default=0, description="Number of linked interviews.")


class PaginatedExperimentSummary(BaseModel):
    """Paginated list of experiment summaries."""

    data: list[ExperimentSummary] = Field(description="List of experiments.")
    pagination: PaginationMeta = Field(description="Pagination metadata.")


# =============================================================================
# Validation
# =============================================================================

if __name__ == "__main__":
    import sys

    all_validation_failures: list[str] = []
    total_tests = 0

    # Test 1: ExperimentCreate with required fields only
    total_tests += 1
    try:
        req = ExperimentCreate(
            name="Test Feature",
            hypothesis="Test hypothesis",
            synth_group_id="grp_00000001")
        if req.name != "Test Feature":
            all_validation_failures.append(f"Name mismatch: {req.name}")
        if req.scorecard_data is not None:
            all_validation_failures.append("scorecard_data should be None by default")
    except Exception as e:
        all_validation_failures.append(f"ExperimentCreate creation failed: {e}")

    # Test 1b: ExperimentCreate without synth_group_id uses default
    total_tests += 1
    try:
        req = ExperimentCreate(
            name="Test Feature",
            hypothesis="Test hypothesis")
        if req.synth_group_id != DEFAULT_SYNTH_GROUP_ID:
            all_validation_failures.append(
                f"synth_group_id should default to {DEFAULT_SYNTH_GROUP_ID}, got {req.synth_group_id}")
    except Exception as e:
        all_validation_failures.append(f"ExperimentCreate without synth_group_id failed: {e}")

    # Test 2: ExperimentCreate with scorecard
    total_tests += 1
    try:
        scorecard = ScorecardDataSchema(
            feature_name="Test",
            description_text="Test description")
        req = ExperimentCreate(
            name="Test",
            hypothesis="Test",
            synth_group_id="grp_00000001",
            scorecard_data=scorecard)
        if req.scorecard_data is None:
            all_validation_failures.append("scorecard_data should not be None")
        elif req.scorecard_data.feature_name != "Test":
            all_validation_failures.append(f"Feature name mismatch: {req.scorecard_data.feature_name}")
    except Exception as e:
        all_validation_failures.append(f"ExperimentCreate with scorecard failed: {e}")

    # Test 5: ExperimentUpdate optional fields
    total_tests += 1
    try:
        update = ExperimentUpdate()
        if update.name is not None or update.hypothesis is not None:
            all_validation_failures.append("ExperimentUpdate fields should be None by default")
    except Exception as e:
        all_validation_failures.append(f"ExperimentUpdate creation failed: {e}")

    # Test 6: ExperimentResponse with scorecard
    total_tests += 1
    try:
        from datetime import timezone

        scorecard = ScorecardDataSchema(
            feature_name="Test",
            description_text="Test")
        resp = ExperimentResponse(
            id="exp_12345678",
            name="Test",
            hypothesis="Test",
            synth_group_id="grp_00000001",
            synth_group_name="Default Group",
            scorecard_data=scorecard,
            has_scorecard=True,
            created_at=datetime.now(timezone.utc))
        if not resp.has_scorecard:
            all_validation_failures.append("has_scorecard should be True")
    except Exception as e:
        all_validation_failures.append(f"ExperimentResponse creation failed: {e}")

    # Test 7: ExperimentSummary with has_analysis
    total_tests += 1
    try:
        summary = ExperimentSummary(
            id="exp_12345678",
            name="Test",
            hypothesis="Test",
            synth_group_id="grp_00000001",
            synth_group_name="Default Group",
            has_scorecard=True,
            has_analysis=True,
            interview_count=3,
            created_at=datetime.now(timezone.utc))
        if not summary.has_analysis:
            all_validation_failures.append("has_analysis should be True")
        if summary.interview_count != 3:
            all_validation_failures.append(f"interview_count mismatch: {summary.interview_count}")
    except Exception as e:
        all_validation_failures.append(f"ExperimentSummary creation failed: {e}")

    # Test 8: AnalysisSummary with outcomes
    total_tests += 1
    try:
        outcomes = AggregatedOutcomesSchema(
            adopted_rate=0.6,
            not_adopted_rate=0.4)
        analysis = AnalysisSummary(
            id="ana_12345678",
            simulation_id="ana_12345678",
            status="completed",
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            aggregated_outcomes=outcomes)
        if analysis.aggregated_outcomes is None:
            all_validation_failures.append("aggregated_outcomes should not be None")
        elif analysis.aggregated_outcomes.adopted_rate != 0.6:
            all_validation_failures.append("adopted_rate mismatch")
        elif analysis.simulation_id != analysis.id:
            all_validation_failures.append("simulation_id should match id")
    except Exception as e:
        all_validation_failures.append(f"AnalysisSummary creation failed: {e}")

    # Test 9: ExperimentDetail with analysis and interviews
    total_tests += 1
    try:
        analysis = AnalysisSummary(
            id="ana_12345678",
            simulation_id="ana_12345678",
            status="completed",
            started_at=datetime.now(timezone.utc))
        interview = InterviewSummary(
            exec_id="exec_001",
            topic_name="Test Topic",
            status="completed",
            synth_count=10,
            has_summary=True,
            started_at=datetime.now(timezone.utc))
        detail = ExperimentDetail(
            id="exp_12345678",
            name="Test",
            hypothesis="Test",
            synth_group_id=DEFAULT_SYNTH_GROUP_ID,
            synth_group_name="Default Synth Group",
            has_scorecard=False,
            created_at=datetime.now(timezone.utc),
            analysis=analysis,
            interviews=[interview],
            interview_count=1)
        if detail.analysis is None:
            all_validation_failures.append("analysis should not be None")
        if len(detail.interviews) != 1:
            all_validation_failures.append(f"interviews count mismatch: {len(detail.interviews)}")
    except Exception as e:
        all_validation_failures.append(f"ExperimentDetail creation failed: {e}")

    # Final validation result
    if all_validation_failures:
        failed = len(all_validation_failures)
        print(f"VALIDATION FAILED - {failed} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
