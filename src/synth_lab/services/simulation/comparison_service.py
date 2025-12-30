"""
Scenario comparison service for feature impact simulation.

Compares simulation results across different scenarios to identify
context-sensitive synth groups.

Classes:
- ComparisonService: Compares outcomes across scenarios

References:
    - Spec: specs/016-feature-impact-simulation/spec.md
    - API: specs/016-feature-impact-simulation/contracts/simulation-api.yaml

Sample usage:
    from synth_lab.services.simulation.comparison_service import ComparisonService
    from synth_lab.infrastructure.database import DatabaseManager

    db = DatabaseManager("output/synthlab.db")
    service = ComparisonService(db)
    result = service.compare_simulations(["sim_1", "sim_2", "sim_3"])

Expected output:
    CompareResult with simulations and most_affected_regions
"""

from typing import Any

from loguru import logger

from synth_lab.infrastructure.database import DatabaseManager
from synth_lab.repositories.region_repository import RegionRepository
from synth_lab.repositories.simulation_repository import SimulationRepository


class ComparisonService:
    """Service for comparing simulation results across scenarios."""

    def __init__(self, db: DatabaseManager) -> None:
        """
        Initialize comparison service.

        Args:
            db: Database manager instance
        """
        self.db = db
        self.simulation_repo = SimulationRepository(db)
        self.region_repo = RegionRepository(db)
        self.logger = logger.bind(component="comparison_service")

    def compare_simulations(self, simulation_ids: list[str]) -> dict[str, Any]:
        """
        Compare multiple simulations across scenarios.

        Args:
            simulation_ids: List of simulation IDs to compare (2-5 simulations)

        Returns:
            CompareResult dict with:
            - simulations: List of simulation info with aggregated outcomes
            - most_affected_regions: Regions with highest variance across scenarios

        Raises:
            ValueError: If fewer than 2 or more than 5 simulations provided
            ValueError: If any simulation not found
        """
        if len(simulation_ids) < 2:
            raise ValueError("Need at least 2 simulations to compare")
        if len(simulation_ids) > 5:
            raise ValueError("Cannot compare more than 5 simulations")

        self.logger.info(f"Comparing {len(simulation_ids)} simulations")

        # Load all simulations
        simulations = []
        for sim_id in simulation_ids:
            run = self.simulation_repo.get_simulation_run(sim_id)
            if not run:
                raise ValueError(f"Simulation not found: {sim_id}")

            simulations.append(
                {
                    "id": run.id,
                    "scenario_id": run.scenario_id,
                    "aggregated_outcomes": run.aggregated_outcomes or {},
                }
            )

        # Get regions for each simulation
        regions_by_simulation = {}
        for sim_id in simulation_ids:
            regions = self.region_repo.get_region_analyses(sim_id)
            regions_by_simulation[sim_id] = regions

        # Identify most affected regions (highest variance across scenarios)
        most_affected = self._find_most_affected_regions(simulations, regions_by_simulation)

        self.logger.info(
            f"Comparison complete: {len(simulations)} simulations, "
            f"{len(most_affected)} affected regions"
        )

        return {
            "simulations": simulations,
            "most_affected_regions": most_affected,
        }

    def _find_most_affected_regions(
        self,
        simulations: list[dict[str, Any]],
        regions_by_simulation: dict[str, list[Any]],
    ) -> list[dict[str, Any]]:
        """
        Identify regions with highest variance across scenarios.

        Strategy:
        1. Group regions across simulations by similar rules
        2. Calculate variance in failure rates for each region group
        3. Return top regions with highest variance

        Args:
            simulations: List of simulation info
            regions_by_simulation: Map of simulation_id to list of RegionAnalysis

        Returns:
            List of most affected regions with outcomes by scenario
        """
        # Map rule_text to outcomes by scenario
        region_map: dict[str, dict[str, float]] = {}

        for sim in simulations:
            sim_id = sim["id"]
            scenario_id = sim["scenario_id"]
            regions = regions_by_simulation.get(sim_id, [])

            for region in regions:
                rule_text = region.rule_text

                # Initialize if first time seeing this rule
                if rule_text not in region_map:
                    region_map[rule_text] = {}

                # Store failure rate for this scenario
                region_map[rule_text][scenario_id] = region.failed_rate

        # Calculate variance for each region across scenarios
        region_variances = []
        for rule_text, outcomes_by_scenario in region_map.items():
            # Only include regions that appear in at least 2 scenarios
            if len(outcomes_by_scenario) < 2:
                continue

            # Calculate variance in failure rates
            failure_rates = list(outcomes_by_scenario.values())
            mean_rate = sum(failure_rates) / len(failure_rates)
            variance = sum((rate - mean_rate) ** 2 for rate in failure_rates) / len(failure_rates)

            region_variances.append(
                {
                    "rule_text": rule_text,
                    "outcomes_by_scenario": {
                        scenario_id: round(rate, 3)
                        for scenario_id, rate in outcomes_by_scenario.items()
                    },
                    "variance": round(variance, 3),
                }
            )

        # Sort by variance descending and return top regions
        region_variances.sort(key=lambda x: x["variance"], reverse=True)

        # Return top 10 most affected regions
        most_affected = []
        for region in region_variances[:10]:
            most_affected.append(
                {
                    "rule_text": region["rule_text"],
                    "outcomes_by_scenario": region["outcomes_by_scenario"],
                }
            )

        return most_affected


if __name__ == "__main__":
    import sys

    print("=== Comparison Service Validation ===\n")

    all_validation_failures = []
    total_tests = 0

    # Initialize database and service
    db = DatabaseManager("output/synthlab.db")
    service = ComparisonService(db)

    # Get existing simulations from database
    sql = """
        SELECT id, scenario_id
        FROM simulation_runs
        WHERE status = 'completed'
        ORDER BY started_at DESC
        LIMIT 3
    """
    rows = db.fetchall(sql)

    if len(rows) < 2:
        print("⚠️  WARNING: Need at least 2 completed simulations in database")
        print("   Skipping validation - run simulations first via:")
        print("   uv run python docs/guides/test_simulation.py")
        sys.exit(0)

    test_sim_ids = [row["id"] for row in rows]
    print(f"Using simulations: {test_sim_ids}\n")

    # Test 1: Compare simulations
    total_tests += 1
    try:
        result = service.compare_simulations(test_sim_ids)

        if "simulations" not in result:
            all_validation_failures.append("Result missing 'simulations' key")
        elif len(result["simulations"]) != len(test_sim_ids):
            all_validation_failures.append(
                f"Expected {len(test_sim_ids)} simulations, got {len(result['simulations'])}"
            )
        else:
            print(f"Test 1 PASSED: Compared {len(result['simulations'])} simulations")
    except Exception as e:
        all_validation_failures.append(f"Compare simulations failed: {e}")

    # Test 2: Verify simulation structure
    total_tests += 1
    try:
        if result and "simulations" in result:
            first_sim = result["simulations"][0]
            required_fields = ["id", "scenario_id", "aggregated_outcomes"]
            missing = [f for f in required_fields if f not in first_sim]

            if missing:
                all_validation_failures.append(f"Simulation missing fields: {missing}")
            else:
                print("Test 2 PASSED: Simulation structure is correct")
    except Exception as e:
        all_validation_failures.append(f"Simulation structure check failed: {e}")

    # Test 3: Verify most_affected_regions structure
    total_tests += 1
    try:
        if result and "most_affected_regions" in result:
            regions = result["most_affected_regions"]
            if not isinstance(regions, list):
                all_validation_failures.append("most_affected_regions should be a list")
            elif len(regions) > 0:
                first_region = regions[0]
                if "rule_text" not in first_region:
                    all_validation_failures.append("Region missing 'rule_text'")
                elif "outcomes_by_scenario" not in first_region:
                    all_validation_failures.append("Region missing 'outcomes_by_scenario'")
                else:
                    print(f"Test 3 PASSED: Found {len(regions)} most affected regions")
            else:
                print("Test 3 PASSED: No affected regions (expected if no region overlap)")
    except Exception as e:
        all_validation_failures.append(f"Most affected regions check failed: {e}")

    # Test 4: Test with invalid input (too few simulations)
    total_tests += 1
    try:
        service.compare_simulations([test_sim_ids[0]])
        all_validation_failures.append("Should raise error with only 1 simulation")
    except ValueError as e:
        if "at least 2" in str(e):
            print("Test 4 PASSED: Correctly rejects < 2 simulations")
        else:
            all_validation_failures.append(f"Wrong error message: {e}")
    except Exception as e:
        all_validation_failures.append(f"Unexpected error for invalid input: {e}")

    # Test 5: Test with non-existent simulation
    total_tests += 1
    try:
        service.compare_simulations([test_sim_ids[0], "non_existent_sim"])
        all_validation_failures.append("Should raise error for non-existent simulation")
    except ValueError as e:
        if "not found" in str(e):
            print("Test 5 PASSED: Correctly rejects non-existent simulation")
        else:
            all_validation_failures.append(f"Wrong error message: {e}")
    except Exception as e:
        all_validation_failures.append(f"Unexpected error for non-existent simulation: {e}")

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
        print(f"✅ VALIDATION PASSED - All {total_tests} tests produced expected results")
        print("ComparisonService is validated and ready for use")
        sys.exit(0)
