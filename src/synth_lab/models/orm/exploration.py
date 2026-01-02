"""
SQLAlchemy ORM models for explorations and scenario nodes.

These models map to the 'explorations' and 'scenario_nodes' tables.

References:
    - data-model.md: Exploration and ScenarioNode entity definitions
    - SQLAlchemy relationships: https://docs.sqlalchemy.org/en/20/orm/relationships.html
"""

from typing import TYPE_CHECKING, Any

from sqlalchemy import Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from synth_lab.models.orm.base import Base, MutableJSON

if TYPE_CHECKING:
    from synth_lab.models.orm.analysis import AnalysisRun
    from synth_lab.models.orm.experiment import Experiment


class Exploration(Base):
    """
    Scenario exploration for an experiment.

    Represents an AI-driven exploration of possible scenarios
    to achieve a specific goal.

    Attributes:
        id: Exploration identifier (format: expl_[8 hex chars])
        experiment_id: Link to parent experiment
        baseline_analysis_id: Starting analysis run
        goal: Exploration goal as JSON
        config: Configuration as JSON
        status: running/goal_achieved/depth_limit_reached/cost_limit_reached/no_viable_paths
        current_depth: Current tree depth
        total_nodes: Total nodes explored
        total_llm_calls: Number of LLM API calls
        best_success_rate: Best success rate found
        started_at: ISO timestamp of start
        completed_at: ISO timestamp of completion

    Relationships:
        experiment: N:1 - Parent experiment
        baseline_analysis: N:1 - Starting analysis run
        nodes: 1:N - Scenario nodes in exploration
    """

    __tablename__ = "explorations"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    experiment_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
    )
    baseline_analysis_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("analysis_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    goal: Mapped[dict[str, Any]] = mapped_column(MutableJSON, nullable=False)
    config: Mapped[dict[str, Any]] = mapped_column(MutableJSON, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="running")
    current_depth: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_nodes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_llm_calls: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    best_success_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    started_at: Mapped[str] = mapped_column(String(50), nullable=False)
    completed_at: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Relationships
    experiment: Mapped["Experiment"] = relationship(
        "Experiment",
        back_populates="explorations",
    )
    baseline_analysis: Mapped["AnalysisRun"] = relationship(
        "AnalysisRun",
        back_populates="explorations",
    )
    nodes: Mapped[list["ScenarioNode"]] = relationship(
        "ScenarioNode",
        back_populates="exploration",
        cascade="all, delete-orphan",
    )

    # Indexes
    __table_args__ = (
        Index("idx_explorations_experiment", "experiment_id"),
        Index("idx_explorations_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<Exploration(id={self.id!r}, status={self.status!r})>"


class ScenarioNode(Base):
    """
    Node in an exploration tree.

    Represents a single scenario with scorecard parameters
    and simulation results.

    Attributes:
        id: Node identifier (format: node_[8 hex chars])
        exploration_id: Link to parent exploration
        parent_id: Link to parent node (self-referential tree)
        depth: Tree depth (0 = root)
        action_applied: Action description
        action_category: Action category
        rationale: Why this action was taken
        short_action: Brief action summary
        scorecard_params: Scorecard parameters as JSON
        simulation_results: Simulation results as JSON
        execution_time_seconds: Node execution time
        node_status: active/dominated/winner/expansion_failed
        created_at: ISO timestamp

    Relationships:
        exploration: N:1 - Parent exploration
        parent: N:1 - Parent node (self-referential)
        children: 1:N - Child nodes
    """

    __tablename__ = "scenario_nodes"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    exploration_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("explorations.id", ondelete="CASCADE"),
        nullable=False,
    )
    parent_id: Mapped[str | None] = mapped_column(
        String(50),
        ForeignKey("scenario_nodes.id", ondelete="SET NULL"),
        nullable=True,
    )
    depth: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    action_applied: Mapped[str | None] = mapped_column(Text, nullable=True)
    action_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    short_action: Mapped[str | None] = mapped_column(String(200), nullable=True)
    scorecard_params: Mapped[dict[str, Any]] = mapped_column(MutableJSON, nullable=False)
    simulation_results: Mapped[dict[str, Any] | None] = mapped_column(MutableJSON, nullable=True)
    execution_time_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    node_status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    created_at: Mapped[str] = mapped_column(String(50), nullable=False)

    # Relationships
    exploration: Mapped["Exploration"] = relationship(
        "Exploration",
        back_populates="nodes",
    )
    parent: Mapped["ScenarioNode | None"] = relationship(
        "ScenarioNode",
        remote_side=[id],
        back_populates="children",
    )
    children: Mapped[list["ScenarioNode"]] = relationship(
        "ScenarioNode",
        back_populates="parent",
        cascade="all, delete-orphan",
    )

    # Indexes
    __table_args__ = (
        Index("idx_scenario_nodes_exploration", "exploration_id"),
        Index("idx_scenario_nodes_parent", "parent_id"),
        Index("idx_scenario_nodes_status", "exploration_id", "node_status"),
        Index("idx_scenario_nodes_depth", "exploration_id", "depth"),
    )

    def __repr__(self) -> str:
        return f"<ScenarioNode(id={self.id!r}, depth={self.depth}, status={self.node_status!r})>"


if __name__ == "__main__":
    import sys

    # Validation
    all_validation_failures = []
    total_tests = 0

    # Test 1: Exploration has correct table name
    total_tests += 1
    if Exploration.__tablename__ != "explorations":
        all_validation_failures.append(
            f"Exploration table name is {Exploration.__tablename__}, expected 'explorations'"
        )

    # Test 2: ScenarioNode has correct table name
    total_tests += 1
    if ScenarioNode.__tablename__ != "scenario_nodes":
        all_validation_failures.append(
            f"ScenarioNode table name is {ScenarioNode.__tablename__}, expected 'scenario_nodes'"
        )

    # Test 3: Exploration has required columns
    total_tests += 1
    required_columns = {"id", "experiment_id", "baseline_analysis_id", "goal", "config", "status", "current_depth", "total_nodes", "total_llm_calls", "best_success_rate", "started_at", "completed_at"}
    actual_columns = set(Exploration.__table__.columns.keys())
    missing = required_columns - actual_columns
    if missing:
        all_validation_failures.append(f"Exploration missing columns: {missing}")

    # Test 4: ScenarioNode has required columns
    total_tests += 1
    required_columns = {"id", "exploration_id", "parent_id", "depth", "action_applied", "action_category", "rationale", "short_action", "scorecard_params", "simulation_results", "execution_time_seconds", "node_status", "created_at"}
    actual_columns = set(ScenarioNode.__table__.columns.keys())
    missing = required_columns - actual_columns
    if missing:
        all_validation_failures.append(f"ScenarioNode missing columns: {missing}")

    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
