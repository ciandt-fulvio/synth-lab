"""
Simulation run entities for synth-lab.

Defines models for simulation execution and configuration.

References:
    - Spec: specs/016-feature-impact-simulation/spec.md
    - Data model: specs/016-feature-impact-simulation/data-model.md
"""

import secrets
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


def generate_simulation_id() -> str:
    """Generate a simulation ID in format sim_XXXXXXXX."""
    return f"sim_{secrets.token_hex(4)}"


class SimulationConfig(BaseModel):
    """Configuration for a simulation run."""

    n_synths: int = Field(
        default=500,
        ge=1,
        description="Number of synths to simulate.",
    )

    n_executions: int = Field(
        default=100,
        ge=1,
        description="Number of executions per synth.",
    )

    sigma: float = Field(
        default=0.05,
        ge=0.0,
        le=0.5,
        description="Noise level for latent trait sampling.",
    )

    seed: int | None = Field(
        default=None,
        description="Random seed for reproducibility.",
    )


class SimulationRun(BaseModel):
    """Record of a simulation execution."""

    id: str = Field(
        default_factory=generate_simulation_id,
        pattern=r"^sim_[a-zA-Z0-9]{8}$",
        description="Simulation ID in format sim_XXXXXXXX.",
    )

    scorecard_id: str = Field(description="ID of the feature scorecard used.")

    scenario_id: str = Field(description="ID of the scenario used.")

    config: SimulationConfig = Field(
        default_factory=SimulationConfig,
        description="Simulation configuration.",
    )

    # Status
    status: Literal["pending", "running", "completed", "failed"] = Field(
        default="pending",
        description="Current simulation status.",
    )

    started_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Simulation start timestamp.",
    )

    completed_at: datetime | None = Field(
        default=None,
        description="Simulation completion timestamp.",
    )

    # Aggregated metrics
    total_synths: int = Field(
        default=0,
        description="Total number of synths simulated.",
    )

    aggregated_outcomes: dict[str, float] | None = Field(
        default=None,
        description="Aggregated outcomes: {did_not_try, failed, success}.",
    )

    # Performance
    execution_time_seconds: float | None = Field(
        default=None,
        description="Total execution time in seconds.",
    )


if __name__ == "__main__":
    import sys

    all_validation_failures = []
    total_tests = 0

    # Test 1: Create valid SimulationConfig
    total_tests += 1
    try:
        config = SimulationConfig(
            n_synths=500,
            n_executions=100,
            sigma=0.05,
            seed=42,
        )
        if config.n_synths != 500:
            all_validation_failures.append(f"n_synths mismatch: {config.n_synths}")
    except Exception as e:
        all_validation_failures.append(f"SimulationConfig creation failed: {e}")

    # Test 2: SimulationConfig defaults
    total_tests += 1
    try:
        config = SimulationConfig()
        if config.n_synths != 500:
            all_validation_failures.append(f"Default n_synths should be 500: {config.n_synths}")
        if config.n_executions != 100:
            all_validation_failures.append(
                f"Default n_executions should be 100: {config.n_executions}"
            )
        if config.sigma != 0.05:
            all_validation_failures.append(f"Default sigma should be 0.05: {config.sigma}")
    except Exception as e:
        all_validation_failures.append(f"SimulationConfig defaults failed: {e}")

    # Test 3: Reject invalid sigma
    total_tests += 1
    try:
        SimulationConfig(sigma=0.6)
        all_validation_failures.append("Should reject sigma > 0.5")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Unexpected error for invalid sigma: {e}")

    # Test 4: Create valid SimulationRun
    total_tests += 1
    try:
        run = SimulationRun(
            scorecard_id="abc12345",
            scenario_id="baseline",
        )
        if not run.id.startswith("sim_"):
            all_validation_failures.append(f"ID should start with sim_: {run.id}")
        if run.status != "pending":
            all_validation_failures.append(f"Default status should be pending: {run.status}")
    except Exception as e:
        all_validation_failures.append(f"SimulationRun creation failed: {e}")

    # Test 5: ID generation format
    total_tests += 1
    try:
        id1 = generate_simulation_id()
        id2 = generate_simulation_id()
        if not id1.startswith("sim_"):
            all_validation_failures.append(f"ID should start with sim_: {id1}")
        if len(id1) != 12:  # sim_ + 8 chars
            all_validation_failures.append(f"ID length should be 12: {len(id1)}")
        if id1 == id2:
            all_validation_failures.append("Generated IDs should be unique")
    except Exception as e:
        all_validation_failures.append(f"ID generation test failed: {e}")

    # Test 6: SimulationRun with aggregated outcomes
    total_tests += 1
    try:
        run = SimulationRun(
            scorecard_id="abc12345",
            scenario_id="baseline",
            status="completed",
            total_synths=500,
            aggregated_outcomes={
                "did_not_try": 0.22,
                "failed": 0.38,
                "success": 0.40,
            },
            execution_time_seconds=25.3,
        )
        if run.aggregated_outcomes is None:
            all_validation_failures.append("aggregated_outcomes should be set")
        elif run.aggregated_outcomes.get("success") != 0.40:
            all_validation_failures.append(
                f"success rate mismatch: {run.aggregated_outcomes.get('success')}"
            )
    except Exception as e:
        all_validation_failures.append(f"SimulationRun with outcomes failed: {e}")

    # Test 7: Model dump produces valid dict
    total_tests += 1
    try:
        run = SimulationRun(
            scorecard_id="abc12345",
            scenario_id="baseline",
        )
        dump = run.model_dump()
        if "config" not in dump:
            all_validation_failures.append("model_dump missing config")
        if "status" not in dump:
            all_validation_failures.append("model_dump missing status")
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
