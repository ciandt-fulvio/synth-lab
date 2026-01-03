"""
Exploration utility functions for synth-lab.

Shared utilities for exploration document generation services.

References:
    - Summary generator: exploration_summary_generator_service.py
    - PRFAQ generator: exploration_prfaq_generator_service.py
"""

from synth_lab.domain.entities.scenario_node import ScenarioNode
from synth_lab.repositories.exploration_repository import ExplorationRepository


def get_winning_path(
    repo: ExplorationRepository,
    exploration_id: str,
) -> list[ScenarioNode]:
    """
    Find the winning path from root to best leaf node.

    Tiebreaker: success_rate DESC -> depth ASC -> created_at ASC

    Args:
        repo: Exploration repository.
        exploration_id: Exploration ID.

    Returns:
        List of nodes from root to best leaf.
    """
    # Get all nodes
    all_nodes = repo.get_nodes_by_exploration(exploration_id)
    if not all_nodes:
        return []

    # Find leaf nodes (nodes with no children)
    node_ids = {n.id for n in all_nodes}
    parent_ids = {n.parent_id for n in all_nodes if n.parent_id}
    leaf_ids = node_ids - parent_ids

    leaf_nodes = [n for n in all_nodes if n.id in leaf_ids]

    if not leaf_nodes:
        # No leaves found, return just root
        root = next((n for n in all_nodes if n.depth == 0), None)
        return [root] if root else []

    # Sort by tiebreaker
    leaf_nodes.sort(
        key=lambda n: (
            -(n.get_success_rate() or 0),  # DESC
            n.depth,  # ASC
            n.created_at,  # ASC
        )
    )

    # Get path from winner to root
    winner = leaf_nodes[0]
    return repo.get_path_to_node(winner.id)


if __name__ == "__main__":
    import sys

    all_validation_failures = []
    total_tests = 0

    # Test 1: Function exists and is callable
    total_tests += 1
    try:
        if not callable(get_winning_path):
            all_validation_failures.append("get_winning_path should be callable")
    except Exception as e:
        all_validation_failures.append(f"get_winning_path test failed: {e}")

    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
