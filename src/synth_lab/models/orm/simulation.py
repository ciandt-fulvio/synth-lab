"""
SQLAlchemy ORM models for causal simulation tables.

Maps to the simulation-related tables created in migration 20260126_0001.

References:
    - Migration: src/synth_lab/alembic/versions/20260126_0001_add_causal_simulation_tables.py
    - Data model: specs/035-causal-simulation/data-model.md
    - SQLAlchemy 2.0: https://docs.sqlalchemy.org/en/20/orm/
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Float, ForeignKey, Index, Integer, JSON, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from synth_lab.models.orm.base import Base, MutableJSON, MutableJSONList

if TYPE_CHECKING:
    pass


class Simulation(Base):
    """
    Simulation ORM model.

    Root aggregate for a complete causal simulation session.

    Attributes:
        id: Unique identifier (sim_[a-f0-9]{8})
        question: Original natural language question
        problem_decomposition: Structured problem (JSONB)
        status: Current simulation status
        random_seed: Master random seed for reproducibility
        n_worlds: Number of synthetic worlds to simulate
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "simulations"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    problem_decomposition: Mapped[dict | None] = mapped_column(
        MutableJSON, nullable=True
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    random_seed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    n_worlds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()"
    )

    # Relationships
    causal_dags: Mapped[list["CausalDAG"]] = relationship(
        "CausalDAG", back_populates="simulation", cascade="all, delete-orphan"
    )
    hypotheses: Mapped[list["Hypothesis"]] = relationship(
        "Hypothesis", back_populates="simulation", cascade="all, delete-orphan"
    )
    hypothesis_versions: Mapped[list["HypothesisVersion"]] = relationship(
        "HypothesisVersion", back_populates="simulation", cascade="all, delete-orphan"
    )
    simulated_worlds: Mapped[list["SimulatedWorld"]] = relationship(
        "SimulatedWorld", back_populates="simulation", cascade="all, delete-orphan"
    )
    insights: Mapped[list["Insight"]] = relationship(
        "Insight", back_populates="simulation", cascade="all, delete-orphan"
    )
    audit_trails: Mapped[list["AuditTrail"]] = relationship(
        "AuditTrail", back_populates="simulation", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_simulations_status", "status"),
        Index("ix_simulations_created_at", "created_at"),
    )


class CausalDAG(Base):
    """
    CausalDAG ORM model.

    Directed acyclic graph of causal relationships.

    Attributes:
        id: Unique identifier (dag_[a-f0-9]{8})
        simulation_id: Parent simulation ID
        version: Version number for DAG edits
        nodes: Array of Variable objects (JSONB)
        edges: Array of causal relationships (JSONB)
        assumptions: Declared modeling assumptions (JSONB)
        risks: Identified uncertainties (JSONB)
        created_at: Creation timestamp
    """

    __tablename__ = "causal_dags"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    simulation_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("simulations.id", ondelete="CASCADE"),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="1"
    )
    nodes: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    edges: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    assumptions: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    risks: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()"
    )

    # Relationships
    simulation: Mapped["Simulation"] = relationship(
        "Simulation", back_populates="causal_dags"
    )
    variables: Mapped[list["Variable"]] = relationship(
        "Variable", back_populates="dag", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_causal_dags_simulation_id", "simulation_id"),)


class Variable(Base):
    """
    Variable ORM model.

    Individual variable in a causal DAG (denormalized for querying).

    Attributes:
        id: Unique identifier
        dag_id: Parent DAG ID
        name: Variable name
        type: Variable type (observable, latent, etc.)
        scope: Variable scope (world, user)
        controllable: Whether variable is controllable
    """

    __tablename__ = "variables"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    dag_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("causal_dags.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    scope: Mapped[str] = mapped_column(String(50), nullable=False)
    controllable: Mapped[bool] = mapped_column(
        nullable=False, server_default="false"
    )

    # Relationships
    dag: Mapped["CausalDAG"] = relationship(
        "CausalDAG", back_populates="variables"
    )
    hypotheses: Mapped[list["Hypothesis"]] = relationship(
        "Hypothesis", back_populates="variable", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_variables_dag_id", "dag_id"),)


class Hypothesis(Base):
    """
    Hypothesis ORM model.

    Quantified distribution for a variable.

    Attributes:
        id: Unique identifier (hyp_[a-f0-9]{8})
        simulation_id: Parent simulation ID
        variable_id: Variable ID
        distribution_type: Type of distribution
        distribution_params: Distribution parameters (JSONB)
        range_min: Minimum value
        range_max: Maximum value
        correlations: Correlations with other variables (JSONB)
        created_at: Creation timestamp
    """

    __tablename__ = "hypotheses"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    simulation_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("simulations.id", ondelete="CASCADE"),
        nullable=False,
    )
    variable_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("variables.id", ondelete="CASCADE"),
        nullable=False,
    )
    distribution_type: Mapped[str] = mapped_column(String(50), nullable=False)
    distribution_params: Mapped[dict] = mapped_column(
        MutableJSON, nullable=False
    )
    range_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    range_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    correlations: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()"
    )

    # Relationships
    simulation: Mapped["Simulation"] = relationship(
        "Simulation", back_populates="hypotheses"
    )
    variable: Mapped["Variable"] = relationship(
        "Variable", back_populates="hypotheses"
    )

    __table_args__ = (Index("ix_hypotheses_simulation_id", "simulation_id"),)


class HypothesisVersion(Base):
    """
    HypothesisVersion ORM model.

    Versioned snapshot of complete hypothesis set.

    Attributes:
        id: Unique identifier (hv_[a-f0-9]{8})
        simulation_id: Parent simulation ID
        version_name: User-provided name
        description: User-provided description
        dag_snapshot: DAG snapshot (JSONB)
        hypotheses_snapshot: Hypotheses snapshot (JSONB)
        created_at: Creation timestamp
    """

    __tablename__ = "hypothesis_versions"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    simulation_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("simulations.id", ondelete="CASCADE"),
        nullable=False,
    )
    version_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    dag_snapshot: Mapped[dict] = mapped_column(MutableJSON, nullable=False)
    hypotheses_snapshot: Mapped[dict] = mapped_column(
        MutableJSON, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()"
    )

    # Relationships
    simulation: Mapped["Simulation"] = relationship(
        "Simulation", back_populates="hypothesis_versions"
    )

    __table_args__ = (
        Index("ix_hypothesis_versions_simulation_id", "simulation_id"),
    )


class SimulatedWorld(Base):
    """
    SimulatedWorld ORM model.

    Individual world simulation result.

    Attributes:
        id: Unique identifier (world_[a-f0-9]{8})
        simulation_id: Parent simulation ID
        world_index: Sequential world number
        world_params: World-level variable values (JSONB)
        outcome_value: Outcome value
        created_at: Creation timestamp
    """

    __tablename__ = "simulated_worlds"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    simulation_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("simulations.id", ondelete="CASCADE"),
        nullable=False,
    )
    world_index: Mapped[int] = mapped_column(Integer, nullable=False)
    world_params: Mapped[dict] = mapped_column(MutableJSON, nullable=False)
    outcome_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()"
    )

    # Relationships
    simulation: Mapped["Simulation"] = relationship(
        "Simulation", back_populates="simulated_worlds"
    )

    __table_args__ = (
        Index("ix_simulated_worlds_simulation_id", "simulation_id"),
    )


class Insight(Base):
    """
    Insight ORM model.

    Generated insight with traceability.

    Attributes:
        id: Unique identifier (ins_[a-f0-9]{8})
        simulation_id: Parent simulation ID
        insight_type: Type of insight
        message: Insight message
        evidence: Evidence links (JSONB)
        recommendations: Recommendations (JSONB)
        created_at: Creation timestamp
    """

    __tablename__ = "insights"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    simulation_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("simulations.id", ondelete="CASCADE"),
        nullable=False,
    )
    insight_type: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[dict] = mapped_column(MutableJSON, nullable=False)
    recommendations: Mapped[list | None] = mapped_column(
        JSON, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()"
    )

    # Relationships
    simulation: Mapped["Simulation"] = relationship(
        "Simulation", back_populates="insights"
    )

    __table_args__ = (Index("ix_insights_simulation_id", "simulation_id"),)


class AuditTrail(Base):
    """
    AuditTrail ORM model.

    Complete reproducibility audit trail.

    Attributes:
        id: Unique identifier (audit_[a-f0-9]{8})
        simulation_id: Parent simulation ID
        question: Original question
        dag_snapshot: DAG snapshot (JSONB)
        hypotheses_snapshot: Hypotheses snapshot (JSONB)
        random_seed: Random seed
        evidence_snapshot: Evidence snapshot (JSONB)
        insights_snapshot: Insights snapshot (JSONB)
        created_at: Creation timestamp
    """

    __tablename__ = "audit_trails"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    simulation_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("simulations.id", ondelete="CASCADE"),
        nullable=False,
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    dag_snapshot: Mapped[dict] = mapped_column(MutableJSON, nullable=False)
    hypotheses_snapshot: Mapped[dict] = mapped_column(
        MutableJSON, nullable=False
    )
    random_seed: Mapped[int] = mapped_column(Integer, nullable=False)
    evidence_snapshot: Mapped[dict] = mapped_column(MutableJSON, nullable=False)
    insights_snapshot: Mapped[dict] = mapped_column(MutableJSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()"
    )

    # Relationships
    simulation: Mapped["Simulation"] = relationship(
        "Simulation", back_populates="audit_trails"
    )

    __table_args__ = (Index("ix_audit_trails_simulation_id", "simulation_id"),)
