"""
SimulationAdapter for LLM-assisted scenario exploration.

Bridges the exploration tree nodes to the existing MonteCarloEngine,
converting between ScenarioNode parameters and simulation entities.

References:
    - Spec: specs/024-llm-scenario-exploration/spec.md
    - MonteCarloEngine: src/synth_lab/services/simulation/engine.py

Sample usage:
    from synth_lab.services.exploration.simulation_adapter import SimulationAdapter

    adapter = SimulationAdapter(seed=42)
    results = adapter.run_simulation(node, synths)

Expected output:
    SimulationResults from MonteCarloEngine with success/fail/did_not_try rates
"""

from typing import Any

from loguru import logger

from synth_lab.domain.entities.feature_scorecard import (
    FeatureScorecard,
    ScorecardDimension,
    ScorecardIdentification,
)
from synth_lab.domain.entities.scenario import Scenario
from synth_lab.domain.entities.scenario_node import ScenarioNode, ScorecardParams, SimulationResults
from synth_lab.services.simulation.engine import MonteCarloEngine


class SimulationAdapter:
    """
    Adapter for running Monte Carlo simulations on exploration nodes.

    Converts between the exploration tree's ScorecardParams and the
    simulation engine's FeatureScorecard format.
    """

    def __init__(
        self,
        seed: int | None = None,
        sigma: float = 0.1,
        n_executions: int = 100,
    ):
        """
        Initialize the simulation adapter.

        Args:
            seed: Random seed for reproducibility.
            sigma: Standard deviation for state sampling noise.
            n_executions: Number of Monte Carlo executions per synth.
        """
        self.seed = seed
        self.sigma = sigma
        self.n_executions = n_executions
        self.engine = MonteCarloEngine(seed=seed, sigma=sigma)
        self.logger = logger.bind(component="simulation_adapter")

    def run_simulation(
        self,
        scorecard_params: ScorecardParams,
        synths: list[dict[str, Any]],
    ) -> tuple[SimulationResults, float]:
        """
        Run Monte Carlo simulation for a set of scorecard parameters.

        Args:
            scorecard_params: The scorecard parameters to simulate.
            synths: List of synth dicts with simulation_attributes.

        Returns:
            Tuple of (SimulationResults, execution_time_seconds).
        """
        # Convert ScorecardParams to FeatureScorecard
        scorecard = self._params_to_scorecard(scorecard_params)

        # Use baseline scenario (no modifiers)
        scenario = Scenario(
            id="baseline_exploration",
            name="Exploration Baseline",
            description="Standard baseline for exploration simulations",
            motivation_modifier=0.0,
            trust_modifier=0.0,
            friction_modifier=0.0,
            task_criticality=0.5,
        )

        # Run simulation
        self.logger.debug(
            f"Running simulation: {len(synths)} synths, {self.n_executions} executions"
        )
        engine_results = self.engine.run_simulation(
            synths=synths,
            scorecard=scorecard,
            scenario=scenario,
            n_executions=self.n_executions,
        )

        # Convert results to exploration SimulationResults
        sim_results = SimulationResults(
            success_rate=engine_results.aggregated_success,
            fail_rate=engine_results.aggregated_failed,
            did_not_try_rate=engine_results.aggregated_did_not_try,
        )

        self.logger.debug(
            f"Simulation complete: success_rate={sim_results.success_rate:.2%}, "
            f"time={engine_results.execution_time_seconds:.3f}s"
        )

        return sim_results, engine_results.execution_time_seconds

    def run_simulation_for_node(
        self,
        node: ScenarioNode,
        synths: list[dict[str, Any]],
    ) -> tuple[SimulationResults, float]:
        """
        Run Monte Carlo simulation for a scenario node.

        Args:
            node: The scenario node to simulate.
            synths: List of synth dicts with simulation_attributes.

        Returns:
            Tuple of (SimulationResults, execution_time_seconds).
        """
        return self.run_simulation(node.scorecard_params, synths)

    def _params_to_scorecard(self, params: ScorecardParams) -> FeatureScorecard:
        """
        Convert ScorecardParams to FeatureScorecard.

        Args:
            params: ScorecardParams from a scenario node.

        Returns:
            FeatureScorecard compatible with MonteCarloEngine.
        """
        return FeatureScorecard(
            # Use default factory for valid ID
            identification=ScorecardIdentification(
                feature_name="Exploration Simulation",
                use_scenario="Scenario exploration",
            ),
            description_text="Generated for exploration simulation",
            complexity=ScorecardDimension(
                score=params.complexity,
                rules_applied=[],
            ),
            initial_effort=ScorecardDimension(
                score=params.initial_effort,
                rules_applied=[],
            ),
            perceived_risk=ScorecardDimension(
                score=params.perceived_risk,
                rules_applied=[],
            ),
            time_to_value=ScorecardDimension(
                score=params.time_to_value,
                rules_applied=[],
            ),
            justification="",
            impact_hypotheses=[],
        )


if __name__ == "__main__":
    import sys

    all_validation_failures = []
    total_tests = 0

    # Test 1: Adapter instantiation
    total_tests += 1
    try:
        adapter = SimulationAdapter(seed=42)
        if adapter.engine is None:
            all_validation_failures.append("Engine should not be None")
        if adapter.n_executions != 100:
            all_validation_failures.append(f"Default n_executions should be 100: {adapter.n_executions}")
    except Exception as e:
        all_validation_failures.append(f"Adapter instantiation failed: {e}")

    # Test 2: Convert params to scorecard
    total_tests += 1
    try:
        adapter = SimulationAdapter(seed=42)
        params = ScorecardParams(
            complexity=0.45,
            initial_effort=0.30,
            perceived_risk=0.25,
            time_to_value=0.40,
        )
        scorecard = adapter._params_to_scorecard(params)
        if abs(scorecard.complexity.score - 0.45) > 0.001:
            all_validation_failures.append(
                f"Complexity mismatch: {scorecard.complexity.score}"
            )
        if abs(scorecard.perceived_risk.score - 0.25) > 0.001:
            all_validation_failures.append(
                f"Perceived risk mismatch: {scorecard.perceived_risk.score}"
            )
    except Exception as e:
        all_validation_failures.append(f"Params to scorecard failed: {e}")

    # Test 3: Run simulation with synthetic synth data
    total_tests += 1
    try:
        adapter = SimulationAdapter(seed=42, n_executions=10)
        params = ScorecardParams(
            complexity=0.30,
            initial_effort=0.20,
            perceived_risk=0.15,
            time_to_value=0.25,
        )
        # Create minimal synth data
        synths = [
            {
                "id": f"synth_{i}",
                "simulation_attributes": {
                    "latent_traits": {
                        "capability_mean": 0.6,
                        "trust_mean": 0.5,
                        "friction_tolerance_mean": 0.5,
                        "exploration_prob": 0.5,
                    }
                },
            }
            for i in range(5)
        ]

        sim_results, exec_time = adapter.run_simulation(params, synths)

        if sim_results.success_rate < 0.0 or sim_results.success_rate > 1.0:
            all_validation_failures.append(
                f"Success rate out of range: {sim_results.success_rate}"
            )
        if exec_time <= 0:
            all_validation_failures.append(f"Execution time should be positive: {exec_time}")

        # Rates should sum to approximately 1.0
        total_rate = sim_results.success_rate + sim_results.fail_rate + sim_results.did_not_try_rate
        if abs(total_rate - 1.0) > 0.01:
            all_validation_failures.append(f"Rates don't sum to 1.0: {total_rate}")
    except Exception as e:
        all_validation_failures.append(f"Run simulation failed: {e}")

    # Test 4: Run simulation for node
    total_tests += 1
    try:
        adapter = SimulationAdapter(seed=42, n_executions=10)
        node = ScenarioNode(
            exploration_id="expl_12345678",
            depth=0,
            scorecard_params=ScorecardParams(
                complexity=0.40,
                initial_effort=0.30,
                perceived_risk=0.20,
                time_to_value=0.35,
            ),
        )
        synths = [
            {
                "id": "synth_test",
                "simulation_attributes": {
                    "latent_traits": {
                        "capability_mean": 0.5,
                        "trust_mean": 0.5,
                        "friction_tolerance_mean": 0.5,
                        "exploration_prob": 0.5,
                    }
                },
            }
        ]

        sim_results, exec_time = adapter.run_simulation_for_node(node, synths)

        if sim_results is None:
            all_validation_failures.append("Simulation results should not be None")
    except Exception as e:
        all_validation_failures.append(f"Run simulation for node failed: {e}")

    # Test 5: Reproducibility with same seed
    total_tests += 1
    try:
        params = ScorecardParams(
            complexity=0.50,
            initial_effort=0.50,
            perceived_risk=0.50,
            time_to_value=0.50,
        )
        synths = [
            {
                "id": "synth_repro",
                "simulation_attributes": {
                    "latent_traits": {
                        "capability_mean": 0.5,
                        "trust_mean": 0.5,
                        "friction_tolerance_mean": 0.5,
                        "exploration_prob": 0.5,
                    }
                },
            }
        ]

        # Run twice with same seed
        adapter1 = SimulationAdapter(seed=123, n_executions=50)
        result1, _ = adapter1.run_simulation(params, synths)

        adapter2 = SimulationAdapter(seed=123, n_executions=50)
        result2, _ = adapter2.run_simulation(params, synths)

        if abs(result1.success_rate - result2.success_rate) > 0.001:
            all_validation_failures.append(
                f"Same seed should produce same results: {result1.success_rate} vs {result2.success_rate}"
            )
    except Exception as e:
        all_validation_failures.append(f"Reproducibility test failed: {e}")

    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
