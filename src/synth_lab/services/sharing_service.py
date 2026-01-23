"""Sharing service for resource sharing operations.

Handles sharing of experiments and synth_groups between users.
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from synth_lab.domain.entities.share import ExperimentShare, SynthGroupShare, PermissionLevel
from synth_lab.repositories.share_repository import ShareRepository


class SharingService:
    """Service for sharing resources between users."""

    def __init__(self, db: AsyncSession):
        """Initialize sharing service.

        Args:
            db: SQLAlchemy async session
        """
        self.db = db
        self.share_repo = ShareRepository(db)

    async def share_experiment(
        self,
        experiment_id: str,
        owner_id: str,
        target_user_id: str,
        permission_level: PermissionLevel,
    ) -> ExperimentShare:
        """Share experiment with another user.

        Automatically shares the associated synth_group with the same permission level.

        Args:
            experiment_id: Experiment ID to share
            owner_id: Owner user ID (granting access)
            target_user_id: User ID to share with
            permission_level: Permission level to grant

        Returns:
            Created ExperimentShare

        Raises:
            ValueError: If experiment not found, user is not owner, or validation fails
        """
        # Validate experiment exists and user is owner
        query = text("""
            SELECT owner_id, synth_group_id FROM experiments WHERE id = :experiment_id
        """)
        result = await self.db.execute(query, {"experiment_id": experiment_id})
        row = result.fetchone()

        if not row:
            raise ValueError(f"Experiment {experiment_id} not found")

        if row[0] != owner_id:
            raise ValueError(f"User {owner_id} is not the owner of experiment {experiment_id}")

        # Prevent self-sharing
        if owner_id == target_user_id:
            raise ValueError("Cannot share experiment with yourself")

        # Check if target user exists
        user_query = text("SELECT id FROM users WHERE id = :user_id")
        user_result = await self.db.execute(user_query, {"user_id": target_user_id})
        if not user_result.fetchone():
            raise ValueError(f"Target user {target_user_id} not found")

        # Check if share already exists
        existing_share = await self.share_repo.get_experiment_share(
            experiment_id, target_user_id
        )
        if existing_share:
            raise ValueError(
                f"Experiment {experiment_id} is already shared with user {target_user_id}"
            )

        # Create experiment share
        experiment_share = await self.share_repo.create_experiment_share(
            experiment_id=experiment_id,
            user_id=target_user_id,
            permission_level=permission_level,
            granted_by_id=owner_id,
        )

        logger.info(
            f"Experiment {experiment_id} shared with user {target_user_id} "
            f"({permission_level.value}) by {owner_id}"
        )

        # Automatically share associated synth_group if it exists
        synth_group_id = row[1]
        if synth_group_id:
            try:
                await self.share_repo.create_synth_group_share(
                    synth_group_id=synth_group_id,
                    user_id=target_user_id,
                    permission_level=permission_level,
                    granted_by_id=owner_id,
                )
                logger.info(
                    f"Synth group {synth_group_id} automatically shared with user {target_user_id} "
                    f"({permission_level.value})"
                )
            except Exception as e:
                # If synth_group share fails, we don't rollback the experiment share
                # This is to handle cases where the synth_group might already be shared
                logger.warning(
                    f"Failed to automatically share synth_group {synth_group_id}: {str(e)}"
                )

        return experiment_share

    async def revoke_experiment_share(
        self,
        experiment_id: str,
        owner_id: str,
        target_user_id: str,
    ) -> bool:
        """Revoke experiment access from user.

        Args:
            experiment_id: Experiment ID
            owner_id: Owner user ID (revoking access)
            target_user_id: User ID to revoke access from

        Returns:
            True if share was revoked, False if not found

        Raises:
            ValueError: If user is not owner or validation fails
        """
        # Validate experiment exists and user is owner
        query = text("SELECT owner_id FROM experiments WHERE id = :experiment_id")
        result = await self.db.execute(query, {"experiment_id": experiment_id})
        row = result.fetchone()

        if not row:
            raise ValueError(f"Experiment {experiment_id} not found")

        if row[0] != owner_id:
            raise ValueError(f"User {owner_id} is not the owner of experiment {experiment_id}")

        # Revoke share
        revoked = await self.share_repo.revoke_experiment_share(experiment_id, target_user_id)

        if revoked:
            logger.info(
                f"Experiment {experiment_id} access revoked for user {target_user_id} by {owner_id}"
            )
        else:
            logger.warning(
                f"Attempted to revoke non-existent share: experiment {experiment_id}, "
                f"user {target_user_id}"
            )

        return revoked

    async def list_experiment_shares(self, experiment_id: str, owner_id: str) -> List[dict]:
        """List all users who have access to an experiment.

        Args:
            experiment_id: Experiment ID
            owner_id: Owner user ID (requesting the list)

        Returns:
            List of share dictionaries with user info

        Raises:
            ValueError: If experiment not found or user is not owner
        """
        # Validate experiment exists and user is owner
        query = text("SELECT owner_id FROM experiments WHERE id = :experiment_id")
        result = await self.db.execute(query, {"experiment_id": experiment_id})
        row = result.fetchone()

        if not row:
            raise ValueError(f"Experiment {experiment_id} not found")

        if row[0] != owner_id:
            raise ValueError(f"User {owner_id} is not the owner of experiment {experiment_id}")

        # Get shares with user information
        shares = await self.share_repo.get_experiment_shares(experiment_id)

        # Enrich with user information
        result_list = []
        for share in shares:
            user_query = text("""
                SELECT id, email, display_name, profile_picture_url
                FROM users WHERE id = :user_id
            """)
            user_result = await self.db.execute(user_query, {"user_id": share.user_id})
            user_row = user_result.fetchone()

            if user_row:
                result_list.append({
                    "share_id": str(share.id),
                    "user_id": str(share.user_id),
                    "email": user_row[1],
                    "display_name": user_row[2],
                    "profile_picture_url": user_row[3],
                    "permission_level": share.permission_level.value,
                    "granted_at": share.granted_at,
                    "granted_by_id": str(share.granted_by_id),
                })

        return result_list

    async def share_synth_group(
        self,
        synth_group_id: str,
        owner_id: str,
        target_user_id: str,
        permission_level: PermissionLevel,
    ) -> SynthGroupShare:
        """Share synth_group with another user independently.

        Args:
            synth_group_id: Synth group ID to share
            owner_id: Owner user ID (granting access)
            target_user_id: User ID to share with
            permission_level: Permission level to grant

        Returns:
            Created SynthGroupShare

        Raises:
            ValueError: If synth_group not found, user is not owner, or validation fails
        """
        # Validate synth_group exists and user is owner
        query = text("""
            SELECT owner_id FROM synth_groups WHERE id = :synth_group_id
        """)
        result = await self.db.execute(query, {"synth_group_id": synth_group_id})
        row = result.fetchone()

        if not row:
            raise ValueError(f"Synth group {synth_group_id} not found")

        if row[0] != owner_id:
            raise ValueError(f"User {owner_id} is not the owner of synth group {synth_group_id}")

        # Prevent self-sharing
        if owner_id == target_user_id:
            raise ValueError("Cannot share synth group with yourself")

        # Check if target user exists
        user_query = text("SELECT id FROM users WHERE id = :user_id")
        user_result = await self.db.execute(user_query, {"user_id": target_user_id})
        if not user_result.fetchone():
            raise ValueError(f"Target user {target_user_id} not found")

        # Check if share already exists
        existing_shares = await self.share_repo.get_synth_group_shares(synth_group_id)
        for share in existing_shares:
            if str(share.user_id) == target_user_id:
                raise ValueError(
                    f"Synth group {synth_group_id} is already shared with user {target_user_id}"
                )

        # Create synth_group share
        synth_group_share = await self.share_repo.create_synth_group_share(
            synth_group_id=synth_group_id,
            user_id=target_user_id,
            permission_level=permission_level,
            granted_by_id=owner_id,
        )

        return synth_group_share

    async def revoke_synth_group_share(
        self,
        synth_group_id: str,
        owner_id: str,
        target_user_id: str,
    ) -> bool:
        """Revoke synth_group access from user.

        Args:
            synth_group_id: Synth group ID
            owner_id: Owner user ID (revoking access)
            target_user_id: User ID to revoke access from

        Returns:
            True if share was revoked, False if not found

        Raises:
            ValueError: If user is not owner or validation fails
        """
        # Validate synth_group exists and user is owner
        query = text("SELECT owner_id FROM synth_groups WHERE id = :synth_group_id")
        result = await self.db.execute(query, {"synth_group_id": synth_group_id})
        row = result.fetchone()

        if not row:
            raise ValueError(f"Synth group {synth_group_id} not found")

        if row[0] != owner_id:
            raise ValueError(f"User {owner_id} is not the owner of synth group {synth_group_id}")

        # Revoke share
        query = text("""
            DELETE FROM synth_group_shares
            WHERE synth_group_id = :synth_group_id AND user_id = :user_id
        """)
        result = await self.db.execute(query, {
            "synth_group_id": synth_group_id,
            "user_id": target_user_id,
        })
        await self.db.commit()

        return result.rowcount > 0

    async def list_synth_group_shares(
        self,
        synth_group_id: str,
        owner_id: str,
    ) -> List[dict]:
        """List all users who have access to a synth_group.

        Args:
            synth_group_id: Synth group ID
            owner_id: Owner user ID (requesting the list)

        Returns:
            List of share dictionaries with user info

        Raises:
            ValueError: If synth_group not found or user is not owner
        """
        # Validate synth_group exists and user is owner
        query = text("SELECT owner_id FROM synth_groups WHERE id = :synth_group_id")
        result = await self.db.execute(query, {"synth_group_id": synth_group_id})
        row = result.fetchone()

        if not row:
            raise ValueError(f"Synth group {synth_group_id} not found")

        if row[0] != owner_id:
            raise ValueError(f"User {owner_id} is not the owner of synth group {synth_group_id}")

        # Get shares with user information
        shares = await self.share_repo.get_synth_group_shares(synth_group_id)

        # Enrich with user information
        result_list = []
        for share in shares:
            user_query = text("""
                SELECT id, email, display_name, profile_picture_url
                FROM users WHERE id = :user_id
            """)
            user_result = await self.db.execute(user_query, {"user_id": share.user_id})
            user_row = user_result.fetchone()

            if user_row:
                result_list.append({
                    "share_id": str(share.id),
                    "user_id": str(share.user_id),
                    "email": user_row[1],
                    "display_name": user_row[2],
                    "profile_picture_url": user_row[3],
                    "permission_level": share.permission_level.value,
                    "granted_at": share.granted_at,
                    "granted_by_id": str(share.granted_by_id),
                })

        return result_list
