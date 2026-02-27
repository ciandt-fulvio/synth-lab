"""Share repository for database operations.

Handles CRUD operations for sharing relationships.
"""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from synth_lab.domain.entities.share import (
    ExperimentShare,
    PendingInvite,
    PermissionLevel,
    SynthGroupShare,
)


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

    # ── Pending Invites ──────────────────────────────────────────────────

    def create_pending_invite(self, invite: PendingInvite) -> PendingInvite:
        """Create a pending invite for a user who hasn't registered yet.

        Args:
            invite: PendingInvite entity

        Returns:
            Created PendingInvite
        """
        query = text(
            "INSERT INTO pending_invites"
            " (id, resource_type, resource_id, invited_email, invited_by_id, created_at)"
            " VALUES (:id, :resource_type, :resource_id, :invited_email,"
            " :invited_by_id, :created_at)"
        )
        self.db.execute(query, invite.to_dict())
        self.db.commit()
        return invite

    def get_pending_invites_for_resource(
        self, resource_type: str, resource_id: str
    ) -> List[PendingInvite]:
        """Get all pending invites for a resource.

        Args:
            resource_type: 'experiment' or 'synth_group'
            resource_id: Resource ID

        Returns:
            List of PendingInvite entities
        """
        query = text("""
            SELECT id, resource_type, resource_id, invited_email, invited_by_id, created_at
            FROM pending_invites
            WHERE resource_type = :resource_type AND resource_id = :resource_id
        """)
        result = self.db.execute(query, {
            "resource_type": resource_type,
            "resource_id": resource_id,
        })
        return [
            PendingInvite(
                id=row[0],
                resource_type=row[1],
                resource_id=row[2],
                invited_email=row[3],
                invited_by_id=row[4],
                created_at=row[5],
            )
            for row in result.fetchall()
        ]

    def get_pending_invites_by_email(self, email: str) -> List[PendingInvite]:
        """Get all pending invites for a given email.

        Args:
            email: User email (case-insensitive)

        Returns:
            List of PendingInvite entities
        """
        query = text("""
            SELECT id, resource_type, resource_id, invited_email, invited_by_id, created_at
            FROM pending_invites
            WHERE invited_email = :email
        """)
        result = self.db.execute(query, {"email": email.lower().strip()})
        return [
            PendingInvite(
                id=row[0],
                resource_type=row[1],
                resource_id=row[2],
                invited_email=row[3],
                invited_by_id=row[4],
                created_at=row[5],
            )
            for row in result.fetchall()
        ]

    def delete_pending_invite(self, invite_id: str) -> bool:
        """Delete a pending invite by ID.

        Args:
            invite_id: Invite ID

        Returns:
            True if deleted, False if not found
        """
        query = text("DELETE FROM pending_invites WHERE id = :id")
        result = self.db.execute(query, {"id": invite_id})
        self.db.commit()
        return result.rowcount > 0

    def delete_pending_invites_by_email(self, email: str) -> int:
        """Delete all pending invites for a given email.

        Args:
            email: User email

        Returns:
            Number of invites deleted
        """
        query = text("DELETE FROM pending_invites WHERE invited_email = :email")
        result = self.db.execute(query, {"email": email.lower().strip()})
        self.db.commit()
        return result.rowcount

    def revoke_pending_invite(
        self, resource_type: str, resource_id: str, email: str
    ) -> bool:
        """Revoke a pending invite for a specific resource and email.

        Args:
            resource_type: 'experiment' or 'synth_group'
            resource_id: Resource ID
            email: Invited email

        Returns:
            True if deleted, False if not found
        """
        query = text("""
            DELETE FROM pending_invites
            WHERE resource_type = :resource_type
              AND resource_id = :resource_id
              AND invited_email = :email
        """)
        result = self.db.execute(query, {
            "resource_type": resource_type,
            "resource_id": resource_id,
            "email": email.lower().strip(),
        })
        self.db.commit()
        return result.rowcount > 0
