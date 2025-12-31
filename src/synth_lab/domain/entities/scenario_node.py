"""
ScenarioNode entity for LLM-assisted scenario exploration.

Represents a node in the exploration tree, containing scorecard parameters,
simulation results, and the action that created it.

References:
    - Spec: specs/024-llm-scenario-exploration/spec.md
    - Data model: specs/024-llm-scenario-exploration/data-model.md
"""

import secrets
from datetime import datetime, timezone
from enum import Enum
from typing import Self

from pydantic import BaseModel, Field, field_validator, model_validator


def generate_node_id() -> str:
    """
    Generate a node ID with node_ prefix and 8-char hex suffix.

    Returns:
        str: ID in format node_[a-f0-9]{8}
    """
    return f"node_{secrets.token_hex(4)}"


class NodeStatus(str, Enum):
    """Status of a scenario node in the exploration tree."""

    ACTIVE = "active"
    DOMINATED = "dominated"
    WINNER = "winner"
    EXPANSION_FAILED = "expansion_failed"


class ScorecardParams(BaseModel):
    """
    Scorecard parameters for a scenario.

    All values are normalized to [0, 1] range.

    Attributes:
        complexity: Complexity dimension score
        initial_effort: Initial effort dimension score
        perceived_risk: Perceived risk dimension score
        time_to_value: Time to value dimension score
    """

    complexity: float = Field(
        ge=0.0,
        le=1.0,
        description="Complexity dimension score.",
    )

    initial_effort: float = Field(
        ge=0.0,
        le=1.0,
        description="Initial effort dimension score.",
    )

    perceived_risk: float = Field(
        ge=0.0,
        le=1.0,
        description="Perceived risk dimension score.",
    )

    time_to_value: float = Field(
        ge=0.0,
        le=1.0,
        description="Time to value dimension score.",
    )

    def apply_impacts(self, impacts: dict[str, float]) -> "ScorecardParams":
        """
        Apply impacts to create new scorecard params.

        Values are clamped to [0, 1] range.

        Args:
            impacts: Dictionary of parameter deltas {param: delta}

        Returns:
            New ScorecardParams with applied impacts
        """
        def clamp(value: float) -> float:
            return max(0.0, min(1.0, value))

        return ScorecardParams(
            complexity=clamp(self.complexity + impacts.get("complexity", 0.0)),
            initial_effort=clamp(self.initial_effort + impacts.get("initial_effort", 0.0)),
            perceived_risk=clamp(self.perceived_risk + impacts.get("perceived_risk", 0.0)),
            time_to_value=clamp(self.time_to_value + impacts.get("time_to_value", 0.0)),
        )


class SimulationResults(BaseModel):
    """
    Results from Monte Carlo simulation.

    Attributes:
        success_rate: Rate of successful outcomes [0, 1]
        fail_rate: Rate of failed outcomes [0, 1]
        did_not_try_rate: Rate of did-not-try outcomes [0, 1]
    """

    success_rate: float = Field(
        ge=0.0,
        le=1.0,
        description="Rate of successful outcomes.",
    )

    fail_rate: float = Field(
        ge=0.0,
        le=1.0,
        description="Rate of failed outcomes.",
    )

    did_not_try_rate: float = Field(
        ge=0.0,
        le=1.0,
        description="Rate of did-not-try outcomes.",
    )

    @model_validator(mode="after")
    def validate_rates_sum(self) -> Self:
        """Ensure rates sum to approximately 1.0."""
        total = self.success_rate + self.fail_rate + self.did_not_try_rate
        if abs(total - 1.0) > 0.01:  # Allow small floating point errors
            raise ValueError(f"Rates must sum to 1.0, got {total}")
        return self


class ScenarioNode(BaseModel):
    """
    A node in the exploration tree.

    Represents a scenario with specific scorecard parameters and simulation results.
    Contains the action that created it (except for root node).

    Attributes:
        id: Unique identifier (node_[a-f0-9]{8})
        exploration_id: Reference to parent exploration
        parent_id: Reference to parent node (None for root)
        depth: Depth in tree (0 for root)
        action_applied: Action that created this node (None for root)
        action_category: Category of action from catalog
        rationale: Rationale for the action
        scorecard_params: Current scorecard parameters
        simulation_results: Results from simulation (None if not yet simulated)
        execution_time_seconds: Time taken for simulation
        node_status: Current status of node
        created_at: Creation timestamp
    """

    id: str = Field(
        default_factory=generate_node_id,
        pattern=r"^node_[a-f0-9]{8}$",
        description="Unique node ID.",
    )

    exploration_id: str = Field(
        pattern=r"^expl_[a-f0-9]{8}$",
        description="Reference to parent exploration.",
    )

    parent_id: str | None = Field(
        default=None,
        pattern=r"^node_[a-f0-9]{8}$",
        description="Reference to parent node (None for root).",
    )

    depth: int = Field(
        ge=0,
        description="Depth in tree (0 for root).",
    )

    action_applied: str | None = Field(
        default=None,
        max_length=500,
        description="Action that created this node.",
    )

    action_category: str | None = Field(
        default=None,
        description="Category of action from catalog.",
    )

    rationale: str | None = Field(
        default=None,
        max_length=200,
        description="Rationale for the action.",
    )

    scorecard_params: ScorecardParams = Field(
        description="Current scorecard parameters.",
    )

    simulation_results: SimulationResults | None = Field(
        default=None,
        description="Results from simulation.",
    )

    execution_time_seconds: float | None = Field(
        default=None,
        ge=0.0,
        description="Time taken for simulation.",
    )

    node_status: NodeStatus = Field(
        default=NodeStatus.ACTIVE,
        description="Current status of node.",
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp.",
    )

    @field_validator("parent_id")
    @classmethod
    def validate_parent_id_pattern(cls, v: str | None) -> str | None:
        """Allow None or valid pattern."""
        return v

    @model_validator(mode="after")
    def validate_root_node(self) -> Self:
        """Ensure root node (depth=0) has no parent and no action."""
        if self.depth == 0:
            if self.parent_id is not None:
                raise ValueError("Root node (depth=0) must have parent_id=None")
            if self.action_applied is not None:
                raise ValueError("Root node (depth=0) must have action_applied=None")
        else:
            if self.parent_id is None:
                raise ValueError(f"Non-root node (depth={self.depth}) must have parent_id")
        return self

    def is_root(self) -> bool:
        """Check if this is the root node."""
        return self.depth == 0

    def is_active(self) -> bool:
        """Check if node is still active in frontier."""
        return self.node_status == NodeStatus.ACTIVE

    def is_dominated(self) -> bool:
        """Check if node has been dominated."""
        return self.node_status == NodeStatus.DOMINATED

    def is_winner(self) -> bool:
        """Check if node achieved the goal."""
        return self.node_status == NodeStatus.WINNER

    def mark_dominated(self) -> None:
        """Mark this node as dominated."""
        self.node_status = NodeStatus.DOMINATED

    def mark_winner(self) -> None:
        """Mark this node as winner."""
        self.node_status = NodeStatus.WINNER

    def mark_expansion_failed(self) -> None:
        """Mark this node as having failed expansion."""
        self.node_status = NodeStatus.EXPANSION_FAILED

    def get_success_rate(self) -> float | None:
        """Get success rate from simulation results."""
        if self.simulation_results is None:
            return None
        return self.simulation_results.success_rate


if __name__ == "__main__":
    import sys

    all_validation_failures = []
    total_tests = 0

    # Test 1: Generate unique IDs
    total_tests += 1
    try:
        ids = {generate_node_id() for _ in range(100)}
        if len(ids) != 100:
            all_validation_failures.append("IDs should be unique")
        for nid in ids:
            if not nid.startswith("node_") or len(nid) != 13:
                all_validation_failures.append(f"Invalid ID format: {nid}")
                break
    except Exception as e:
        all_validation_failures.append(f"ID generation test failed: {e}")

    # Test 2: ScorecardParams creation
    total_tests += 1
    try:
        params = ScorecardParams(
            complexity=0.45,
            initial_effort=0.30,
            perceived_risk=0.25,
            time_to_value=0.40,
        )
        if params.complexity != 0.45:
            all_validation_failures.append(f"Complexity mismatch: {params.complexity}")
    except Exception as e:
        all_validation_failures.append(f"ScorecardParams creation test failed: {e}")

    # Test 3: ScorecardParams apply_impacts
    total_tests += 1
    try:
        params = ScorecardParams(
            complexity=0.50,
            initial_effort=0.30,
            perceived_risk=0.25,
            time_to_value=0.40,
        )
        new_params = params.apply_impacts({"complexity": -0.02, "time_to_value": -0.01})
        if abs(new_params.complexity - 0.48) > 0.001:
            all_validation_failures.append(f"Complexity after impact: {new_params.complexity}")
        if abs(new_params.time_to_value - 0.39) > 0.001:
            all_validation_failures.append(f"time_to_value after impact: {new_params.time_to_value}")
        # Unchanged values should remain
        if new_params.initial_effort != 0.30:
            all_validation_failures.append(f"initial_effort should be unchanged: {new_params.initial_effort}")
    except Exception as e:
        all_validation_failures.append(f"apply_impacts test failed: {e}")

    # Test 4: ScorecardParams clamping
    total_tests += 1
    try:
        params = ScorecardParams(
            complexity=0.05,
            initial_effort=0.95,
            perceived_risk=0.50,
            time_to_value=0.50,
        )
        new_params = params.apply_impacts({"complexity": -0.10, "initial_effort": 0.10})
        if new_params.complexity != 0.0:
            all_validation_failures.append(f"Complexity should be clamped to 0: {new_params.complexity}")
        if new_params.initial_effort != 1.0:
            all_validation_failures.append(f"initial_effort should be clamped to 1: {new_params.initial_effort}")
    except Exception as e:
        all_validation_failures.append(f"Clamping test failed: {e}")

    # Test 5: SimulationResults validation
    total_tests += 1
    try:
        results = SimulationResults(
            success_rate=0.35,
            fail_rate=0.40,
            did_not_try_rate=0.25,
        )
        if results.success_rate != 0.35:
            all_validation_failures.append(f"success_rate mismatch: {results.success_rate}")
    except Exception as e:
        all_validation_failures.append(f"SimulationResults creation test failed: {e}")

    # Test 6: SimulationResults rates must sum to 1
    total_tests += 1
    try:
        SimulationResults(
            success_rate=0.50,
            fail_rate=0.30,
            did_not_try_rate=0.30,
        )
        all_validation_failures.append("Should reject rates not summing to 1")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Unexpected error for invalid rates: {e}")

    # Test 7: Create root node
    total_tests += 1
    try:
        node = ScenarioNode(
            exploration_id="expl_12345678",
            depth=0,
            scorecard_params=ScorecardParams(
                complexity=0.45,
                initial_effort=0.30,
                perceived_risk=0.25,
                time_to_value=0.40,
            ),
        )
        if not node.id.startswith("node_"):
            all_validation_failures.append(f"Node ID should start with node_: {node.id}")
        if not node.is_root():
            all_validation_failures.append("Should be root node")
        if node.parent_id is not None:
            all_validation_failures.append("Root should have no parent")
    except Exception as e:
        all_validation_failures.append(f"Create root node test failed: {e}")

    # Test 8: Root node must not have parent
    total_tests += 1
    try:
        ScenarioNode(
            exploration_id="expl_12345678",
            parent_id="node_87654321",
            depth=0,
            scorecard_params=ScorecardParams(
                complexity=0.45,
                initial_effort=0.30,
                perceived_risk=0.25,
                time_to_value=0.40,
            ),
        )
        all_validation_failures.append("Root node should not have parent")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Unexpected error for root with parent: {e}")

    # Test 9: Non-root node must have parent
    total_tests += 1
    try:
        ScenarioNode(
            exploration_id="expl_12345678",
            depth=1,
            scorecard_params=ScorecardParams(
                complexity=0.45,
                initial_effort=0.30,
                perceived_risk=0.25,
                time_to_value=0.40,
            ),
        )
        all_validation_failures.append("Non-root node should have parent")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Unexpected error for non-root without parent: {e}")

    # Test 10: Create child node
    total_tests += 1
    try:
        node = ScenarioNode(
            exploration_id="expl_12345678",
            parent_id="node_87654321",
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
        if node.is_root():
            all_validation_failures.append("Should not be root node")
        if node.action_applied != "Adicionar tooltip contextual":
            all_validation_failures.append(f"Action mismatch: {node.action_applied}")
        if node.get_success_rate() != 0.32:
            all_validation_failures.append(f"Success rate mismatch: {node.get_success_rate()}")
    except Exception as e:
        all_validation_failures.append(f"Create child node test failed: {e}")

    # Test 11: Node status transitions
    total_tests += 1
    try:
        node = ScenarioNode(
            exploration_id="expl_12345678",
            depth=0,
            scorecard_params=ScorecardParams(
                complexity=0.45,
                initial_effort=0.30,
                perceived_risk=0.25,
                time_to_value=0.40,
            ),
        )
        if not node.is_active():
            all_validation_failures.append("New node should be active")
        node.mark_dominated()
        if not node.is_dominated():
            all_validation_failures.append("Node should be dominated")
        if node.node_status != NodeStatus.DOMINATED:
            all_validation_failures.append(f"Status should be DOMINATED: {node.node_status}")
    except Exception as e:
        all_validation_failures.append(f"Node status transitions test failed: {e}")

    # Test 12: Serialization
    total_tests += 1
    try:
        node = ScenarioNode(
            exploration_id="expl_12345678",
            depth=0,
            scorecard_params=ScorecardParams(
                complexity=0.45,
                initial_effort=0.30,
                perceived_risk=0.25,
                time_to_value=0.40,
            ),
        )
        data = node.model_dump()
        if data["scorecard_params"]["complexity"] != 0.45:
            all_validation_failures.append("Serialization complexity mismatch")
        if data["node_status"] != "active":
            all_validation_failures.append(f"Serialization status mismatch: {data['node_status']}")
    except Exception as e:
        all_validation_failures.append(f"Serialization test failed: {e}")

    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
