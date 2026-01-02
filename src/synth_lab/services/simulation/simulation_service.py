"""
Simulation service for synth-lab.

Orchestrates Monte Carlo simulation workflow including synth loading,
simulation execution, and result persistence.

Classes:
- SimulationService: Main service for running simulations

References:
    - Spec: specs/016-feature-impact-simulation/spec.md
    - Engine: src/synth_lab/services/simulation/engine.py

Sample usage:
    from synth_lab.services.simulation.simulation_service import SimulationService

    service = SimulationService()
    run = service.execute_simulation(
        scorecard_id="abc12345",
        scenario_id="baseline",
        synth_ids=["synth_1", "synth_2"],
        n_executions=100)

Expected output:
    SimulationRun with status="completed" and aggregated_outcomes
"""

import json
from datetime import datetime, timezone
from typing import Any

from loguru import logger

from synth_lab.domain.entities import (
    Scenario,
    SimulationConfig,
    SimulationRun,
    SynthOutcome)
from synth_lab.domain.entities.simulation_attributes import SimulationAttributes
from synth_lab.repositories.scorecard_repository import ScorecardRepository
from synth_lab.repositories.simulation_repository import SimulationRepository
from synth_lab.services.simulation.engine import MonteCarloEngine


class SimulationService:
    """Service for executing feature impact simulations."""

    def __init__(
        self,
        simulation_repo: SimulationRepository | None = None,
        scorecard_repo: ScorecardRepository | None = None) -> None:
        """
        Initialize simulation service.

        Args:
            simulation_repo: Simulation repository. Defaults to new instance.
            scorecard_repo: Scorecard repository. Defaults to new instance.
        """
        self.simulation_repo = simulation_repo or SimulationRepository()
        self.scorecard_repo = scorecard_repo or ScorecardRepository()
        self.logger = logger.bind(component="simulation_service")

    def execute_simulation(
        self,
        scorecard_id: str,
        scenario_id: str,
        synth_ids: list[str] | None = None,
        n_executions: int = 100,
        sigma: float = 0.1,
        seed: int | None = None) -> SimulationRun:
        """
        Execute a Monte Carlo simulation.

        Workflow:
        1. Load scorecard from database
        2. Load scenario from JSON
        3. Load synths (all or filtered by IDs)
        4. Create simulation run record
        5. Execute Monte Carlo simulation
        6. Save synth outcomes
        7. Update simulation run with results

        Args:
            scorecard_id: ID of the feature scorecard to use
            scenario_id: ID of the scenario (from scenarios.json)
            synth_ids: Optional list of synth IDs to include (default: all synths)
            n_executions: Number of Monte Carlo executions per synth
            sigma: Standard deviation for state sampling noise
            seed: Random seed for reproducibility

        Returns:
            SimulationRun: Completed simulation run with results

        Raises:
            ValueError: If scorecard or scenario not found
        """
        self.logger.info(
            f"Starting simulation for scorecard {scorecard_id}, scenario {scenario_id}"
        )

        # Load scorecard
        scorecard = self.scorecard_repo.get_scorecard(scorecard_id)
        if scorecard is None:
            raise ValueError(f"Scorecard not found: {scorecard_id}")

        # Load scenario
        scenario = self._load_scenario(scenario_id)
        if scenario is None:
            raise ValueError(f"Scenario not found: {scenario_id}")

        # Load synths
        synths = self._load_synths(synth_ids)
        if not synths:
            raise ValueError("No synths found for simulation")

        self.logger.info(f"Loaded {len(synths)} synths for simulation")

        # Create simulation config
        config = SimulationConfig(
            n_synths=len(synths),
            n_executions=n_executions,
            sigma=sigma,
            seed=seed)

        # Create simulation run
        run = SimulationRun(
            scorecard_id=scorecard_id,
            scenario_id=scenario_id,
            config=config,
            status="running",
            started_at=datetime.now(timezone.utc),
            total_synths=len(synths))
        self.simulation_repo.create_simulation_run(run)

        try:
            # Execute simulation
            engine = MonteCarloEngine(seed=seed, sigma=sigma)
            results = engine.run_simulation(
                synths=synths,
                scorecard=scorecard,
                scenario=scenario,
                n_executions=n_executions)

            # Convert results to SynthOutcome entities
            synth_outcomes = self._convert_to_synth_outcomes(
                simulation_id=run.id,
                results=results,
                synths=synths)

            # Save outcomes
            self.simulation_repo.save_synth_outcomes(run.id, synth_outcomes)

            # Update run with results
            run.status = "completed"
            run.completed_at = datetime.now(timezone.utc)
            run.aggregated_outcomes = {
                "did_not_try": results.aggregated_did_not_try,
                "failed": results.aggregated_failed,
                "success": results.aggregated_success,
            }
            run.execution_time_seconds = results.execution_time_seconds
            self.simulation_repo.update_simulation_run(run)

            self.logger.info(
                f"Simulation {run.id} completed: "
                f"success={results.aggregated_success:.3f}, "
                f"time={results.execution_time_seconds:.3f}s"
            )

        except Exception as e:
            self.logger.error(f"Simulation {run.id} failed: {e}")
            run.status = "failed"
            run.completed_at = datetime.now(timezone.utc)
            self.simulation_repo.update_simulation_run(run)
            raise

        return run

    def get_simulation(self, run_id: str) -> SimulationRun | None:
        """
        Get a simulation run by ID.

        Args:
            run_id: Simulation run ID

        Returns:
            SimulationRun if found, None otherwise
        """
        return self.simulation_repo.get_simulation_run(run_id)

    def list_simulations(
        self,
        scorecard_id: str | None = None,
        scenario_id: str | None = None,
        status: str | None = None,
        limit: int = 20,
        offset: int = 0) -> dict[str, Any]:
        """
        List simulation runs with optional filters.

        Args:
            scorecard_id: Filter by scorecard
            scenario_id: Filter by scenario
            status: Filter by status
            limit: Maximum results
            offset: Results to skip

        Returns:
            Dict with items list and pagination info
        """
        runs, total = self.simulation_repo.list_simulation_runs(
            scorecard_id=scorecard_id,
            scenario_id=scenario_id,
            status=status,
            limit=limit,
            offset=offset)
        return {
            "items": [run.model_dump(mode="json") for run in runs],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    def get_simulation_outcomes(
        self,
        run_id: str,
        limit: int = 100,
        offset: int = 0) -> dict[str, Any]:
        """
        Get synth outcomes for a simulation.

        Args:
            run_id: Simulation run ID
            limit: Maximum results
            offset: Results to skip

        Returns:
            Dict with items list and pagination info
        """
        outcomes, total = self.simulation_repo.get_synth_outcomes(
            simulation_id=run_id,
            limit=limit,
            offset=offset)
        return {
            "items": [outcome.model_dump(mode="json") for outcome in outcomes],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    def _load_scenario(self, scenario_id: str) -> Scenario | None:
        """Load scenario from scenarios.json."""
        try:
            from pathlib import Path

            # Load from project root data/config directory
            scenarios_path = (
                Path(__file__).parent.parent.parent.parent.parent
                / "data"
                / "config"
                / "scenarios.json"
            )
            with open(scenarios_path) as f:
                scenarios_data = json.load(f)

            # Scenarios are stored as {id: scenario_dict}
            if scenario_id in scenarios_data:
                return Scenario.model_validate(scenarios_data[scenario_id])

            return None
        except Exception as e:
            self.logger.error(f"Failed to load scenario {scenario_id}: {e}")
            return None

    def _load_synths(self, synth_ids: list[str] | None = None) -> list[dict[str, Any]]:
        """
        Load synths from database with simulation_attributes.

        For v2.3.0+ synths: Uses pre-computed observables from synth.data
        and derives latent_traits at simulation time.

        For legacy synths: Generates default observables based on demographics.

        Args:
            synth_ids: Optional list of synth IDs to load (default: all)

        Returns:
            List of synth dicts with simulation_attributes (observables + latent_traits)
        """
        from sqlalchemy import select
        from synth_lab.infrastructure.database_v2 import get_session
        from synth_lab.models.orm.synth import Synth as SynthORM

        with get_session() as session:
            stmt = select(SynthORM)
            if synth_ids:
                stmt = stmt.where(SynthORM.id.in_(synth_ids))
            else:
                stmt = stmt.limit(500)  # Safety limit
            orm_synths = list(session.execute(stmt).scalars().all())

        synths = []
        for orm_synth in orm_synths:
            synth_data = orm_synth.data if isinstance(orm_synth.data, dict) else {}
            synth_data["id"] = orm_synth.id

            # Convert real synth data to simulation_attributes
            synth_data["simulation_attributes"] = self._generate_simulation_attributes(synth_data)

            synths.append(synth_data)

        return synths

    def _generate_simulation_attributes(self, synth_data: dict[str, Any]) -> dict[str, Any]:
        """
        Generate simulation_attributes from synth data.

        For v2.3.0+ synths: Uses pre-computed observables from synth data and
        derives latent_traits using the standard derivation formulas.

        For legacy synths: Creates default observables based on available data.

        Args:
            synth_data: Raw synth data from database

        Returns:
            Dict with observables and latent_traits
        """
        from synth_lab.domain.entities.simulation_attributes import (
            SimulationObservables)
        from synth_lab.gen_synth.simulation_attributes import derive_latent_traits

        # Check if synth already has pre-computed observables (v2.3.0+)
        existing_observables = synth_data.get("observables")
        if existing_observables and all(
            k in existing_observables
            for k in [
                "digital_literacy",
                "similar_tool_experience",
                "motor_ability",
                "time_availability",
                "domain_expertise",
            ]
        ):
            # Use existing observables and derive latent traits
            observables = SimulationObservables.model_validate(existing_observables)
            latent_traits = derive_latent_traits(observables)

            return {
                "observables": observables.model_dump(),
                "latent_traits": latent_traits.model_dump(),
            }

        # Legacy synth - generate default observables
        deficiencias = synth_data.get("deficiencias", {})
        demografia = synth_data.get("demografia", {})

        # 1. digital_literacy: default based on escolaridade
        escolaridade = demografia.get("escolaridade", "").lower()
        if "superior" in escolaridade or "pós" in escolaridade:
            digital_literacy = 0.7
        elif "médio" in escolaridade:
            digital_literacy = 0.5
        else:
            digital_literacy = 0.3

        # 2. motor_ability: from deficiencias.motora
        motora = deficiencias.get("motora", {})
        tipo_motora = motora.get("tipo", "nenhuma")
        motor_ability_map = {
            "nenhuma": 1.0,
            "leve": 0.8,
            "moderada": 0.5,
            "severa": 0.2,
        }
        motor_ability = motor_ability_map.get(tipo_motora, 1.0)

        # 3. similar_tool_experience: default based on escolaridade
        if "superior" in escolaridade or "pós" in escolaridade:
            similar_tool_experience = 0.6
        elif "médio" in escolaridade:
            similar_tool_experience = 0.4
        else:
            similar_tool_experience = 0.3

        # 4. time_availability: derive from idade and ocupacao
        idade = demografia.get("idade", 40)
        ocupacao = demografia.get("ocupacao", "").lower()

        if ocupacao in ["aposentado", "desempregado", "estudante"]:
            time_availability = 0.7
        elif idade < 25 or idade > 65:
            time_availability = 0.6
        else:
            time_availability = 0.4

        # 5. domain_expertise: derive from escolaridade
        if "superior" in escolaridade or "pós" in escolaridade:
            domain_expertise = 0.7
        elif "médio" in escolaridade:
            domain_expertise = 0.5
        else:
            domain_expertise = 0.3

        # Create observables
        observables = SimulationObservables(
            digital_literacy=round(digital_literacy, 3),
            similar_tool_experience=round(similar_tool_experience, 3),
            motor_ability=round(motor_ability, 3),
            time_availability=round(time_availability, 3),
            domain_expertise=round(domain_expertise, 3))

        # Derive latent traits using standard formula
        latent_traits = derive_latent_traits(observables)

        return {
            "observables": observables.model_dump(),
            "latent_traits": latent_traits.model_dump(),
        }

    def _convert_to_synth_outcomes(
        self,
        simulation_id: str,
        results: Any,  # SimulationResults from engine
        synths: list[dict[str, Any]]) -> list[SynthOutcome]:
        """
        Convert engine results to SynthOutcome entities.

        Args:
            simulation_id: ID of the simulation run (used as analysis_id)
            results: SimulationResults from Monte Carlo engine
            synths: Original synth dicts with simulation_attributes

        Returns:
            List of SynthOutcome entities
        """
        from synth_lab.domain.entities.simulation_attributes import (
            SimulationLatentTraits,
            SimulationObservables)

        # Default attributes for synths without simulation_attributes
        def create_default_attrs() -> SimulationAttributes:
            return SimulationAttributes(
                observables=SimulationObservables(
                    digital_literacy=0.5,
                    similar_tool_experience=0.5,
                    motor_ability=1.0,
                    time_availability=0.5,
                    domain_expertise=0.5),
                latent_traits=SimulationLatentTraits(
                    capability_mean=0.5,
                    trust_mean=0.5,
                    friction_tolerance_mean=0.5,
                    exploration_prob=0.5))

        # Build synth_id -> simulation_attributes mapping
        synth_attrs_map = {}
        for synth in synths:
            synth_id = synth.get("id", "unknown")
            sim_attrs = synth.get("simulation_attributes", {})
            if sim_attrs and sim_attrs.get("observables") and sim_attrs.get("latent_traits"):
                try:
                    synth_attrs_map[synth_id] = SimulationAttributes.model_validate(sim_attrs)
                except Exception:
                    # Use defaults if validation fails
                    synth_attrs_map[synth_id] = create_default_attrs()
            else:
                synth_attrs_map[synth_id] = create_default_attrs()

        # Convert simulation_id to analysis_id format (sim_ -> ana_)
        # SynthOutcome expects ana_ prefix for analysis_id
        analysis_id = simulation_id.replace("sim_", "ana_")

        outcomes = []
        for result in results.synth_outcomes:
            synth_attrs = synth_attrs_map.get(result.synth_id, create_default_attrs())
            outcomes.append(
                SynthOutcome(
                    analysis_id=analysis_id,
                    synth_id=result.synth_id,
                    did_not_try_rate=result.did_not_try_rate,
                    failed_rate=result.failed_rate,
                    success_rate=result.success_rate,
                    synth_attributes=synth_attrs)
            )

        return outcomes


def list_scenarios() -> list[dict[str, Any]]:
    """
    List all available scenarios from scenarios.json.

    Returns:
        List of scenario dicts
    """
    try:
        from pathlib import Path

        # Load from project root data/config directory
        scenarios_path = (
            Path(__file__).parent.parent.parent.parent.parent / "data" / "config" / "scenarios.json"
        )
        with open(scenarios_path) as f:
            scenarios_data = json.load(f)

        # Scenarios are stored as {id: scenario_dict}
        return list(scenarios_data.values())
    except Exception as e:
        logger.error(f"Failed to load scenarios: {e}")
        return []


def get_scenario(scenario_id: str) -> dict[str, Any] | None:
    """
    Get a single scenario by ID.

    Args:
        scenario_id: Scenario ID to retrieve

    Returns:
        Scenario dict if found, None otherwise
    """
    try:
        from pathlib import Path

        # Load from project root data/config directory
        scenarios_path = (
            Path(__file__).parent.parent.parent.parent.parent / "data" / "config" / "scenarios.json"
        )
        with open(scenarios_path) as f:
            scenarios_data = json.load(f)

        return scenarios_data.get(scenario_id)
    except Exception as e:
        logger.error(f"Failed to load scenario {scenario_id}: {e}")
        return None


if __name__ == "__main__":
    import sys
    import tempfile
    from pathlib import Path

    from synth_lab.domain.entities import (
        FeatureScorecard,
        ScorecardDimension,
        ScorecardIdentification)

    print("=== Simulation Service Validation ===\n")

    all_validation_failures = []
    total_tests = 0

    # Test 1: list_scenarios function
    total_tests += 1
    try:
        scenarios = list_scenarios()
        if not isinstance(scenarios, list):
            all_validation_failures.append(f"list_scenarios should return list: {type(scenarios)}")
        elif len(scenarios) < 1:
            all_validation_failures.append("list_scenarios should return at least 1 scenario")
        else:
            print(f"Test 1 PASSED: list_scenarios returned {len(scenarios)} scenarios")
    except Exception as e:
        all_validation_failures.append(f"list_scenarios failed: {e}")

    # Test 2: get_scenario function
    total_tests += 1
    try:
        scenario = get_scenario("baseline")
        if scenario is None:
            all_validation_failures.append("get_scenario('baseline') returned None")
        elif scenario.get("id") != "baseline":
            all_validation_failures.append(
                f"get_scenario returned wrong scenario: {scenario.get('id')}"
            )
        else:
            print("Test 2 PASSED: get_scenario returned baseline scenario")
    except Exception as e:
        all_validation_failures.append(f"get_scenario failed: {e}")

    # Test 3: get_scenario for non-existent
    total_tests += 1
    try:
        scenario = get_scenario("nonexistent")
        if scenario is not None:
            all_validation_failures.append("get_scenario('nonexistent') should return None")
        else:
            print("Test 3 PASSED: get_scenario returns None for non-existent")
    except Exception as e:
        all_validation_failures.append(f"get_scenario non-existent test failed: {e}")

    # Tests requiring database
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        init_database(db_path)
        db = DatabaseManager(db_path)
        service = SimulationService()

        # Create test scorecard
        scorecard_repo = ScorecardRepository()
        test_scorecard = FeatureScorecard(
            id="simtest1",
            identification=ScorecardIdentification(
                feature_name="Test Feature",
                use_scenario="Testing simulation service"),
            description_text="A test scorecard",
            complexity=ScorecardDimension(score=0.4),
            initial_effort=ScorecardDimension(score=0.3),
            perceived_risk=ScorecardDimension(score=0.2),
            time_to_value=ScorecardDimension(score=0.5))
        scorecard_repo.create_scorecard(test_scorecard)

        # Create test synths with observables (new v2.3.0 format)

        test_synths_data = []
        for i in range(5):
            synth_id = f"simsynth{i}"
            # New format: observables at top level of synth data
            synth_data = {
                "observables": {
                    "digital_literacy": 0.4 + i * 0.1,
                    "similar_tool_experience": 0.5,
                    "motor_ability": 1.0,
                    "time_availability": 0.5,
                    "domain_expertise": 0.5,
                },
            }
            # Insert synth into database with required columns
            sql = """
                INSERT INTO synths (id, nome, created_at, data)
                VALUES (?, ?, datetime('now'), ?)
            """
            with db.transaction() as conn:
                conn.execute(sql, (synth_id, f"Test Synth {i}", json.dumps(synth_data)))
            test_synths_data.append(synth_id)

        # Note: analysis_runs entries are automatically created by the repository
        # when saving synth_outcomes (see _ensure_analysis_run_exists)

        # Test 4: Execute simulation
        total_tests += 1
        try:
            run = service.execute_simulation(
                scorecard_id="simtest1",
                scenario_id="baseline",
                synth_ids=test_synths_data,
                n_executions=50,
                seed=42)
            if run.status != "completed":
                all_validation_failures.append(f"Simulation should be completed: {run.status}")
            elif run.total_synths != 5:
                all_validation_failures.append(f"Expected 5 synths, got {run.total_synths}")
            elif run.aggregated_outcomes is None:
                all_validation_failures.append("aggregated_outcomes should not be None")
            else:
                success_rate = run.aggregated_outcomes.get("success", 0)
                print(f"Test 4 PASSED: Simulation completed (success={success_rate:.3f})")
        except Exception as e:
            all_validation_failures.append(f"Execute simulation failed: {e}")

        # Test 5: Get simulation
        total_tests += 1
        try:
            if "run" in locals():
                retrieved = service.get_simulation(run.id)
                if retrieved is None:
                    all_validation_failures.append("get_simulation returned None")
                elif retrieved.id != run.id:
                    all_validation_failures.append(f"ID mismatch: {retrieved.id} != {run.id}")
                else:
                    print(f"Test 5 PASSED: Retrieved simulation {retrieved.id}")
            else:
                all_validation_failures.append("Test 5 skipped: no run from Test 4")
        except Exception as e:
            all_validation_failures.append(f"get_simulation failed: {e}")

        # Test 6: List simulations
        total_tests += 1
        try:
            result = service.list_simulations()
            if result["total"] < 1:
                all_validation_failures.append(
                    f"Expected at least 1 simulation, got {result['total']}"
                )
            else:
                print(f"Test 6 PASSED: Listed {result['total']} simulations")
        except Exception as e:
            all_validation_failures.append(f"list_simulations failed: {e}")

        # Test 7: Get simulation outcomes
        total_tests += 1
        try:
            if "run" in locals():
                result = service.get_simulation_outcomes(run.id)
                if result["total"] != 5:
                    all_validation_failures.append(f"Expected 5 outcomes, got {result['total']}")
                else:
                    print(f"Test 7 PASSED: Retrieved {result['total']} outcomes")
            else:
                all_validation_failures.append("Test 7 skipped: no run from Test 4")
        except Exception as e:
            all_validation_failures.append(f"get_simulation_outcomes failed: {e}")

        # Test 8: Scorecard not found error
        total_tests += 1
        try:
            service.execute_simulation(
                scorecard_id="nonexist",
                scenario_id="baseline",
                synth_ids=test_synths_data)
            all_validation_failures.append("Should raise ValueError for non-existent scorecard")
        except ValueError:
            print("Test 8 PASSED: ValueError raised for non-existent scorecard")
        except Exception as e:
            all_validation_failures.append(f"Unexpected error for non-existent scorecard: {e}")

        # Test 9: Scenario not found error
        total_tests += 1
        try:
            service.execute_simulation(
                scorecard_id="simtest1",
                scenario_id="nonexistent_scenario",
                synth_ids=test_synths_data)
            all_validation_failures.append("Should raise ValueError for non-existent scenario")
        except ValueError:
            print("Test 9 PASSED: ValueError raised for non-existent scenario")
        except Exception as e:
            all_validation_failures.append(f"Unexpected error for non-existent scenario: {e}")

        db.close()

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
