"""
AuditTrailRepository for synth-lab.

Data access layer for audit trail storage and retrieval.

References:
    - Spec: specs/035-causal-simulation/spec.md
    - Data model: specs/035-causal-simulation/data-model.md
    - ORM models: synth_lab.models.orm.simulation
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from synth_lab.domain.entities.audit_trail import (
    AuditTrail,
    DAGSnapshot,
    EvidenceSnapshot,
    HypothesisSnapshotItem,
    InsightSnapshot,
)
from synth_lab.models.orm.simulation import AuditTrail as AuditTrailORM
from synth_lab.repositories.base import BaseRepository


class AuditTrailRepository(BaseRepository):
    """
    Repository for audit trail data access.

    Provides CRUD operations for simulation audit trails.

    Usage:
        repo = AuditTrailRepository(session=db_session)
        audit = repo.create(audit_trail)
    """

    def __init__(self, session: Session | None = None):
        """
        Initialize repository.

        Args:
            session: SQLAlchemy session. If not provided, uses global session factory.
        """
        super().__init__(session=session)

    def create(self, audit_trail: AuditTrail) -> AuditTrail:
        """
        Create a new audit trail.

        Args:
            audit_trail: AuditTrail entity to create

        Returns:
            Created audit trail with persisted data

        Example:
            >>> audit = AuditTrail(
            ...     simulation_id="sim_12345678",
            ...     question="What adoption rate?",
            ...     dag_snapshot=dag_snapshot,
            ...     random_seed=42,
            ... )
            >>> created = repo.create(audit)
        """
        # Serialize snapshots to JSONB
        dag_dict = audit_trail.dag_snapshot.model_dump()
        hypotheses_dict = {
            "hypotheses": [h.model_dump() for h in audit_trail.hypotheses_snapshot]
        }
        evidence_dict = audit_trail.evidence_snapshot.model_dump()
        insights_dict = {
            "insights": [i.model_dump() for i in audit_trail.insights_snapshot]
        }

        orm_audit = AuditTrailORM(
            id=audit_trail.id,
            simulation_id=audit_trail.simulation_id,
            question=audit_trail.question,
            dag_snapshot=dag_dict,
            hypotheses_snapshot=hypotheses_dict,
            random_seed=audit_trail.random_seed,
            evidence_snapshot=evidence_dict,
            insights_snapshot=insights_dict,
            created_at=audit_trail.created_at,
        )

        self.session.add(orm_audit)
        self.session.commit()
        self.session.refresh(orm_audit)

        return self._orm_to_entity(orm_audit)

    def get(self, audit_id: str) -> AuditTrail | None:
        """
        Get audit trail by ID.

        Args:
            audit_id: Audit trail ID

        Returns:
            AuditTrail entity or None if not found

        Example:
            >>> audit = repo.get("audit_12345678")
        """
        stmt = select(AuditTrailORM).where(AuditTrailORM.id == audit_id)
        orm_audit = self.session.execute(stmt).scalar_one_or_none()

        if orm_audit is None:
            return None

        return self._orm_to_entity(orm_audit)

    def get_by_simulation_id(self, simulation_id: str) -> AuditTrail | None:
        """
        Get latest audit trail for a simulation.

        Args:
            simulation_id: Simulation ID

        Returns:
            Latest AuditTrail entity or None

        Example:
            >>> audit = repo.get_by_simulation_id("sim_12345678")
        """
        stmt = (
            select(AuditTrailORM)
            .where(AuditTrailORM.simulation_id == simulation_id)
            .order_by(AuditTrailORM.created_at.desc())
            .limit(1)
        )
        orm_audit = self.session.execute(stmt).scalar_one_or_none()

        if orm_audit is None:
            return None

        return self._orm_to_entity(orm_audit)

    def list_by_simulation_id(self, simulation_id: str) -> list[AuditTrail]:
        """
        List all audit trails for a simulation.

        Args:
            simulation_id: Simulation ID

        Returns:
            List of AuditTrail entities

        Example:
            >>> audits = repo.list_by_simulation_id("sim_12345678")
        """
        stmt = (
            select(AuditTrailORM)
            .where(AuditTrailORM.simulation_id == simulation_id)
            .order_by(AuditTrailORM.created_at.desc())
        )
        orm_audits = self.session.execute(stmt).scalars().all()

        return [self._orm_to_entity(orm) for orm in orm_audits]

    def delete(self, audit_id: str) -> bool:
        """
        Delete an audit trail.

        Args:
            audit_id: Audit trail ID

        Returns:
            True if deleted, False if not found
        """
        stmt = select(AuditTrailORM).where(AuditTrailORM.id == audit_id)
        orm_audit = self.session.execute(stmt).scalar_one_or_none()

        if orm_audit is None:
            return False

        self.session.delete(orm_audit)
        self.session.commit()

        return True

    def _orm_to_entity(self, orm: AuditTrailORM) -> AuditTrail:
        """
        Convert ORM model to domain entity.

        Args:
            orm: SQLAlchemy ORM model

        Returns:
            AuditTrail domain entity
        """
        # Deserialize DAG snapshot
        dag_snapshot = DAGSnapshot(
            version=orm.dag_snapshot.get("version", 1),
            nodes=orm.dag_snapshot.get("nodes", []),
            edges=orm.dag_snapshot.get("edges", []),
        )

        # Deserialize hypotheses snapshot
        hyp_list = orm.hypotheses_snapshot.get("hypotheses", [])
        hypotheses_snapshot = [
            HypothesisSnapshotItem(
                variable_id=h.get("variable_id", ""),
                variable_name=h.get("variable_name", ""),
                distribution_type=h.get("distribution_type", "normal"),
                parameters=h.get("parameters", {}),
            )
            for h in hyp_list
        ]

        # Deserialize evidence snapshot
        evidence_snapshot = EvidenceSnapshot(
            outcome_distributions=orm.evidence_snapshot.get("outcome_distributions", {}),
            variance_explained=orm.evidence_snapshot.get("variance_explained", []),
            n_failure_modes=orm.evidence_snapshot.get("n_failure_modes", 0),
            n_clusters=orm.evidence_snapshot.get("n_clusters", 0),
        )

        # Deserialize insights snapshot
        ins_list = orm.insights_snapshot.get("insights", [])
        insights_snapshot = [
            InsightSnapshot(
                id=i.get("id", ""),
                insight_type=i.get("insight_type", "recommendation"),
                title=i.get("title", ""),
                description=i.get("description", ""),
            )
            for i in ins_list
        ]

        return AuditTrail(
            id=orm.id,
            simulation_id=orm.simulation_id,
            question=orm.question,
            dag_snapshot=dag_snapshot,
            hypotheses_snapshot=hypotheses_snapshot,
            random_seed=orm.random_seed,
            evidence_snapshot=evidence_snapshot,
            insights_snapshot=insights_snapshot,
            created_at=orm.created_at,
        )
