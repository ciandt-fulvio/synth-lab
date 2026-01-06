"""
TagRepository for synth-lab.

Data access layer for tag data. Uses SQLAlchemy ORM for database operations.

References:
    - ORM models: synth_lab.models.orm.tag
    - Domain entities: synth_lab.domain.entities.tag
"""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from synth_lab.domain.entities.tag import Tag
from synth_lab.models.orm.tag import Tag as TagORM
from synth_lab.models.orm.tag import ExperimentTag as ExperimentTagORM
from synth_lab.repositories.base import BaseRepository


class TagRepository(BaseRepository):
    """Repository for tag data access.

    Uses SQLAlchemy ORM for database operations.

    Usage:
        repo = TagRepository(session=session)
    """

    def __init__(self, session: Session | None = None):
        super().__init__(session=session)

    def create(self, tag: Tag) -> Tag:
        """
        Create a new tag.

        Args:
            tag: Tag entity to create.

        Returns:
            Created tag with persisted data.
        """
        orm_tag = TagORM(
            id=tag.id,
            name=tag.name,
            created_at=tag.created_at.isoformat(),
            updated_at=tag.updated_at.isoformat() if tag.updated_at else None,
        )
        self._add(orm_tag)
        self._flush()
        self._commit()
        return tag

    def get_by_name(self, name: str) -> Tag | None:
        """
        Get a tag by name.

        Args:
            name: Tag name to search for.

        Returns:
            Tag if found, None otherwise.
        """
        stmt = select(TagORM).where(TagORM.name == name)
        result = self.session.execute(stmt).scalar_one_or_none()
        if result is None:
            return None
        return self._orm_to_tag(result)

    def list_tags(self) -> list[Tag]:
        """
        List all tags.

        Returns:
            List of all tags, ordered by name.
        """
        stmt = select(TagORM).order_by(TagORM.name.asc())
        results = list(self.session.execute(stmt).scalars().all())
        return [self._orm_to_tag(tag) for tag in results]

    def get_tags_for_experiment(self, experiment_id: str) -> list[Tag]:
        """
        Get all tags for an experiment.

        Args:
            experiment_id: ID of the experiment.

        Returns:
            List of tags associated with the experiment, ordered by name.
        """
        stmt = (
            select(TagORM)
            .join(ExperimentTagORM)
            .where(ExperimentTagORM.experiment_id == experiment_id)
            .order_by(TagORM.name.asc())
        )
        results = list(self.session.execute(stmt).scalars().all())
        return [self._orm_to_tag(tag) for tag in results]

    def add_tag_to_experiment(self, experiment_id: str, tag_id: str) -> bool:
        """
        Add a tag to an experiment.

        Args:
            experiment_id: ID of the experiment.
            tag_id: ID of the tag.

        Returns:
            True if added successfully, False if already exists.
        """
        # Check if relationship already exists
        stmt = select(ExperimentTagORM).where(
            ExperimentTagORM.experiment_id == experiment_id,
            ExperimentTagORM.tag_id == tag_id,
        )
        existing = self.session.execute(stmt).scalar_one_or_none()
        if existing is not None:
            return False  # Already exists

        # Create new relationship
        experiment_tag = ExperimentTagORM(
            experiment_id=experiment_id,
            tag_id=tag_id,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._add(experiment_tag)
        self._flush()
        self._commit()
        return True

    def remove_tag_from_experiment(self, experiment_id: str, tag_id: str) -> bool:
        """
        Remove a tag from an experiment.

        Args:
            experiment_id: ID of the experiment.
            tag_id: ID of the tag.

        Returns:
            True if removed successfully, False if not found.
        """
        stmt = select(ExperimentTagORM).where(
            ExperimentTagORM.experiment_id == experiment_id,
            ExperimentTagORM.tag_id == tag_id,
        )
        experiment_tag = self.session.execute(stmt).scalar_one_or_none()
        if experiment_tag is None:
            return False

        self.session.delete(experiment_tag)
        self._flush()
        self._commit()
        return True

    def _orm_to_tag(self, orm_tag: TagORM) -> Tag:
        """Convert ORM model to Tag entity."""
        created_at = orm_tag.created_at
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        updated_at = orm_tag.updated_at
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)

        return Tag(
            id=orm_tag.id,
            name=orm_tag.name,
            created_at=created_at,
            updated_at=updated_at,
        )
