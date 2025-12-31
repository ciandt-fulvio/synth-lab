"""
ChartInsight entity for synth-lab.

Represents an AI-generated insight for a specific chart type in quantitative analysis.

References:
    - Spec: specs/023-quantitative-ai-insights/spec.md
    - Data Model: specs/023-quantitative-ai-insights/data-model.md
"""

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

# Type alias for chart types
ChartType = Literal[
    "try_vs_success",
    "distribution",
    "failure_heatmap",
    "scatter",
    "box_plot",
    "clustering",
    "outliers",
    "shap_summary",
    "pdp",
    "dendrogram",
    "extreme_cases",
    "pca_scatter",
    "radar_comparison",
]


class ChartInsight(BaseModel):
    """AI-generated insight for a specific chart type."""

    analysis_id: str = Field(
        pattern=r"^ana_[a-f0-9]{8}$",
        description="Parent analysis ID",
    )
    chart_type: str = Field(
        description="Chart type identifier (e.g., 'try_vs_success', 'shap_summary')",
    )
    summary: str = Field(
        description="AI-generated insight summary in Portuguese",
        max_length=2000,
    )
    generation_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When this insight was generated",
    )
    status: str = Field(
        description="Generation status: pending|completed|failed",
        pattern="^(pending|completed|failed)$",
    )
    model: str = Field(
        description="LLM model used (e.g., 'gpt-4.1-mini')",
        default="gpt-4.1-mini",
    )

    def to_cache_json(self) -> dict:
        """Convert to JSON format for storage in analysis_cache.data."""
        data = self.model_dump()
        # Convert datetime to ISO string for JSON serialization
        if isinstance(data.get("generation_timestamp"), datetime):
            data["generation_timestamp"] = data["generation_timestamp"].isoformat()
        return data

    @classmethod
    def from_cache_json(cls, data: dict) -> "ChartInsight":
        """Create from JSON stored in analysis_cache.data."""
        return cls(**data)


class SimulationInsights(BaseModel):
    """Collection of all insights for a simulation."""

    simulation_id: str = Field(description="Simulation ID")
    insights: list[ChartInsight] = Field(
        default_factory=list,
        description="List of chart insights",
    )
    executive_summary: str | None = Field(
        default=None,
        description="Executive summary synthesizing all insights",
    )
    total_charts_analyzed: int = Field(
        default=0,
        description="Total number of charts analyzed",
    )


if __name__ == "__main__":
    import sys

    all_validation_failures = []
    total_tests = 0

    # Test 1: Create minimal insight
    total_tests += 1
    try:
        insight = ChartInsight(
            analysis_id="ana_12345678",
            chart_type="try_vs_success",
            summary="Insight sobre o gráfico de tentativa vs sucesso",
            status="completed",
        )
        if insight.chart_type != "try_vs_success":
            all_validation_failures.append(
                f"chart_type mismatch: {insight.chart_type}")
    except Exception as e:
        all_validation_failures.append(f"Create minimal insight failed: {e}")

    # Test 2: Validate status pattern
    total_tests += 1
    try:
        ChartInsight(
            analysis_id="ana_12345678",
            chart_type="pca_scatter",
            summary="Test",
            status="invalid_status",  # Should fail
        )
        all_validation_failures.append("Should reject invalid status")
    except ValueError:
        pass  # Expected

    # Test 3: JSON serialization roundtrip
    total_tests += 1
    try:
        original = ChartInsight(
            analysis_id="ana_12345678",
            chart_type="radar_comparison",
            summary="Segmentação revela padrões comportamentais distintos",
            status="completed",
        )
        json_data = original.to_cache_json()
        restored = ChartInsight.from_cache_json(json_data)
        if restored.chart_type != original.chart_type:
            all_validation_failures.append(
                f"JSON roundtrip chart_type mismatch: {restored.chart_type}"
            )
        if restored.summary != original.summary:
            all_validation_failures.append(
                "JSON roundtrip summary mismatch")
    except Exception as e:
        all_validation_failures.append(
            f"JSON serialization roundtrip failed: {e}")

    # Test 4: Default model is gpt-4.1-mini
    total_tests += 1
    try:
        insight = ChartInsight(
            analysis_id="ana_12345678",
            chart_type="extreme_cases",
            summary="Test",
            status="pending",
        )
        if insight.model != "gpt-4.1-mini":
            all_validation_failures.append(
                f"Default model should be gpt-4.1-mini, got {insight.model}")
    except Exception as e:
        all_validation_failures.append(f"Default model test failed: {e}")

    # Final validation result
    if all_validation_failures:
        print(
            f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(
            f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("ChartInsight entity is validated and ready for use")
        sys.exit(0)
