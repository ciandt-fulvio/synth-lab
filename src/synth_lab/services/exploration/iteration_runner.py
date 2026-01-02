"""
IterationRunner for LLM-assisted scenario exploration.

Orchestrates a single iteration of the exploration loop:
1. Get frontier nodes
2. Generate proposals via LLM
3. Create child nodes and run simulations (parallel)
4. Apply Pareto dominance filter
5. Apply beam search
6. Check termination conditions

References:
    - Spec: specs/024-llm-scenario-exploration/spec.md
    - Data model: specs/024-llm-scenario-exploration/data-model.md

Sample usage:
    from synth_lab.services.exploration.iteration_runner import IterationRunner

    runner = IterationRunner()
    result = await runner.run_iteration(exploration, experiment, synths)

Expected output:
    IterationResult with expanded nodes, dominated nodes, and status
"""

import asyncio
from dataclasses import dataclass
from typing import Any

from loguru import logger

from synth_lab.domain.entities.experiment import Experiment
from synth_lab.domain.entities.exploration import Exploration
from synth_lab.domain.entities.scenario_node import NodeStatus, ScenarioNode, SimulationResults
from synth_lab.repositories.exploration_repository import ExplorationRepository
from synth_lab.services.exploration.action_proposal_service import ActionProposalService
from synth_lab.services.exploration.simulation_adapter import SimulationAdapter
from synth_lab.services.exploration.tree_manager import TreeManager


@dataclass
class IterationResult:
    """Result of a single exploration iteration."""

    iteration_number: int
    nodes_expanded: int
    nodes_created: int
    nodes_dominated: int
    llm_calls_made: int
    best_success_rate: float
    frontier_size: int
    goal_achieved: bool = False
    termination_reason: str | None = None


@dataclass
class NodeWithSimulation:
    """Node with pending or completed simulation."""

    node: ScenarioNode
    sim_results: SimulationResults | None = None
    exec_time: float = 0.0


class IterationRunner:
    """
    Runs a single iteration of the exploration loop.

    Handles proposal generation, node expansion, simulation,
    and filtering in a coordinated manner.
    """

    def __init__(
        self,
        repository: ExplorationRepository | None = None,
        tree_manager: TreeManager | None = None,
        proposal_service: ActionProposalService | None = None,
        seed: int | None = None,
        n_executions: int = 100,
        sigma: float = 0.1):
        """
        Initialize the iteration runner.

        Args:
            repository: Repository for exploration data.
            tree_manager: Manager for tree operations.
            proposal_service: Service for generating LLM proposals.
            seed: Random seed for simulations.
            n_executions: Monte Carlo executions per simulation.
            sigma: Standard deviation for simulation noise.
        """
        self.repository = repository or ExplorationRepository()
        self.tree_manager = tree_manager or TreeManager(self.repository)
        self.proposal_service = proposal_service or ActionProposalService()
        self.simulation_adapter = SimulationAdapter(
            seed=seed,
            n_executions=n_executions,
            sigma=sigma)
        self.logger = logger.bind(component="iteration_runner")

    async def run_iteration(
        self,
        exploration: Exploration,
        experiment: Experiment,
        synths: list[dict[str, Any]]) -> IterationResult:
        """
        Run a single iteration of the exploration loop.

        Args:
            exploration: The current exploration state.
            experiment: The source experiment.
            synths: List of synths for simulation.

        Returns:
            IterationResult with stats about this iteration.
        """
        iteration_number = exploration.current_depth + 1
        self.logger.info(
            f"Starting iteration {iteration_number} for exploration {exploration.id}"
        )

        # Get frontier nodes (active nodes to expand)
        frontier = self.tree_manager.get_frontier(exploration.id)
        if not frontier:
            self.logger.warning("No active nodes in frontier")
            return IterationResult(
                iteration_number=iteration_number,
                nodes_expanded=0,
                nodes_created=0,
                nodes_dominated=0,
                llm_calls_made=0,
                best_success_rate=exploration.best_success_rate or 0.0,
                frontier_size=0,
                termination_reason="no_viable_paths")

        # Limit frontier to beam_width for expansion
        beam_width = exploration.config.beam_width
        nodes_to_expand = frontier[:beam_width]

        self.logger.debug(
            f"Expanding {len(nodes_to_expand)} nodes (beam_width={beam_width})"
        )

        # Generate proposals for each node
        llm_calls = 0
        all_new_nodes: list[NodeWithSimulation] = []

        for node in nodes_to_expand:
            proposals = self.proposal_service.generate_proposals(
                node=node,
                experiment=experiment,
                max_proposals=4)
            llm_calls += 1

            # Create child nodes for each proposal
            for proposal in proposals:
                child = self.tree_manager.create_child_node(
                    parent=node,
                    proposal=proposal)
                all_new_nodes.append(NodeWithSimulation(node=child))

        self.logger.debug(f"Created {len(all_new_nodes)} child nodes")

        # Run simulations in parallel for all new nodes
        if all_new_nodes:
            await self._run_simulations_parallel(all_new_nodes, synths)

        # Update nodes with simulation results
        for nws in all_new_nodes:
            if nws.sim_results:
                nws.node.simulation_results = nws.sim_results
                nws.node.execution_time_seconds = nws.exec_time
                self.repository.update_node_simulation(
                    nws.node.id,
                    nws.sim_results,
                    nws.exec_time)

        # Check for goal achievement in new nodes
        goal_achieved = False
        winner_node: ScenarioNode | None = None
        for nws in all_new_nodes:
            if nws.sim_results:
                success_rate = nws.sim_results.success_rate
                if exploration.goal.is_achieved(success_rate):
                    goal_achieved = True
                    winner_node = nws.node
                    self.logger.info(
                        f"Goal achieved! Node {nws.node.id} reached "
                        f"success_rate={success_rate:.2%}"
                    )
                    break

        # Apply Pareto dominance filter
        dominated_count = self._apply_pareto_filter(exploration.id)

        # Apply beam search (keep top K by success_rate)
        self._apply_beam_search(exploration.id, beam_width)

        # Get updated frontier and best success rate
        new_frontier = self.tree_manager.get_frontier(exploration.id)
        best_success_rate = self._get_best_success_rate(exploration.id)

        # Handle goal achievement
        if goal_achieved and winner_node:
            winner_node.mark_winner()
            self.repository.update_node_status(winner_node.id, NodeStatus.WINNER)
            return IterationResult(
                iteration_number=iteration_number,
                nodes_expanded=len(nodes_to_expand),
                nodes_created=len(all_new_nodes),
                nodes_dominated=dominated_count,
                llm_calls_made=llm_calls,
                best_success_rate=best_success_rate,
                frontier_size=len(new_frontier),
                goal_achieved=True)

        # Build result
        return IterationResult(
            iteration_number=iteration_number,
            nodes_expanded=len(nodes_to_expand),
            nodes_created=len(all_new_nodes),
            nodes_dominated=dominated_count,
            llm_calls_made=llm_calls,
            best_success_rate=best_success_rate,
            frontier_size=len(new_frontier))

    async def _run_simulations_parallel(
        self,
        nodes: list[NodeWithSimulation],
        synths: list[dict[str, Any]]) -> None:
        """Run simulations in parallel for multiple nodes."""
        self.logger.debug(f"Running {len(nodes)} simulations in parallel")

        async def simulate_node(nws: NodeWithSimulation) -> None:
            # Run simulation in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            sim_results, exec_time = await loop.run_in_executor(
                None,
                self.simulation_adapter.run_simulation,
                nws.node.scorecard_params,
                synths)
            nws.sim_results = sim_results
            nws.exec_time = exec_time

        # Run all simulations concurrently
        await asyncio.gather(*[simulate_node(nws) for nws in nodes])

    def _apply_pareto_filter(self, exploration_id: str) -> int:
        """
        Apply Pareto dominance filter to active nodes.

        A node A dominates B if:
        - A.success_rate >= B.success_rate
        - A.complexity <= B.complexity
        - A.perceived_risk <= B.perceived_risk
        - AND at least one strict inequality

        Returns:
            Number of nodes marked as dominated.
        """
        nodes = self.repository.get_frontier_nodes(exploration_id)
        if len(nodes) < 2:
            return 0

        dominated_ids: set[str] = set()

        for i, node_a in enumerate(nodes):
            if node_a.id in dominated_ids:
                continue

            for node_b in nodes[i + 1:]:
                if node_b.id in dominated_ids:
                    continue

                if self._dominates(node_a, node_b):
                    dominated_ids.add(node_b.id)
                elif self._dominates(node_b, node_a):
                    dominated_ids.add(node_a.id)
                    break

        # Mark dominated nodes
        for node_id in dominated_ids:
            self.repository.update_node_status(node_id, NodeStatus.DOMINATED)

        if dominated_ids:
            self.logger.debug(f"Marked {len(dominated_ids)} nodes as dominated")

        return len(dominated_ids)

    def _dominates(self, a: ScenarioNode, b: ScenarioNode) -> bool:
        """Check if node A dominates node B."""
        if not a.simulation_results or not b.simulation_results:
            return False

        a_sr = a.simulation_results.success_rate
        b_sr = b.simulation_results.success_rate
        a_cx = a.scorecard_params.complexity
        b_cx = b.scorecard_params.complexity
        a_pr = a.scorecard_params.perceived_risk
        b_pr = b.scorecard_params.perceived_risk

        # A must be >= B in all objectives
        if a_sr < b_sr or a_cx > b_cx or a_pr > b_pr:
            return False

        # A must be strictly better in at least one objective
        return a_sr > b_sr or a_cx < b_cx or a_pr < b_pr

    def _apply_beam_search(self, exploration_id: str, beam_width: int) -> None:
        """
        Apply beam search to limit frontier size.

        Keeps the top K nodes by success_rate, marks others as dominated.
        """
        nodes = self.repository.get_frontier_nodes(exploration_id)
        if len(nodes) <= beam_width:
            return

        # Sort by success_rate descending
        sorted_nodes = sorted(
            nodes,
            key=lambda n: n.simulation_results.success_rate
            if n.simulation_results
            else 0.0,
            reverse=True)

        # Mark nodes beyond beam_width as dominated
        for node in sorted_nodes[beam_width:]:
            self.repository.update_node_status(node.id, NodeStatus.DOMINATED)

        self.logger.debug(
            f"Beam search: kept {beam_width} nodes, "
            f"dominated {len(nodes) - beam_width}"
        )

    def _get_best_success_rate(self, exploration_id: str) -> float:
        """Get the best success rate across all nodes."""
        nodes = self.repository.get_nodes_by_exploration(exploration_id)
        best = 0.0
        for node in nodes:
            if node.simulation_results:
                best = max(best, node.simulation_results.success_rate)
        return best


if __name__ == "__main__":
    import sys

    all_validation_failures = []
    total_tests = 0

    # Test 1: IterationResult dataclass
    total_tests += 1
    try:
        result = IterationResult(
            iteration_number=1,
            nodes_expanded=3,
            nodes_created=5,
            nodes_dominated=2,
            llm_calls_made=3,
            best_success_rate=0.35,
            frontier_size=3)
        if result.goal_achieved:
            all_validation_failures.append("goal_achieved should be False by default")
        if result.termination_reason is not None:
            all_validation_failures.append("termination_reason should be None by default")
    except Exception as e:
        all_validation_failures.append(f"IterationResult creation failed: {e}")

    # Test 2: Pareto dominance check
    total_tests += 1
    try:
        from synth_lab.domain.entities.scenario_node import ScorecardParams

        # Node A dominates B (better success_rate, same or better other metrics)
        node_a = ScenarioNode(
            exploration_id="expl_12345678",
            parent_id="node_00000001",  # Required for depth=1
            depth=1,
            scorecard_params=ScorecardParams(
                complexity=0.30,
                initial_effort=0.30,
                perceived_risk=0.20,
                time_to_value=0.30),
            simulation_results=SimulationResults(
                success_rate=0.40,
                fail_rate=0.35,
                did_not_try_rate=0.25))

        node_b = ScenarioNode(
            exploration_id="expl_12345678",
            parent_id="node_00000001",  # Required for depth=1
            depth=1,
            scorecard_params=ScorecardParams(
                complexity=0.35,
                initial_effort=0.30,
                perceived_risk=0.25,
                time_to_value=0.30),
            simulation_results=SimulationResults(
                success_rate=0.35,
                fail_rate=0.40,
                did_not_try_rate=0.25))

        runner = IterationRunner()
        if not runner._dominates(node_a, node_b):
            all_validation_failures.append("Node A should dominate Node B")
        if runner._dominates(node_b, node_a):
            all_validation_failures.append("Node B should NOT dominate Node A")
    except Exception as e:
        all_validation_failures.append(f"Pareto dominance test failed: {e}")

    # Test 3: Non-domination (Pareto front)
    total_tests += 1
    try:
        # Node C and D are on the Pareto front (neither dominates)
        node_c = ScenarioNode(
            exploration_id="expl_12345678",
            parent_id="node_00000001",  # Required for depth=1
            depth=1,
            scorecard_params=ScorecardParams(
                complexity=0.20,  # Better complexity
                initial_effort=0.30,
                perceived_risk=0.30,
                time_to_value=0.30),
            simulation_results=SimulationResults(
                success_rate=0.30,  # Worse success_rate
                fail_rate=0.40,
                did_not_try_rate=0.30))

        node_d = ScenarioNode(
            exploration_id="expl_12345678",
            parent_id="node_00000001",  # Required for depth=1
            depth=1,
            scorecard_params=ScorecardParams(
                complexity=0.40,  # Worse complexity
                initial_effort=0.30,
                perceived_risk=0.25,
                time_to_value=0.30),
            simulation_results=SimulationResults(
                success_rate=0.45,  # Better success_rate
                fail_rate=0.35,
                did_not_try_rate=0.20))

        runner = IterationRunner()
        if runner._dominates(node_c, node_d):
            all_validation_failures.append("Node C should NOT dominate Node D (Pareto front)")
        if runner._dominates(node_d, node_c):
            all_validation_failures.append("Node D should NOT dominate Node C (Pareto front)")
    except Exception as e:
        all_validation_failures.append(f"Pareto front test failed: {e}")

    # Test 4: Service instantiation
    total_tests += 1
    try:
        runner = IterationRunner(seed=42, n_executions=50)
        if runner.tree_manager is None:
            all_validation_failures.append("tree_manager should not be None")
        if runner.proposal_service is None:
            all_validation_failures.append("proposal_service should not be None")
        if runner.simulation_adapter is None:
            all_validation_failures.append("simulation_adapter should not be None")
    except Exception as e:
        all_validation_failures.append(f"Service instantiation failed: {e}")

    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
