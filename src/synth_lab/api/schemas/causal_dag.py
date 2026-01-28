"""
Pydantic schemas for Causal DAG API requests and responses.

References:
    - Spec: specs/035-causal-simulation/spec.md
    - Entity: domain/entities/causal_dag.py
"""

from datetime import datetime

from pydantic import BaseModel, Field


class VariableSchema(BaseModel):
    """Schema for a single DAG variable/node."""

    name: str = Field(..., description="Variable identifier")
    label: str = Field(..., description="Human-readable label")
    variable_type: str = Field(
        ...,
        description="Type: input, intermediate, output",
    )
    scope: str = Field(
        default="world",
        description="Scope: world or user",
    )
    description: str | None = Field(
        default=None,
        description="Variable description",
    )
    unit: str | None = Field(
        default=None,
        description="Unit of measurement",
    )
    position_x: float | None = Field(
        default=None,
        description="X position for visualization",
    )
    position_y: float | None = Field(
        default=None,
        description="Y position for visualization",
    )


class EdgeSchema(BaseModel):
    """Schema for a DAG edge."""

    source: str = Field(..., description="Source variable name")
    target: str = Field(..., description="Target variable name")
    relationship_type: str = Field(
        default="causal",
        description="Relationship type: causal, correlation",
    )
    strength: float | None = Field(
        default=None,
        ge=-1.0,
        le=1.0,
        description="Edge strength (-1 to 1)",
    )
    description: str | None = Field(
        default=None,
        description="Edge description",
    )


class DAGCreateRequest(BaseModel):
    """Request schema for creating/updating a DAG."""

    nodes: list[VariableSchema] = Field(
        ...,
        min_length=1,
        description="List of variables/nodes",
    )
    edges: list[EdgeSchema] = Field(
        default_factory=list,
        description="List of edges",
    )


class DAGUpdateRequest(BaseModel):
    """Request schema for updating a DAG."""

    nodes: list[VariableSchema] | None = Field(
        default=None,
        description="Updated nodes (replaces all)",
    )
    edges: list[EdgeSchema] | None = Field(
        default=None,
        description="Updated edges (replaces all)",
    )
    add_nodes: list[VariableSchema] | None = Field(
        default=None,
        description="Nodes to add",
    )
    remove_nodes: list[str] | None = Field(
        default=None,
        description="Node names to remove",
    )
    add_edges: list[EdgeSchema] | None = Field(
        default=None,
        description="Edges to add",
    )
    remove_edges: list[tuple[str, str]] | None = Field(
        default=None,
        description="Edges to remove (source, target)",
    )


class DAGResponse(BaseModel):
    """Response schema for DAG details."""

    id: str = Field(..., description="DAG ID")
    simulation_id: str = Field(..., description="Parent simulation ID")
    nodes: list[VariableSchema] = Field(..., description="DAG nodes")
    edges: list[EdgeSchema] = Field(..., description="DAG edges")
    version: int = Field(default=1, description="DAG version")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime | None = Field(
        default=None,
        description="Last update timestamp",
    )

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class DAGValidationRequest(BaseModel):
    """Request schema for DAG validation."""

    nodes: list[VariableSchema] = Field(..., description="Nodes to validate")
    edges: list[EdgeSchema] = Field(..., description="Edges to validate")


class DAGValidationResponse(BaseModel):
    """Response schema for DAG validation."""

    valid: bool = Field(..., description="Whether DAG is valid")
    errors: list[str] = Field(
        default_factory=list,
        description="Validation errors",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Validation warnings",
    )
    has_cycles: bool = Field(
        default=False,
        description="Whether DAG has cycles",
    )
    orphan_nodes: list[str] = Field(
        default_factory=list,
        description="Nodes without connections",
    )


class DAGVersionResponse(BaseModel):
    """Response schema for DAG version."""

    version: int = Field(..., description="Version number")
    created_at: datetime = Field(..., description="Version timestamp")
    node_count: int = Field(..., description="Number of nodes")
    edge_count: int = Field(..., description="Number of edges")
    description: str | None = Field(
        default=None,
        description="Version description",
    )


class DAGCompareRequest(BaseModel):
    """Request schema for comparing DAG versions."""

    version_a: int = Field(..., description="First version to compare")
    version_b: int = Field(..., description="Second version to compare")


class DAGCompareResponse(BaseModel):
    """Response schema for DAG comparison."""

    added_nodes: list[str] = Field(
        default_factory=list,
        description="Nodes added in version B",
    )
    removed_nodes: list[str] = Field(
        default_factory=list,
        description="Nodes removed in version B",
    )
    added_edges: list[tuple[str, str]] = Field(
        default_factory=list,
        description="Edges added in version B",
    )
    removed_edges: list[tuple[str, str]] = Field(
        default_factory=list,
        description="Edges removed in version B",
    )
    modified_nodes: list[str] = Field(
        default_factory=list,
        description="Nodes with changed properties",
    )


# =============================================================================
# Variable Enrichment Schemas
# =============================================================================


class VariableEnrichRequest(BaseModel):
    """Request schema for variable enrichment."""

    variable_name: str = Field(..., description="Name of the variable to enrich")
    intervention_hint: str | None = Field(
        default=None,
        description="Intervention description for context",
    )
    outcome_hint: str | None = Field(
        default=None,
        description="Outcome description for context",
    )


class SuggestedEdgeSchema(BaseModel):
    """Schema for a suggested edge from enrichment."""

    source: str = Field(..., description="Source variable name")
    target: str = Field(..., description="Target variable name")
    relationship_type: str = Field(
        default="causal",
        description="Relationship type",
    )
    rationale: str = Field(..., description="Why this edge is suggested")


class VariableEnrichResponse(BaseModel):
    """Response schema for variable enrichment."""

    name: str = Field(..., description="Variable name")
    variable_type: str = Field(..., description="Inferred variable type")
    scope: str = Field(..., description="Inferred scope")
    description: str = Field(..., description="Generated description")
    controllability: str = Field(..., description="Inferred controllability")
    is_intervention: bool = Field(default=False, description="Is intervention variable")
    is_outcome: bool = Field(default=False, description="Is outcome variable")
    suggested_edges: list[SuggestedEdgeSchema] = Field(
        default_factory=list,
        description="Suggested relationships with existing variables",
    )
