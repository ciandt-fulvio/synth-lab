"""
ExperimentRepository for synth-lab.

Data access layer for experiment data. Uses SQLAlchemy ORM for database operations.

References:
    - Spec: specs/019-experiment-refactor/spec.md
    - Data model: specs/019-experiment-refactor/data-model.md
    - ORM models: synth_lab.models.orm.experiment
"""

from datetime import datetime, timezone

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from synth_lab.domain.entities.experiment import Experiment
from synth_lab.models.orm.experiment import Experiment as ExperimentORM
from synth_lab.models.pagination import PaginatedResponse, PaginationMeta, PaginationParams
from synth_lab.repositories.base import BaseRepository


class ExperimentSummary(BaseModel):
    """Summary of an experiment for list display."""

    id: str = Field(description="Experiment ID.")
    name: str = Field(description="Short name of the feature.")
    hypothesis: str = Field(description="Hypothesis description.")
    description: str | None = Field(default=None, description="Additional context.")
    synth_group_id: str = Field(description="ID of the synth group used for this experiment.")
    synth_group_name: str = Field(description="Name of the synth group used for this experiment.")
    has_interview_guide: bool = Field(
        default=False, description="Whether interview guide is configured."
    )
    interview_count: int = Field(default=0, description="Number of linked interviews.")
    tags: list[str] = Field(default_factory=list, description="Tag names associated with this experiment.")
    created_at: datetime = Field(description="Creation timestamp.")
    updated_at: datetime | None = Field(default=None, description="Last update timestamp.")


class ExperimentRepository(BaseRepository):
    """Repository for experiment data access.

    Uses SQLAlchemy ORM for database operations.

    Usage:
        # ORM mode
        repo = ExperimentRepository(db=database_manager)

        # ORM mode (SQLAlchemy)
        repo = ExperimentRepository(session=session)
    """

    def __init__(
        self,
session: Session | None = None):
        super().__init__( session=session)

    def create(self, experiment: Experiment) -> Experiment:
        """
        Create a new experiment.

        Args:
            experiment: Experiment entity to create.

        Returns:
            Created experiment with persisted data.
        """
        return self._create_orm(experiment)

    def _create_orm(self, experiment: Experiment) -> Experiment:
        """Create experiment using ORM."""
        orm_exp = ExperimentORM(
            id=experiment.id,
            name=experiment.name,
            hypothesis=experiment.hypothesis,
            description=experiment.description,
            synth_group_id=experiment.synth_group_id,
            owner_id=experiment.owner_id,
            status="active",
            created_at=experiment.created_at.isoformat(),
            updated_at=experiment.updated_at.isoformat() if experiment.updated_at else None)
        self._add(orm_exp)
        self._flush()
        self._commit()
        return experiment

    def get_by_id(self, experiment_id: str) -> Experiment | None:
        """
        Get an experiment by ID.

        Only returns active experiments (not soft-deleted).

        Args:
            experiment_id: Experiment ID to retrieve.

        Returns:
            Experiment if found and active, None otherwise.
        """
        return self._get_by_id_orm(experiment_id)

    def _get_by_id_orm(self, experiment_id: str) -> Experiment | None:
        """Get experiment by ID using ORM."""
        from sqlalchemy.orm import joinedload

        stmt = select(ExperimentORM).where(
            ExperimentORM.id == experiment_id,
            ExperimentORM.status == "active"
        ).options(joinedload(ExperimentORM.synth_group))
        result = self.session.execute(stmt).scalar_one_or_none()
        if result is None:
            return None
        return self._orm_to_experiment(result)

    def list_experiments(
        self, params: PaginationParams, user_id: str | None = None
    ) -> PaginatedResponse[ExperimentSummary]:
        """
        List experiments with pagination.

        Only returns active experiments (not soft-deleted).
        When user_id is provided, only returns experiments owned by or shared with the user.

        Args:
            params: Pagination parameters.
            user_id: If provided, filter to experiments the user can access.

        Returns:
            Paginated response with experiment summaries.
        """
        return self._list_experiments_orm(params, user_id=user_id)

    def _list_experiments_orm(
        self, params: PaginationParams, user_id: str | None = None
    ) -> PaginatedResponse[ExperimentSummary]:
        """List experiments using ORM with eager-loaded relationships."""
        from sqlalchemy import func as sqlfunc
        from sqlalchemy import or_
        from sqlalchemy.orm import joinedload

        from synth_lab.models.orm.share import ExperimentShare as ExperimentShareORM
        from synth_lab.models.orm.tag import ExperimentTag as ExperimentTagORM
        from synth_lab.models.orm.tag import Tag as TagORM

        # Base query for active experiments with eager-loaded synth_group
        stmt = select(ExperimentORM).where(ExperimentORM.status == "active").options(
            joinedload(ExperimentORM.synth_group)
        )
        count_where = [ExperimentORM.status == "active"]

        # Filter by user access (ownership or shares)
        if user_id:
            access_filter = or_(
                ExperimentORM.owner_id == user_id,
                ExperimentORM.id.in_(
                    select(ExperimentShareORM.experiment_id).where(
                        ExperimentShareORM.user_id == user_id
                    )
                ),
            )
            stmt = stmt.where(access_filter)
            count_where.append(access_filter)

        # Apply tag filter
        if params.tag:
            # Join with experiment_tags and tags to filter by tag name
            stmt = stmt.join(ExperimentTagORM).join(TagORM).where(TagORM.name == params.tag)
            count_where.append(TagORM.name == params.tag)

        # Apply search filter (name OR hypothesis, case-insensitive)
        if params.search:
            search_pattern = f"%{params.search}%"
            search_filter = or_(
                ExperimentORM.name.ilike(search_pattern),
                ExperimentORM.hypothesis.ilike(search_pattern)
            )
            stmt = stmt.where(search_filter)
            count_where.append(search_filter)

        # Apply sorting
        if params.sort_by == "name":
            order_col = ExperimentORM.name.asc() if params.sort_order == "asc" else ExperimentORM.name.desc()
        else:
            # Default: created_at DESC
            order_col = ExperimentORM.created_at.asc() if params.sort_order == "asc" else ExperimentORM.created_at.desc()
        stmt = stmt.order_by(order_col)

        # Get total count (with search and tag filters applied)
        # Need to rebuild JOINs for count query when tag filter is active
        # IMPORTANT: JOINs must be applied BEFORE WHERE conditions
        count_base = select(ExperimentORM)
        if params.tag:
            count_base = count_base.join(ExperimentTagORM).join(TagORM)
        count_base = count_base.where(*count_where)
        count_stmt = select(sqlfunc.count()).select_from(count_base.subquery())
        total = self.session.execute(count_stmt).scalar() or 0

        # Apply pagination
        stmt = stmt.limit(params.limit).offset(params.offset)
        experiments = list(self.session.execute(stmt).scalars().all())

        # Convert to summaries with relationship checks
        summaries = [self._orm_to_summary(exp) for exp in experiments]
        meta = PaginationMeta.from_params(total, params)

        return PaginatedResponse(data=summaries, pagination=meta)

    def update(
        self,
        experiment_id: str,
        name: str | None = None,
        hypothesis: str | None = None,
        description: str | None = None,
        synth_group_id: str | None = None) -> Experiment | None:
        """
        Update an experiment.

        Args:
            experiment_id: ID of experiment to update.
            name: New name (optional).
            hypothesis: New hypothesis (optional).
            description: New description (optional).
            synth_group_id: New synth group ID (optional).

        Returns:
            Updated experiment if found, None otherwise.
        """
        return self._update_orm(experiment_id, name, hypothesis, description, synth_group_id)

    def _update_orm(
        self,
        experiment_id: str,
        name: str | None = None,
        hypothesis: str | None = None,
        description: str | None = None,
        synth_group_id: str | None = None) -> Experiment | None:
        """Update experiment using ORM."""
        stmt = select(ExperimentORM).where(
            ExperimentORM.id == experiment_id,
            ExperimentORM.status == "active")
        orm_exp = self.session.execute(stmt).scalar_one_or_none()
        if orm_exp is None:
            return None

        if name is not None:
            orm_exp.name = name
        if hypothesis is not None:
            orm_exp.hypothesis = hypothesis
        if description is not None:
            orm_exp.description = description
        if synth_group_id is not None:
            orm_exp.synth_group_id = synth_group_id

        orm_exp.updated_at = datetime.now(timezone.utc).isoformat()
        self._flush()
        self._commit()

        return self._orm_to_experiment(orm_exp)

    def delete(self, experiment_id: str) -> bool:
        """
        Soft delete an experiment by setting status to 'deleted'.

        The experiment data is preserved but will be hidden from listings.

        Args:
            experiment_id: ID of experiment to delete.

        Returns:
            True if deleted, False if not found.
        """
        return self._delete_orm(experiment_id)

    def _delete_orm(self, experiment_id: str) -> bool:
        """Soft delete experiment using ORM."""
        stmt = select(ExperimentORM).where(
            ExperimentORM.id == experiment_id,
            ExperimentORM.status == "active")
        orm_exp = self.session.execute(stmt).scalar_one_or_none()
        if orm_exp is None:
            return False

        orm_exp.status = "deleted"
        orm_exp.updated_at = datetime.now(timezone.utc).isoformat()
        self._flush()
        self._commit()
        return True

    def _row_to_experiment(self, row) -> Experiment:
        """Convert a database row to Experiment entity."""
        created_at = row["created_at"]
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        updated_at = row["updated_at"]
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)

        return Experiment(
            id=row["id"],
            name=row["name"],
            hypothesis=row["hypothesis"],
            description=row["description"],
            created_at=created_at,
            updated_at=updated_at)

    def _row_to_summary(self, row) -> ExperimentSummary:
        """Convert a database row to ExperimentSummary."""
        created_at = row["created_at"]
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        updated_at = row["updated_at"]
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)

        # Get synth_group_name if available in row, otherwise default to "Unknown"
        synth_group_name = row.get("synth_group_name", "Unknown")

        return ExperimentSummary(
            id=row["id"],
            name=row["name"],
            hypothesis=row["hypothesis"],
            description=row["description"],
            synth_group_id=row["synth_group_id"],
            synth_group_name=synth_group_name,
            has_interview_guide=(
                bool(row["has_interview_guide"]) if "has_interview_guide" in row.keys() else False
            ),
            interview_count=row["interview_count"] if "interview_count" in row.keys() else 0,
            tags=[],  # Raw SQL conversion doesn't load tags
            created_at=created_at,
            updated_at=updated_at)

    # =========================================================================
    # ORM conversion methods
    # =========================================================================

    def _orm_to_experiment(self, orm_exp: ExperimentORM) -> Experiment:
        """Convert ORM model to Experiment entity."""
        created_at = orm_exp.created_at
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        updated_at = orm_exp.updated_at
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)

        # Get tag names from experiment_tags relationship
        tags = [et.tag.name for et in orm_exp.experiment_tags] if orm_exp.experiment_tags else []

        return Experiment(
            id=orm_exp.id,
            name=orm_exp.name,
            hypothesis=orm_exp.hypothesis,
            description=orm_exp.description,
            synth_group_id=orm_exp.synth_group_id,
            tags=tags,
            created_at=created_at,
            updated_at=updated_at)

    def _orm_to_summary(self, orm_exp: ExperimentORM) -> ExperimentSummary:
        """Convert ORM model to ExperimentSummary."""
        created_at = orm_exp.created_at
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        updated_at = orm_exp.updated_at
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)

        # Check relationships via lazy loading
        has_interview_guide = orm_exp.interview_guide is not None
        interview_count = len(orm_exp.research_executions) if orm_exp.research_executions else 0

        # Get tag names from experiment_tags relationship
        tags = [et.tag.name for et in orm_exp.experiment_tags] if orm_exp.experiment_tags else []

        # Get synth group name from relationship
        synth_group_name = "Unknown"
        try:
            if orm_exp.synth_group:
                synth_group_name = orm_exp.synth_group.name
        except Exception:
            # If relationship fails to load, use default
            pass

        return ExperimentSummary(
            id=orm_exp.id,
            name=orm_exp.name,
            hypothesis=orm_exp.hypothesis,
            description=orm_exp.description,
            synth_group_id=orm_exp.synth_group_id,
            synth_group_name=synth_group_name,
            has_interview_guide=has_interview_guide,
            interview_count=interview_count,
            tags=tags,
            created_at=created_at,
            updated_at=updated_at)


if __name__ == "__main__":
    print("ExperimentRepository - requires PostgreSQL database for validation")
