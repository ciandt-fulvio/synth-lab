"""
Explainability entities for UX Research analysis using SHAP and PDP.

This module defines entities for explaining individual synth outcomes
using SHAP (SHapley Additive exPlanations) values and Partial Dependence
Plots (PDP).

References:
    - SHAP: github.com/shap/shap
    - SHAP Paper: arxiv.org/abs/1705.07874
    - PDP: scikit-learn.org/stable/modules/partial_dependence.html

Sample Input:
    outcomes: list[SynthOutcome], synth_id: str

Expected Output:
    ShapExplanation: Feature contributions explaining why synth succeeded/failed
    PDPResult: How changing features affects success probability
"""

from pydantic import BaseModel, Field


class ShapContribution(BaseModel):
    """SHAP contribution for a single feature."""

    feature_name: str = Field(..., description="Name of the feature")
    feature_value: float = Field(..., description="Actual value of the feature")
    shap_value: float = Field(
        ..., description="SHAP value (contribution to prediction)"
    )
    baseline_value: float = Field(
        ..., description="Average feature value in population"
    )
    impact: str = Field(
        ...,
        description="Impact direction: positive (increases success), negative (decreases success)",
    )


class ShapExplanation(BaseModel):
    """SHAP explanation for a single synth."""

    synth_id: str = Field(..., description="Synth identifier")
    simulation_id: str = Field(..., description="Simulation identifier")
    predicted_success_rate: float = Field(
        ..., description="Model's predicted success rate"
    )
    actual_success_rate: float = Field(..., description="Actual observed success rate")
    baseline_prediction: float = Field(
        ..., description="Average prediction across all synths"
    )
    contributions: list[ShapContribution] = Field(
        ..., description="SHAP contributions for each feature, sorted by absolute value"
    )
    explanation_text: str = Field(
        ...,
        description="Human-readable explanation of why synth succeeded/failed",
    )
    model_type: str = Field(
        default="gradient_boosting", description="ML model used for predictions"
    )


class ShapSummary(BaseModel):
    """Global SHAP summary showing feature importance."""

    simulation_id: str = Field(..., description="Simulation identifier")
    feature_importances: dict[str, float] = Field(
        ..., description="Average absolute SHAP value per feature"
    )
    top_features: list[str] = Field(
        ..., description="Top 10 most important features"
    )
    total_synths: int = Field(..., description="Number of synths analyzed")
    model_score: float = Field(
        ..., description="Model R² score (goodness of fit)"
    )


class PDPPoint(BaseModel):
    """Single point in a partial dependence plot."""

    feature_value: float = Field(..., description="Value of the feature")
    predicted_success: float = Field(
        ..., description="Predicted success rate at this feature value"
    )
    confidence_lower: float | None = Field(
        None, description="Lower bound of confidence interval (if available)"
    )
    confidence_upper: float | None = Field(
        None, description="Upper bound of confidence interval (if available)"
    )


class PDPResult(BaseModel):
    """Partial dependence plot for a single feature."""

    simulation_id: str = Field(..., description="Simulation identifier")
    feature_name: str = Field(..., description="Feature being analyzed")
    feature_display_name: str = Field(..., description="Human-readable feature name")
    pdp_values: list[PDPPoint] = Field(
        ..., description="PDP curve values (sorted by feature_value)"
    )
    effect_type: str = Field(
        ...,
        description="Type of effect: monotonic_increasing, monotonic_decreasing, non_linear, flat",
    )
    effect_strength: float = Field(
        ...,
        description="Strength of effect (range of predicted values)",
    )
    baseline_value: float = Field(
        ..., description="Average feature value in population"
    )


class PDPComparison(BaseModel):
    """Comparison of PDPs for multiple features."""

    simulation_id: str = Field(..., description="Simulation identifier")
    pdp_results: list[PDPResult] = Field(
        ..., description="PDP curves for different features"
    )
    feature_ranking: list[str] = Field(
        ..., description="Features ranked by effect_strength"
    )
    total_synths: int = Field(..., description="Number of synths analyzed")
