"""
TreeManager for LLM-assisted scenario exploration.

Manages the exploration tree structure, including creating root nodes,
expanding nodes with proposals, and tracking tree state.

References:
    - Spec: specs/024-llm-scenario-exploration/spec.md
    - Data model: specs/024-llm-scenario-exploration/data-model.md
"""

from loguru import logger

from synth_lab.domain.entities.action_proposal import ActionProposal
from synth_lab.domain.entities.analysis_run import AnalysisRun
from synth_lab.domain.entities.experiment import Experiment
from synth_lab.domain.entities.exploration import Exploration
from synth_lab.domain.entities.scenario_node import (
    ScenarioNode,
    ScorecardParams,
    SimulationResults)
from synth_lab.repositories.exploration_repository import ExplorationRepository


class TreeManager:
    """
    Manages the exploration tree structure.

    Responsible for creating nodes, applying impacts, and maintaining
    the tree hierarchy.
    """

    def __init__(self, repository: ExplorationRepository | None = None):
        """
        Initialize the tree manager.

        Args:
            repository: Repository for persisting nodes.
        """
        self.repository = repository or ExplorationRepository()
        self.logger = logger.bind(component="tree_manager")

    def create_root_node(
        self,
        exploration: Exploration,
        experiment: Experiment,
        analysis_run: AnalysisRun) -> ScenarioNode:
        """
        Create the root node for an exploration.

        Extracts scorecard parameters from the experiment and simulation
        results from the baseline analysis.

        Args:
            exploration: The exploration this node belongs to.
            experiment: The source experiment with scorecard data.
            analysis_run: The baseline analysis with results.

        Returns:
            The created root node.

        Raises:
            ValueError: If experiment has no scorecard or analysis has no results.
        """
        if not experiment.scorecard_data:
            raise ValueError(f"Experiment {experiment.id} has no scorecard data")

        if not analysis_run.aggregated_outcomes:
            raise ValueError(f"Analysis {analysis_run.id} has no aggregated outcomes")

        # Extract scorecard params from experiment
        scorecard = experiment.scorecard_data
        scorecard_params = ScorecardParams(
            complexity=scorecard.complexity.score,
            initial_effort=scorecard.initial_effort.score,
            perceived_risk=scorecard.perceived_risk.score,
            time_to_value=scorecard.time_to_value.score)

        # Extract simulation results from analysis
        outcomes = analysis_run.aggregated_outcomes
        simulation_results = SimulationResults(
            success_rate=outcomes.success_rate,
            fail_rate=outcomes.failed_rate,
            did_not_try_rate=outcomes.did_not_try_rate)

        # Create root node
        root_node = ScenarioNode(
            exploration_id=exploration.id,
            depth=0,
            scorecard_params=scorecard_params,
            simulation_results=simulation_results)

        # Persist and return
        self.repository.create_node(root_node)
        self.logger.info(
            f"Created root node {root_node.id} for exploration {exploration.id} "
            f"with success_rate={simulation_results.success_rate:.2%}"
        )

        return root_node

    def create_child_node(
        self,
        parent: ScenarioNode,
        proposal: ActionProposal,
        simulation_results: SimulationResults | None = None,
        execution_time: float | None = None) -> ScenarioNode:
        """
        Create a child node from a proposal.

        Applies the proposal's impacts to the parent's scorecard params.

        Args:
            parent: The parent node.
            proposal: The action proposal to apply.
            simulation_results: Results from simulating this scenario.
            execution_time: Time taken for simulation.

        Returns:
            The created child node.
        """
        # Apply impacts to get new scorecard params
        new_params = parent.scorecard_params.apply_impacts(proposal.impacts)

        # Create child node
        child_node = ScenarioNode(
            exploration_id=parent.exploration_id,
            parent_id=parent.id,
            depth=parent.depth + 1,
            action_applied=proposal.action,
            action_category=proposal.category,
            rationale=proposal.rationale,
            short_action=proposal.short_action,
            scorecard_params=new_params,
            simulation_results=simulation_results,
            execution_time_seconds=execution_time)

        # Persist and return
        self.repository.create_node(child_node)
        self.logger.debug(
            f"Created child node {child_node.id} from parent {parent.id} "
            f"with action: {proposal.action[:50]}..."
        )

        return child_node

    def get_frontier(self, exploration_id: str) -> list[ScenarioNode]:
        """
        Get the active frontier nodes for expansion.

        Args:
            exploration_id: The exploration to get frontier for.

        Returns:
            List of active nodes in the frontier.
        """
        return self.repository.get_frontier_nodes(exploration_id)

    def get_path_to_node(self, node_id: str) -> list[ScenarioNode]:
        """
        Get the path from root to a specific node.

        Args:
            node_id: Target node ID.

        Returns:
            List of nodes from root to target.
        """
        return self.repository.get_path_to_node(node_id)

    def get_all_nodes(self, exploration_id: str) -> list[ScenarioNode]:
        """
        Get all nodes in an exploration.

        Args:
            exploration_id: The exploration ID.

        Returns:
            List of all nodes.
        """
        return self.repository.get_nodes_by_exploration(exploration_id)


if __name__ == "__main__":
    import sys
    import tempfile
    from pathlib import Path

    from synth_lab.domain.entities.experiment import (
        Experiment,
        ScorecardData,
        ScorecardDimension)
    from synth_lab.domain.entities.exploration import Exploration, Goal

    all_validation_failures = []
    total_tests = 0

    with tempfile.TemporaryDirectory() as tmpdir:
        test_db_path = Path(tmpdir) / "test.db"
        init_database(test_db_path)
        db = DatabaseManager(test_db_path)
        repo = ExplorationRepository()
        tree_manager = TreeManager(repo)

        # Create test data
        db.execute(
            """
            INSERT INTO experiments (id, name, hypothesis, scorecard_data, created_at)
            VALUES ('exp_12345678', 'Test', 'Hypothesis', ?, datetime('now'))
            """,
            (
                '{"feature_name":"Test","description_text":"Test",'
                '"complexity":{"score":0.45},"initial_effort":{"score":0.30},'
                '"perceived_risk":{"score":0.25},"time_to_value":{"score":0.40}}'))
        db.execute(
            """
            INSERT INTO analysis_runs (id, experiment_id, config, status, aggregated_outcomes, started_at)
            VALUES ('ana_87654321', 'exp_12345678', '{}', 'completed', ?, datetime('now'))
            """,
            ('{"success_rate":0.25,"fail_rate":0.45,"did_not_try_rate":0.30}'))

        # Create experiment and analysis objects
        experiment = Experiment(
            id="exp_12345678",
            name="Test",
            hypothesis="Hypothesis",
            scorecard_data=ScorecardData(
                feature_name="Test",
                description_text="Test",
                complexity=ScorecardDimension(score=0.45),
                initial_effort=ScorecardDimension(score=0.30),
                perceived_risk=ScorecardDimension(score=0.25),
                time_to_value=ScorecardDimension(score=0.40)))

        from synth_lab.domain.entities.analysis_run import AggregatedOutcomes

        analysis_run = AnalysisRun(
            id="ana_87654321",
            experiment_id="exp_12345678",
            aggregated_outcomes=AggregatedOutcomes(
                success_rate=0.25,
                failed_rate=0.45,
                did_not_try_rate=0.30))

        exploration = Exploration(
            experiment_id="exp_12345678",
            baseline_analysis_id="ana_87654321",
            goal=Goal(value=0.40))
        repo.create_exploration(exploration)

        # Test 1: Create root node
        total_tests += 1
        try:
            root = tree_manager.create_root_node(exploration, experiment, analysis_run)
            if root.depth != 0:
                all_validation_failures.append(f"Root depth should be 0: {root.depth}")
            if root.parent_id is not None:
                all_validation_failures.append("Root should have no parent")
            if abs(root.scorecard_params.complexity - 0.45) > 0.001:
                all_validation_failures.append(
                    f"Complexity mismatch: {root.scorecard_params.complexity}"
                )
            if abs(root.simulation_results.success_rate - 0.25) > 0.001:
                all_validation_failures.append(
                    f"Success rate mismatch: {root.simulation_results.success_rate}"
                )
        except Exception as e:
            all_validation_failures.append(f"Create root node failed: {e}")

        # Test 2: Create child node
        total_tests += 1
        try:
            proposal = ActionProposal(
                action="Adicionar tooltip contextual",
                short_action="Tooltip contextual",
                category="ux_interface",
                rationale="Reduz friccao",
                impacts={"complexity": -0.02, "time_to_value": -0.02})
            child = tree_manager.create_child_node(
                parent=root,
                proposal=proposal,
                simulation_results=SimulationResults(
                    success_rate=0.32,
                    fail_rate=0.40,
                    did_not_try_rate=0.28))
            if child.depth != 1:
                all_validation_failures.append(f"Child depth should be 1: {child.depth}")
            if child.parent_id != root.id:
                all_validation_failures.append(f"Child parent mismatch: {child.parent_id}")
            if abs(child.scorecard_params.complexity - 0.43) > 0.001:
                all_validation_failures.append(
                    f"Child complexity should be 0.43: {child.scorecard_params.complexity}"
                )
        except Exception as e:
            all_validation_failures.append(f"Create child node failed: {e}")

        # Test 3: Get frontier
        total_tests += 1
        try:
            frontier = tree_manager.get_frontier(exploration.id)
            if len(frontier) != 2:
                all_validation_failures.append(f"Frontier should have 2 nodes: {len(frontier)}")
        except Exception as e:
            all_validation_failures.append(f"Get frontier failed: {e}")

        # Test 4: Get path to node
        total_tests += 1
        try:
            path = tree_manager.get_path_to_node(child.id)
            if len(path) != 2:
                all_validation_failures.append(f"Path should have 2 nodes: {len(path)}")
            if path[0].id != root.id:
                all_validation_failures.append("Path should start with root")
            if path[1].id != child.id:
                all_validation_failures.append("Path should end with child")
        except Exception as e:
            all_validation_failures.append(f"Get path failed: {e}")

        # Test 5: Get all nodes
        total_tests += 1
        try:
            all_nodes = tree_manager.get_all_nodes(exploration.id)
            if len(all_nodes) != 2:
                all_validation_failures.append(f"Should have 2 nodes: {len(all_nodes)}")
        except Exception as e:
            all_validation_failures.append(f"Get all nodes failed: {e}")

        db.close()

    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
