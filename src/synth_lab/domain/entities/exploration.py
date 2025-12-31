"""
Exploration entity for LLM-assisted scenario exploration.

Represents a session of scenario exploration where an LLM proposes improvement
actions that are translated to scorecard impacts and simulated.

References:
    - Spec: specs/024-llm-scenario-exploration/spec.md
    - Data model: specs/024-llm-scenario-exploration/data-model.md
"""

import secrets
from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field, field_validator


def generate_exploration_id() -> str:
    """
    Generate an exploration ID with expl_ prefix and 8-char hex suffix.

    Returns:
        str: ID in format expl_[a-f0-9]{8}
    """
    return f"expl_{secrets.token_hex(4)}"


class ExplorationStatus(str, Enum):
    """Status of an exploration session."""

    RUNNING = "running"
    GOAL_ACHIEVED = "goal_achieved"
    DEPTH_LIMIT_REACHED = "depth_limit_reached"
    COST_LIMIT_REACHED = "cost_limit_reached"
    NO_VIABLE_PATHS = "no_viable_paths"


class Goal(BaseModel):
    """
    Goal definition for exploration.

    Attributes:
        metric: The metric to optimize (currently only success_rate)
        operator: Comparison operator (currently only >=)
        value: Target value to achieve
    """

    metric: str = Field(
        default="success_rate",
        description="Metric to optimize.",
    )

    operator: str = Field(
        default=">=",
        description="Comparison operator.",
    )

    value: float = Field(
        ge=0.0,
        le=1.0,
        description="Target value to achieve.",
    )

    @field_validator("metric")
    @classmethod
    def validate_metric(cls, v: str) -> str:
        """Ensure metric is supported."""
        if v != "success_rate":
            raise ValueError(f"Unsupported metric: {v}. Only 'success_rate' is supported.")
        return v

    @field_validator("operator")
    @classmethod
    def validate_operator(cls, v: str) -> str:
        """Ensure operator is supported."""
        if v != ">=":
            raise ValueError(f"Unsupported operator: {v}. Only '>=' is supported.")
        return v

    def is_achieved(self, current_value: float) -> bool:
        """Check if goal is achieved with current value."""
        return current_value >= self.value


class ExplorationConfig(BaseModel):
    """
    Configuration for exploration search.

    Attributes:
        beam_width: Number of scenarios to keep per iteration (1-10)
        max_depth: Maximum depth of exploration tree (1-10)
        max_llm_calls: Maximum number of LLM calls allowed (1-100)
        n_executions: Monte Carlo executions per simulation (10-1000)
        sigma: Standard deviation for noise in simulations
        seed: Random seed for reproducibility
    """

    beam_width: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of scenarios to keep per iteration.",
    )

    max_depth: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Maximum depth of exploration tree.",
    )

    max_llm_calls: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of LLM calls allowed.",
    )

    n_executions: int = Field(
        default=100,
        ge=10,
        le=1000,
        description="Monte Carlo executions per simulation.",
    )

    sigma: float = Field(
        default=0.1,
        ge=0.0,
        le=0.5,
        description="Standard deviation for noise.",
    )

    seed: int | None = Field(
        default=None,
        description="Random seed for reproducibility.",
    )


class Exploration(BaseModel):
    """
    Exploration session entity.

    Represents a complete exploration session from a baseline analysis,
    tracking the search tree and progress toward the goal.

    Attributes:
        id: Unique identifier (expl_[a-f0-9]{8})
        experiment_id: Reference to source experiment
        baseline_analysis_id: Reference to baseline analysis
        goal: Performance goal to achieve
        config: Search configuration
        status: Current status of exploration
        current_depth: Current depth reached in tree
        total_nodes: Total nodes created
        total_llm_calls: Total LLM calls made
        best_success_rate: Best success rate achieved
        started_at: Start timestamp
        completed_at: Completion timestamp (if finished)
    """

    id: str = Field(
        default_factory=generate_exploration_id,
        pattern=r"^expl_[a-f0-9]{8}$",
        description="Unique exploration ID.",
    )

    experiment_id: str = Field(
        pattern=r"^exp_[a-f0-9]{8}$",
        description="Reference to source experiment.",
    )

    baseline_analysis_id: str = Field(
        pattern=r"^ana_[a-f0-9]{8}$",
        description="Reference to baseline analysis.",
    )

    goal: Goal = Field(
        description="Performance goal to achieve.",
    )

    config: ExplorationConfig = Field(
        default_factory=ExplorationConfig,
        description="Search configuration.",
    )

    status: ExplorationStatus = Field(
        default=ExplorationStatus.RUNNING,
        description="Current status of exploration.",
    )

    current_depth: int = Field(
        default=0,
        ge=0,
        description="Current depth reached in tree.",
    )

    total_nodes: int = Field(
        default=0,
        ge=0,
        description="Total nodes created.",
    )

    total_llm_calls: int = Field(
        default=0,
        ge=0,
        description="Total LLM calls made.",
    )

    best_success_rate: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Best success rate achieved.",
    )

    started_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Start timestamp.",
    )

    completed_at: datetime | None = Field(
        default=None,
        description="Completion timestamp.",
    )

    def is_running(self) -> bool:
        """Check if exploration is still running."""
        return self.status == ExplorationStatus.RUNNING

    def is_completed(self) -> bool:
        """Check if exploration has completed (any terminal status)."""
        return self.status != ExplorationStatus.RUNNING

    def has_reached_depth_limit(self) -> bool:
        """Check if depth limit has been reached."""
        return self.current_depth >= self.config.max_depth

    def has_reached_cost_limit(self) -> bool:
        """Check if LLM call limit has been reached."""
        return self.total_llm_calls >= self.config.max_llm_calls

    def mark_completed(self, status: ExplorationStatus) -> None:
        """Mark exploration as completed with given status."""
        self.status = status
        self.completed_at = datetime.now(timezone.utc)


if __name__ == "__main__":
    import sys

    all_validation_failures = []
    total_tests = 0

    # Test 1: Generate unique IDs
    total_tests += 1
    try:
        ids = {generate_exploration_id() for _ in range(100)}
        if len(ids) != 100:
            all_validation_failures.append("IDs should be unique")
        for eid in ids:
            if not eid.startswith("expl_") or len(eid) != 13:
                all_validation_failures.append(f"Invalid ID format: {eid}")
                break
    except Exception as e:
        all_validation_failures.append(f"ID generation test failed: {e}")

    # Test 2: Goal validation
    total_tests += 1
    try:
        goal = Goal(value=0.40)
        if goal.metric != "success_rate":
            all_validation_failures.append(f"Goal metric should be success_rate: {goal.metric}")
        if goal.operator != ">=":
            all_validation_failures.append(f"Goal operator should be >=: {goal.operator}")
        if not goal.is_achieved(0.45):
            all_validation_failures.append("Goal should be achieved at 0.45")
        if goal.is_achieved(0.35):
            all_validation_failures.append("Goal should not be achieved at 0.35")
    except Exception as e:
        all_validation_failures.append(f"Goal validation test failed: {e}")

    # Test 3: Goal rejects invalid metric
    total_tests += 1
    try:
        Goal(metric="invalid", value=0.5)
        all_validation_failures.append("Should reject invalid metric")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Unexpected error for invalid metric: {e}")

    # Test 4: ExplorationConfig defaults
    total_tests += 1
    try:
        config = ExplorationConfig()
        if config.beam_width != 3:
            all_validation_failures.append(f"Default beam_width should be 3: {config.beam_width}")
        if config.max_depth != 5:
            all_validation_failures.append(f"Default max_depth should be 5: {config.max_depth}")
        if config.max_llm_calls != 20:
            all_validation_failures.append(
                f"Default max_llm_calls should be 20: {config.max_llm_calls}"
            )
    except Exception as e:
        all_validation_failures.append(f"ExplorationConfig defaults test failed: {e}")

    # Test 5: ExplorationConfig validation
    total_tests += 1
    try:
        ExplorationConfig(beam_width=15)
        all_validation_failures.append("Should reject beam_width > 10")
    except ValueError:
        pass  # Expected
    except Exception as e:
        all_validation_failures.append(f"Unexpected error for beam_width > 10: {e}")

    # Test 6: Create exploration
    total_tests += 1
    try:
        exploration = Exploration(
            experiment_id="exp_12345678",
            baseline_analysis_id="ana_87654321",
            goal=Goal(value=0.40),
        )
        if not exploration.id.startswith("expl_"):
            all_validation_failures.append(f"Exploration ID should start with expl_: {exploration.id}")
        if exploration.status != ExplorationStatus.RUNNING:
            all_validation_failures.append(f"Initial status should be RUNNING: {exploration.status}")
        if not exploration.is_running():
            all_validation_failures.append("New exploration should be running")
    except Exception as e:
        all_validation_failures.append(f"Create exploration test failed: {e}")

    # Test 7: Exploration status methods
    total_tests += 1
    try:
        exploration = Exploration(
            experiment_id="exp_12345678",
            baseline_analysis_id="ana_87654321",
            goal=Goal(value=0.40),
            config=ExplorationConfig(max_depth=3, max_llm_calls=10),
        )
        exploration.current_depth = 3
        if not exploration.has_reached_depth_limit():
            all_validation_failures.append("Should detect depth limit reached")
        exploration.total_llm_calls = 10
        if not exploration.has_reached_cost_limit():
            all_validation_failures.append("Should detect cost limit reached")
    except Exception as e:
        all_validation_failures.append(f"Exploration status methods test failed: {e}")

    # Test 8: Mark exploration completed
    total_tests += 1
    try:
        exploration = Exploration(
            experiment_id="exp_12345678",
            baseline_analysis_id="ana_87654321",
            goal=Goal(value=0.40),
        )
        exploration.mark_completed(ExplorationStatus.GOAL_ACHIEVED)
        if exploration.status != ExplorationStatus.GOAL_ACHIEVED:
            all_validation_failures.append(
                f"Status should be GOAL_ACHIEVED: {exploration.status}"
            )
        if exploration.completed_at is None:
            all_validation_failures.append("completed_at should be set")
        if exploration.is_running():
            all_validation_failures.append("Completed exploration should not be running")
    except Exception as e:
        all_validation_failures.append(f"Mark completed test failed: {e}")

    # Test 9: Serialization
    total_tests += 1
    try:
        exploration = Exploration(
            experiment_id="exp_12345678",
            baseline_analysis_id="ana_87654321",
            goal=Goal(value=0.40),
            config=ExplorationConfig(beam_width=5),
        )
        data = exploration.model_dump()
        if data["goal"]["value"] != 0.40:
            all_validation_failures.append("Serialization goal value mismatch")
        if data["config"]["beam_width"] != 5:
            all_validation_failures.append("Serialization config beam_width mismatch")
        if data["status"] != "running":
            all_validation_failures.append(f"Serialization status mismatch: {data['status']}")
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
