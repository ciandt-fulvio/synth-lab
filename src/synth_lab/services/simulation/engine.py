"""
Monte Carlo simulation engine for feature impact simulation.

Executes N synths x M executions simulation and aggregates results.

Classes:
- MonteCarloEngine: Main simulation engine

References:
    - Spec: specs/016-feature-impact-simulation/spec.md
    - Research: specs/016-feature-impact-simulation/research.md

Sample usage:
    from synth_lab.services.simulation.engine import MonteCarloEngine
    import numpy as np

    engine = MonteCarloEngine(seed=42)
    results = engine.run_simulation(synths, scorecard, scenario, n_executions=100)

Expected output:
    SimulationResults with outcomes per synth and aggregated outcomes
"""

import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from synth_lab.domain.entities import FeatureScorecard, Scenario
from synth_lab.services.simulation.probability import (
    calculate_p_attempt,
    calculate_p_success,
    sample_outcome)
from synth_lab.services.simulation.sample_state import sample_user_state


@dataclass
class SynthOutcomeResult:
    """Outcome rates for a single synth."""

    synth_id: str
    did_not_try_rate: float
    failed_rate: float
    success_rate: float
    synth_attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class SimulationResults:
    """Complete simulation results."""

    synth_outcomes: list[SynthOutcomeResult]
    aggregated_did_not_try: float
    aggregated_failed: float
    aggregated_success: float
    total_synths: int
    n_executions: int
    execution_time_seconds: float


class MonteCarloEngine:
    """
    Monte Carlo simulation engine for feature impact.

    Executes N synths x M executions simulation to estimate outcome rates.
    """

    def __init__(
        self,
        seed: int | None = None,
        sigma: float = 0.1) -> None:
        """
        Initialize Monte Carlo engine.

        Args:
            seed: Random seed for reproducibility
            sigma: Standard deviation for state sampling noise
        """
        self.rng = np.random.default_rng(seed)
        self.sigma = sigma

    def run_simulation(
        self,
        synths: list[dict[str, Any]],
        scorecard: FeatureScorecard,
        scenario: Scenario,
        n_executions: int = 100) -> SimulationResults:
        """
        Run Monte Carlo simulation.

        For each synth, executes M simulation runs and aggregates outcomes.

        Args:
            synths: List of synth dicts with simulation_attributes
            scorecard: Feature scorecard with dimension scores
            scenario: Scenario with modifiers
            n_executions: Number of executions per synth

        Returns:
            SimulationResults with per-synth and aggregated outcomes

        Performance:
            - Target: 100 synths x 100 executions in < 1 second
            - Uses vectorized operations where possible
        """
        start_time = time.perf_counter()

        # Extract scorecard scores
        scorecard_scores = {
            "complexity": scorecard.complexity.score,
            "initial_effort": scorecard.initial_effort.score,
            "perceived_risk": scorecard.perceived_risk.score,
            "time_to_value": scorecard.time_to_value.score,
        }

        # Extract scenario modifiers
        scenario_dict = {
            "trust_modifier": scenario.trust_modifier,
            "friction_modifier": scenario.friction_modifier,
            "motivation_modifier": scenario.motivation_modifier,
            "task_criticality": scenario.task_criticality,
        }

        # Run simulation for each synth
        synth_outcomes: list[SynthOutcomeResult] = []
        total_did_not_try = 0.0
        total_failed = 0.0
        total_success = 0.0

        for synth in synths:
            # Extract latent traits from simulation_attributes
            sim_attrs = synth.get("simulation_attributes", {})
            latent_traits = sim_attrs.get("latent_traits", {})

            if not latent_traits:
                # Use defaults if no simulation attributes
                latent_traits = {
                    "capability_mean": 0.5,
                    "trust_mean": 0.5,
                    "friction_tolerance_mean": 0.5,
                    "exploration_prob": 0.5,
                }

            # Run M executions
            outcomes = self._run_synth_executions(
                latent_traits=latent_traits,
                scorecard_scores=scorecard_scores,
                scenario=scenario_dict,
                n_executions=n_executions)

            # Calculate rates with 3 decimal precision
            did_not_try_rate = round(outcomes["did_not_try"] / n_executions, 3)
            failed_rate = round(outcomes["failed"] / n_executions, 3)
            success_rate = round(outcomes["success"] / n_executions, 3)

            synth_outcomes.append(
                SynthOutcomeResult(
                    synth_id=synth.get("id", "unknown"),
                    did_not_try_rate=did_not_try_rate,
                    failed_rate=failed_rate,
                    success_rate=success_rate,
                    synth_attributes=sim_attrs)
            )

            # Accumulate for aggregation
            total_did_not_try += did_not_try_rate
            total_failed += failed_rate
            total_success += success_rate

        # Calculate aggregated rates (average across synths) with 3 decimal precision
        n_synths = len(synths)
        aggregated_did_not_try = round(total_did_not_try / n_synths, 3) if n_synths > 0 else 0.0
        aggregated_failed = round(total_failed / n_synths, 3) if n_synths > 0 else 0.0
        aggregated_success = round(total_success / n_synths, 3) if n_synths > 0 else 0.0

        execution_time = time.perf_counter() - start_time

        return SimulationResults(
            synth_outcomes=synth_outcomes,
            aggregated_did_not_try=aggregated_did_not_try,
            aggregated_failed=aggregated_failed,
            aggregated_success=aggregated_success,
            total_synths=n_synths,
            n_executions=n_executions,
            execution_time_seconds=execution_time)

    def _run_synth_executions(
        self,
        latent_traits: dict[str, float],
        scorecard_scores: dict[str, float],
        scenario: dict[str, float],
        n_executions: int) -> dict[str, int]:
        """
        Run M executions for a single synth.

        Args:
            latent_traits: Synth's latent traits
            scorecard_scores: Feature scorecard scores
            scenario: Scenario modifiers
            n_executions: Number of executions

        Returns:
            Dict with outcome counts: did_not_try, failed, success
        """
        outcomes = {"did_not_try": 0, "failed": 0, "success": 0}

        for _ in range(n_executions):
            # Sample user state
            user_state = sample_user_state(
                latent_traits=latent_traits,
                scenario=scenario,
                sigma=self.sigma,
                rng=self.rng)

            # Calculate probabilities
            p_attempt = calculate_p_attempt(user_state, scorecard_scores)
            p_success = calculate_p_success(user_state, scorecard_scores)

            # Sample outcome
            outcome = sample_outcome(p_attempt, p_success, self.rng)
            outcomes[outcome] += 1

        return outcomes


if __name__ == "__main__":
    import sys

    from synth_lab.domain.entities import (
        ScorecardDimension,
        ScorecardIdentification)

    print("=== Monte Carlo Engine Validation ===\n")

    all_validation_failures = []
    total_tests = 0

    # Create test scorecard
    test_scorecard = FeatureScorecard(
        identification=ScorecardIdentification(
            feature_name="Test Feature",
            use_scenario="Test"),
        description_text="Test",
        complexity=ScorecardDimension(score=0.4),
        initial_effort=ScorecardDimension(score=0.3),
        perceived_risk=ScorecardDimension(score=0.2),
        time_to_value=ScorecardDimension(score=0.5))

    # Create test scenario (baseline)
    test_scenario = Scenario(
        id="baseline",
        name="Baseline",
        description="Test baseline",
        motivation_modifier=0.0,
        trust_modifier=0.0,
        friction_modifier=0.0,
        task_criticality=0.5)

    # Create test synths with simulation_attributes
    test_synths = [
        {
            "id": f"synth_{i}",
            "simulation_attributes": {
                "observables": {
                    "digital_literacy": 0.4 + i * 0.1,
                    "similar_tool_experience": 0.5,
                    "motor_ability": 1.0,
                    "time_availability": 0.5,
                    "domain_expertise": 0.5,
                },
                "latent_traits": {
                    "capability_mean": 0.4 + i * 0.1,
                    "trust_mean": 0.5,
                    "friction_tolerance_mean": 0.5,
                    "exploration_prob": 0.5,
                },
            },
        }
        for i in range(10)
    ]

    # Test 1: Basic simulation run
    total_tests += 1
    try:
        engine = MonteCarloEngine(seed=42)
        results = engine.run_simulation(
            synths=test_synths,
            scorecard=test_scorecard,
            scenario=test_scenario,
            n_executions=100)

        if results.total_synths != 10:
            all_validation_failures.append(f"Expected 10 synths, got {results.total_synths}")
        if results.n_executions != 100:
            all_validation_failures.append(f"Expected 100 executions, got {results.n_executions}")
        else:
            print(
                f"Test 1 PASSED: Basic simulation ({results.total_synths} synths x {results.n_executions} executions)"
            )
    except Exception as e:
        all_validation_failures.append(f"Basic simulation failed: {e}")

    # Test 2: Outcome rates sum to 1.0 for each synth
    total_tests += 1
    try:
        for outcome in results.synth_outcomes:
            total = outcome.did_not_try_rate + outcome.failed_rate + outcome.success_rate
            if abs(total - 1.0) > 0.001:
                all_validation_failures.append(
                    f"Synth {outcome.synth_id} rates don't sum to 1: {total}"
                )
                break
        else:
            print("Test 2 PASSED: All synth outcome rates sum to 1.0")
    except Exception as e:
        all_validation_failures.append(f"Outcome rates test failed: {e}")

    # Test 3: Aggregated rates sum to 1.0
    total_tests += 1
    try:
        agg_total = (
            results.aggregated_did_not_try + results.aggregated_failed + results.aggregated_success
        )
        if abs(agg_total - 1.0) > 0.001:
            all_validation_failures.append(f"Aggregated rates don't sum to 1: {agg_total}")
        else:
            print(
                f"Test 3 PASSED: Aggregated rates sum to 1.0 (success={results.aggregated_success:.3f})"
            )
    except Exception as e:
        all_validation_failures.append(f"Aggregated rates test failed: {e}")

    # Test 4: Reproducibility with same seed
    total_tests += 1
    try:
        engine1 = MonteCarloEngine(seed=123)
        engine2 = MonteCarloEngine(seed=123)

        results1 = engine1.run_simulation(
            test_synths[:3], test_scorecard, test_scenario, n_executions=50
        )
        results2 = engine2.run_simulation(
            test_synths[:3], test_scorecard, test_scenario, n_executions=50
        )

        if results1.aggregated_success != results2.aggregated_success:
            all_validation_failures.append(
                "Reproducibility failed: different results with same seed"
            )
        else:
            print("Test 4 PASSED: Reproducibility with same seed")
    except Exception as e:
        all_validation_failures.append(f"Reproducibility test failed: {e}")

    # Test 5: Performance test (100x100 in < 1 second)
    total_tests += 1
    try:
        # Generate 100 synths
        perf_synths = [
            {
                "id": f"perf_{i}",
                "simulation_attributes": {
                    "latent_traits": {
                        "capability_mean": np.random.random(),
                        "trust_mean": np.random.random(),
                        "friction_tolerance_mean": np.random.random(),
                        "exploration_prob": np.random.random(),
                    },
                },
            }
            for i in range(100)
        ]

        engine = MonteCarloEngine(seed=42)
        results = engine.run_simulation(
            perf_synths, test_scorecard, test_scenario, n_executions=100
        )

        if results.execution_time_seconds > 1.0:
            all_validation_failures.append(
                f"Performance: 100x100 took {results.execution_time_seconds:.3f}s (>1s)"
            )
        else:
            print(f"Test 5 PASSED: Performance 100x100 in {results.execution_time_seconds:.3f}s")
    except Exception as e:
        all_validation_failures.append(f"Performance test failed: {e}")

    # Test 6: Higher capability leads to higher success
    total_tests += 1
    try:
        # Low capability synths
        low_cap_synths = [
            {
                "id": f"low_{i}",
                "simulation_attributes": {
                    "latent_traits": {
                        "capability_mean": 0.2,
                        "trust_mean": 0.5,
                        "friction_tolerance_mean": 0.5,
                        "exploration_prob": 0.5,
                    },
                },
            }
            for i in range(20)
        ]

        # High capability synths
        high_cap_synths = [
            {
                "id": f"high_{i}",
                "simulation_attributes": {
                    "latent_traits": {
                        "capability_mean": 0.8,
                        "trust_mean": 0.5,
                        "friction_tolerance_mean": 0.5,
                        "exploration_prob": 0.5,
                    },
                },
            }
            for i in range(20)
        ]

        engine = MonteCarloEngine(seed=42)
        low_results = engine.run_simulation(
            low_cap_synths, test_scorecard, test_scenario, n_executions=100
        )
        engine = MonteCarloEngine(seed=42)  # Reset
        high_results = engine.run_simulation(
            high_cap_synths, test_scorecard, test_scenario, n_executions=100
        )

        if high_results.aggregated_success <= low_results.aggregated_success:
            all_validation_failures.append(
                f"Higher capability should lead to more success: "
                f"{high_results.aggregated_success:.3f} <= {low_results.aggregated_success:.3f}"
            )
        else:
            print(
                f"Test 6 PASSED: Higher capability leads to more success "
                f"({low_results.aggregated_success:.3f} -> {high_results.aggregated_success:.3f})"
            )
    except Exception as e:
        all_validation_failures.append(f"Capability effect test failed: {e}")

    # Final result
    print()
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
