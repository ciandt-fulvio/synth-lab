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
    ShapExplanation: Feature contributions explaining why synth adopted/not adopted
    PDPResult: How changing features affects adoption probability
"""

from pydantic import BaseModel, Field


class ShapContribution(BaseModel):
    """SHAP contribution for a single feature."""

    feature_name: str = Field(..., description="Name of the feature")
    feature_value: float = Field(..., description="Actual value of the feature")
    shap_value: float = Field(..., description="SHAP value (contribution to prediction)")
    baseline_value: float = Field(..., description="Average feature value in population")
    impact: str = Field(
        ...,
        description="Impact direction: positive (increases adoption), negative (decreases adoption)",
    )


class ShapExplanation(BaseModel):
    """SHAP explanation for a single synth."""

    synth_id: str = Field(..., description="Synth identifier")
    simulation_id: str = Field(..., description="Simulation identifier")
    predicted_adopted_rate: float = Field(..., description="Model's predicted adopted rate")
    actual_adopted_rate: float = Field(..., description="Actual observed adopted rate")
    baseline_prediction: float = Field(..., description="Average prediction across all synths")
    contributions: list[ShapContribution] = Field(
        ..., description="SHAP contributions for each feature, sorted by absolute value"
    )
    explanation_text: str = Field(
        ...,
        description="Human-readable explanation of why synth adopted/not adopted",
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
    top_features: list[str] = Field(..., description="Top 10 most important features")
    total_synths: int = Field(..., description="Number of synths analyzed")
    model_score: float = Field(..., description="Model R² score (goodness of fit)")
