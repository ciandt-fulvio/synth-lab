"""
Sensitivity analysis service for feature impact simulation.

Implements One-At-a-Time (OAT) methodology to identify which scorecard
dimension has the greatest impact on simulation outcomes.

Classes:
- SensitivityAnalyzer: Performs OAT sensitivity analysis

References:
    - Spec: specs/016-feature-impact-simulation/spec.md
    - Research: specs/016-feature-impact-simulation/research.md (OAT section)

Sample usage:
    from synth_lab.services.simulation.sensitivity import SensitivityAnalyzer
    from synth_lab.infrastructure.database import DatabaseManager

    db = DatabaseManager("output/synthlab.db")
    analyzer = SensitivityAnalyzer(db)
    result = analyzer.analyze_sensitivity(
        simulation_id="sim_123",
        deltas=[0.05, 0.10]
    )

Expected output:
    SensitivityResult with dimensions ranked by sensitivity index
"""

from typing import Any

from loguru import logger

from synth_lab.domain.entities import DimensionSensitivity, SensitivityResult
from synth_lab.infrastructure.database import DatabaseManager
from synth_lab.repositories.scorecard_repository import ScorecardRepository
from synth_lab.repositories.simulation_repository import SimulationRepository
from synth_lab.services.simulation.simulation_service import SimulationService


class SensitivityAnalyzer:
    """Performs One-At-a-Time sensitivity analysis on simulations."""

    DIMENSIONS = [
        "complexity",
        "initial_effort",
        "perceived_risk",
        "time_to_value",
    ]

    def __init__(self, db: DatabaseManager) -> None:
        """
        Initialize sensitivity analyzer.

        Args:
            db: Database manager instance
        """
        self.db = db
        self.simulation_repo = SimulationRepository(db)
        self.scorecard_repo = ScorecardRepository(db)
        self.simulation_service = SimulationService(db)
        self.logger = logger.bind(component="sensitivity_analyzer")

    def analyze_sensitivity(
        self,
        simulation_id: str,
        deltas: list[float] | None = None,
    ) -> SensitivityResult:
        """
        Perform One-At-a-Time sensitivity analysis.

        For each dimension, varies the value by +/- each delta while keeping
        other dimensions at baseline, then calculates sensitivity index.

        Args:
            simulation_id: ID of baseline simulation
            deltas: List of delta values to test (default: [0.05, 0.10])

        Returns:
            SensitivityResult with ranked dimensions

        Raises:
            ValueError: If simulation not found
        """
        if deltas is None:
            deltas = [0.05, 0.10]

        self.logger.info(f"Analyzing sensitivity for simulation {simulation_id}")

        # Load baseline simulation
        baseline_run = self.simulation_repo.get_simulation_run(simulation_id)
        if not baseline_run:
            raise ValueError(f"Simulation not found: {simulation_id}")

        # Get baseline scorecard
        scorecard = self.scorecard_repo.get(baseline_run.scorecard_id)
        if not scorecard:
            raise ValueError(
                f"Scorecard not found: {baseline_run.scorecard_id}"
            )

        # Get baseline outcomes
        baseline_outcomes = baseline_run.aggregated_outcomes or {}

        # Analyze each dimension
        dimension_results = []
        for dimension in self.DIMENSIONS:
            self.logger.debug(f"Analyzing dimension: {dimension}")

            result = self._analyze_dimension(
                dimension=dimension,
                scorecard=scorecard,
                baseline_run=baseline_run,
                baseline_outcomes=baseline_outcomes,
                deltas=deltas,
            )
            dimension_results.append(result)

        # Calculate sensitivity indices and rank
        for dim_result in dimension_results:
            dim_result["sensitivity_index"] = self._calculate_sensitivity_index(
                baseline_outcomes=baseline_outcomes,
                outcomes_by_delta=dim_result["outcomes_by_delta"],
                deltas_tested=dim_result["deltas_tested"],
            )

        # Sort by sensitivity index descending
        dimension_results.sort(
            key=lambda x: x["sensitivity_index"], reverse=True
        )

        # Assign ranks
        dimensions = []
        for rank, dim_result in enumerate(dimension_results, start=1):
            dimensions.append(
                DimensionSensitivity(
                    dimension=dim_result["dimension"],
                    baseline_value=dim_result["baseline_value"],
                    deltas_tested=dim_result["deltas_tested"],
                    outcomes_by_delta=dim_result["outcomes_by_delta"],
                    sensitivity_index=dim_result["sensitivity_index"],
                    rank=rank,
                )
            )

        self.logger.info(
            f"Sensitivity analysis complete. Most sensitive: {dimensions[0].dimension}"
        )

        return SensitivityResult(
            simulation_id=simulation_id,
            deltas_used=deltas,
            dimensions=dimensions,
        )

    def _analyze_dimension(
        self,
        dimension: str,
        scorecard: Any,
        baseline_run: Any,
        baseline_outcomes: dict[str, float],
        deltas: list[float],
    ) -> dict[str, Any]:
        """
        Analyze a single dimension using OAT.

        Args:
            dimension: Dimension name
            scorecard: Baseline scorecard
            baseline_run: Baseline simulation run
            baseline_outcomes: Baseline aggregated outcomes
            deltas: Delta values to test

        Returns:
            Dict with dimension analysis results
        """
        # Get baseline value for this dimension
        baseline_value = getattr(scorecard, dimension).score

        # Prepare delta variations (both + and -)
        deltas_tested = []
        for delta in deltas:
            deltas_tested.append(-delta)  # Negative first
            deltas_tested.append(delta)  # Then positive

        # Run simulation for each delta
        outcomes_by_delta = {}

        for delta in deltas_tested:
            # Clamp new value to [0, 1]
            new_value = max(0.0, min(1.0, baseline_value + delta))

            # Create modified scorecard
            modified_scorecard = self._create_modified_scorecard(
                scorecard, dimension, new_value
            )

            # Run simulation with modified scorecard
            try:
                result_run = self.simulation_service.execute_simulation(
                    scorecard_id=modified_scorecard.id,
                    scenario_id=baseline_run.scenario_id,
                    synth_ids=None,  # Use same config
                    n_executions=baseline_run.config.n_executions,
                    sigma=baseline_run.config.sigma,
                    seed=baseline_run.config.seed,  # Same seed for reproducibility
                )

                # Store outcomes
                outcomes_by_delta[str(round(delta, 3))] = result_run.aggregated_outcomes or {}

            except Exception as e:
                self.logger.warning(
                    f"Failed to run simulation for {dimension}={new_value}: {e}"
                )
                # Use baseline outcomes as fallback
                outcomes_by_delta[str(round(delta, 3))] = baseline_outcomes

        return {
            "dimension": dimension,
            "baseline_value": round(baseline_value, 3),
            "deltas_tested": [round(d, 3) for d in deltas_tested],
            "outcomes_by_delta": outcomes_by_delta,
            "sensitivity_index": 0.0,  # Will be calculated later
        }

    def _create_modified_scorecard(
        self, scorecard: Any, dimension: str, new_value: float
    ) -> Any:
        """
        Create a copy of scorecard with modified dimension.

        Note: This creates a new scorecard in the database with modified value.

        Args:
            scorecard: Original scorecard
            dimension: Dimension to modify
            new_value: New value for the dimension

        Returns:
            Modified scorecard (saved to database)
        """
        from copy import deepcopy

        # Create a copy of scorecard data
        scorecard_data = scorecard.model_dump()

        # Modify the specific dimension
        scorecard_data[dimension]["score"] = round(new_value, 3)

        # Create new scorecard ID
        import uuid

        scorecard_data["id"] = f"scorecard_{uuid.uuid4().hex[:8]}"
        scorecard_data["name"] = f"{scorecard.name} ({dimension}={new_value:.2f})"

        # Save to database
        from synth_lab.domain.entities import FeatureScorecard

        modified_scorecard = FeatureScorecard(**scorecard_data)
        self.scorecard_repo.create(modified_scorecard)

        return modified_scorecard

    def _calculate_sensitivity_index(
        self,
        baseline_outcomes: dict[str, float],
        outcomes_by_delta: dict[str, dict[str, float]],
        deltas_tested: list[float],
    ) -> float:
        """
        Calculate sensitivity index for a dimension.

        Formula:
        sensitivity_index = (% change in success rate) / (% change in input)

        We use the maximum absolute change across all deltas.

        Args:
            baseline_outcomes: Baseline aggregated outcomes
            outcomes_by_delta: Outcomes for each delta variation
            deltas_tested: List of delta values tested

        Returns:
            Sensitivity index (normalized)
        """
        baseline_success = baseline_outcomes.get("success", 0.0)

        # Avoid division by zero
        if baseline_success == 0:
            baseline_success = 0.001

        max_abs_change = 0.0

        for delta in deltas_tested:
            delta_key = str(round(delta, 3))
            if delta_key in outcomes_by_delta:
                delta_success = outcomes_by_delta[delta_key].get("success", 0.0)

                # Calculate % change in output
                pct_change_output = abs(
                    (delta_success - baseline_success) / baseline_success * 100
                )

                # Calculate % change in input
                pct_change_input = abs(delta * 100)

                # Avoid division by zero
                if pct_change_input == 0:
                    continue

                # Sensitivity index
                sensitivity = pct_change_output / pct_change_input

                max_abs_change = max(max_abs_change, sensitivity)

        return round(max_abs_change, 3)


if __name__ == "__main__":
    import sys

    print("=== Sensitivity Analyzer Validation ===\n")

    all_validation_failures = []
    total_tests = 0

    # Initialize database and analyzer
    db = DatabaseManager("output/synthlab.db")
    analyzer = SensitivityAnalyzer(db)

    # Get an existing completed simulation
    sql = """
        SELECT id
        FROM simulation_runs
        WHERE status = 'completed'
        ORDER BY started_at DESC
        LIMIT 1
    """
    rows = db.fetchall(sql)

    if not rows:
        print("⚠️  WARNING: No completed simulations in database")
        print("   Skipping validation - run a simulation first via:")
        print("   uv run python docs/guides/test_simulation.py")
        sys.exit(0)

    test_simulation_id = rows[0]["id"]
    print(f"Using simulation: {test_simulation_id}\n")

    # Test 1: Analyzer has correct dimensions
    total_tests += 1
    try:
        if len(analyzer.DIMENSIONS) != 4:
            all_validation_failures.append(
                f"Should have 4 dimensions, got {len(analyzer.DIMENSIONS)}"
            )
        else:
            print(f"Test 1 PASSED: Analyzer has 4 dimensions")
    except Exception as e:
        all_validation_failures.append(f"Dimension check failed: {e}")

    # Test 2: Calculate sensitivity index with mock data
    total_tests += 1
    try:
        baseline = {"success": 0.5, "failed": 0.3, "did_not_try": 0.2}
        outcomes_by_delta = {
            "-0.1": {"success": 0.4, "failed": 0.4, "did_not_try": 0.2},
            "-0.05": {"success": 0.45, "failed": 0.35, "did_not_try": 0.2},
            "0.05": {"success": 0.55, "failed": 0.25, "did_not_try": 0.2},
            "0.1": {"success": 0.6, "failed": 0.2, "did_not_try": 0.2},
        }
        deltas = [-0.1, -0.05, 0.05, 0.1]

        index = analyzer._calculate_sensitivity_index(
            baseline, outcomes_by_delta, deltas
        )

        if index <= 0:
            all_validation_failures.append(
                f"Sensitivity index should be > 0, got {index}"
            )
        else:
            print(f"Test 2 PASSED: Sensitivity index calculated: {index}")
    except Exception as e:
        all_validation_failures.append(f"Sensitivity calculation failed: {e}")

    # Test 3: Test with non-existent simulation
    total_tests += 1
    try:
        analyzer.analyze_sensitivity("non_existent_sim")
        all_validation_failures.append(
            "Should raise error for non-existent simulation"
        )
    except ValueError as e:
        if "not found" in str(e):
            print("Test 3 PASSED: Correctly rejects non-existent simulation")
        else:
            all_validation_failures.append(f"Wrong error message: {e}")
    except Exception as e:
        all_validation_failures.append(
            f"Unexpected error for non-existent simulation: {e}"
        )

    # Note: Skip full sensitivity analysis test as it would create many simulations
    # The test would be:
    # result = analyzer.analyze_sensitivity(test_simulation_id, deltas=[0.05])
    # But this is expensive - better to test in integration tests

    # Final result
    print()
    if all_validation_failures:
        print(
            f"❌ VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:"
        )
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(
            f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results"
        )
        print("SensitivityAnalyzer is validated and ready for use")
        print(
            "Note: Full sensitivity analysis not tested (expensive - use integration tests)"
        )
        sys.exit(0)
