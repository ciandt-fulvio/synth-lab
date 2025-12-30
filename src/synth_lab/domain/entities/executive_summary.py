"""
ExecutiveSummary entity for synth-lab.

Represents aggregated synthesis of all chart insights for an analysis.

References:
    - Spec: specs/023-quantitative-ai-insights/spec.md
    - Data Model: specs/023-quantitative-ai-insights/data-model.md
"""

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class ExecutiveSummary(BaseModel):
    """Aggregated synthesis of all chart insights."""

    analysis_id: str = Field(
        pattern=r"^ana_[a-f0-9]{8}$",
        description="Parent analysis ID",
    )
    overview: str = Field(
        description="What was tested and overall results (≤200 words)",
        max_length=1000,
    )
    explainability: str = Field(
        description="Key drivers and feature impacts (≤200 words)",
        max_length=1000,
    )
    segmentation: str = Field(
        description="User groups and behavioral patterns (≤200 words)",
        max_length=1000,
    )
    edge_cases: str = Field(
        description="Surprises, anomalies, unexpected findings (≤200 words)",
        max_length=1000,
    )
    recommendations: list[str] = Field(
        description="2-3 actionable recommendations for product team",
        min_length=2,
        max_length=3,
    )
    included_chart_types: list[str] = Field(
        description="Chart types that contributed to this summary",
        min_length=1,
    )
    generation_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When this summary was generated",
    )
    status: str = Field(
        description="Generation status: pending|completed|failed|partial",
        pattern="^(pending|completed|failed|partial)$",
    )
    model: str = Field(
        description="LLM model used (e.g., '04-mini')",
        default="04-mini",
    )

    def to_cache_json(self) -> dict:
        """Convert to JSON format for storage in analysis_cache.data."""
        data = self.model_dump()
        # Convert datetime to ISO string for JSON serialization
        if isinstance(data.get("generation_timestamp"), datetime):
            data["generation_timestamp"] = data["generation_timestamp"].isoformat()
        return data

    @classmethod
    def from_cache_json(cls, data: dict) -> "ExecutiveSummary":
        """Create from JSON stored in analysis_cache.data."""
        return cls(**data)


if __name__ == "__main__":
    import sys

    all_validation_failures = []
    total_tests = 0

    # Test 1: Create minimal summary
    total_tests += 1
    try:
        summary = ExecutiveSummary(
            analysis_id="ana_12345678",
            overview="Tested checkout flow with 500 synths",
            explainability="Trust and capability are main drivers",
            segmentation="3 distinct user groups identified",
            edge_cases="High-capability users failing unexpectedly",
            recommendations=["Simplify payment form", "Add trust signals"],
            included_chart_types=["try_vs_success", "shap_summary"],
            status="completed",
        )
        if summary.analysis_id != "ana_12345678":
            all_validation_failures.append(
                f"analysis_id mismatch: {summary.analysis_id}")
    except Exception as e:
        all_validation_failures.append(f"Create minimal summary failed: {e}")

    # Test 2: Validate recommendations length constraints
    total_tests += 1
    try:
        # Too few recommendations (< 2)
        ExecutiveSummary(
            analysis_id="ana_12345678",
            overview="Test",
            explainability="Test",
            segmentation="Test",
            edge_cases="Test",
            recommendations=["Only one"],  # Should fail
            included_chart_types=["try_vs_success"],
            status="completed",
        )
        all_validation_failures.append("Should reject < 2 recommendations")
    except ValueError:
        pass  # Expected

    # Test 3: Validate recommendations max length
    total_tests += 1
    try:
        # Too many recommendations (> 3)
        ExecutiveSummary(
            analysis_id="ana_12345678",
            overview="Test",
            explainability="Test",
            segmentation="Test",
            edge_cases="Test",
            recommendations=["R1", "R2", "R3", "R4"],  # Should fail
            included_chart_types=["try_vs_success"],
            status="completed",
        )
        all_validation_failures.append("Should reject > 3 recommendations")
    except ValueError:
        pass  # Expected

    # Test 4: Validate status pattern (including 'partial')
    total_tests += 1
    try:
        summary = ExecutiveSummary(
            analysis_id="ana_12345678",
            overview="Partial summary",
            explainability="Limited data",
            segmentation="Awaiting insights",
            edge_cases="Not yet analyzed",
            recommendations=["Wait for completion", "Review partial data"],
            included_chart_types=["try_vs_success"],
            status="partial",  # Should be valid
        )
        if summary.status != "partial":
            all_validation_failures.append(
                f"Status 'partial' should be valid, got {summary.status}")
    except Exception as e:
        all_validation_failures.append(f"Partial status test failed: {e}")

    # Test 5: JSON serialization roundtrip
    total_tests += 1
    try:
        original = ExecutiveSummary(
            analysis_id="ana_12345678",
            overview="Comprehensive test of checkout UX",
            explainability="SHAP analysis shows trust is #1 driver",
            segmentation="PCA reveals 3 behavioral clusters",
            edge_cases="10 high-capability users failed due to security concerns",
            recommendations=[
                "Add visible security badges",
                "Simplify payment form fields",
                "Provide onboarding for new users",
            ],
            included_chart_types=[
                "try_vs_success",
                "shap_summary",
                "pdp",
                "pca_scatter",
                "radar_comparison",
                "extreme_cases",
                "outliers",
            ],
            status="completed",
        )
        json_data = original.to_cache_json()
        restored = ExecutiveSummary.from_cache_json(json_data)
        if restored.analysis_id != original.analysis_id:
            all_validation_failures.append(
                f"JSON roundtrip analysis_id mismatch: {restored.analysis_id}"
            )
        if len(restored.recommendations) != len(original.recommendations):
            all_validation_failures.append(
                "JSON roundtrip recommendations count mismatch")
        if len(restored.included_chart_types) != 7:
            all_validation_failures.append(
                f"JSON roundtrip included_chart_types count: expected 7, got {len(restored.included_chart_types)}"
            )
    except Exception as e:
        all_validation_failures.append(
            f"JSON serialization roundtrip failed: {e}")

    # Test 6: included_chart_types minimum length
    total_tests += 1
    try:
        ExecutiveSummary(
            analysis_id="ana_12345678",
            overview="Test",
            explainability="Test",
            segmentation="Test",
            edge_cases="Test",
            recommendations=["R1", "R2"],
            included_chart_types=[],  # Should fail (min 1)
            status="completed",
        )
        all_validation_failures.append(
            "Should reject empty included_chart_types")
    except ValueError:
        pass  # Expected

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
        print("ExecutiveSummary entity is validated and ready for use")
        sys.exit(0)
