"""
SimulationInsightRepository for synth-lab.

Data access layer for causal simulation insights with full traceability.

References:
    - Spec: specs/035-causal-simulation/spec.md
    - Data model: specs/035-causal-simulation/data-model.md
    - ORM models: synth_lab.models.orm.simulation
"""

import secrets

from sqlalchemy import select
from sqlalchemy.orm import Session

from synth_lab.models.orm.simulation import Insight as InsightORM
from synth_lab.repositories.base import BaseRepository


def generate_insight_id() -> str:
    """Generate a unique insight ID with ins_ prefix."""
    return f"ins_{secrets.token_hex(4)}"


class SimulationInsightRepository(BaseRepository):
    """
    Repository for simulation insight data access.

    Uses SQLAlchemy ORM with JSONB for flexible evidence and recommendation storage.

    Usage:
        repo = SimulationInsightRepository(session=db_session)
        insights = repo.create_batch(insight_dicts)
    """

    def __init__(self, session: Session | None = None):
        """
        Initialize repository.

        Args:
            session: SQLAlchemy session. If not provided, uses global session factory.
        """
        super().__init__(session=session)

    def create_batch(self, insights: list[dict]) -> list[dict]:
        """
        Create multiple insights in a batch.

        Args:
            insights: List of insight dictionaries from InsightGeneratorService

        Returns:
            List of created insights with IDs

        Example:
            >>> insights = [{"simulation_id": "sim_123", ...}]
            >>> created = repo.create_batch(insights)
        """
        orm_insights = []

        for insight in insights:
            orm_insight = InsightORM(
                id=generate_insight_id(),
                simulation_id=insight["simulation_id"],
                insight_type=insight["insight_type"],
                message=f"{insight['title']}\n\n{insight['description']}",
                evidence=insight.get("evidence_references", {}),
                recommendations=insight.get("recommended_actions", []),
            )
            orm_insights.append(orm_insight)

        # Batch insert
        self.session.add_all(orm_insights)
        self.session.commit()

        # Refresh all and convert back
        results = []
        for orm_insight in orm_insights:
            self.session.refresh(orm_insight)
            results.append(self._orm_to_dict(orm_insight))

        return results

    def get_by_simulation_id(self, simulation_id: str) -> list[dict]:
        """
        Get all insights for a simulation.

        Args:
            simulation_id: Simulation ID

        Returns:
            List of insight dictionaries

        Example:
            >>> insights = repo.get_by_simulation_id("sim_12345678")
        """
        stmt = (
            select(InsightORM)
            .where(InsightORM.simulation_id == simulation_id)
            .order_by(InsightORM.created_at)
        )
        orm_insights = self.session.execute(stmt).scalars().all()

        return [self._orm_to_dict(orm_insight) for orm_insight in orm_insights]

    def get(self, insight_id: str) -> dict | None:
        """
        Get insight by ID.

        Args:
            insight_id: Insight ID

        Returns:
            Insight dictionary or None if not found

        Example:
            >>> insight = repo.get("ins_12345678")
        """
        stmt = select(InsightORM).where(InsightORM.id == insight_id)
        orm_insight = self.session.execute(stmt).scalar_one_or_none()

        if orm_insight is None:
            return None

        return self._orm_to_dict(orm_insight)

    def _orm_to_dict(self, orm: InsightORM) -> dict:
        """
        Convert ORM model to dictionary.

        Args:
            orm: SQLAlchemy ORM model

        Returns:
            Insight dictionary
        """
        # Parse message into title and description
        parts = orm.message.split("\n\n", 1)
        title = parts[0] if len(parts) > 0 else ""
        description = parts[1] if len(parts) > 1 else ""

        return {
            "id": orm.id,
            "simulation_id": orm.simulation_id,
            "insight_type": orm.insight_type,
            "title": title,
            "description": description,
            "evidence_references": orm.evidence,
            "recommended_actions": orm.recommendations,
            "created_at": orm.created_at.isoformat(),
        }
