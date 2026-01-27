"""
CausalDAG and Variable entities for causal simulation system.

Represents directed acyclic graphs (DAGs) of causal relationships between
variables, with comprehensive validation and versioning support.

References:
    - Spec: specs/035-causal-simulation/spec.md
    - Data model: specs/035-causal-simulation/data-model.md
    - NetworkX docs: https://networkx.org/documentation/stable/
"""

import secrets
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


def generate_dag_id() -> str:
    """
    Generate a DAG ID with dag_ prefix and 8-char hex suffix.

    Returns:
        str: ID in format dag_[a-f0-9]{8}
    """
    return f"dag_{secrets.token_hex(4)}"


class VariableType(str, Enum):
    """Type classification for causal variables."""

    OBSERVABLE = "observable"  # Directly measurable (e.g., price, churn_rate)
    LATENT = "latent"  # Not directly measurable (e.g., brand_perception)
    FRICTION = "friction"  # Impediments (e.g., delivery_failures)
    FAILURE = "failure"  # Binary failure modes (e.g., payment_declined)
    PROCESS = "process"  # Sequential/temporal (e.g., onboarding_step)
    TEMPORAL = "temporal"  # Time-dependent (e.g., seasonality)


class VariableScope(str, Enum):
    """Scope level for variable simulation."""

    WORLD = "world"  # System-level variable (sampled once per world)
    USER = "user"  # Individual-level variable (sampled per user in world)


class Controllability(str, Enum):
    """Degree to which a variable can be controlled/influenced."""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RelationshipType(str, Enum):
    """Type of causal relationship between variables."""

    CAUSAL = "causal"  # Direct causal effect
    MEDIATING = "mediating"  # Mediator in causal chain
    CONFOUNDING = "confounding"  # Common cause
    MODERATING = "moderating"  # Effect modifier


class ConfidenceLevel(str, Enum):
    """Confidence level for assumptions and risks."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ImpactLevel(str, Enum):
    """Impact level for identified risks."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Variable(BaseModel):
    """
    Individual node in the causal DAG.

    Attributes:
        id: Unique identifier within DAG
        name: Human-readable variable name
        type: Classification (observable, latent, friction, etc.)
        scope: Level (world or user)
        description: Explanation of what this variable represents
        controllability: Degree of control/influence
        is_intervention: True if this is the intervention variable
        is_outcome: True if this is a primary/secondary outcome
    """

    id: str = Field(..., description="Unique variable ID within DAG")

    name: str = Field(..., description="Human-readable variable name")

    type: VariableType = Field(
        ..., description="Classification of variable type"
    )

    scope: VariableScope = Field(
        ..., description="Simulation scope (world or user level)"
    )

    description: str = Field(
        ..., description="Explanation of what this variable represents"
    )

    controllability: Controllability = Field(
        ..., description="Degree to which variable can be controlled"
    )

    is_intervention: bool = Field(
        default=False, description="True if this is the intervention variable"
    )

    is_outcome: bool = Field(
        default=False, description="True if this is a primary/secondary outcome"
    )

    position_x: Optional[float] = Field(
        default=None, description="X coordinate for visualization (saved user position)"
    )

    position_y: Optional[float] = Field(
        default=None, description="Y coordinate for visualization (saved user position)"
    )

    class Config:
        """Pydantic configuration."""

        use_enum_values = True


class Edge(BaseModel):
    """
    Directed edge representing causal relationship in DAG.

    Attributes:
        from_var: Source variable ID
        to_var: Target variable ID
        relationship_type: Type of causal relationship
    """

    from_var: str = Field(..., alias="from", description="Source variable ID")

    to_var: str = Field(..., alias="to", description="Target variable ID")

    relationship_type: RelationshipType = Field(
        default=RelationshipType.CAUSAL,
        description="Type of causal relationship",
    )

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
        populate_by_name = True


class Assumption(BaseModel):
    """
    Declared modeling assumption.

    Attributes:
        assumption: Statement of assumption
        rationale: Why this assumption is necessary
        confidence: Confidence level in this assumption
    """

    assumption: str = Field(..., description="Statement of assumption")

    rationale: str = Field(
        ..., description="Why this assumption is necessary"
    )

    confidence: ConfidenceLevel = Field(
        ..., description="Confidence level in this assumption"
    )

    class Config:
        """Pydantic configuration."""

        use_enum_values = True


class Risk(BaseModel):
    """
    Identified risk or uncertainty in the model.

    Attributes:
        risk: Description of identified risk
        impact: Potential impact level
        mitigation: How to address this risk
    """

    risk: str = Field(..., description="Description of identified risk")

    impact: ImpactLevel = Field(..., description="Potential impact level")

    mitigation: str = Field(..., description="How to address this risk")

    class Config:
        """Pydantic configuration."""

        use_enum_values = True


class ValidationError(BaseModel):
    """
    Validation error detected in DAG.

    Attributes:
        error_type: Type of validation error (cycle, orphan, etc.)
        description: Human-readable error description
        affected_nodes: Variable IDs involved in this error
    """

    error_type: str = Field(
        ..., description="Type of validation error (cycle, orphan, etc.)"
    )

    description: str = Field(
        ..., description="Human-readable error description"
    )

    affected_nodes: list[str] = Field(
        default_factory=list, description="Variable IDs involved in this error"
    )


class CausalDAG(BaseModel):
    """
    Directed acyclic graph representing causal relationships.

    Attributes:
        id: Unique identifier (dag_[a-f0-9]{8})
        simulation_id: Parent simulation ID
        nodes: Array of Variable objects
        edges: Array of causal relationships
        assumptions: Declared modeling assumptions
        risks: Identified uncertainties
        is_validated: Whether DAG passed validation
        validation_errors: Detected validation issues
        version: Version number for DAG edits
        created_at: ISO 8601 timestamp of creation
    """

    id: str = Field(
        default_factory=generate_dag_id,
        pattern=r"^dag_[a-f0-9]{8}$",
        description="Unique DAG ID",
    )

    simulation_id: str = Field(
        ...,
        pattern=r"^sim_[a-f0-9]{8}$",
        description="Parent simulation ID",
    )

    nodes: list[Variable] = Field(
        default_factory=list, description="Variables in the DAG"
    )

    edges: list[Edge] = Field(
        default_factory=list, description="Causal relationships"
    )

    assumptions: list[Assumption] = Field(
        default_factory=list, description="Declared modeling assumptions"
    )

    risks: list[Risk] = Field(
        default_factory=list, description="Identified uncertainties"
    )

    is_validated: bool = Field(
        default=False, description="Whether DAG passed validation"
    )

    validation_errors: Optional[list[ValidationError]] = Field(
        default=None, description="Cycle detection, orphan nodes, etc."
    )

    version: int = Field(default=1, description="Version number for DAG edits")

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp (UTC)",
    )

    class Config:
        """Pydantic configuration."""

        use_enum_values = True
