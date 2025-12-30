"""
Simulation context entity for synth-lab.

Defines the SimulationContext dataclass that holds simulation results
to be passed to interview prompts for coherent behavior.

References:
    - Spec: specs/022-observable-latent-traits/spec.md (FR-016, FR-017, US2)
    - Data model: specs/022-observable-latent-traits/data-model.md
"""

from dataclasses import dataclass


@dataclass
class SimulationContext:
    """
    Context about a synth's prior simulation performance.

    Used to make interview responses coherent with simulated behavior.
    Passed to the interviewee system prompt.

    Attributes:
        synth_id: ID of the synth
        analysis_id: ID of the analysis/simulation run
        attempt_rate: Rate at which synth attempted the feature [0, 1]
        success_rate: Rate of successful attempts [0, 1]
        failure_rate: Rate of failed attempts [0, 1]
        n_executions: Number of Monte Carlo executions
    """

    synth_id: str
    analysis_id: str
    attempt_rate: float
    success_rate: float
    failure_rate: float
    n_executions: int

    def __post_init__(self):
        """Validate values are in expected ranges."""
        if not 0.0 <= self.attempt_rate <= 1.0:
            raise ValueError(f"attempt_rate must be in [0, 1], got {self.attempt_rate}")
        if not 0.0 <= self.success_rate <= 1.0:
            raise ValueError(f"success_rate must be in [0, 1], got {self.success_rate}")
        if not 0.0 <= self.failure_rate <= 1.0:
            raise ValueError(f"failure_rate must be in [0, 1], got {self.failure_rate}")
        if self.n_executions < 1:
            raise ValueError(f"n_executions must be >= 1, got {self.n_executions}")

    @property
    def no_attempt_rate(self) -> float:
        """Rate at which synth did not attempt the feature."""
        return max(0.0, 1.0 - self.attempt_rate)

    @property
    def performance_label(self) -> str:
        """Get a human-readable performance label."""
        if self.success_rate >= 0.8:
            return "excelente"
        elif self.success_rate >= 0.6:
            return "bom"
        elif self.success_rate >= 0.4:
            return "moderado"
        elif self.success_rate >= 0.2:
            return "baixo"
        else:
            return "muito baixo"


if __name__ == "__main__":
    import sys

    all_validation_failures: list[str] = []
    total_tests = 0

    # Test 1: Create valid SimulationContext
    total_tests += 1
    try:
        ctx = SimulationContext(
            synth_id="abc123",
            analysis_id="analysis_456",
            attempt_rate=0.80,
            success_rate=0.60,
            failure_rate=0.40,
            n_executions=1000,
        )
        if ctx.synth_id != "abc123":
            all_validation_failures.append(f"synth_id mismatch: {ctx.synth_id}")
        if ctx.success_rate != 0.60:
            all_validation_failures.append(f"success_rate mismatch: {ctx.success_rate}")
    except Exception as e:
        all_validation_failures.append(f"SimulationContext creation failed: {e}")

    # Test 2: no_attempt_rate property
    total_tests += 1
    if "ctx" in locals():
        expected_no_attempt = 0.20
        if abs(ctx.no_attempt_rate - expected_no_attempt) > 0.001:
            all_validation_failures.append(
                f"no_attempt_rate wrong: expected {expected_no_attempt}, got {ctx.no_attempt_rate}"
            )

    # Test 3: performance_label property
    total_tests += 1
    test_cases = [
        (0.85, "excelente"),
        (0.65, "bom"),
        (0.45, "moderado"),
        (0.25, "baixo"),
        (0.10, "muito baixo"),
    ]
    for success_rate, expected_label in test_cases:
        test_ctx = SimulationContext(
            synth_id="test",
            analysis_id="test",
            attempt_rate=1.0,
            success_rate=success_rate,
            failure_rate=1.0 - success_rate,
            n_executions=100,
        )
        if test_ctx.performance_label != expected_label:
            all_validation_failures.append(
                f"performance_label wrong for {success_rate}: "
                f"expected '{expected_label}', got '{test_ctx.performance_label}'"
            )

    # Test 4: Reject invalid attempt_rate
    total_tests += 1
    try:
        SimulationContext(
            synth_id="test",
            analysis_id="test",
            attempt_rate=1.5,  # Invalid
            success_rate=0.5,
            failure_rate=0.5,
            n_executions=100,
        )
        all_validation_failures.append("Should reject attempt_rate > 1.0")
    except ValueError:
        pass  # Expected

    # Test 5: Reject invalid n_executions
    total_tests += 1
    try:
        SimulationContext(
            synth_id="test",
            analysis_id="test",
            attempt_rate=0.8,
            success_rate=0.5,
            failure_rate=0.5,
            n_executions=0,  # Invalid
        )
        all_validation_failures.append("Should reject n_executions < 1")
    except ValueError:
        pass  # Expected

    # Final validation result
    if all_validation_failures:
        failed = len(all_validation_failures)
        print(f"VALIDATION FAILED - {failed} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("SimulationContext entity ready for use")
        sys.exit(0)
