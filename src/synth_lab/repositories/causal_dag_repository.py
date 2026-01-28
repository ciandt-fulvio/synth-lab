"""
CausalDAGRepository for synth-lab.

Data access layer for causal DAG data with JSONB storage.

References:
    - Spec: specs/035-causal-simulation/spec.md
    - Data model: specs/035-causal-simulation/data-model.md
    - ORM models: synth_lab.models.orm.simulation
"""

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from synth_lab.domain.entities.causal_dag import (
    Assumption,
    CausalDAG,
    Edge,
    Risk,
    Variable,
    generate_dag_id,
)
from synth_lab.models.orm.simulation import CausalDAG as CausalDAGORM
from synth_lab.models.orm.simulation import Variable as VariableORM
from synth_lab.repositories.base import BaseRepository


class CausalDAGRepository(BaseRepository):
    """
    Repository for causal DAG data access.

    Uses SQLAlchemy ORM with JSONB for flexible DAG storage.

    Usage:
        repo = CausalDAGRepository(session=db_session)
        dag = repo.create(dag_entity)
    """

    def __init__(self, session: Session | None = None):
        """
        Initialize repository.

        Args:
            session: SQLAlchemy session. If not provided, uses global session factory.
        """
        super().__init__(session=session)

    def create(self, dag: CausalDAG) -> CausalDAG:
        """
        Create a new causal DAG.

        Args:
            dag: CausalDAG entity to create

        Returns:
            Created DAG with persisted data

        Example:
            >>> dag = CausalDAG(simulation_id="sim_12345678", nodes=[...])
            >>> created = repo.create(dag)
        """
        # Serialize nodes (Variable entities) to JSONB
        nodes_dict = [node.model_dump() for node in dag.nodes]

        # Serialize edges to JSONB
        edges_dict = [edge.model_dump() for edge in dag.edges]

        # Serialize assumptions to JSONB
        assumptions_dict = (
            [assump.model_dump() for assump in dag.assumptions]
            if dag.assumptions
            else None
        )

        # Serialize risks to JSONB
        risks_dict = (
            [risk.model_dump() for risk in dag.risks] if dag.risks else None
        )

        # Create ORM instance
        orm_dag = CausalDAGORM(
            id=dag.id,
            simulation_id=dag.simulation_id,
            version=dag.version,
            nodes=nodes_dict,
            edges=edges_dict,
            assumptions=assumptions_dict,
            risks=risks_dict,
            created_at=dag.created_at,
        )

        # Persist DAG to database
        self.session.add(orm_dag)
        self.session.flush()  # Flush to get the DAG ID for FK reference

        # Create Variable ORM records for each node
        # This is required because hypotheses table has FK to variables table
        for node in dag.nodes:
            # Map controllability enum to boolean (for legacy 'controllable' field)
            # controllable = True if controllability is not 'none'
            controllable = (
                node.controllability != "none"
                if isinstance(node.controllability, str)
                else node.controllability.value != "none"
            )

            # Extract enum values as strings
            def _extract_value(v):
                return v if isinstance(v, str) else (v.value if hasattr(v, "value") else str(v))

            orm_variable = VariableORM(
                id=node.id,
                dag_id=orm_dag.id,
                name=node.name,
                label=node.label if hasattr(node, "label") else node.name,
                description=node.description,
                type=_extract_value(node.type),
                scope=_extract_value(node.scope),
                controllability=_extract_value(node.controllability),
                controllable=controllable,  # Legacy boolean field
                is_intervention=node.is_intervention,
                is_outcome=node.is_outcome,
                is_critical_uncertainty=node.is_critical_uncertainty,
                position_x=node.position_x,
                position_y=node.position_y,
                unit=node.unit if hasattr(node, "unit") else None,
            )
            self.session.add(orm_variable)

        self.session.commit()
        self.session.refresh(orm_dag)

        # Convert back to entity
        return self._orm_to_entity(orm_dag)

    def get_by_simulation_id(self, simulation_id: str) -> CausalDAG | None:
        """
        Get latest DAG for a simulation.

        Args:
            simulation_id: Simulation ID

        Returns:
            CausalDAG entity or None if not found

        Example:
            >>> dag = repo.get_by_simulation_id("sim_12345678")
        """
        stmt = (
            select(CausalDAGORM)
            .where(CausalDAGORM.simulation_id == simulation_id)
            .order_by(CausalDAGORM.version.desc(), CausalDAGORM.created_at.desc())
            .limit(1)
        )
        orm_dag = self.session.execute(stmt).scalar_one_or_none()

        if orm_dag is None:
            return None

        return self._orm_to_entity(orm_dag)

    def get(self, dag_id: str) -> CausalDAG | None:
        """
        Get DAG by ID.

        Args:
            dag_id: DAG ID

        Returns:
            CausalDAG entity or None if not found
        """
        stmt = select(CausalDAGORM).where(CausalDAGORM.id == dag_id)
        orm_dag = self.session.execute(stmt).scalar_one_or_none()

        if orm_dag is None:
            return None

        return self._orm_to_entity(orm_dag)

    def _orm_to_entity(self, orm: CausalDAGORM) -> CausalDAG:
        """
        Convert ORM model to domain entity.

        Args:
            orm: SQLAlchemy ORM model

        Returns:
            CausalDAG domain entity
        """
        # Deserialize nodes from JSONB
        nodes = [Variable(**node_data) for node_data in orm.nodes]

        # Deserialize edges from JSONB
        edges = [Edge(**edge_data) for edge_data in orm.edges]

        # Deserialize assumptions from JSONB
        assumptions = (
            [Assumption(**assump_data) for assump_data in orm.assumptions]
            if orm.assumptions
            else []
        )

        # Deserialize risks from JSONB
        risks = (
            [Risk(**risk_data) for risk_data in orm.risks]
            if orm.risks
            else []
        )

        return CausalDAG(
            id=orm.id,
            simulation_id=orm.simulation_id,
            version=orm.version,
            nodes=nodes,
            edges=edges,
            assumptions=assumptions,
            risks=risks,
            created_at=orm.created_at,
        )

    def update(self, dag: CausalDAG) -> CausalDAG:
        """
        Update an existing DAG.

        Creates a new version record for version history.

        Args:
            dag: Updated CausalDAG entity

        Returns:
            Updated DAG with new version

        Example:
            >>> dag.nodes.append(new_node)
            >>> updated = repo.update(dag)
        """
        from datetime import datetime

        # Serialize to JSONB
        nodes_dict = [node.model_dump() for node in dag.nodes]
        edges_dict = [edge.model_dump() for edge in dag.edges]
        assumptions_dict = (
            [assump.model_dump() for assump in dag.assumptions]
            if dag.assumptions
            else None
        )
        risks_dict = (
            [risk.model_dump() for risk in dag.risks] if dag.risks else None
        )

        # Create new version record with new ID
        new_dag_id = generate_dag_id()
        orm_dag = CausalDAGORM(
            id=new_dag_id,
            simulation_id=dag.simulation_id,
            version=dag.version,
            nodes=nodes_dict,
            edges=edges_dict,
            assumptions=assumptions_dict,
            risks=risks_dict,
            created_at=datetime.utcnow(),
        )

        self.session.add(orm_dag)
        self.session.flush()  # Flush to get the DAG ID for FK reference

        # Create Variable ORM records for each node in the new version
        # Use ON CONFLICT DO NOTHING to handle variables that already exist
        # (from a previous DAG version)
        for node in dag.nodes:
            # Map controllability enum to boolean
            controllable = (
                node.controllability != "none"
                if isinstance(node.controllability, str)
                else node.controllability.value != "none"
            )

            # Use PostgreSQL INSERT ON CONFLICT DO NOTHING
            stmt = pg_insert(VariableORM).values(
                id=node.id,
                dag_id=orm_dag.id,
                name=node.name,
                type=node.type if isinstance(node.type, str) else node.type.value,
                scope=node.scope if isinstance(node.scope, str) else node.scope.value,
                controllable=controllable,
            ).on_conflict_do_nothing(index_elements=["id"])
            self.session.execute(stmt)

        self.session.commit()
        self.session.refresh(orm_dag)

        return self._orm_to_entity(orm_dag)

    def get_versions(self, simulation_id: str) -> list[dict]:
        """
        Get all DAG versions for a simulation.

        Args:
            simulation_id: Simulation ID

        Returns:
            List of version summaries with metadata

        Example:
            >>> versions = repo.get_versions("sim_12345678")
        """
        stmt = (
            select(CausalDAGORM)
            .where(CausalDAGORM.simulation_id == simulation_id)
            .order_by(CausalDAGORM.version.desc())
        )
        orm_dags = self.session.execute(stmt).scalars().all()

        return [
            {
                "version": orm.version,
                "created_at": orm.created_at,
                "node_count": len(orm.nodes) if orm.nodes else 0,
                "edge_count": len(orm.edges) if orm.edges else 0,
                "description": None,  # Could be added to schema
            }
            for orm in orm_dags
        ]

    def get_version(self, simulation_id: str, version: int) -> CausalDAG | None:
        """
        Get a specific DAG version.

        Args:
            simulation_id: Simulation ID
            version: Version number

        Returns:
            CausalDAG entity or None if not found

        Example:
            >>> dag_v1 = repo.get_version("sim_12345678", 1)
        """
        stmt = (
            select(CausalDAGORM)
            .where(CausalDAGORM.simulation_id == simulation_id)
            .where(CausalDAGORM.version == version)
        )
        orm_dag = self.session.execute(stmt).scalar_one_or_none()

        if orm_dag is None:
            return None

        return self._orm_to_entity(orm_dag)

    def update_in_place(self, dag: CausalDAG) -> CausalDAG:
        """
        Update DAG in-place without creating a new version.

        Use this for UI state updates like node positions that shouldn't
        increment the version number.

        Args:
            dag: CausalDAG entity to update

        Returns:
            Updated DAG entity

        Example:
            >>> dag.nodes[0].position_x = 100
            >>> updated = repo.update_in_place(dag)
        """
        # Get existing ORM instance
        stmt = select(CausalDAGORM).where(CausalDAGORM.id == dag.id)
        orm_dag = self.session.execute(stmt).scalar_one_or_none()

        if orm_dag is None:
            raise ValueError(f"DAG {dag.id} not found")

        # Update JSONB fields in-place
        orm_dag.nodes = [node.model_dump() for node in dag.nodes]
        orm_dag.edges = [edge.model_dump() for edge in dag.edges]
        orm_dag.assumptions = (
            [assump.model_dump() for assump in dag.assumptions]
            if dag.assumptions
            else None
        )
        orm_dag.risks = (
            [risk.model_dump() for risk in dag.risks] if dag.risks else None
        )

        self.session.commit()
        self.session.refresh(orm_dag)

        return self._orm_to_entity(orm_dag)
