"""
ExplorationService for LLM-assisted scenario exploration.

Main orchestration service that coordinates exploration sessions,
including starting explorations, running iterations, and managing state.

References:
    - Spec: specs/024-llm-scenario-exploration/spec.md
    - Data model: specs/024-llm-scenario-exploration/data-model.md
"""

from loguru import logger

from synth_lab.domain.entities.exploration import (
    Exploration,
    ExplorationConfig,
    ExplorationStatus,
    Goal,
)
from synth_lab.domain.entities.scenario_node import NodeStatus
from synth_lab.repositories.analysis_repository import AnalysisRepository
from synth_lab.repositories.experiment_repository import ExperimentRepository
from synth_lab.repositories.exploration_repository import ExplorationRepository
from synth_lab.services.exploration.tree_manager import TreeManager


class ExplorationError(Exception):
    """Base exception for exploration errors."""

    pass


class ExperimentNotFoundError(ExplorationError):
    """Experiment not found."""

    pass


class NoScorecardError(ExplorationError):
    """Experiment has no scorecard data."""

    pass


class NoBaselineAnalysisError(ExplorationError):
    """Experiment has no completed baseline analysis."""

    pass


class ExplorationNotFoundError(ExplorationError):
    """Exploration not found."""

    pass


class ExplorationService:
    """
    Main service for managing scenario explorations.

    Coordinates exploration sessions, managing tree expansion,
    filtering, and goal tracking.
    """

    def __init__(
        self,
        exploration_repo: ExplorationRepository | None = None,
        experiment_repo: ExperimentRepository | None = None,
        analysis_repo: AnalysisRepository | None = None,
        tree_manager: TreeManager | None = None,
    ):
        """
        Initialize the exploration service.

        Args:
            exploration_repo: Repository for exploration data.
            experiment_repo: Repository for experiment data.
            analysis_repo: Repository for analysis data.
            tree_manager: Manager for tree operations.
        """
        self.exploration_repo = exploration_repo or ExplorationRepository()
        self.experiment_repo = experiment_repo or ExperimentRepository()
        self.analysis_repo = analysis_repo or AnalysisRepository()
        self.tree_manager = tree_manager or TreeManager(self.exploration_repo)
        self.logger = logger.bind(component="exploration_service")

    def start_exploration(
        self,
        experiment_id: str,
        goal_value: float,
        beam_width: int = 3,
        max_depth: int = 5,
        max_llm_calls: int = 20,
        n_executions: int = 100,
        seed: int | None = None,
    ) -> Exploration:
        """
        Start a new exploration from an experiment.

        Creates an exploration session with a root node based on the
        experiment's scorecard and baseline analysis.

        Args:
            experiment_id: ID of the source experiment.
            goal_value: Target success_rate to achieve (0-1).
            beam_width: Number of scenarios to keep per iteration.
            max_depth: Maximum depth of exploration tree.
            max_llm_calls: Maximum LLM calls allowed.
            n_executions: Monte Carlo executions per simulation.
            seed: Random seed for reproducibility.

        Returns:
            The created exploration.

        Raises:
            ExperimentNotFoundError: If experiment doesn't exist.
            NoScorecardError: If experiment has no scorecard.
            NoBaselineAnalysisError: If experiment has no completed analysis.
        """
        # Validate experiment exists
        experiment = self.experiment_repo.get_by_id(experiment_id)
        if experiment is None:
            raise ExperimentNotFoundError(f"Experiment {experiment_id} not found")

        # Validate scorecard exists
        if not experiment.has_scorecard():
            raise NoScorecardError(f"Experiment {experiment_id} has no scorecard data")

        # Get baseline analysis
        analysis = self.analysis_repo.get_by_experiment_id(experiment_id)
        if analysis is None or analysis.status != "completed":
            raise NoBaselineAnalysisError(
                f"Experiment {experiment_id} has no completed baseline analysis"
            )

        # Create exploration
        goal = Goal(value=goal_value)
        config = ExplorationConfig(
            beam_width=beam_width,
            max_depth=max_depth,
            max_llm_calls=max_llm_calls,
            n_executions=n_executions,
            seed=seed,
        )

        exploration = Exploration(
            experiment_id=experiment_id,
            baseline_analysis_id=analysis.id,
            goal=goal,
            config=config,
        )

        # Persist exploration
        self.exploration_repo.create_exploration(exploration)
        self.logger.info(
            f"Created exploration {exploration.id} for experiment {experiment_id} "
            f"with goal success_rate >= {goal_value:.0%}"
        )

        # Create root node from baseline
        root_node = self.tree_manager.create_root_node(exploration, experiment, analysis)

        # Update exploration stats
        exploration.total_nodes = 1
        root_success_rate = root_node.get_success_rate()
        if root_success_rate is not None:
            exploration.best_success_rate = root_success_rate

            # Check if goal already achieved
            if exploration.goal.is_achieved(root_success_rate):
                self.logger.info(
                    f"Goal already achieved at start! success_rate={root_success_rate:.2%}"
                )
                root_node.mark_winner()
                self.exploration_repo.update_node_status(root_node.id, NodeStatus.WINNER)
                exploration.mark_completed(ExplorationStatus.GOAL_ACHIEVED)

        self.exploration_repo.update_exploration(exploration)

        return exploration

    def get_exploration(self, exploration_id: str) -> Exploration:
        """
        Get an exploration by ID.

        Args:
            exploration_id: The exploration ID.

        Returns:
            The exploration.

        Raises:
            ExplorationNotFoundError: If exploration doesn't exist.
        """
        exploration = self.exploration_repo.get_exploration_by_id(exploration_id)
        if exploration is None:
            raise ExplorationNotFoundError(f"Exploration {exploration_id} not found")
        return exploration

    def get_exploration_tree(self, exploration_id: str) -> dict:
        """
        Get the complete exploration tree.

        Args:
            exploration_id: The exploration ID.

        Returns:
            Dictionary with exploration, nodes, and status counts.
        """
        exploration = self.get_exploration(exploration_id)
        nodes = self.tree_manager.get_all_nodes(exploration_id)
        status_counts = self.exploration_repo.count_nodes_by_status(exploration_id)

        return {
            "exploration": exploration,
            "nodes": nodes,
            "node_count_by_status": status_counts,
        }

    def get_winning_path(self, exploration_id: str) -> dict | None:
        """
        Get the path from root to winning node.

        Args:
            exploration_id: The exploration ID.

        Returns:
            Dictionary with path info, or None if no winner.
        """
        exploration = self.get_exploration(exploration_id)

        # Check if exploration has a winner
        if exploration.status != ExplorationStatus.GOAL_ACHIEVED:
            return None

        winner = self.exploration_repo.get_winner_node(exploration_id)
        if winner is None:
            return None

        path = self.tree_manager.get_path_to_node(winner.id)

        # Build path steps with deltas
        steps = []
        prev_success_rate = 0.0
        for node in path:
            success_rate = node.get_success_rate() or 0.0
            delta = success_rate - prev_success_rate

            steps.append({
                "depth": node.depth,
                "action": node.action_applied,
                "category": node.action_category,
                "rationale": node.rationale,
                "success_rate": success_rate,
                "delta_success_rate": delta,
            })
            prev_success_rate = success_rate

        root = path[0] if path else None
        root_success = root.get_success_rate() if root else 0.0
        winner_success = winner.get_success_rate() or 0.0
        total_improvement = winner_success - root_success

        return {
            "exploration_id": exploration_id,
            "winner_node_id": winner.id,
            "path": steps,
            "total_improvement": total_improvement,
        }

    async def run_exploration(
        self,
        exploration_id: str,
        synths: list[dict],
    ) -> Exploration:
        """
        Run the exploration loop until termination.

        Iterates through the exploration tree, expanding nodes,
        running simulations, and checking termination conditions.

        Args:
            exploration_id: The exploration to run.
            synths: List of synths for simulation.

        Returns:
            The completed exploration.
        """
        from synth_lab.services.exploration.iteration_runner import IterationRunner

        exploration = self.get_exploration(exploration_id)
        experiment = self.experiment_repo.get_by_id(exploration.experiment_id)

        if experiment is None:
            raise ExperimentNotFoundError(
                f"Experiment {exploration.experiment_id} not found"
            )

        runner = IterationRunner(
            repository=self.exploration_repo,
            tree_manager=self.tree_manager,
            seed=exploration.config.seed,
            n_executions=exploration.config.n_executions,
            sigma=exploration.config.sigma,
        )

        self.logger.info(f"Starting exploration loop for {exploration_id}")

        while exploration.is_running():
            # Check limits
            if exploration.has_reached_depth_limit():
                exploration.mark_completed(ExplorationStatus.DEPTH_LIMIT_REACHED)
                break

            if exploration.has_reached_cost_limit():
                exploration.mark_completed(ExplorationStatus.COST_LIMIT_REACHED)
                break

            # Run iteration
            result = await runner.run_iteration(exploration, experiment, synths)

            # Update exploration stats
            exploration.current_depth = result.iteration_number
            exploration.total_nodes += result.nodes_created
            exploration.total_llm_calls += result.llm_calls_made
            if result.best_success_rate > (exploration.best_success_rate or 0.0):
                exploration.best_success_rate = result.best_success_rate

            # Check termination
            if result.goal_achieved:
                exploration.mark_completed(ExplorationStatus.GOAL_ACHIEVED)
                break

            if result.termination_reason == "no_viable_paths":
                exploration.mark_completed(ExplorationStatus.NO_VIABLE_PATHS)
                break

            if result.frontier_size == 0:
                exploration.mark_completed(ExplorationStatus.NO_VIABLE_PATHS)
                break

            # Persist progress
            self.exploration_repo.update_exploration(exploration)

        # Final update
        self.exploration_repo.update_exploration(exploration)
        self.logger.info(
            f"Exploration {exploration_id} completed with status {exploration.status.value}"
        )

        return exploration


if __name__ == "__main__":
    import sys
    import tempfile
    from pathlib import Path

    from synth_lab.domain.entities.analysis_run import AggregatedOutcomes, AnalysisRun
    from synth_lab.domain.entities.experiment import (
        Experiment,
        ScorecardData,
        ScorecardDimension,
    )
    from synth_lab.infrastructure.database import DatabaseManager, init_database

    all_validation_failures = []
    total_tests = 0

    with tempfile.TemporaryDirectory() as tmpdir:
        test_db_path = Path(tmpdir) / "test.db"
        init_database(test_db_path)
        db = DatabaseManager(test_db_path)

        exploration_repo = ExplorationRepository(db)
        experiment_repo = ExperimentRepository(db)
        analysis_repo = AnalysisRepository(db)
        tree_manager = TreeManager(exploration_repo)

        service = ExplorationService(
            exploration_repo=exploration_repo,
            experiment_repo=experiment_repo,
            analysis_repo=analysis_repo,
            tree_manager=tree_manager,
        )

        # Create test experiment with scorecard
        experiment = Experiment(
            name="Test Experiment",
            hypothesis="Test hypothesis",
            scorecard_data=ScorecardData(
                feature_name="Test Feature",
                description_text="Test description",
                complexity=ScorecardDimension(score=0.45),
                initial_effort=ScorecardDimension(score=0.30),
                perceived_risk=ScorecardDimension(score=0.25),
                time_to_value=ScorecardDimension(score=0.40),
            ),
        )
        experiment_repo.create(experiment)

        # Test 1: Start exploration without analysis fails
        total_tests += 1
        try:
            service.start_exploration(experiment.id, goal_value=0.40)
            all_validation_failures.append("Should fail without baseline analysis")
        except NoBaselineAnalysisError:
            pass  # Expected
        except Exception as e:
            all_validation_failures.append(f"Unexpected error: {e}")

        # Create analysis
        analysis = AnalysisRun(
            experiment_id=experiment.id,
            status="completed",
            aggregated_outcomes=AggregatedOutcomes(
                success_rate=0.25,
                failed_rate=0.45,
                did_not_try_rate=0.30,
            ),
        )
        analysis_repo.create(analysis)

        # Test 2: Start exploration successfully
        total_tests += 1
        try:
            exploration = service.start_exploration(
                experiment.id,
                goal_value=0.40,
                beam_width=3,
                max_depth=5,
            )
            if exploration.status != ExplorationStatus.RUNNING:
                all_validation_failures.append(f"Status should be RUNNING: {exploration.status}")
            if exploration.total_nodes != 1:
                all_validation_failures.append(f"Should have 1 node: {exploration.total_nodes}")
            if exploration.best_success_rate != 0.25:
                all_validation_failures.append(
                    f"Best success_rate should be 0.25: {exploration.best_success_rate}"
                )
        except Exception as e:
            all_validation_failures.append(f"Start exploration failed: {e}")

        # Test 3: Get exploration
        total_tests += 1
        try:
            retrieved = service.get_exploration(exploration.id)
            if retrieved.id != exploration.id:
                all_validation_failures.append(f"ID mismatch: {retrieved.id}")
        except Exception as e:
            all_validation_failures.append(f"Get exploration failed: {e}")

        # Test 4: Get exploration tree
        total_tests += 1
        try:
            tree = service.get_exploration_tree(exploration.id)
            if len(tree["nodes"]) != 1:
                all_validation_failures.append(f"Should have 1 node: {len(tree['nodes'])}")
            if tree["node_count_by_status"]["active"] != 1:
                all_validation_failures.append("Should have 1 active node")
        except Exception as e:
            all_validation_failures.append(f"Get tree failed: {e}")

        # Test 5: Get winning path (no winner yet)
        total_tests += 1
        try:
            path = service.get_winning_path(exploration.id)
            if path is not None:
                all_validation_failures.append("Should return None - no winner yet")
        except Exception as e:
            all_validation_failures.append(f"Get winning path failed: {e}")

        # Test 6: Experiment not found
        total_tests += 1
        try:
            service.start_exploration("exp_nonexist", goal_value=0.40)
            all_validation_failures.append("Should raise ExperimentNotFoundError")
        except ExperimentNotFoundError:
            pass  # Expected
        except Exception as e:
            all_validation_failures.append(f"Unexpected error: {e}")

        # Test 7: No scorecard error
        total_tests += 1
        try:
            exp_no_scorecard = Experiment(name="No Scorecard", hypothesis="Test")
            experiment_repo.create(exp_no_scorecard)
            service.start_exploration(exp_no_scorecard.id, goal_value=0.40)
            all_validation_failures.append("Should raise NoScorecardError")
        except NoScorecardError:
            pass  # Expected
        except Exception as e:
            all_validation_failures.append(f"Unexpected error: {e}")

        # Test 8: Goal already achieved at start
        total_tests += 1
        try:
            # Create experiment with high success rate baseline
            exp_high = Experiment(
                name="High Success",
                hypothesis="Already good",
                scorecard_data=ScorecardData(
                    feature_name="Good Feature",
                    description_text="Already works well",
                    complexity=ScorecardDimension(score=0.20),
                    initial_effort=ScorecardDimension(score=0.20),
                    perceived_risk=ScorecardDimension(score=0.10),
                    time_to_value=ScorecardDimension(score=0.20),
                ),
            )
            experiment_repo.create(exp_high)

            ana_high = AnalysisRun(
                experiment_id=exp_high.id,
                status="completed",
                aggregated_outcomes=AggregatedOutcomes(
                    success_rate=0.50,  # Already > 0.40
                    failed_rate=0.30,
                    did_not_try_rate=0.20,
                ),
            )
            analysis_repo.create(ana_high)

            expl_high = service.start_exploration(exp_high.id, goal_value=0.40)
            if expl_high.status != ExplorationStatus.GOAL_ACHIEVED:
                all_validation_failures.append(
                    f"Should be GOAL_ACHIEVED: {expl_high.status}"
                )
        except Exception as e:
            all_validation_failures.append(f"Goal at start test failed: {e}")

        db.close()

    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
