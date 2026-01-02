"""
API schemas for exploration endpoints.

Request and response models for LLM-assisted scenario exploration.

References:
    - Spec: specs/024-llm-scenario-exploration/spec.md
    - API contract: specs/024-llm-scenario-exploration/contracts/exploration-api.yaml
"""

from datetime import datetime

from pydantic import BaseModel, Field

# ========== Request Schemas ==========


class ExplorationCreate(BaseModel):
    """Request to create a new exploration."""

    experiment_id: str = Field(
        pattern=r"^exp_[a-f0-9]{8}$",
        description="ID of the source experiment.",
        json_schema_extra={"example": "exp_12345678"})

    goal_value: float = Field(
        ge=0.0,
        le=1.0,
        description="Target success_rate to achieve (0-1).",
        json_schema_extra={"example": 0.40})

    beam_width: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of scenarios to keep per iteration.")

    max_depth: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Maximum depth of exploration tree.")

    max_llm_calls: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of LLM calls.")

    n_executions: int = Field(
        default=100,
        ge=10,
        le=1000,
        description="Monte Carlo executions per simulation.")

    seed: int | None = Field(
        default=None,
        description="Random seed for reproducibility.")


# ========== Response Schemas ==========


class GoalResponse(BaseModel):
    """Goal definition in response."""

    metric: str = Field(description="Metric to optimize (success_rate).")
    operator: str = Field(description="Comparison operator (>=).")
    value: float = Field(description="Target value.")


class ConfigResponse(BaseModel):
    """Configuration in response."""

    beam_width: int
    max_depth: int
    max_llm_calls: int
    n_executions: int
    sigma: float
    seed: int | None


class ExplorationSummary(BaseModel):
    """Summary of exploration for list view."""

    id: str = Field(description="Exploration ID.")
    status: str = Field(description="Current status.")
    goal_value: float = Field(description="Target success_rate.")
    best_success_rate: float | None = Field(description="Best success rate achieved.")
    total_nodes: int = Field(description="Total nodes created.")
    started_at: datetime = Field(description="Start timestamp.")
    completed_at: datetime | None = Field(description="Completion timestamp.")


class ExplorationResponse(BaseModel):
    """Response for exploration data."""

    id: str = Field(description="Exploration ID.")
    experiment_id: str = Field(description="Source experiment ID.")
    baseline_analysis_id: str = Field(description="Baseline analysis ID.")
    goal: GoalResponse = Field(description="Performance goal.")
    config: ConfigResponse = Field(description="Search configuration.")
    status: str = Field(description="Current status.")
    current_depth: int = Field(description="Current depth reached.")
    total_nodes: int = Field(description="Total nodes created.")
    total_llm_calls: int = Field(description="Total LLM calls made.")
    best_success_rate: float | None = Field(description="Best success rate achieved.")
    started_at: datetime = Field(description="Start timestamp.")
    completed_at: datetime | None = Field(description="Completion timestamp.")


class ScorecardParamsResponse(BaseModel):
    """Scorecard parameters in response."""

    complexity: float
    initial_effort: float
    perceived_risk: float
    time_to_value: float


class SimulationResultsResponse(BaseModel):
    """Simulation results in response."""

    success_rate: float
    fail_rate: float
    did_not_try_rate: float


class ScenarioNodeResponse(BaseModel):
    """Response for a scenario node."""

    id: str = Field(description="Node ID.")
    exploration_id: str = Field(description="Parent exploration ID.")
    parent_id: str | None = Field(description="Parent node ID.")
    depth: int = Field(description="Depth in tree.")
    action_applied: str | None = Field(description="Action that created this node.")
    action_category: str | None = Field(description="Category of action.")
    rationale: str | None = Field(description="Rationale for action.")
    short_action: str | None = Field(description="Short 3-word action label.")
    scorecard_params: ScorecardParamsResponse = Field(description="Scorecard parameters.")
    simulation_results: SimulationResultsResponse | None = Field(
        description="Simulation results."
    )
    execution_time_seconds: float | None = Field(description="Simulation time.")
    node_status: str = Field(description="Node status.")
    created_at: datetime = Field(description="Creation timestamp.")


class ExplorationTreeResponse(BaseModel):
    """Response for exploration tree."""

    exploration: ExplorationResponse = Field(description="Exploration data.")
    nodes: list[ScenarioNodeResponse] = Field(description="All nodes in tree.")
    node_count_by_status: dict[str, int] = Field(description="Count by status.")


class PathStepResponse(BaseModel):
    """A step in the winning path."""

    depth: int
    action: str | None
    category: str | None
    rationale: str | None
    success_rate: float
    delta_success_rate: float


class WinningPathResponse(BaseModel):
    """Response for winning path."""

    exploration_id: str = Field(description="Exploration ID.")
    winner_node_id: str = Field(description="Winner node ID.")
    path: list[PathStepResponse] = Field(description="Path from root to winner.")
    total_improvement: float = Field(description="Total success_rate improvement.")


class IterationResultResponse(BaseModel):
    """Response for iteration result."""

    exploration_id: str
    iteration_number: int
    status: str
    nodes_expanded: int
    nodes_created: int
    nodes_dominated: int
    llm_calls_made: int
    best_success_rate: float
    frontier_size: int


# ========== Catalog Schemas ==========


class ImpactRangeResponse(BaseModel):
    """Impact range for an action example."""

    min: float
    max: float


class ActionExampleResponse(BaseModel):
    """Example action in catalog."""

    action: str
    typical_impacts: dict[str, ImpactRangeResponse]


class ActionCategoryResponse(BaseModel):
    """Action category in catalog."""

    id: str
    name: str
    description: str
    examples: list[ActionExampleResponse]


class ActionCatalogResponse(BaseModel):
    """Response for action catalog."""

    version: str
    categories: list[ActionCategoryResponse]


# ========== Conversion Functions ==========


def exploration_to_response(exploration) -> ExplorationResponse:
    """Convert Exploration entity to response schema."""
    return ExplorationResponse(
        id=exploration.id,
        experiment_id=exploration.experiment_id,
        baseline_analysis_id=exploration.baseline_analysis_id,
        goal=GoalResponse(
            metric=exploration.goal.metric,
            operator=exploration.goal.operator,
            value=exploration.goal.value),
        config=ConfigResponse(
            beam_width=exploration.config.beam_width,
            max_depth=exploration.config.max_depth,
            max_llm_calls=exploration.config.max_llm_calls,
            n_executions=exploration.config.n_executions,
            sigma=exploration.config.sigma,
            seed=exploration.config.seed),
        status=exploration.status.value,
        current_depth=exploration.current_depth,
        total_nodes=exploration.total_nodes,
        total_llm_calls=exploration.total_llm_calls,
        best_success_rate=exploration.best_success_rate,
        started_at=exploration.started_at,
        completed_at=exploration.completed_at)


def node_to_response(node) -> ScenarioNodeResponse:
    """Convert ScenarioNode entity to response schema."""
    simulation_results = None
    if node.simulation_results:
        simulation_results = SimulationResultsResponse(
            success_rate=node.simulation_results.success_rate,
            fail_rate=node.simulation_results.fail_rate,
            did_not_try_rate=node.simulation_results.did_not_try_rate)

    return ScenarioNodeResponse(
        id=node.id,
        exploration_id=node.exploration_id,
        parent_id=node.parent_id,
        depth=node.depth,
        action_applied=node.action_applied,
        action_category=node.action_category,
        rationale=node.rationale,
        short_action=node.short_action,
        scorecard_params=ScorecardParamsResponse(
            complexity=node.scorecard_params.complexity,
            initial_effort=node.scorecard_params.initial_effort,
            perceived_risk=node.scorecard_params.perceived_risk,
            time_to_value=node.scorecard_params.time_to_value),
        simulation_results=simulation_results,
        execution_time_seconds=node.execution_time_seconds,
        node_status=node.node_status.value,
        created_at=node.created_at)
