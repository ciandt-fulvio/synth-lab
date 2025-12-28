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

from synth_lab.models.pagination import PaginationMeta

# =============================================================================
# Scorecard Schemas (Embedded in Experiment)
# =============================================================================


class ScorecardDimensionSchema(BaseModel):
    """Schema for a single scorecard dimension."""

    score: float = Field(
        ge=0.0,
        le=1.0,
        description="Dimension score (0-1).",
        examples=[0.65],
    )

    rules_applied: list[str] = Field(
        default_factory=list,
        description="List of rules that influenced this score.",
        examples=[["High learning curve", "Similar tools exist"]],
    )

    lower_bound: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Lower bound of the score range.",
    )

    upper_bound: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Upper bound of the score range.",
    )


class ScorecardDataSchema(BaseModel):
    """Schema for embedded scorecard data."""

    feature_name: str = Field(
        description="Name of the feature being scored.",
        examples=["Novo Fluxo de Checkout"],
    )

    scenario: str = Field(
        default="baseline",
        description="Scenario identifier.",
        examples=["baseline", "optimistic", "pessimistic"],
    )

    description_text: str = Field(
        description="Detailed description of the feature.",
        examples=["Sistema de checkout simplificado com menos etapas"],
    )

    description_media_urls: list[str] = Field(
        default_factory=list,
        description="URLs to media files describing the feature.",
    )

    complexity: ScorecardDimensionSchema = Field(
        description="Complexity dimension (how hard to understand/use).",
    )

    initial_effort: ScorecardDimensionSchema = Field(
        description="Initial effort dimension (setup/learning cost).",
    )

    perceived_risk: ScorecardDimensionSchema = Field(
        description="Perceived risk dimension (fear of failure/loss).",
    )

    time_to_value: ScorecardDimensionSchema = Field(
        description="Time to value dimension (how long until benefit).",
    )

    justification: str | None = Field(
        default=None,
        description="LLM justification for the scores.",
    )

    impact_hypotheses: list[str] = Field(
        default_factory=list,
        description="Impact hypotheses from LLM analysis.",
    )


class ScorecardEstimateResponse(BaseModel):
    """Response from AI scorecard estimation."""

    complexity: ScorecardDimensionSchema = Field(
        description="Estimated complexity dimension.",
    )

    initial_effort: ScorecardDimensionSchema = Field(
        description="Estimated initial effort dimension.",
    )

    perceived_risk: ScorecardDimensionSchema = Field(
        description="Estimated perceived risk dimension.",
    )

    time_to_value: ScorecardDimensionSchema = Field(
        description="Estimated time to value dimension.",
    )

    justification: str = Field(
        description="LLM justification for the estimates.",
    )

    impact_hypotheses: list[str] = Field(
        default_factory=list,
        description="Impact hypotheses from LLM analysis.",
    )


# =============================================================================
# Experiment Request Schemas
# =============================================================================


class ExperimentCreate(BaseModel):
    """Schema for creating a new experiment."""

    name: str = Field(
        max_length=100,
        description="Short name of the feature.",
        examples=["Novo Fluxo de Checkout"],
    )

    hypothesis: str = Field(
        max_length=500,
        description="Description of the hypothesis to test.",
        examples=["Reduzir etapas do checkout aumentará conversão em 15%"],
    )

    description: str | None = Field(
        default=None,
        max_length=2000,
        description="Additional context, links, references.",
        examples=["Baseado em feedback de usuários e análise de abandono"],
    )

    scorecard_data: ScorecardDataSchema | None = Field(
        default=None,
        description="Optional embedded scorecard data.",
    )


class ExperimentUpdate(BaseModel):
    """Schema for updating an experiment."""

    name: str | None = Field(
        default=None,
        max_length=100,
        description="Short name of the feature.",
    )

    hypothesis: str | None = Field(
        default=None,
        max_length=500,
        description="Description of the hypothesis to test.",
    )

    description: str | None = Field(
        default=None,
        max_length=2000,
        description="Additional context, links, references.",
    )


# =============================================================================
# Related Entity Summaries (for ExperimentDetail)
# =============================================================================


class AggregatedOutcomesSchema(BaseModel):
    """Schema for aggregated analysis outcomes."""

    did_not_try_rate: float = Field(
        ge=0.0,
        le=1.0,
        description="Proportion that did not try.",
    )

    failed_rate: float = Field(
        ge=0.0,
        le=1.0,
        description="Proportion that tried but failed.",
    )

    success_rate: float = Field(
        ge=0.0,
        le=1.0,
        description="Proportion that succeeded.",
    )


class AnalysisSummary(BaseModel):
    """Summary of analysis linked to an experiment (1:1 relationship)."""

    id: str = Field(description="Analysis run ID.")
    status: str = Field(description="Analysis status (pending, running, completed, failed).")
    started_at: datetime = Field(description="Start timestamp.")
    completed_at: datetime | None = Field(default=None, description="Completion timestamp.")
    aggregated_outcomes: AggregatedOutcomesSchema | None = Field(
        default=None,
        description="Aggregated outcomes from analysis.",
    )


class InterviewSummary(BaseModel):
    """Summary of an interview linked to an experiment."""

    exec_id: str = Field(description="Execution ID.")
    topic_name: str = Field(description="Research topic name.")
    status: str = Field(description="Interview status.")
    synth_count: int = Field(description="Number of synths interviewed.")
    has_summary: bool = Field(default=False, description="Whether summary is available.")
    has_prfaq: bool = Field(default=False, description="Whether PR-FAQ is available.")
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
    scorecard_data: ScorecardDataSchema | None = Field(
        default=None,
        description="Embedded scorecard data.",
    )
    has_scorecard: bool = Field(default=False, description="Whether scorecard is filled.")
    created_at: datetime = Field(description="Creation timestamp.")
    updated_at: datetime | None = Field(default=None, description="Last update timestamp.")


class ExperimentSummary(BaseModel):
    """Summary of an experiment for list display."""

    id: str = Field(description="Experiment ID.", examples=["exp_a1b2c3d4"])
    name: str = Field(description="Short name of the feature.")
    hypothesis: str = Field(description="Hypothesis description.")
    description: str | None = Field(default=None, description="Additional context.")
    has_scorecard: bool = Field(default=False, description="Whether scorecard is filled.")
    has_analysis: bool = Field(default=False, description="Whether analysis exists.")
    interview_count: int = Field(default=0, description="Number of linked interviews.")
    created_at: datetime = Field(description="Creation timestamp.")
    updated_at: datetime | None = Field(default=None, description="Last update timestamp.")


class ExperimentDetail(ExperimentResponse):
    """Full experiment details including linked analysis and interviews."""

    analysis: AnalysisSummary | None = Field(
        default=None,
        description="Linked analysis (1:1 relationship).",
    )
    interviews: list[InterviewSummary] = Field(
        default_factory=list,
        description="Linked interviews (N:1 relationship).",
    )
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
        )
        if req.name != "Test Feature":
            all_validation_failures.append(f"Name mismatch: {req.name}")
        if req.scorecard_data is not None:
            all_validation_failures.append("scorecard_data should be None by default")
    except Exception as e:
        all_validation_failures.append(f"ExperimentCreate creation failed: {e}")

    # Test 2: ExperimentCreate with scorecard
    total_tests += 1
    try:
        scorecard = ScorecardDataSchema(
            feature_name="Test",
            description_text="Test description",
            complexity=ScorecardDimensionSchema(score=0.3),
            initial_effort=ScorecardDimensionSchema(score=0.4),
            perceived_risk=ScorecardDimensionSchema(score=0.2),
            time_to_value=ScorecardDimensionSchema(score=0.5),
        )
        req = ExperimentCreate(
            name="Test",
            hypothesis="Test",
            scorecard_data=scorecard,
        )
        if req.scorecard_data is None:
            all_validation_failures.append("scorecard_data should not be None")
        elif req.scorecard_data.complexity.score != 0.3:
            score = req.scorecard_data.complexity.score
            all_validation_failures.append(f"Complexity score mismatch: {score}")
    except Exception as e:
        all_validation_failures.append(f"ExperimentCreate with scorecard failed: {e}")

    # Test 3: ScorecardDimensionSchema with all fields
    total_tests += 1
    try:
        dim = ScorecardDimensionSchema(
            score=0.65,
            rules_applied=["Rule 1", "Rule 2"],
            lower_bound=0.5,
            upper_bound=0.8,
        )
        if dim.score != 0.65:
            all_validation_failures.append(f"Score mismatch: {dim.score}")
        if len(dim.rules_applied) != 2:
            all_validation_failures.append(f"Rules count mismatch: {len(dim.rules_applied)}")
    except Exception as e:
        all_validation_failures.append(f"ScorecardDimensionSchema creation failed: {e}")

    # Test 4: Reject score > 1
    total_tests += 1
    try:
        ScorecardDimensionSchema(score=1.5)
        all_validation_failures.append("Should reject score > 1")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Unexpected error for score > 1: {e}")

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
            description_text="Test",
            complexity=ScorecardDimensionSchema(score=0.3),
            initial_effort=ScorecardDimensionSchema(score=0.4),
            perceived_risk=ScorecardDimensionSchema(score=0.2),
            time_to_value=ScorecardDimensionSchema(score=0.5),
        )
        resp = ExperimentResponse(
            id="exp_12345678",
            name="Test",
            hypothesis="Test",
            scorecard_data=scorecard,
            has_scorecard=True,
            created_at=datetime.now(timezone.utc),
        )
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
            has_scorecard=True,
            has_analysis=True,
            interview_count=3,
            created_at=datetime.now(timezone.utc),
        )
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
            did_not_try_rate=0.2,
            failed_rate=0.3,
            success_rate=0.5,
        )
        analysis = AnalysisSummary(
            id="ana_12345678",
            status="completed",
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            aggregated_outcomes=outcomes,
        )
        if analysis.aggregated_outcomes is None:
            all_validation_failures.append("aggregated_outcomes should not be None")
        elif analysis.aggregated_outcomes.success_rate != 0.5:
            all_validation_failures.append("success_rate mismatch")
    except Exception as e:
        all_validation_failures.append(f"AnalysisSummary creation failed: {e}")

    # Test 9: ExperimentDetail with analysis and interviews
    total_tests += 1
    try:
        analysis = AnalysisSummary(
            id="ana_12345678",
            status="completed",
            started_at=datetime.now(timezone.utc),
        )
        interview = InterviewSummary(
            exec_id="exec_001",
            topic_name="Test Topic",
            status="completed",
            synth_count=10,
            has_summary=True,
            started_at=datetime.now(timezone.utc),
        )
        detail = ExperimentDetail(
            id="exp_12345678",
            name="Test",
            hypothesis="Test",
            has_scorecard=False,
            created_at=datetime.now(timezone.utc),
            analysis=analysis,
            interviews=[interview],
            interview_count=1,
        )
        if detail.analysis is None:
            all_validation_failures.append("analysis should not be None")
        if len(detail.interviews) != 1:
            all_validation_failures.append(f"interviews count mismatch: {len(detail.interviews)}")
    except Exception as e:
        all_validation_failures.append(f"ExperimentDetail creation failed: {e}")

    # Test 10: ScorecardEstimateResponse
    total_tests += 1
    try:
        estimate = ScorecardEstimateResponse(
            complexity=ScorecardDimensionSchema(score=0.4),
            initial_effort=ScorecardDimensionSchema(score=0.3),
            perceived_risk=ScorecardDimensionSchema(score=0.2),
            time_to_value=ScorecardDimensionSchema(score=0.6),
            justification="Based on feature complexity...",
            impact_hypotheses=["Users may struggle initially"],
        )
        if estimate.justification == "":
            all_validation_failures.append("justification should not be empty")
    except Exception as e:
        all_validation_failures.append(f"ScorecardEstimateResponse creation failed: {e}")

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
