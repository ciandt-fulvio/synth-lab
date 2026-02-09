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
        adopted_rate: Rate of adoption [0, 1]
        not_adopted_rate: Rate of non-adoption [0, 1]
        n_executions: Number of Monte Carlo executions
    """

    synth_id: str
    analysis_id: str
    adopted_rate: float
    not_adopted_rate: float
    n_executions: int

    def __post_init__(self):
        """Validate values are in expected ranges."""
        if not 0.0 <= self.adopted_rate <= 1.0:
            raise ValueError(f"adopted_rate must be in [0, 1], got {self.adopted_rate}")
        if not 0.0 <= self.not_adopted_rate <= 1.0:
            raise ValueError(f"not_adopted_rate must be in [0, 1], got {self.not_adopted_rate}")
        if self.n_executions < 1:
            raise ValueError(f"n_executions must be >= 1, got {self.n_executions}")

    @property
    def performance_label(self) -> str:
        """Get a human-readable performance label."""
        if self.adopted_rate >= 0.8:
            return "excelente"
        elif self.adopted_rate >= 0.6:
            return "bom"
        elif self.adopted_rate >= 0.4:
            return "moderado"
        elif self.adopted_rate >= 0.2:
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
            adopted_rate=0.60,
            not_adopted_rate=0.40,
            n_executions=1000,
        )
        if ctx.synth_id != "abc123":
            all_validation_failures.append(f"synth_id mismatch: {ctx.synth_id}")
        if ctx.adopted_rate != 0.60:
            all_validation_failures.append(f"adopted_rate mismatch: {ctx.adopted_rate}")
    except Exception as e:
        all_validation_failures.append(f"SimulationContext creation failed: {e}")

    # Test 2: performance_label property
    total_tests += 1
    test_cases = [
        (0.85, "excelente"),
        (0.65, "bom"),
        (0.45, "moderado"),
        (0.25, "baixo"),
        (0.10, "muito baixo"),
    ]
    for adopted_rate, expected_label in test_cases:
        test_ctx = SimulationContext(
            synth_id="test",
            analysis_id="test",
            adopted_rate=adopted_rate,
            not_adopted_rate=1.0 - adopted_rate,
            n_executions=100,
        )
        if test_ctx.performance_label != expected_label:
            all_validation_failures.append(
                f"performance_label wrong for {adopted_rate}: "
                f"expected '{expected_label}', got '{test_ctx.performance_label}'"
            )

    # Test 3: Reject invalid adopted_rate
    total_tests += 1
    try:
        SimulationContext(
            synth_id="test",
            analysis_id="test",
            adopted_rate=1.5,  # Invalid
            not_adopted_rate=0.5,
            n_executions=100,
        )
        all_validation_failures.append("Should reject adopted_rate > 1.0")
    except ValueError:
        pass  # Expected

    # Test 4: Reject invalid n_executions
    total_tests += 1
    try:
        SimulationContext(
            synth_id="test",
            analysis_id="test",
            adopted_rate=0.5,
            not_adopted_rate=0.5,
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
