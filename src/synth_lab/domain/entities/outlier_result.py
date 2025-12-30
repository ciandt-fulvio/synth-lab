"""
Outlier detection entities for UX Research analysis.

This module defines entities for identifying extreme cases and outliers
in simulation results, helping UX Researchers find interesting synths
for qualitative interviews.

References:
    - Isolation Forest: scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html
    - Outlier Detection: scikit-learn.org/stable/modules/outlier_detection.html

Sample Input:
    outcomes: list[SynthOutcome] with success/failure rates

Expected Output:
    ExtremeCasesTable: Top 10 worst failures, best successes, unexpected cases
    OutlierResult: Synths identified as outliers with anomaly scores
"""

from pydantic import BaseModel, Field, computed_field


class ExtremeSynth(BaseModel):
    """Single extreme case synth for qualitative analysis."""

    synth_id: str = Field(..., description="Synth identifier")
    synth_name: str = Field(default="", description="Synth display name")
    category: str = Field(
        ...,
        description="Category: worst_failure, best_success, or unexpected",
    )
    success_rate: float = Field(..., description="Success rate (0-1)")
    failed_rate: float = Field(..., description="Failed rate (0-1)")
    did_not_try_rate: float = Field(..., description="Did not try rate (0-1)")
    profile_summary: str = Field(..., description="Human-readable summary of synth profile")
    interview_questions: list[str] = Field(
        ..., description="Suggested questions for qualitative interview"
    )
    capability_mean: float = Field(..., description="Capability mean value")
    trust_mean: float = Field(..., description="Trust mean value")
    friction_tolerance_mean: float = Field(..., description="Friction tolerance mean value")


class ExtremeCasesTable(BaseModel):
    """Collection of extreme cases for qualitative research."""

    simulation_id: str = Field(..., description="Simulation identifier")
    worst_failures: list[ExtremeSynth] = Field(
        ..., description="Top 10 synths with worst failure rates"
    )
    best_successes: list[ExtremeSynth] = Field(
        ..., description="Top 10 synths with best success rates"
    )
    unexpected_cases: list[ExtremeSynth] = Field(
        ...,
        description="Synths with unexpected outcomes given their attributes",
    )
    total_synths: int = Field(..., description="Total number of synths analyzed")


class OutlierSynth(BaseModel):
    """Single outlier synth identified by statistical methods."""

    synth_id: str = Field(..., description="Synth identifier")
    outlier_type: str = Field(
        ...,
        description="Type: unexpected_failure, unexpected_success, or atypical_profile",
    )
    anomaly_score: float = Field(..., description="Anomaly score from Isolation Forest (-1 to 1)")
    success_rate: float = Field(..., description="Success rate (0-1)")
    failed_rate: float = Field(..., description="Failed rate (0-1)")
    did_not_try_rate: float = Field(..., description="Did not try rate (0-1)")
    explanation: str = Field(..., description="Explanation of why this synth is an outlier")
    capability_mean: float = Field(..., description="Capability mean value")
    trust_mean: float = Field(..., description="Trust mean value")
    friction_tolerance_mean: float = Field(..., description="Friction tolerance mean value")
    digital_literacy: float = Field(..., description="Digital literacy observable")
    similar_tool_experience: float = Field(..., description="Similar tool experience observable")


class OutlierResult(BaseModel):
    """Result of outlier detection analysis."""

    simulation_id: str = Field(..., description="Simulation identifier")
    method: str = Field(default="isolation_forest", description="Detection method used")
    contamination: float = Field(..., description="Expected proportion of outliers (0-0.5)")
    outliers: list[OutlierSynth] = Field(..., description="List of identified outliers")
    total_synths: int = Field(..., description="Total number of synths analyzed")
    n_outliers: int = Field(..., description="Number of outliers detected")
    features_used: list[str] = Field(..., description="Features used for outlier detection")

    @computed_field
    @property
    def outlier_percentage(self) -> float:
        """Calculate outlier percentage for frontend display."""
        if self.total_synths == 0:
            return 0.0
        return (self.n_outliers / self.total_synths) * 100
