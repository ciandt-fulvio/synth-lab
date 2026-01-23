"""Share repository for database operations.

Handles CRUD operations for sharing relationships.
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import datetime

from synth_lab.domain.entities.share import ExperimentShare, SynthGroupShare, PermissionLevel


class ShareRepository:
    """Repository for share data access operations."""

    def __init__(self, db: Session):
        """Initialize repository with database session.

        Args:
            db: SQLAlchemy session
        """
        self.db = db

    def create_experiment_share(
        self,
        experiment_id: str,
        user_id: str,
        permission_level: PermissionLevel,
        granted_by_id: str,
    ) -> ExperimentShare:
        """Create experiment share.

        Args:
            experiment_id: Experiment ID
            user_id: User receiving access
            permission_level: Permission level
            granted_by_id: User granting access

        Returns:
            Created ExperimentShare

        Raises:
            ValueError: If share already exists or validation fails
        """
        share = ExperimentShare(
            experiment_id=experiment_id,
            user_id=UUID(user_id),
            permission_level=permission_level,
            granted_by_id=UUID(granted_by_id),
        )

        query = text("""
            INSERT INTO experiment_shares (id, experiment_id, user_id, permission_level, granted_at, granted_by_id)
            VALUES (:id, :experiment_id, :user_id, :permission_level, :granted_at, :granted_by_id)
        """)

        self.db.execute(query, {
            "id": share.id,
            "experiment_id": share.experiment_id,
            "user_id": share.user_id,
            "permission_level": share.permission_level.value,
            "granted_at": share.granted_at,
            "granted_by_id": share.granted_by_id,
        })
        self.db.commit()

        return share

    def create_synth_group_share(
        self,
        synth_group_id: str,
        user_id: str,
        permission_level: PermissionLevel,
        granted_by_id: str,
    ) -> SynthGroupShare:
        """Create synth group share.

        Args:
            synth_group_id: Synth group ID
            user_id: User receiving access
            permission_level: Permission level
            granted_by_id: User granting access

        Returns:
            Created SynthGroupShare

        Raises:
            ValueError: If share already exists or validation fails
        """
        share = SynthGroupShare(
            synth_group_id=synth_group_id,
            user_id=UUID(user_id),
            permission_level=permission_level,
            granted_by_id=UUID(granted_by_id),
        )

        query = text("""
            INSERT INTO synth_group_shares (id, synth_group_id, user_id, permission_level, granted_at, granted_by_id)
            VALUES (:id, :synth_group_id, :user_id, :permission_level, :granted_at, :granted_by_id)
        """)

        self.db.execute(query, {
            "id": share.id,
            "synth_group_id": share.synth_group_id,
            "user_id": share.user_id,
            "permission_level": share.permission_level.value,
            "granted_at": share.granted_at,
            "granted_by_id": share.granted_by_id,
        })
        self.db.commit()

        return share

    def get_experiment_shares(self, experiment_id: str) -> List[ExperimentShare]:
        """Get all shares for an experiment.

        Args:
            experiment_id: Experiment ID

        Returns:
            List of ExperimentShare entities
        """
        query = text("""
            SELECT id, experiment_id, user_id, permission_level, granted_at, granted_by_id
            FROM experiment_shares
            WHERE experiment_id = :experiment_id
        """)

        result = self.db.execute(query, {"experiment_id": experiment_id})
        rows = result.fetchall()

        return [
            ExperimentShare(
                id=UUID(row[0]),
                experiment_id=row[1],
                user_id=UUID(row[2]),
                permission_level=PermissionLevel(row[3]),
                granted_at=row[4],
                granted_by_id=UUID(row[5]),
            )
            for row in rows
        ]

    def get_synth_group_shares(self, synth_group_id: str) -> List[SynthGroupShare]:
        """Get all shares for a synth group.

        Args:
            synth_group_id: Synth group ID

        Returns:
            List of SynthGroupShare entities
        """
        query = text("""
            SELECT id, synth_group_id, user_id, permission_level, granted_at, granted_by_id
            FROM synth_group_shares
            WHERE synth_group_id = :synth_group_id
        """)

        result = self.db.execute(query, {"synth_group_id": synth_group_id})
        rows = result.fetchall()

        return [
            SynthGroupShare(
                id=UUID(row[0]),
                synth_group_id=row[1],
                user_id=UUID(row[2]),
                permission_level=PermissionLevel(row[3]),
                granted_at=row[4],
                granted_by_id=UUID(row[5]),
            )
            for row in rows
        ]

    def revoke_experiment_share(self, experiment_id: str, user_id: str) -> bool:
        """Revoke experiment access from user.

        Args:
            experiment_id: Experiment ID
            user_id: User ID to revoke access from

        Returns:
            True if share was deleted, False if not found
        """
        query = text("""
            DELETE FROM experiment_shares
            WHERE experiment_id = :experiment_id AND user_id = :user_id
        """)

        result = self.db.execute(query, {
            "experiment_id": experiment_id,
            "user_id": user_id,
        })
        self.db.commit()

        return result.rowcount > 0

    def get_experiment_share(
        self,
        experiment_id: str,
        user_id: str
    ) -> Optional[ExperimentShare]:
        """Get specific experiment share.

        Args:
            experiment_id: Experiment ID
            user_id: User ID

        Returns:
            ExperimentShare if found, None otherwise
        """
        query = text("""
            SELECT id, experiment_id, user_id, permission_level, granted_at, granted_by_id
            FROM experiment_shares
            WHERE experiment_id = :experiment_id AND user_id = :user_id
        """)

        result = self.db.execute(query, {
            "experiment_id": experiment_id,
            "user_id": user_id,
        })
        row = result.fetchone()

        if row:
            return ExperimentShare(
                id=UUID(row[0]),
                experiment_id=row[1],
                user_id=UUID(row[2]),
                permission_level=PermissionLevel(row[3]),
                granted_at=row[4],
                granted_by_id=UUID(row[5]),
            )

        return None
