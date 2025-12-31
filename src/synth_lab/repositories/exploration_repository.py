"""
ExplorationRepository for synth-lab.

Data access layer for exploration and scenario node data in SQLite database.
Supports tree traversal, frontier management, and path reconstruction.

References:
    - Spec: specs/024-llm-scenario-exploration/spec.md
    - Data model: specs/024-llm-scenario-exploration/data-model.md
"""

import json
from datetime import datetime

from synth_lab.domain.entities.exploration import (
    Exploration,
    ExplorationConfig,
    ExplorationStatus,
    Goal,
)
from synth_lab.domain.entities.scenario_node import (
    NodeStatus,
    ScenarioNode,
    ScorecardParams,
    SimulationResults,
)
from synth_lab.infrastructure.database import DatabaseManager
from synth_lab.repositories.base import BaseRepository


class ExplorationRepository(BaseRepository):
    """Repository for exploration and scenario node data access."""

    def __init__(self, db: DatabaseManager | None = None):
        super().__init__(db)

    # ========== Exploration Methods ==========

    def create_exploration(self, exploration: Exploration) -> Exploration:
        """
        Create a new exploration.

        Args:
            exploration: Exploration entity to create.

        Returns:
            Created exploration with persisted data.
        """
        goal_json = json.dumps(exploration.goal.model_dump())
        config_json = json.dumps(exploration.config.model_dump())

        self.db.execute(
            """
            INSERT INTO explorations (
                id, experiment_id, baseline_analysis_id, goal, config, status,
                current_depth, total_nodes, total_llm_calls, best_success_rate,
                started_at, completed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                exploration.id,
                exploration.experiment_id,
                exploration.baseline_analysis_id,
                goal_json,
                config_json,
                exploration.status.value,
                exploration.current_depth,
                exploration.total_nodes,
                exploration.total_llm_calls,
                exploration.best_success_rate,
                exploration.started_at.isoformat(),
                exploration.completed_at.isoformat() if exploration.completed_at else None,
            ),
        )
        return exploration

    def get_exploration_by_id(self, exploration_id: str) -> Exploration | None:
        """
        Get an exploration by ID.

        Args:
            exploration_id: Exploration ID to retrieve.

        Returns:
            Exploration if found, None otherwise.
        """
        row = self.db.fetchone(
            "SELECT * FROM explorations WHERE id = ?",
            (exploration_id,),
        )
        if row is None:
            return None
        return self._row_to_exploration(row)

    def update_exploration(self, exploration: Exploration) -> Exploration:
        """
        Update an existing exploration.

        Args:
            exploration: Exploration entity with updated values.

        Returns:
            Updated exploration.
        """
        goal_json = json.dumps(exploration.goal.model_dump())
        config_json = json.dumps(exploration.config.model_dump())

        self.db.execute(
            """
            UPDATE explorations SET
                goal = ?, config = ?, status = ?, current_depth = ?,
                total_nodes = ?, total_llm_calls = ?, best_success_rate = ?,
                completed_at = ?
            WHERE id = ?
            """,
            (
                goal_json,
                config_json,
                exploration.status.value,
                exploration.current_depth,
                exploration.total_nodes,
                exploration.total_llm_calls,
                exploration.best_success_rate,
                exploration.completed_at.isoformat() if exploration.completed_at else None,
                exploration.id,
            ),
        )
        return exploration

    def list_explorations_by_experiment(self, experiment_id: str) -> list[Exploration]:
        """
        List all explorations for an experiment.

        Args:
            experiment_id: Experiment ID to filter by.

        Returns:
            List of explorations.
        """
        rows = self.db.fetchall(
            "SELECT * FROM explorations WHERE experiment_id = ? ORDER BY started_at DESC",
            (experiment_id,),
        )
        return [self._row_to_exploration(row) for row in rows]

    # ========== ScenarioNode Methods ==========

    def create_node(self, node: ScenarioNode) -> ScenarioNode:
        """
        Create a new scenario node.

        Args:
            node: ScenarioNode entity to create.

        Returns:
            Created node with persisted data.
        """
        scorecard_json = json.dumps(node.scorecard_params.model_dump())
        simulation_json = (
            json.dumps(node.simulation_results.model_dump())
            if node.simulation_results
            else None
        )

        self.db.execute(
            """
            INSERT INTO scenario_nodes (
                id, exploration_id, parent_id, depth, action_applied, action_category,
                rationale, scorecard_params, simulation_results, execution_time_seconds,
                node_status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                node.id,
                node.exploration_id,
                node.parent_id,
                node.depth,
                node.action_applied,
                node.action_category,
                node.rationale,
                scorecard_json,
                simulation_json,
                node.execution_time_seconds,
                node.node_status.value,
                node.created_at.isoformat(),
            ),
        )
        return node

    def get_node_by_id(self, node_id: str) -> ScenarioNode | None:
        """
        Get a scenario node by ID.

        Args:
            node_id: Node ID to retrieve.

        Returns:
            ScenarioNode if found, None otherwise.
        """
        row = self.db.fetchone(
            "SELECT * FROM scenario_nodes WHERE id = ?",
            (node_id,),
        )
        if row is None:
            return None
        return self._row_to_node(row)

    def update_node(self, node: ScenarioNode) -> ScenarioNode:
        """
        Update an existing scenario node.

        Args:
            node: ScenarioNode entity with updated values.

        Returns:
            Updated node.
        """
        scorecard_json = json.dumps(node.scorecard_params.model_dump())
        simulation_json = (
            json.dumps(node.simulation_results.model_dump())
            if node.simulation_results
            else None
        )

        self.db.execute(
            """
            UPDATE scenario_nodes SET
                scorecard_params = ?, simulation_results = ?,
                execution_time_seconds = ?, node_status = ?
            WHERE id = ?
            """,
            (
                scorecard_json,
                simulation_json,
                node.execution_time_seconds,
                node.node_status.value,
                node.id,
            ),
        )
        return node

    def update_node_status(self, node_id: str, status: NodeStatus) -> None:
        """
        Update the status of a scenario node.

        Args:
            node_id: Node ID to update.
            status: New status.
        """
        self.db.execute(
            "UPDATE scenario_nodes SET node_status = ? WHERE id = ?",
            (status.value, node_id),
        )

    def update_node_simulation(
        self,
        node_id: str,
        simulation_results: SimulationResults,
        execution_time_seconds: float,
    ) -> None:
        """
        Update a node's simulation results.

        Args:
            node_id: Node ID to update.
            simulation_results: Simulation results to store.
            execution_time_seconds: Time taken for simulation.
        """
        simulation_json = json.dumps(simulation_results.model_dump())
        self.db.execute(
            """
            UPDATE scenario_nodes SET
                simulation_results = ?,
                execution_time_seconds = ?
            WHERE id = ?
            """,
            (simulation_json, execution_time_seconds, node_id),
        )

    def get_nodes_by_exploration(self, exploration_id: str) -> list[ScenarioNode]:
        """
        Get all nodes for an exploration.

        Args:
            exploration_id: Exploration ID to filter by.

        Returns:
            List of all nodes, ordered by depth.
        """
        rows = self.db.fetchall(
            """
            SELECT * FROM scenario_nodes
            WHERE exploration_id = ?
            ORDER BY depth ASC, created_at ASC
            """,
            (exploration_id,),
        )
        return [self._row_to_node(row) for row in rows]

    def get_frontier_nodes(self, exploration_id: str) -> list[ScenarioNode]:
        """
        Get active nodes in the frontier (nodes that can be expanded).

        Args:
            exploration_id: Exploration ID to filter by.

        Returns:
            List of active nodes.
        """
        rows = self.db.fetchall(
            """
            SELECT * FROM scenario_nodes
            WHERE exploration_id = ? AND node_status = 'active'
            ORDER BY depth DESC, created_at ASC
            """,
            (exploration_id,),
        )
        return [self._row_to_node(row) for row in rows]

    def get_root_node(self, exploration_id: str) -> ScenarioNode | None:
        """
        Get the root node of an exploration.

        Args:
            exploration_id: Exploration ID.

        Returns:
            Root node if found, None otherwise.
        """
        row = self.db.fetchone(
            "SELECT * FROM scenario_nodes WHERE exploration_id = ? AND depth = 0",
            (exploration_id,),
        )
        if row is None:
            return None
        return self._row_to_node(row)

    def get_winner_node(self, exploration_id: str) -> ScenarioNode | None:
        """
        Get the winner node of an exploration.

        Args:
            exploration_id: Exploration ID.

        Returns:
            Winner node if found, None otherwise.
        """
        row = self.db.fetchone(
            "SELECT * FROM scenario_nodes WHERE exploration_id = ? AND node_status = 'winner'",
            (exploration_id,),
        )
        if row is None:
            return None
        return self._row_to_node(row)

    def get_path_to_node(self, node_id: str) -> list[ScenarioNode]:
        """
        Get the path from root to a specific node.

        Uses recursive CTE to traverse the tree.

        Args:
            node_id: Target node ID.

        Returns:
            List of nodes from root to target, ordered by depth.
        """
        rows = self.db.fetchall(
            """
            WITH RECURSIVE path AS (
                SELECT * FROM scenario_nodes WHERE id = ?
                UNION ALL
                SELECT sn.* FROM scenario_nodes sn
                INNER JOIN path p ON sn.id = p.parent_id
            )
            SELECT * FROM path ORDER BY depth ASC
            """,
            (node_id,),
        )
        return [self._row_to_node(row) for row in rows]

    def count_nodes_by_status(self, exploration_id: str) -> dict[str, int]:
        """
        Count nodes by status for an exploration.

        Args:
            exploration_id: Exploration ID.

        Returns:
            Dictionary mapping status to count.
        """
        rows = self.db.fetchall(
            """
            SELECT node_status, COUNT(*) as count
            FROM scenario_nodes
            WHERE exploration_id = ?
            GROUP BY node_status
            """,
            (exploration_id,),
        )
        result = {status.value: 0 for status in NodeStatus}
        for row in rows:
            result[row["node_status"]] = row["count"]
        return result

    def get_best_node_by_success_rate(self, exploration_id: str) -> ScenarioNode | None:
        """
        Get the node with highest success rate.

        Args:
            exploration_id: Exploration ID.

        Returns:
            Best node if found, None otherwise.
        """
        row = self.db.fetchone(
            """
            SELECT * FROM scenario_nodes
            WHERE exploration_id = ? AND simulation_results IS NOT NULL
            ORDER BY json_extract(simulation_results, '$.success_rate') DESC
            LIMIT 1
            """,
            (exploration_id,),
        )
        if row is None:
            return None
        return self._row_to_node(row)

    def get_children(self, parent_id: str) -> list[ScenarioNode]:
        """
        Get all child nodes of a parent.

        Args:
            parent_id: Parent node ID.

        Returns:
            List of child nodes.
        """
        rows = self.db.fetchall(
            "SELECT * FROM scenario_nodes WHERE parent_id = ? ORDER BY created_at ASC",
            (parent_id,),
        )
        return [self._row_to_node(row) for row in rows]

    # ========== Private Conversion Methods ==========

    def _row_to_exploration(self, row) -> Exploration:
        """Convert a database row to Exploration entity."""
        started_at = row["started_at"]
        if isinstance(started_at, str):
            started_at = datetime.fromisoformat(started_at)

        completed_at = row["completed_at"]
        if isinstance(completed_at, str):
            completed_at = datetime.fromisoformat(completed_at)

        goal_dict = json.loads(row["goal"])
        config_dict = json.loads(row["config"])

        return Exploration(
            id=row["id"],
            experiment_id=row["experiment_id"],
            baseline_analysis_id=row["baseline_analysis_id"],
            goal=Goal(**goal_dict),
            config=ExplorationConfig(**config_dict),
            status=ExplorationStatus(row["status"]),
            current_depth=row["current_depth"],
            total_nodes=row["total_nodes"],
            total_llm_calls=row["total_llm_calls"],
            best_success_rate=row["best_success_rate"],
            started_at=started_at,
            completed_at=completed_at,
        )

    def _row_to_node(self, row) -> ScenarioNode:
        """Convert a database row to ScenarioNode entity."""
        created_at = row["created_at"]
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        scorecard_dict = json.loads(row["scorecard_params"])
        simulation_dict = (
            json.loads(row["simulation_results"])
            if row["simulation_results"]
            else None
        )

        return ScenarioNode(
            id=row["id"],
            exploration_id=row["exploration_id"],
            parent_id=row["parent_id"],
            depth=row["depth"],
            action_applied=row["action_applied"],
            action_category=row["action_category"],
            rationale=row["rationale"],
            scorecard_params=ScorecardParams(**scorecard_dict),
            simulation_results=(
                SimulationResults(**simulation_dict) if simulation_dict else None
            ),
            execution_time_seconds=row["execution_time_seconds"],
            node_status=NodeStatus(row["node_status"]),
            created_at=created_at,
        )


if __name__ == "__main__":
    import sys
    import tempfile
    from pathlib import Path

    from synth_lab.infrastructure.database import DatabaseManager, init_database

    # Validation
    all_validation_failures = []
    total_tests = 0

    # Use a temporary database for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db_path = Path(tmpdir) / "test.db"
        init_database(test_db_path)
        db = DatabaseManager(test_db_path)
        repo = ExplorationRepository(db)

        # Create test experiment and analysis
        db.execute(
            """
            INSERT INTO experiments (id, name, hypothesis, created_at)
            VALUES ('exp_12345678', 'Test Experiment', 'Test hypothesis', datetime('now'))
            """
        )
        db.execute(
            """
            INSERT INTO analysis_runs (id, experiment_id, config, status, started_at)
            VALUES ('ana_87654321', 'exp_12345678', '{}', 'completed', datetime('now'))
            """
        )

        # Test 1: Create exploration
        total_tests += 1
        try:
            exploration = Exploration(
                experiment_id="exp_12345678",
                baseline_analysis_id="ana_87654321",
                goal=Goal(value=0.40),
            )
            result = repo.create_exploration(exploration)
            if result.id != exploration.id:
                all_validation_failures.append(f"ID mismatch: {result.id}")
        except Exception as e:
            all_validation_failures.append(f"Create exploration failed: {e}")

        # Test 2: Get exploration by ID
        total_tests += 1
        try:
            retrieved = repo.get_exploration_by_id(exploration.id)
            if retrieved is None:
                all_validation_failures.append("Get by ID returned None")
            elif retrieved.goal.value != 0.40:
                all_validation_failures.append(f"Goal value mismatch: {retrieved.goal.value}")
        except Exception as e:
            all_validation_failures.append(f"Get exploration by ID failed: {e}")

        # Test 3: Create root node
        total_tests += 1
        try:
            root_node = ScenarioNode(
                exploration_id=exploration.id,
                depth=0,
                scorecard_params=ScorecardParams(
                    complexity=0.45,
                    initial_effort=0.30,
                    perceived_risk=0.25,
                    time_to_value=0.40,
                ),
                simulation_results=SimulationResults(
                    success_rate=0.25,
                    fail_rate=0.45,
                    did_not_try_rate=0.30,
                ),
            )
            result = repo.create_node(root_node)
            if result.id != root_node.id:
                all_validation_failures.append(f"Root node ID mismatch: {result.id}")
        except Exception as e:
            all_validation_failures.append(f"Create root node failed: {e}")

        # Test 4: Get root node
        total_tests += 1
        try:
            retrieved_root = repo.get_root_node(exploration.id)
            if retrieved_root is None:
                all_validation_failures.append("Get root node returned None")
            elif retrieved_root.depth != 0:
                all_validation_failures.append(f"Root depth mismatch: {retrieved_root.depth}")
        except Exception as e:
            all_validation_failures.append(f"Get root node failed: {e}")

        # Test 5: Create child node
        total_tests += 1
        try:
            child_node = ScenarioNode(
                exploration_id=exploration.id,
                parent_id=root_node.id,
                depth=1,
                action_applied="Adicionar tooltip contextual",
                action_category="ux_interface",
                rationale="Reduz friccao cognitiva",
                scorecard_params=ScorecardParams(
                    complexity=0.43,
                    initial_effort=0.30,
                    perceived_risk=0.25,
                    time_to_value=0.38,
                ),
                simulation_results=SimulationResults(
                    success_rate=0.32,
                    fail_rate=0.40,
                    did_not_try_rate=0.28,
                ),
            )
            result = repo.create_node(child_node)
            if result.parent_id != root_node.id:
                all_validation_failures.append(f"Child parent_id mismatch: {result.parent_id}")
        except Exception as e:
            all_validation_failures.append(f"Create child node failed: {e}")

        # Test 6: Get frontier nodes
        total_tests += 1
        try:
            frontier = repo.get_frontier_nodes(exploration.id)
            if len(frontier) != 2:
                all_validation_failures.append(f"Expected 2 frontier nodes, got {len(frontier)}")
        except Exception as e:
            all_validation_failures.append(f"Get frontier nodes failed: {e}")

        # Test 7: Update node status
        total_tests += 1
        try:
            repo.update_node_status(root_node.id, NodeStatus.DOMINATED)
            updated = repo.get_node_by_id(root_node.id)
            if updated is None:
                all_validation_failures.append("Updated node not found")
            elif updated.node_status != NodeStatus.DOMINATED:
                all_validation_failures.append(f"Status not updated: {updated.node_status}")
        except Exception as e:
            all_validation_failures.append(f"Update node status failed: {e}")

        # Test 8: Get path to node
        total_tests += 1
        try:
            path = repo.get_path_to_node(child_node.id)
            if len(path) != 2:
                all_validation_failures.append(f"Expected path length 2, got {len(path)}")
            elif path[0].depth != 0:
                all_validation_failures.append(f"Path should start at root: {path[0].depth}")
            elif path[1].depth != 1:
                all_validation_failures.append(f"Path should end at child: {path[1].depth}")
        except Exception as e:
            all_validation_failures.append(f"Get path to node failed: {e}")

        # Test 9: Count nodes by status
        total_tests += 1
        try:
            counts = repo.count_nodes_by_status(exploration.id)
            if counts["active"] != 1:
                all_validation_failures.append(f"Expected 1 active, got {counts['active']}")
            if counts["dominated"] != 1:
                all_validation_failures.append(f"Expected 1 dominated, got {counts['dominated']}")
        except Exception as e:
            all_validation_failures.append(f"Count nodes by status failed: {e}")

        # Test 10: Get best node by success rate
        total_tests += 1
        try:
            best = repo.get_best_node_by_success_rate(exploration.id)
            if best is None:
                all_validation_failures.append("Get best node returned None")
            elif best.id != child_node.id:
                all_validation_failures.append(f"Best node should be child: {best.id}")
        except Exception as e:
            all_validation_failures.append(f"Get best node failed: {e}")

        # Test 11: Update exploration
        total_tests += 1
        try:
            exploration.current_depth = 1
            exploration.total_nodes = 2
            exploration.best_success_rate = 0.32
            result = repo.update_exploration(exploration)
            retrieved = repo.get_exploration_by_id(exploration.id)
            if retrieved.current_depth != 1:
                all_validation_failures.append(f"current_depth not updated: {retrieved.current_depth}")
            if retrieved.best_success_rate != 0.32:
                all_validation_failures.append(f"best_success_rate not updated: {retrieved.best_success_rate}")
        except Exception as e:
            all_validation_failures.append(f"Update exploration failed: {e}")

        # Test 12: Get children
        total_tests += 1
        try:
            children = repo.get_children(root_node.id)
            if len(children) != 1:
                all_validation_failures.append(f"Expected 1 child, got {len(children)}")
            elif children[0].id != child_node.id:
                all_validation_failures.append(f"Child ID mismatch: {children[0].id}")
        except Exception as e:
            all_validation_failures.append(f"Get children failed: {e}")

        db.close()

    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
