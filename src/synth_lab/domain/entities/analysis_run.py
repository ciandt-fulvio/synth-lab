"""
Analysis run entity for synth-lab.

Represents a quantitative analysis execution (1:1 with Experiment).
Each experiment can have at most one analysis run at a time.

References:
    - Spec: specs/019-experiment-refactor/spec.md
    - Data model: specs/019-experiment-refactor/data-model.md
"""

import secrets
from datetime import datetime, timezone
from typing import Literal, Self

from pydantic import BaseModel, Field, model_validator


def generate_analysis_id() -> str:
    """
    Generate an analysis ID with ana_ prefix and 8-char hex suffix.

    Returns:
        str: ID in format ana_[a-f0-9]{8}
    """
    return f"ana_{secrets.token_hex(4)}"


class AnalysisConfig(BaseModel):
    """
    Configuration for quantitative analysis.

    Attributes:
        n_synths: Number of synths to simulate (10-10000)
        n_executions: Number of Monte Carlo executions per synth (10-1000)
        sigma: Standard deviation for noise (0.0-0.5)
        seed: Random seed for reproducibility
    """

    n_synths: int = Field(
        default=500,
        ge=10,
        le=10000,
        description="Number of synths to simulate.",
    )

    n_executions: int = Field(
        default=100,
        ge=10,
        le=1000,
        description="Number of Monte Carlo executions per synth.",
    )

    sigma: float = Field(
        default=0.05,
        ge=0.0,
        le=0.5,
        description="Standard deviation for noise.",
    )

    seed: int | None = Field(
        default=None,
        description="Random seed for reproducibility.",
    )


class AggregatedOutcomes(BaseModel):
    """
    Aggregated outcomes from quantitative analysis.

    Attributes:
        did_not_try_rate: Proportion that did not try (0-1)
        failed_rate: Proportion that tried but failed (0-1)
        success_rate: Proportion that succeeded (0-1)
    """

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

    @model_validator(mode="after")
    def validate_rates_sum(self) -> Self:
        """Ensure rates sum to 1.0 (with tolerance for rounding)."""
        total = self.did_not_try_rate + self.failed_rate + self.success_rate
        if not (0.99 <= total <= 1.01):
            raise ValueError(f"Rates must sum to 1.0, got {total}")
        return self


class AnalysisRun(BaseModel):
    """
    Quantitative analysis run (1:1 with Experiment).

    Represents a Monte Carlo simulation that estimates adoption rates
    for a feature based on synth population characteristics.

    Attributes:
        id: Unique identifier (ana_[a-f0-9]{8})
        experiment_id: Parent experiment ID (UNIQUE constraint enforces 1:1)
        scenario_id: Scenario ID used (baseline, crisis, first-use)
        config: Analysis configuration
        status: Current status (pending, running, completed, failed)
        started_at: When analysis started
        completed_at: When analysis completed
        total_synths: Number of synths in analysis
        aggregated_outcomes: Aggregated results
        execution_time_seconds: How long analysis took
    """

    id: str = Field(
        default_factory=generate_analysis_id,
        pattern=r"^ana_[a-f0-9]{8}$",
        description="Unique analysis ID.",
    )

    experiment_id: str = Field(
        pattern=r"^exp_[a-f0-9]{8}$",
        description="Parent experiment ID (enforces 1:1 relationship).",
    )

    scenario_id: str = Field(
        default="baseline",
        description="Scenario ID used for this analysis (baseline, crisis, first-use).",
    )

    config: AnalysisConfig = Field(
        default_factory=AnalysisConfig,
        description="Analysis configuration.",
    )

    status: Literal["pending", "running", "completed", "failed"] = Field(
        default="pending",
        description="Current status.",
    )

    started_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
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

    aggregated_outcomes: AggregatedOutcomes | None = Field(
        default=None,
        description="Aggregated results.",
    )

    execution_time_seconds: float | None = Field(
        default=None,
        ge=0.0,
        description="How long analysis took in seconds.",
    )

    def is_running(self) -> bool:
        """Check if analysis is currently running."""
        return self.status == "running"

    def is_completed(self) -> bool:
        """Check if analysis has completed."""
        return self.status == "completed"

    def has_results(self) -> bool:
        """Check if analysis has aggregated results."""
        return self.aggregated_outcomes is not None


if __name__ == "__main__":
    import sys

    all_validation_failures = []
    total_tests = 0

    # Test 1: Create with required fields
    total_tests += 1
    try:
        run = AnalysisRun(experiment_id="exp_12345678")
        if not run.id.startswith("ana_"):
            all_validation_failures.append(f"ID should start with ana_: {run.id}")
        if run.status != "pending":
            all_validation_failures.append(f"Status should be pending: {run.status}")
        if run.is_running():
            all_validation_failures.append("New run should not be running")
    except Exception as e:
        all_validation_failures.append(f"Create with required fields failed: {e}")

    # Test 2: ID generation uniqueness
    total_tests += 1
    try:
        ids = {generate_analysis_id() for _ in range(100)}
        if len(ids) != 100:
            all_validation_failures.append("IDs should be unique")
    except Exception as e:
        all_validation_failures.append(f"ID generation test failed: {e}")

    # Test 3: AnalysisConfig defaults
    total_tests += 1
    try:
        config = AnalysisConfig()
        if config.n_synths != 500:
            all_validation_failures.append(f"n_synths default should be 500: {config.n_synths}")
        if config.n_executions != 100:
            all_validation_failures.append("n_executions default should be 100")
        if config.sigma != 0.05:
            all_validation_failures.append("sigma default should be 0.05")
    except Exception as e:
        all_validation_failures.append(f"AnalysisConfig defaults test failed: {e}")

    # Test 4: AnalysisConfig validation
    total_tests += 1
    try:
        AnalysisConfig(n_synths=5)  # Below minimum
        all_validation_failures.append("Should reject n_synths < 10")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Unexpected error for n_synths < 10: {e}")

    # Test 5: AggregatedOutcomes rates sum
    total_tests += 1
    try:
        outcomes = AggregatedOutcomes(
            did_not_try_rate=0.2,
            failed_rate=0.3,
            success_rate=0.5,
        )
        if outcomes.success_rate != 0.5:
            all_validation_failures.append("success_rate mismatch")
    except Exception as e:
        all_validation_failures.append(f"AggregatedOutcomes creation failed: {e}")

    # Test 6: AggregatedOutcomes rates must sum to 1
    total_tests += 1
    try:
        AggregatedOutcomes(
            did_not_try_rate=0.3,
            failed_rate=0.3,
            success_rate=0.3,  # Sum = 0.9
        )
        all_validation_failures.append("Should reject rates that don't sum to 1")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Unexpected error for invalid rates: {e}")

    # Test 7: Create with outcomes
    total_tests += 1
    try:
        outcomes = AggregatedOutcomes(
            did_not_try_rate=0.15,
            failed_rate=0.25,
            success_rate=0.60,
        )
        run = AnalysisRun(
            experiment_id="exp_12345678",
            status="completed",
            total_synths=500,
            aggregated_outcomes=outcomes,
            execution_time_seconds=12.5,
        )
        if not run.has_results():
            all_validation_failures.append("Run should have results")
        if not run.is_completed():
            all_validation_failures.append("Run should be completed")
    except Exception as e:
        all_validation_failures.append(f"Create with outcomes failed: {e}")

    # Test 8: Reject invalid experiment_id format
    total_tests += 1
    try:
        AnalysisRun(experiment_id="invalid_id")
        all_validation_failures.append("Should reject invalid experiment_id format")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Unexpected error for invalid experiment_id: {e}")

    # Test 9: model_dump includes all fields
    total_tests += 1
    try:
        run = AnalysisRun(
            experiment_id="exp_12345678",
            config=AnalysisConfig(n_synths=200),
        )
        data = run.model_dump()
        if "config" not in data:
            all_validation_failures.append("model_dump missing config")
        if data["config"]["n_synths"] != 200:
            all_validation_failures.append("model_dump config n_synths mismatch")
    except Exception as e:
        all_validation_failures.append(f"model_dump test failed: {e}")

    # Test 10: Status transitions
    total_tests += 1
    try:
        run = AnalysisRun(experiment_id="exp_12345678", status="running")
        if not run.is_running():
            all_validation_failures.append("Run with status='running' should be running")
        if run.is_completed():
            all_validation_failures.append("Running run should not be completed")
    except Exception as e:
        all_validation_failures.append(f"Status transitions test failed: {e}")

    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
