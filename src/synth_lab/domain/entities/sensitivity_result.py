"""
Sensitivity result entities for synth-lab.

Defines models for sensitivity analysis results.

References:
    - Spec: specs/016-feature-impact-simulation/spec.md
    - Data model: specs/016-feature-impact-simulation/data-model.md
"""

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class DimensionSensitivity(BaseModel):
    """Sensitivity analysis for a single scorecard dimension."""

    dimension: str = Field(
        description="Dimension name: complexity, initial_effort, perceived_risk, time_to_value",
    )

    # Values tested
    baseline_value: float = Field(
        ge=0.0,
        le=1.0,
        description="Original baseline value of this dimension.",
    )

    deltas_tested: list[float] = Field(
        description="Delta values tested. Ex: [-0.10, -0.05, +0.05, +0.10]",
    )

    # Results by delta
    outcomes_by_delta: dict[str, dict[str, float]] = Field(
        description="Outcomes for each delta. "
        "Ex: {'-0.10': {'did_not_try': 0.20, 'failed': 0.30, 'success': 0.50}}",
    )

    # Sensitivity indices
    sensitivity_index: float = Field(
        description="Sensitivity index: (% change output) / (% change input)",
    )

    # Ranking
    rank: int = Field(
        ge=1,
        description="Rank among dimensions (1 = most sensitive).",
    )


class SensitivityResult(BaseModel):
    """Complete result of sensitivity analysis."""

    simulation_id: str = Field(description="ID of the base simulation.")

    analyzed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of analysis.",
    )

    # Configuration
    deltas_used: list[float] = Field(
        description="Delta values used in analysis. Ex: [0.05, 0.10]",
    )

    # Results per dimension
    dimensions: list[DimensionSensitivity] = Field(
        description="Sensitivity results for each dimension.",
    )

    # Most impactful dimension
    most_sensitive_dimension: str = Field(
        description="Name of the most sensitive dimension.",
    )


if __name__ == "__main__":
    import sys

    all_validation_failures = []
    total_tests = 0

    # Test 1: Create valid DimensionSensitivity
    total_tests += 1
    try:
        dim = DimensionSensitivity(
            dimension="complexity",
            baseline_value=0.4,
            deltas_tested=[-0.10, -0.05, 0.05, 0.10],
            outcomes_by_delta={
                "-0.10": {"did_not_try": 0.18, "failed": 0.30, "success": 0.52},
                "-0.05": {"did_not_try": 0.20, "failed": 0.32, "success": 0.48},
                "+0.05": {"did_not_try": 0.24, "failed": 0.40, "success": 0.36},
                "+0.10": {"did_not_try": 0.26, "failed": 0.46, "success": 0.28},
            },
            sensitivity_index=1.45,
            rank=1,
        )
        if dim.dimension != "complexity":
            all_validation_failures.append(f"dimension mismatch: {dim.dimension}")
    except Exception as e:
        all_validation_failures.append(f"DimensionSensitivity creation failed: {e}")

    # Test 2: Reject invalid baseline_value
    total_tests += 1
    try:
        DimensionSensitivity(
            dimension="test",
            baseline_value=1.5,  # Invalid
            deltas_tested=[0.05],
            outcomes_by_delta={},
            sensitivity_index=0.0,
            rank=1,
        )
        all_validation_failures.append("Should reject baseline > 1")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Unexpected error for invalid baseline: {e}")

    # Test 3: Reject invalid rank
    total_tests += 1
    try:
        DimensionSensitivity(
            dimension="test",
            baseline_value=0.5,
            deltas_tested=[0.05],
            outcomes_by_delta={},
            sensitivity_index=0.0,
            rank=0,  # Invalid (must be >= 1)
        )
        all_validation_failures.append("Should reject rank < 1")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Unexpected error for invalid rank: {e}")

    # Test 4: Create valid SensitivityResult
    total_tests += 1
    try:
        result = SensitivityResult(
            simulation_id="sim_abc12345",
            deltas_used=[0.05, 0.10],
            dimensions=[
                DimensionSensitivity(
                    dimension="complexity",
                    baseline_value=0.4,
                    deltas_tested=[-0.10, 0.10],
                    outcomes_by_delta={},
                    sensitivity_index=1.45,
                    rank=1,
                ),
                DimensionSensitivity(
                    dimension="time_to_value",
                    baseline_value=0.5,
                    deltas_tested=[-0.10, 0.10],
                    outcomes_by_delta={},
                    sensitivity_index=0.82,
                    rank=2,
                ),
            ],
            most_sensitive_dimension="complexity",
        )
        if result.most_sensitive_dimension != "complexity":
            all_validation_failures.append(
                f"most_sensitive mismatch: {result.most_sensitive_dimension}"
            )
    except Exception as e:
        all_validation_failures.append(f"SensitivityResult creation failed: {e}")

    # Test 5: analyzed_at default
    total_tests += 1
    try:
        result = SensitivityResult(
            simulation_id="sim_test",
            deltas_used=[0.05],
            dimensions=[],
            most_sensitive_dimension="test",
        )
        if result.analyzed_at is None:
            all_validation_failures.append("analyzed_at should be set automatically")
    except Exception as e:
        all_validation_failures.append(f"analyzed_at default test failed: {e}")

    # Test 6: Model dump
    total_tests += 1
    try:
        result = SensitivityResult(
            simulation_id="sim_test",
            deltas_used=[0.05, 0.10],
            dimensions=[
                DimensionSensitivity(
                    dimension="complexity",
                    baseline_value=0.4,
                    deltas_tested=[0.05],
                    outcomes_by_delta={},
                    sensitivity_index=1.0,
                    rank=1,
                ),
            ],
            most_sensitive_dimension="complexity",
        )
        dump = result.model_dump()
        if "dimensions" not in dump:
            all_validation_failures.append("model_dump missing dimensions")
        if len(dump["dimensions"]) != 1:
            all_validation_failures.append("model_dump dimensions count mismatch")
    except Exception as e:
        all_validation_failures.append(f"model_dump test failed: {e}")

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
