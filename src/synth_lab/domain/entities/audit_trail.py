"""
AuditTrail entity for causal simulation system.

Represents complete reproducibility audit trail for simulation sessions.

References:
    - Spec: specs/035-causal-simulation/spec.md
    - Data model: specs/035-causal-simulation/data-model.md
"""

import secrets
from datetime import datetime, timezone

from pydantic import BaseModel, Field


def generate_audit_id() -> str:
    """
    Generate an audit trail ID with audit_ prefix and 8-char hex suffix.

    Returns:
        str: ID in format audit_[a-f0-9]{8}
    """
    return f"audit_{secrets.token_hex(4)}"


class DAGSnapshot(BaseModel):
    """
    Snapshot of DAG state.

    Attributes:
        version: DAG version number
        nodes: List of variable definitions
        edges: List of causal edges
    """

    version: int = Field(..., description="DAG version number")
    nodes: list[dict] = Field(default_factory=list, description="Variable definitions")
    edges: list[dict] = Field(default_factory=list, description="Causal edges")


class HypothesisSnapshotItem(BaseModel):
    """
    Snapshot of a single hypothesis.

    Attributes:
        variable_id: Variable ID
        variable_name: Variable name
        distribution_type: Type of distribution
        parameters: Distribution parameters
    """

    variable_id: str = Field(..., description="Variable ID")
    variable_name: str = Field(..., description="Variable name")
    distribution_type: str = Field(..., description="Distribution type")
    parameters: dict = Field(default_factory=dict, description="Distribution parameters")


class EvidenceSnapshot(BaseModel):
    """
    Snapshot of evidence state.

    Attributes:
        outcome_distributions: Percentile distributions
        variance_explained: Sensitivity analysis results
        n_failure_modes: Number of failure modes detected
        n_clusters: Number of clusters detected
    """

    outcome_distributions: dict = Field(
        default_factory=dict, description="Percentile distributions"
    )
    variance_explained: list[dict] = Field(
        default_factory=list, description="Sensitivity analysis results"
    )
    n_failure_modes: int = Field(default=0, description="Number of failure modes")
    n_clusters: int = Field(default=0, description="Number of clusters")


class InsightSnapshot(BaseModel):
    """
    Snapshot of insight.

    Attributes:
        id: Insight ID
        insight_type: Type of insight
        title: Insight title
        description: Brief description
    """

    id: str = Field(..., description="Insight ID")
    insight_type: str = Field(..., description="Type of insight")
    title: str = Field(..., description="Insight title")
    description: str = Field(default="", description="Brief description")


class AuditTrail(BaseModel):
    """
    Complete reproducibility audit trail for a simulation.

    Captures all inputs and outputs to enable exact replay.

    Attributes:
        id: Unique identifier (audit_[a-f0-9]{8})
        simulation_id: Parent simulation ID
        question: Original natural language question
        dag_snapshot: DAG state at simulation time
        hypotheses_snapshot: Hypothesis parameters at simulation time
        random_seed: Master random seed for reproducibility
        n_worlds: Number of worlds simulated
        evidence_snapshot: Evidence summary at simulation time
        insights_snapshot: Generated insights
        created_at: ISO 8601 timestamp of creation
    """

    id: str = Field(
        default_factory=generate_audit_id,
        pattern=r"^audit_[a-f0-9]{8}$",
        description="Unique audit trail ID",
    )

    simulation_id: str = Field(
        ...,
        pattern=r"^sim_[a-f0-9]{8}$",
        description="Parent simulation ID",
    )

    question: str = Field(..., description="Original natural language question")

    dag_snapshot: DAGSnapshot = Field(
        ..., description="DAG state at simulation time"
    )

    hypotheses_snapshot: list[HypothesisSnapshotItem] = Field(
        default_factory=list, description="Hypothesis parameters at simulation time"
    )

    random_seed: int = Field(..., description="Master random seed for reproducibility")

    n_worlds: int = Field(default=500, description="Number of worlds simulated")

    evidence_snapshot: EvidenceSnapshot = Field(
        default_factory=EvidenceSnapshot, description="Evidence summary"
    )

    insights_snapshot: list[InsightSnapshot] = Field(
        default_factory=list, description="Generated insights"
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp (UTC)",
    )

    def get_replay_config(self) -> dict:
        """
        Get configuration for replaying the simulation.

        Returns:
            Dict with replay configuration
        """
        return {
            "simulation_id": self.simulation_id,
            "question": self.question,
            "random_seed": self.random_seed,
            "n_worlds": self.n_worlds,
            "dag_version": self.dag_snapshot.version,
            "created_at": self.created_at.isoformat(),
        }

    def to_export_package(self) -> dict:
        """
        Export full audit trail as a portable package.

        Returns:
            Dict with complete audit trail data
        """
        return {
            "audit_id": self.id,
            "simulation_id": self.simulation_id,
            "question": self.question,
            "dag": self.dag_snapshot.model_dump(),
            "hypotheses": [h.model_dump() for h in self.hypotheses_snapshot],
            "random_seed": self.random_seed,
            "n_worlds": self.n_worlds,
            "evidence_summary": self.evidence_snapshot.model_dump(),
            "insights": [i.model_dump() for i in self.insights_snapshot],
            "created_at": self.created_at.isoformat(),
            "export_format_version": "1.0",
        }
