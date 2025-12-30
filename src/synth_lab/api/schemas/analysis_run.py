"""
API schemas for analysis runs.

Pydantic schemas for analysis run API request/response handling.
Supports 1:1 relationship with experiments.

References:
    - OpenAPI: specs/019-experiment-refactor/contracts/analysis-api.yaml
    - Data model: specs/019-experiment-refactor/data-model.md
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from synth_lab.models.pagination import PaginationMeta

# =============================================================================
# Analysis Configuration
# =============================================================================


class AnalysisConfigSchema(BaseModel):
    """Schema for analysis configuration."""

    n_synths: int = Field(
        default=500,
        ge=10,
        le=10000,
        description="Number of synths to simulate.",
        examples=[500],
    )

    n_executions: int = Field(
        default=100,
        ge=10,
        le=1000,
        description="Number of Monte Carlo executions per synth.",
        examples=[100],
    )

    sigma: float = Field(
        default=0.05,
        ge=0.0,
        le=0.5,
        description="Standard deviation for noise.",
        examples=[0.05],
    )

    seed: int | None = Field(
        default=None,
        description="Random seed for reproducibility.",
        examples=[42],
    )


# =============================================================================
# Aggregated Outcomes
# =============================================================================


class AggregatedOutcomesSchema(BaseModel):
    """Schema for aggregated analysis outcomes."""

    did_not_try_rate: float = Field(
        ge=0.0,
        le=1.0,
        description="Proportion that did not try.",
        examples=[0.2],
    )

    failed_rate: float = Field(
        ge=0.0,
        le=1.0,
        description="Proportion that tried but failed.",
        examples=[0.3],
    )

    success_rate: float = Field(
        ge=0.0,
        le=1.0,
        description="Proportion that succeeded.",
        examples=[0.5],
    )


# =============================================================================
# Analysis Response Schemas
# =============================================================================


class AnalysisResponse(BaseModel):
    """Full response schema for analysis run."""

    id: str = Field(
        description="Analysis run ID.",
        examples=["ana_a1b2c3d4"],
    )

    experiment_id: str = Field(
        description="Parent experiment ID.",
        examples=["exp_a1b2c3d4"],
    )

    config: AnalysisConfigSchema = Field(
        description="Analysis configuration.",
    )

    status: Literal["pending", "running", "completed", "failed"] = Field(
        description="Current status.",
        examples=["completed"],
    )

    started_at: datetime = Field(
        description="When analysis started.",
    )

    completed_at: datetime | None = Field(
        default=None,
        description="When analysis completed.",
    )

    total_synths: int = Field(
        default=0,
        ge=0,
        description="Number of synths in analysis.",
    )

    aggregated_outcomes: AggregatedOutcomesSchema | None = Field(
        default=None,
        description="Aggregated results.",
    )

    execution_time_seconds: float | None = Field(
        default=None,
        ge=0.0,
        description="How long analysis took in seconds.",
    )


# =============================================================================
# Synth Outcome Schemas
# =============================================================================


class SynthAttributesSchema(BaseModel):
    """Schema for synth simulation attributes."""

    observables: dict[str, float] = Field(
        description="Observable attributes (0-1 values).",
        examples=[
            {
                "digital_literacy": 0.65,
                "similar_tool_experience": 0.45,
                "motor_ability": 0.90,
                "time_availability": 0.30,
                "domain_expertise": 0.55,
            }
        ],
    )

    latent_traits: dict[str, float] = Field(
        description="Latent traits (0-1 values).",
        examples=[
            {
                "capability_mean": 0.58,
                "trust_mean": 0.42,
                "friction_tolerance_mean": 0.35,
                "exploration_prob": 0.40,
            }
        ],
    )


class SynthOutcomeResponse(BaseModel):
    """Response schema for individual synth outcome."""

    id: str = Field(
        description="Outcome ID.",
        examples=["out_a1b2c3d4"],
    )

    synth_id: str = Field(
        description="Synth ID.",
        examples=["synth_001"],
    )

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

    synth_attributes: SynthAttributesSchema = Field(
        description="Synth's simulation attributes.",
    )


class PaginatedSynthOutcomes(BaseModel):
    """Paginated list of synth outcomes."""

    data: list[SynthOutcomeResponse] = Field(
        description="List of synth outcomes.",
    )

    pagination: PaginationMeta = Field(
        description="Pagination metadata.",
    )


# =============================================================================
# Region Analysis Schemas
# =============================================================================


class RegionSchema(BaseModel):
    """Schema for a high-risk region cluster."""

    cluster_id: int = Field(
        description="Cluster identifier.",
    )

    synth_count: int = Field(
        ge=0,
        description="Number of synths in cluster.",
    )

    avg_failure_rate: float = Field(
        ge=0.0,
        le=1.0,
        description="Average failure rate in cluster.",
    )

    common_attributes: dict[str, Any] = Field(
        default_factory=dict,
        description="Common attributes of synths in cluster.",
    )

    representative_synths: list[str] = Field(
        default_factory=list,
        description="IDs of representative synths.",
    )


class RegionAnalysisResponse(BaseModel):
    """Response for region analysis."""

    regions: list[RegionSchema] = Field(
        description="Identified high-risk regions.",
    )


# =============================================================================
# Interview Suggestion Schemas
# =============================================================================


class InterviewSuggestionSchema(BaseModel):
    """Schema for a single interview suggestion."""

    synth_id: str = Field(
        description="Synth ID to interview.",
    )

    synth_name: str = Field(
        description="Synth display name.",
    )

    reason: str = Field(
        description="Reason for suggestion.",
    )

    failure_rate: float = Field(
        ge=0.0,
        le=1.0,
        description="Synth's failure rate.",
    )

    cluster_id: int | None = Field(
        default=None,
        description="Cluster the synth belongs to.",
    )


class InterviewSuggestionsResponse(BaseModel):
    """Response for interview suggestions."""

    suggestions: list[InterviewSuggestionSchema] = Field(
        description="List of suggested synths to interview.",
    )


# =============================================================================
# Insights Schemas
# =============================================================================


class InsightSchema(BaseModel):
    """Schema for a single insight."""

    type: Literal["risk", "opportunity", "recommendation"] = Field(
        description="Type of insight.",
    )

    title: str = Field(
        description="Short title of the insight.",
    )

    description: str = Field(
        description="Detailed description.",
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence level (0-1).",
    )


class InsightsResponse(BaseModel):
    """Response for insights."""

    insights: list[InsightSchema] = Field(
        description="List of insights from analysis.",
    )

    generated_at: datetime = Field(
        description="When insights were generated.",
    )


# =============================================================================
# Validation
# =============================================================================

if __name__ == "__main__":
    import sys
    from datetime import timezone

    all_validation_failures: list[str] = []
    total_tests = 0

    # Test 1: AnalysisConfigSchema defaults
    total_tests += 1
    try:
        config = AnalysisConfigSchema()
        if config.n_synths != 500:
            all_validation_failures.append(f"n_synths default mismatch: {config.n_synths}")
        if config.n_executions != 100:
            all_validation_failures.append(f"n_executions default mismatch: {config.n_executions}")
        if config.sigma != 0.05:
            all_validation_failures.append(f"sigma default mismatch: {config.sigma}")
    except Exception as e:
        all_validation_failures.append(f"AnalysisConfigSchema creation failed: {e}")

    # Test 2: AnalysisConfigSchema custom values
    total_tests += 1
    try:
        config = AnalysisConfigSchema(n_synths=1000, n_executions=50, sigma=0.1, seed=42)
        if config.n_synths != 1000:
            all_validation_failures.append(f"n_synths custom mismatch: {config.n_synths}")
        if config.seed != 42:
            all_validation_failures.append(f"seed mismatch: {config.seed}")
    except Exception as e:
        all_validation_failures.append(f"AnalysisConfigSchema custom failed: {e}")

    # Test 3: Reject n_synths < 10
    total_tests += 1
    try:
        AnalysisConfigSchema(n_synths=5)
        all_validation_failures.append("Should reject n_synths < 10")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Unexpected error for n_synths < 10: {e}")

    # Test 4: AggregatedOutcomesSchema
    total_tests += 1
    try:
        outcomes = AggregatedOutcomesSchema(
            did_not_try_rate=0.2,
            failed_rate=0.3,
            success_rate=0.5,
        )
        if outcomes.success_rate != 0.5:
            all_validation_failures.append(f"success_rate mismatch: {outcomes.success_rate}")
    except Exception as e:
        all_validation_failures.append(f"AggregatedOutcomesSchema creation failed: {e}")

    # Test 5: AnalysisResponse complete
    total_tests += 1
    try:
        config = AnalysisConfigSchema()
        outcomes = AggregatedOutcomesSchema(
            did_not_try_rate=0.2,
            failed_rate=0.3,
            success_rate=0.5,
        )
        response = AnalysisResponse(
            id="ana_12345678",
            experiment_id="exp_12345678",
            config=config,
            status="completed",
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            total_synths=500,
            aggregated_outcomes=outcomes,
            execution_time_seconds=12.5,
        )
        if response.status != "completed":
            all_validation_failures.append(f"status mismatch: {response.status}")
        if response.total_synths != 500:
            all_validation_failures.append(f"total_synths mismatch: {response.total_synths}")
    except Exception as e:
        all_validation_failures.append(f"AnalysisResponse creation failed: {e}")

    # Test 6: SynthOutcomeResponse
    total_tests += 1
    try:
        attrs = SynthAttributesSchema(
            observables={
                "digital_literacy": 0.65,
                "similar_tool_experience": 0.45,
            },
            latent_traits={
                "capability_mean": 0.58,
                "trust_mean": 0.42,
            },
        )
        outcome = SynthOutcomeResponse(
            id="out_12345678",
            synth_id="synth_001",
            did_not_try_rate=0.2,
            failed_rate=0.3,
            success_rate=0.5,
            synth_attributes=attrs,
        )
        if outcome.success_rate != 0.5:
            all_validation_failures.append(f"outcome success_rate mismatch: {outcome.success_rate}")
    except Exception as e:
        all_validation_failures.append(f"SynthOutcomeResponse creation failed: {e}")

    # Test 7: RegionSchema
    total_tests += 1
    try:
        region = RegionSchema(
            cluster_id=1,
            synth_count=50,
            avg_failure_rate=0.65,
            common_attributes={"low_digital_literacy": True},
            representative_synths=["synth_001", "synth_015"],
        )
        if region.avg_failure_rate != 0.65:
            all_validation_failures.append(f"avg_failure_rate mismatch: {region.avg_failure_rate}")
    except Exception as e:
        all_validation_failures.append(f"RegionSchema creation failed: {e}")

    # Test 8: InterviewSuggestionSchema
    total_tests += 1
    try:
        suggestion = InterviewSuggestionSchema(
            synth_id="synth_001",
            synth_name="Maria Silva",
            reason="High failure rate in low-trust cluster",
            failure_rate=0.75,
            cluster_id=2,
        )
        if suggestion.failure_rate != 0.75:
            all_validation_failures.append("suggestion failure_rate mismatch")
    except Exception as e:
        all_validation_failures.append(f"InterviewSuggestionSchema creation failed: {e}")

    # Test 9: InsightSchema
    total_tests += 1
    try:
        insight = InsightSchema(
            type="risk",
            title="Low Trust Users",
            description="Users with low trust scores show 70% failure rate",
            confidence=0.85,
        )
        if insight.type != "risk":
            all_validation_failures.append(f"insight type mismatch: {insight.type}")
    except Exception as e:
        all_validation_failures.append(f"InsightSchema creation failed: {e}")

    # Test 10: InsightsResponse
    total_tests += 1
    try:
        insight = InsightSchema(
            type="opportunity",
            title="High-Trust Users",
            description="Users with high trust show 90% success",
            confidence=0.90,
        )
        response = InsightsResponse(
            insights=[insight],
            generated_at=datetime.now(timezone.utc),
        )
        if len(response.insights) != 1:
            all_validation_failures.append(f"insights count mismatch: {len(response.insights)}")
    except Exception as e:
        all_validation_failures.append(f"InsightsResponse creation failed: {e}")

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
