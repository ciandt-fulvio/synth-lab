"""
HypothesisRepository for synth-lab.

Data access layer for hypothesis data with versioning support.

References:
    - Spec: specs/035-causal-simulation/spec.md
    - Data model: specs/035-causal-simulation/data-model.md
    - ORM models: synth_lab.models.orm.simulation
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from synth_lab.domain.entities.hypothesis import (
    BernoulliParams,
    BetaParams,
    Correlation,
    DistributionType,
    Hypothesis,
    HypothesisSnapshot,
    HypothesisVersion,
    LogNormalParams,
    NormalParams,
    UniformParams,
)
from synth_lab.models.orm.simulation import (
    Hypothesis as HypothesisORM,
)
from synth_lab.models.orm.simulation import (
    HypothesisVersion as HypothesisVersionORM,
)
from synth_lab.repositories.base import BaseRepository


class HypothesisRepository(BaseRepository):
    """
    Repository for hypothesis data access with versioning.

    Uses SQLAlchemy ORM with JSONB for flexible parameter storage.

    Usage:
        repo = HypothesisRepository(session=db_session)
        hypotheses = repo.create_batch(hypothesis_list)
    """

    def __init__(self, session: Session | None = None):
        """
        Initialize repository.

        Args:
            session: SQLAlchemy session. If not provided, uses global session factory.
        """
        super().__init__(session=session)

    def create_batch(self, hypotheses: list[Hypothesis]) -> list[Hypothesis]:
        """
        Create multiple hypotheses in a batch.

        Args:
            hypotheses: List of Hypothesis entities

        Returns:
            List of created hypotheses

        Example:
            >>> hyps = [Hypothesis(...), Hypothesis(...)]
            >>> created = repo.create_batch(hyps)
        """
        orm_hypotheses = []

        for hyp in hypotheses:
            # Serialize parameters to JSONB
            params_dict = hyp.parameters.model_dump()

            # Serialize correlations to JSONB
            correlations_dict = (
                [corr.model_dump() for corr in hyp.correlations] if hyp.correlations else None
            )

            # Serialize scenario options to JSONB
            scenario_options_dict = None
            if hyp.scenario_options:
                scenario_options_dict = [
                    {
                        "value": opt.value,
                        "label": opt.label,
                        "min_value": opt.distribution_params.min_value,
                        "mode": opt.distribution_params.mode,
                        "max_value": opt.distribution_params.max_value,
                    }
                    for opt in hyp.scenario_options
                ]

            orm_hyp = HypothesisORM(
                id=hyp.id,
                simulation_id=hyp.simulation_id,
                variable_id=hyp.variable_id,
                variable_name=hyp.variable_name,
                distribution_type=hyp.distribution_type.value
                if isinstance(hyp.distribution_type, DistributionType)
                else hyp.distribution_type,
                distribution_params=params_dict,
                correlations=correlations_dict,
                scenario_options=scenario_options_dict,
                selected_scenario=hyp.selected_scenario,
                created_at=hyp.created_at,
            )
            orm_hypotheses.append(orm_hyp)

        # Batch insert
        self.session.add_all(orm_hypotheses)
        self.session.commit()

        # Refresh all
        for orm_hyp in orm_hypotheses:
            self.session.refresh(orm_hyp)

        # Convert back to entities
        return [self._orm_to_entity(orm_hyp) for orm_hyp in orm_hypotheses]

    def get_by_simulation_id(self, simulation_id: str) -> list[Hypothesis]:
        """
        Get all hypotheses for a simulation.

        Args:
            simulation_id: Simulation ID

        Returns:
            List of Hypothesis entities

        Example:
            >>> hyps = repo.get_by_simulation_id("sim_12345678")
        """
        stmt = (
            select(HypothesisORM)
            .where(HypothesisORM.simulation_id == simulation_id)
            .order_by(HypothesisORM.created_at)
        )
        orm_hypotheses = self.session.execute(stmt).scalars().all()

        return [self._orm_to_entity(orm_hyp) for orm_hyp in orm_hypotheses]

    def get_by_variable(self, simulation_id: str, variable_name: str) -> Hypothesis | None:
        """
        Get hypothesis for a specific variable.

        Args:
            simulation_id: Simulation ID
            variable_name: Variable name

        Returns:
            Hypothesis entity or None
        """
        stmt = (
            select(HypothesisORM)
            .where(HypothesisORM.simulation_id == simulation_id)
            .where(HypothesisORM.variable_id == variable_name)
        )
        orm_hyp = self.session.execute(stmt).scalar_one_or_none()

        if orm_hyp is None:
            return None

        return self._orm_to_entity(orm_hyp)

    def update(self, hypothesis: Hypothesis) -> Hypothesis:
        """
        Update a single hypothesis.

        Args:
            hypothesis: Hypothesis entity to update

        Returns:
            Updated hypothesis
        """
        stmt = select(HypothesisORM).where(HypothesisORM.id == hypothesis.id)
        orm_hyp = self.session.execute(stmt).scalar_one_or_none()

        if orm_hyp is None:
            raise ValueError(f"Hypothesis {hypothesis.id} not found")

        # Update fields
        orm_hyp.variable_name = hypothesis.variable_name
        orm_hyp.distribution_params = hypothesis.parameters.model_dump()
        orm_hyp.correlations = (
            [corr.model_dump() for corr in hypothesis.correlations]
            if hypothesis.correlations
            else None
        )

        # Update scenario options
        if hypothesis.scenario_options:
            orm_hyp.scenario_options = [
                {
                    "value": opt.value,
                    "label": opt.label,
                    "min_value": opt.distribution_params.min_value,
                    "mode": opt.distribution_params.mode,
                    "max_value": opt.distribution_params.max_value,
                }
                for opt in hypothesis.scenario_options
            ]
        else:
            orm_hyp.scenario_options = None

        orm_hyp.selected_scenario = hypothesis.selected_scenario

        self.session.commit()
        self.session.refresh(orm_hyp)

        return self._orm_to_entity(orm_hyp)

    def update_batch(self, hypotheses: list[Hypothesis]) -> list[Hypothesis]:
        """
        Update multiple hypotheses.

        Args:
            hypotheses: List of hypotheses to update

        Returns:
            Updated hypotheses
        """
        updated = []
        for hyp in hypotheses:
            updated.append(self.update(hyp))
        return updated

    def delete_by_variable_id(self, simulation_id: str, variable_id: str) -> bool:
        """
        Delete hypothesis for a specific variable.

        Args:
            simulation_id: Simulation ID
            variable_id: Variable ID to delete hypothesis for

        Returns:
            True if deleted, False if not found
        """
        stmt = (
            select(HypothesisORM)
            .where(HypothesisORM.simulation_id == simulation_id)
            .where(HypothesisORM.variable_id == variable_id)
        )
        orm_hyp = self.session.execute(stmt).scalar_one_or_none()

        if orm_hyp is None:
            return False

        self.session.delete(orm_hyp)
        self.session.commit()
        return True

    def delete_by_variable_ids(self, simulation_id: str, variable_ids: list[str]) -> int:
        """
        Delete hypotheses for multiple variables.

        Args:
            simulation_id: Simulation ID
            variable_ids: List of variable IDs to delete hypotheses for

        Returns:
            Number of deleted hypotheses
        """
        from sqlalchemy import delete

        stmt = (
            delete(HypothesisORM)
            .where(HypothesisORM.simulation_id == simulation_id)
            .where(HypothesisORM.variable_id.in_(variable_ids))
        )
        result = self.session.execute(stmt)
        self.session.commit()
        return result.rowcount or 0

    def get_versions(self, simulation_id: str) -> list[dict]:
        """
        Get version history for simulation hypotheses.

        Args:
            simulation_id: Simulation ID

        Returns:
            List of version summaries
        """
        stmt = (
            select(HypothesisVersionORM)
            .where(HypothesisVersionORM.simulation_id == simulation_id)
            .order_by(HypothesisVersionORM.created_at.desc())
        )
        versions = self.session.execute(stmt).scalars().all()

        return [
            {
                "version": idx + 1,
                "created_at": v.created_at,
                "name": v.version_name,
                "description": v.description,
            }
            for idx, v in enumerate(reversed(list(versions)))
        ]

    def get_at_version(self, simulation_id: str, version: int) -> list[Hypothesis]:
        """
        Get hypotheses at a specific version.

        Args:
            simulation_id: Simulation ID
            version: Version number

        Returns:
            List of hypotheses at that version
        """
        # For now, return current hypotheses
        # In a full implementation, this would restore from snapshot
        return self.get_by_simulation_id(simulation_id)

    def save_version(
        self,
        simulation_id: str,
        version: int,
        name: str,
        description: str | None = None,
    ) -> dict:
        """
        Save a hypothesis version snapshot.

        Args:
            simulation_id: Simulation ID
            version: Version number
            name: Version name
            description: Optional description

        Returns:
            Version info dict
        """
        from datetime import datetime

        # Get current hypotheses
        hypotheses = self.get_by_simulation_id(simulation_id)

        # Serialize snapshot to JSONB
        snapshot_dict = {
            "hypotheses": [
                {
                    "variable_id": h.variable_id,
                    "distribution_type": h.distribution_type.value,
                    "distribution_params": h.parameters.model_dump(),
                    "correlations": [c.model_dump() for c in h.correlations],
                }
                for h in hypotheses
            ],
            "version": version,
        }

        orm_version = HypothesisVersionORM(
            simulation_id=simulation_id,
            version_name=name,
            description=description,
            dag_snapshot={},  # Empty for now
            hypotheses_snapshot=snapshot_dict,
            created_at=datetime.utcnow(),
        )

        self.session.add(orm_version)
        self.session.commit()
        self.session.refresh(orm_version)

        return {
            "version": version,
            "created_at": orm_version.created_at,
            "name": name,
            "description": description,
        }

    def _orm_to_entity(self, orm: HypothesisORM) -> Hypothesis:
        """
        Convert ORM model to domain entity.

        Args:
            orm: SQLAlchemy ORM model

        Returns:
            Hypothesis domain entity
        """
        from synth_lab.domain.entities.hypothesis import ScenarioOption, TriangularParams

        # Deserialize distribution type
        dist_type = DistributionType(orm.distribution_type)

        # Deserialize parameters based on distribution type
        params_data = orm.distribution_params
        if dist_type == DistributionType.UNIFORM:
            params = UniformParams(**params_data)
        elif dist_type == DistributionType.NORMAL:
            params = NormalParams(**params_data)
        elif dist_type == DistributionType.BETA:
            params = BetaParams(**params_data)
        elif dist_type == DistributionType.LOGNORMAL:
            params = LogNormalParams(**params_data)
        elif dist_type == DistributionType.BERNOULLI:
            params = BernoulliParams(**params_data)
        else:
            raise ValueError(f"Unsupported distribution type: {dist_type}")

        # Deserialize correlations
        correlations = []
        if orm.correlations:
            correlations = [Correlation(**corr_data) for corr_data in orm.correlations]

        # Deserialize scenario options
        scenario_options = None
        if orm.scenario_options:
            scenario_options = [
                ScenarioOption(
                    value=opt["value"],
                    label=opt["label"],
                    distribution_params=TriangularParams(
                        min_value=opt["min_value"],
                        mode=opt["mode"],
                        max_value=opt["max_value"],
                    ),
                )
                for opt in orm.scenario_options
            ]

        return Hypothesis(
            id=orm.id,
            simulation_id=orm.simulation_id,
            variable_id=orm.variable_id,
            variable_name=orm.variable_name or "",
            distribution_type=dist_type,
            parameters=params,
            correlations=correlations,
            scenario_options=scenario_options,
            selected_scenario=orm.selected_scenario,
            created_at=orm.created_at,
        )

    def _version_orm_to_entity(self, orm: HypothesisVersionORM) -> HypothesisVersion:
        """
        Convert version ORM model to domain entity.

        Args:
            orm: SQLAlchemy ORM model

        Returns:
            HypothesisVersion domain entity
        """
        snapshot = HypothesisSnapshot(
            hypotheses=[],  # Would need to deserialize if needed
            dag_version=orm.hypotheses_snapshot.get("dag_version", 1),
        )

        return HypothesisVersion(
            id=orm.id,
            simulation_id=orm.simulation_id,
            name=orm.version_name,
            description=orm.description,
            snapshot=snapshot,
            dag_snapshot=orm.dag_snapshot,
            created_at=orm.created_at,
        )
