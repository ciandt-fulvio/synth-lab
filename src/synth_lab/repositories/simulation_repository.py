"""
SimulationRepository for synth-lab.

Data access layer for causal simulation data. Uses SQLAlchemy ORM for database operations.

References:
    - Spec: specs/035-causal-simulation/spec.md
    - Data model: specs/035-causal-simulation/data-model.md
    - ORM models: synth_lab.models.orm.simulation
"""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from synth_lab.domain.entities.simulation import (
    ProblemDecomposition,
    Simulation,
    SimulationStatus,
)
from synth_lab.models.orm.simulation import Simulation as SimulationORM
from synth_lab.repositories.base import BaseRepository


class SimulationRepository(BaseRepository):
    """
    Repository for simulation data access.

    Uses SQLAlchemy ORM for database operations.

    Usage:
        # With explicit session (preferred for FastAPI dependency injection):
        repo = SimulationRepository(session=db_session)

        # Without session (creates new session from global factory):
        repo = SimulationRepository()
    """

    def __init__(self, session: Session | None = None):
        """
        Initialize repository.

        Args:
            session: SQLAlchemy session. If not provided, uses global session factory.
        """
        super().__init__(session=session)

    def create(self, simulation: Simulation) -> Simulation:
        """
        Create a new simulation.

        Args:
            simulation: Simulation entity to create

        Returns:
            Created simulation with persisted data

        Example:
            >>> sim = Simulation(
            ...     question_text="What adoption rate for meal subscription?"
            ... )
            >>> created = repo.create(sim)
            >>> print(created.id)  # sim_a1b2c3d4
        """
        # Convert problem_decomposition to dict if present
        problem_dict = None
        if simulation.problem_decomposition:
            problem_dict = simulation.problem_decomposition.model_dump()

        # Create ORM instance
        orm_simulation = SimulationORM(
            id=simulation.id,
            question=simulation.question_text,
            problem_decomposition=problem_dict,
            status=simulation.status.value
            if isinstance(simulation.status, SimulationStatus)
            else simulation.status,
            random_seed=simulation.random_seed,
            n_worlds=simulation.n_worlds,
            created_at=simulation.created_at,
            updated_at=simulation.created_at,
        )

        # Persist to database
        self.session.add(orm_simulation)
        self.session.commit()
        self.session.refresh(orm_simulation)

        # Convert back to entity
        return self._orm_to_entity(orm_simulation)

    def get(self, simulation_id: str) -> Simulation | None:
        """
        Get simulation by ID.

        Args:
            simulation_id: Simulation ID

        Returns:
            Simulation entity or None if not found

        Example:
            >>> sim = repo.get("sim_a1b2c3d4")
            >>> if sim:
            ...     print(sim.question_text)
        """
        stmt = select(SimulationORM).where(SimulationORM.id == simulation_id)
        orm_simulation = self.session.execute(stmt).scalar_one_or_none()

        if orm_simulation is None:
            return None

        return self._orm_to_entity(orm_simulation)

    def update(self, simulation: Simulation) -> Simulation:
        """
        Update an existing simulation.

        Args:
            simulation: Simulation entity with updated data

        Returns:
            Updated simulation entity

        Raises:
            ValueError: If simulation not found

        Example:
            >>> sim = repo.get("sim_a1b2c3d4")
            >>> sim.status = SimulationStatus.COMPLETED
            >>> sim.completed_at = datetime.now(timezone.utc)
            >>> updated = repo.update(sim)
        """
        stmt = select(SimulationORM).where(SimulationORM.id == simulation.id)
        orm_simulation = self.session.execute(stmt).scalar_one_or_none()

        if orm_simulation is None:
            raise ValueError(f"Simulation not found: {simulation.id}")

        # Update fields
        orm_simulation.question = simulation.question_text
        orm_simulation.problem_decomposition = (
            simulation.problem_decomposition.model_dump()
            if simulation.problem_decomposition
            else None
        )
        orm_simulation.status = (
            simulation.status.value
            if isinstance(simulation.status, SimulationStatus)
            else simulation.status
        )
        orm_simulation.random_seed = simulation.random_seed
        orm_simulation.n_worlds = simulation.n_worlds
        orm_simulation.updated_at = datetime.now(timezone.utc)

        # Persist changes
        self.session.commit()
        self.session.refresh(orm_simulation)

        return self._orm_to_entity(orm_simulation)

    def delete(self, simulation_id: str) -> bool:
        """
        Delete a simulation.

        Args:
            simulation_id: Simulation ID

        Returns:
            True if deleted, False if not found

        Example:
            >>> deleted = repo.delete("sim_a1b2c3d4")
            >>> print(deleted)  # True
        """
        stmt = select(SimulationORM).where(SimulationORM.id == simulation_id)
        orm_simulation = self.session.execute(stmt).scalar_one_or_none()

        if orm_simulation is None:
            return False

        self.session.delete(orm_simulation)
        self.session.commit()

        return True

    def list(
        self, status: SimulationStatus | None = None, limit: int = 100
    ) -> list[Simulation]:
        """
        List simulations with optional filtering.

        Args:
            status: Filter by status (optional)
            limit: Maximum number of results

        Returns:
            List of Simulation entities

        Example:
            >>> sims = repo.list(status=SimulationStatus.COMPLETED, limit=10)
            >>> for sim in sims:
            ...     print(f"{sim.id}: {sim.question_text}")
        """
        stmt = select(SimulationORM).order_by(
            SimulationORM.created_at.desc()
        )

        if status is not None:
            status_value = status.value if isinstance(status, SimulationStatus) else status
            stmt = stmt.where(SimulationORM.status == status_value)

        stmt = stmt.limit(limit)

        orm_simulations = self.session.execute(stmt).scalars().all()

        return [self._orm_to_entity(orm) for orm in orm_simulations]

    def _orm_to_entity(self, orm: SimulationORM) -> Simulation:
        """
        Convert ORM model to domain entity.

        Args:
            orm: SQLAlchemy ORM model

        Returns:
            Simulation domain entity
        """
        problem_decomp = None
        if orm.problem_decomposition:
            problem_decomp = ProblemDecomposition(**orm.problem_decomposition)

        return Simulation(
            id=orm.id,
            question_text=orm.question,
            problem_decomposition=problem_decomp,
            status=SimulationStatus(orm.status),
            random_seed=orm.random_seed,
            n_worlds=orm.n_worlds,
            created_at=orm.created_at,
            completed_at=None,  # Not stored in ORM yet
            error_message=None,  # Not stored in ORM yet
        )
