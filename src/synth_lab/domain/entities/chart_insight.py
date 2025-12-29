"""
ChartInsight entity for synth-lab.

Represents an AI-generated insight for a specific chart type in quantitative analysis.

References:
    - Spec: specs/023-quantitative-ai-insights/spec.md
    - Data Model: specs/023-quantitative-ai-insights/data-model.md
"""

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class ChartInsight(BaseModel):
    """AI-generated insight for a specific chart type."""

    analysis_id: str = Field(
        pattern=r"^ana_[a-f0-9]{8}$",
        description="Parent analysis ID",
    )
    chart_type: str = Field(
        description="Chart type identifier (e.g., 'try_vs_success', 'shap_summary')",
    )
    problem_understanding: str = Field(
        description="AI's understanding of what is being tested",
    )
    trends_observed: str = Field(
        description="Key patterns and trends identified in the data",
    )
    key_findings: list[str] = Field(
        description="2-4 actionable insights for the product team",
        min_length=2,
        max_length=4,
    )
    summary: str = Field(
        description="Concise summary in ≤200 words",
        max_length=1000,  # ~200 words * 5 chars/word
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
        description="LLM model used (e.g., 'o1-mini')",
        default="o1-mini",
    )
    reasoning_trace: str | None = Field(
        description="Optional: LLM reasoning steps for debugging",
        default=None,
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
            problem_understanding="Testing checkout flow",
            trends_observed="High try rate, moderate conversion",
            key_findings=["Finding 1", "Finding 2"],
            summary="Summary of findings",
            status="completed",
        )
        if insight.chart_type != "try_vs_success":
            all_validation_failures.append(f"chart_type mismatch: {insight.chart_type}")
    except Exception as e:
        all_validation_failures.append(f"Create minimal insight failed: {e}")

    # Test 2: Validate key_findings length constraints
    total_tests += 1
    try:
        # Too few findings (< 2)
        ChartInsight(
            analysis_id="ana_12345678",
            chart_type="shap_summary",
            problem_understanding="Test",
            trends_observed="Test",
            key_findings=["Only one"],  # Should fail
            summary="Test",
            status="completed",
        )
        all_validation_failures.append("Should reject < 2 key_findings")
    except ValueError:
        pass  # Expected

    # Test 3: Validate key_findings max length
    total_tests += 1
    try:
        # Too many findings (> 4)
        ChartInsight(
            analysis_id="ana_12345678",
            chart_type="pdp",
            problem_understanding="Test",
            trends_observed="Test",
            key_findings=["F1", "F2", "F3", "F4", "F5"],  # Should fail
            summary="Test",
            status="completed",
        )
        all_validation_failures.append("Should reject > 4 key_findings")
    except ValueError:
        pass  # Expected

    # Test 4: Validate status pattern
    total_tests += 1
    try:
        ChartInsight(
            analysis_id="ana_12345678",
            chart_type="pca_scatter",
            problem_understanding="Test",
            trends_observed="Test",
            key_findings=["F1", "F2"],
            summary="Test",
            status="invalid_status",  # Should fail
        )
        all_validation_failures.append("Should reject invalid status")
    except ValueError:
        pass  # Expected

    # Test 5: JSON serialization roundtrip
    total_tests += 1
    try:
        original = ChartInsight(
            analysis_id="ana_12345678",
            chart_type="radar_comparison",
            problem_understanding="Testing segments",
            trends_observed="3 distinct clusters",
            key_findings=["Cluster 1 high success", "Cluster 2 low trust"],
            summary="Segmentation reveals distinct behavioral patterns",
            status="completed",
            reasoning_trace="Step 1: Analyzed data...",
        )
        json_data = original.to_cache_json()
        restored = ChartInsight.from_cache_json(json_data)
        if restored.chart_type != original.chart_type:
            all_validation_failures.append(
                f"JSON roundtrip chart_type mismatch: {restored.chart_type}"
            )
        if len(restored.key_findings) != len(original.key_findings):
            all_validation_failures.append("JSON roundtrip key_findings count mismatch")
    except Exception as e:
        all_validation_failures.append(f"JSON serialization roundtrip failed: {e}")

    # Test 6: Default model is o1-mini
    total_tests += 1
    try:
        insight = ChartInsight(
            analysis_id="ana_12345678",
            chart_type="extreme_cases",
            problem_understanding="Test",
            trends_observed="Test",
            key_findings=["F1", "F2"],
            summary="Test",
            status="pending",
        )
        if insight.model != "o1-mini":
            all_validation_failures.append(f"Default model should be o1-mini, got {insight.model}")
    except Exception as e:
        all_validation_failures.append(f"Default model test failed: {e}")

    # Final validation result
    if all_validation_failures:
        print(f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("ChartInsight entity is validated and ready for use")
        sys.exit(0)
