"""Sharing service for resource sharing operations.

Handles sharing of experiments and synth_groups between users, including
pending invites for users who haven't registered yet.
"""

from loguru import logger
from sqlalchemy import text
from sqlalchemy.orm import Session

from synth_lab.domain.entities.share import (
    ExperimentShare,
    PendingInvite,
    PermissionLevel,
    SynthGroupShare,
)
from synth_lab.repositories.share_repository import ShareRepository
from synth_lab.repositories.user_repository import UserRepository


class SharingService:
    """Service for sharing resources between users."""

    def __init__(self, db: Session):
        """Initialize sharing service.

        Args:
            db: SQLAlchemy session
        """
        self.db = db
        self.share_repo = ShareRepository(db)
        self.user_repo = UserRepository(db)

    def share_experiment_by_email(
        self,
        experiment_id: str,
        owner_id: str,
        email: str,
    ) -> dict:
        """Share experiment with a user by email.

        If user exists, creates direct share. Otherwise, creates pending invite.
        Automatically shares associated synth_group.

        Args:
            experiment_id: Experiment ID to share
            owner_id: Owner user ID (granting access)
            email: Email of user to share with

        Returns:
            Dict with share info and status ('shared' or 'pending')

        Raises:
            ValueError: If experiment not found, user is not owner, or self-sharing
        """
        email = email.lower().strip()

        # Validate experiment exists and user is owner
        query = text("SELECT owner_id, synth_group_id FROM experiments WHERE id = :experiment_id")
        result = self.db.execute(query, {"experiment_id": experiment_id})
        row = result.fetchone()

        if not row:
            raise ValueError(f"Experiment {experiment_id} not found")
        if row[0] != owner_id:
            raise ValueError(f"User {owner_id} is not the owner of experiment {experiment_id}")

        # Check if owner is trying to share with themselves
        owner = self.user_repo.get_by_id(owner_id)
        if owner and owner.email == email:
            raise ValueError("Cannot share with yourself")

        # Look up target user by email
        target_user = self.user_repo.get_by_email(email)

        if target_user:
            # User exists → direct share
            return self._share_experiment_direct(
                experiment_id=experiment_id,
                owner_id=owner_id,
                target_user_id=str(target_user.id),
                synth_group_id=row[1],
                email=email,
            )
        else:
            # User doesn't exist → pending invite
            return self._create_pending_invite(
                resource_type="experiment",
                resource_id=experiment_id,
                email=email,
                invited_by_id=owner_id,
                synth_group_id=row[1],
            )

    def _share_experiment_direct(
        self,
        experiment_id: str,
        owner_id: str,
        target_user_id: str,
        synth_group_id: str | None,
        email: str,
    ) -> dict:
        """Create direct share for an existing user."""
        # Check if already shared
        existing = self.share_repo.get_experiment_share(experiment_id, target_user_id)
        if existing:
            raise ValueError(f"Experiment already shared with {email}")

        share = self.share_repo.create_experiment_share(
            experiment_id=experiment_id,
            user_id=target_user_id,
            permission_level=PermissionLevel.EDITOR,
            granted_by_id=owner_id,
        )

        logger.info(f"Experiment {experiment_id} shared with {email} (editor) by {owner_id}")

        # Auto-share synth_group
        if synth_group_id:
            self._ensure_synth_group_shared(synth_group_id, target_user_id, owner_id)

        return {
            "status": "shared",
            "share_id": str(share.id),
            "email": email,
            "user_id": target_user_id,
            "permission_level": "editor",
            "granted_at": share.granted_at,
        }

    def _create_pending_invite(
        self,
        resource_type: str,
        resource_id: str,
        email: str,
        invited_by_id: str,
        synth_group_id: str | None = None,
    ) -> dict:
        """Create pending invite for a user who hasn't registered yet."""
        # Check if invite already exists
        existing = self.share_repo.get_pending_invites_for_resource(resource_type, resource_id)
        for inv in existing:
            if inv.invited_email == email:
                raise ValueError(f"Invite already pending for {email}")

        invite = PendingInvite(
            resource_type=resource_type,
            resource_id=resource_id,
            invited_email=email,
            invited_by_id=invited_by_id,
        )
        self.share_repo.create_pending_invite(invite)

        logger.info(f"Pending invite created for {email} on {resource_type} {resource_id}")

        # Also create pending invite for synth_group
        if synth_group_id and resource_type == "experiment":
            existing_sg = self.share_repo.get_pending_invites_for_resource(
                "synth_group", synth_group_id
            )
            already_pending = any(inv.invited_email == email for inv in existing_sg)
            if not already_pending:
                sg_invite = PendingInvite(
                    resource_type="synth_group",
                    resource_id=synth_group_id,
                    invited_email=email,
                    invited_by_id=invited_by_id,
                )
                self.share_repo.create_pending_invite(sg_invite)
                logger.info(f"Pending invite created for {email} on synth_group {synth_group_id}")

        return {
            "status": "pending",
            "invite_id": invite.id,
            "email": email,
            "permission_level": "editor",
            "created_at": invite.created_at,
        }

    def _ensure_synth_group_shared(
        self, synth_group_id: str, target_user_id: str, owner_id: str
    ) -> None:
        """Ensure synth_group is shared with user (skip if already shared)."""
        try:
            existing = self.share_repo.get_synth_group_shares(synth_group_id)
            already_shared = any(str(s.user_id) == target_user_id for s in existing)
            if not already_shared:
                self.share_repo.create_synth_group_share(
                    synth_group_id=synth_group_id,
                    user_id=target_user_id,
                    permission_level=PermissionLevel.EDITOR,
                    granted_by_id=owner_id,
                )
                logger.info(f"Synth group {synth_group_id} auto-shared with user {target_user_id}")
        except Exception as e:
            logger.warning(f"Failed to auto-share synth_group {synth_group_id}: {e}")

    def accept_pending_invites(self, user_id: str, email: str) -> int:
        """Accept all pending invites for a user's email.

        Called during login to convert pending invites into actual shares.

        Args:
            user_id: User ID of the newly logged-in user
            email: User's email

        Returns:
            Number of invites accepted
        """
        email = email.lower().strip()
        invites = self.share_repo.get_pending_invites_by_email(email)

        if not invites:
            return 0

        accepted = 0
        for invite in invites:
            try:
                if invite.resource_type == "experiment":
                    existing = self.share_repo.get_experiment_share(invite.resource_id, user_id)
                    if not existing:
                        self.share_repo.create_experiment_share(
                            experiment_id=invite.resource_id,
                            user_id=user_id,
                            permission_level=PermissionLevel.EDITOR,
                            granted_by_id=invite.invited_by_id,
                        )
                elif invite.resource_type == "synth_group":
                    existing_shares = self.share_repo.get_synth_group_shares(invite.resource_id)
                    already = any(str(s.user_id) == user_id for s in existing_shares)
                    if not already:
                        self.share_repo.create_synth_group_share(
                            synth_group_id=invite.resource_id,
                            user_id=user_id,
                            permission_level=PermissionLevel.EDITOR,
                            granted_by_id=invite.invited_by_id,
                        )

                self.share_repo.delete_pending_invite(invite.id)
                accepted += 1
                logger.info(
                    f"Accepted pending invite for {email}: "
                    f"{invite.resource_type} {invite.resource_id}"
                )
            except Exception as e:
                logger.warning(f"Failed to accept invite {invite.id}: {e}")

        return accepted

    def revoke_experiment_share(
        self,
        experiment_id: str,
        owner_id: str,
        target_email: str,
    ) -> bool:
        """Revoke experiment access by email (handles both active shares and pending invites).

        Args:
            experiment_id: Experiment ID
            owner_id: Owner user ID
            target_email: Email to revoke access from

        Returns:
            True if revoked, False if not found

        Raises:
            ValueError: If user is not owner
        """
        target_email = target_email.lower().strip()

        # Validate ownership
        query = text("SELECT owner_id FROM experiments WHERE id = :experiment_id")
        result = self.db.execute(query, {"experiment_id": experiment_id})
        row = result.fetchone()
        if not row:
            raise ValueError(f"Experiment {experiment_id} not found")
        if row[0] != owner_id:
            raise ValueError(f"User {owner_id} is not the owner of experiment {experiment_id}")

        # Try revoking active share
        target_user = self.user_repo.get_by_email(target_email)
        if target_user:
            revoked = self.share_repo.revoke_experiment_share(experiment_id, str(target_user.id))
            if revoked:
                logger.info(f"Revoked experiment {experiment_id} share for {target_email}")
                return True

        # Try revoking pending invite
        revoked = self.share_repo.revoke_pending_invite("experiment", experiment_id, target_email)
        if revoked:
            logger.info(f"Revoked pending invite for {target_email} on experiment {experiment_id}")
            return True

        return False

    def list_experiment_shares(self, experiment_id: str, requester_id: str) -> dict:
        """List all access for an experiment (active shares + pending invites).

        Args:
            experiment_id: Experiment ID
            requester_id: User requesting (must be owner)

        Returns:
            Dict with 'shares' (active) and 'pending' (invites) lists

        Raises:
            ValueError: If not owner
        """
        query = text("SELECT owner_id FROM experiments WHERE id = :experiment_id")
        result = self.db.execute(query, {"experiment_id": experiment_id})
        row = result.fetchone()
        if not row:
            raise ValueError(f"Experiment {experiment_id} not found")
        if row[0] != requester_id:
            raise ValueError(f"User {requester_id} is not the owner of experiment {experiment_id}")

        # Active shares
        shares = self.share_repo.get_experiment_shares(experiment_id)
        shares_list = []
        for share in shares:
            user = self.user_repo.get_by_id(share.user_id)
            if user:
                shares_list.append({
                    "share_id": str(share.id),
                    "user_id": str(share.user_id),
                    "email": user.email,
                    "display_name": user.display_name,
                    "profile_picture_url": user.profile_picture_url,
                    "permission_level": share.permission_level.value,
                    "granted_at": share.granted_at,
                    "status": "active",
                })

        # Pending invites
        invites = self.share_repo.get_pending_invites_for_resource("experiment", experiment_id)
        pending_list = [
            {
                "invite_id": inv.id,
                "email": inv.invited_email,
                "permission_level": "editor",
                "created_at": inv.created_at,
                "status": "pending",
            }
            for inv in invites
        ]

        return {
            "shares": shares_list,
            "pending": pending_list,
        }

    # ── Synth Group sharing ─────────────────────────────────────────────

    def share_synth_group_by_email(
        self,
        synth_group_id: str,
        owner_id: str,
        email: str,
    ) -> dict:
        """Share synth_group with a user by email."""
        email = email.lower().strip()

        query = text("SELECT owner_id FROM synth_groups WHERE id = :synth_group_id")
        result = self.db.execute(query, {"synth_group_id": synth_group_id})
        row = result.fetchone()
        if not row:
            raise ValueError(f"Synth group {synth_group_id} not found")
        if row[0] != owner_id:
            raise ValueError(f"User {owner_id} is not the owner of synth group {synth_group_id}")

        owner = self.user_repo.get_by_id(owner_id)
        if owner and owner.email == email:
            raise ValueError("Cannot share with yourself")

        target_user = self.user_repo.get_by_email(email)

        if target_user:
            existing = self.share_repo.get_synth_group_shares(synth_group_id)
            already = any(str(s.user_id) == str(target_user.id) for s in existing)
            if already:
                raise ValueError(f"Synth group already shared with {email}")

            share = self.share_repo.create_synth_group_share(
                synth_group_id=synth_group_id,
                user_id=str(target_user.id),
                permission_level=PermissionLevel.EDITOR,
                granted_by_id=owner_id,
            )
            return {
                "status": "shared",
                "share_id": str(share.id),
                "email": email,
                "user_id": str(target_user.id),
                "permission_level": "editor",
                "granted_at": share.granted_at,
            }
        else:
            return self._create_pending_invite(
                resource_type="synth_group",
                resource_id=synth_group_id,
                email=email,
                invited_by_id=owner_id,
            )

    def revoke_synth_group_share(
        self,
        synth_group_id: str,
        owner_id: str,
        target_email: str,
    ) -> bool:
        """Revoke synth_group access by email."""
        target_email = target_email.lower().strip()

        query = text("SELECT owner_id FROM synth_groups WHERE id = :synth_group_id")
        result = self.db.execute(query, {"synth_group_id": synth_group_id})
        row = result.fetchone()
        if not row:
            raise ValueError(f"Synth group {synth_group_id} not found")
        if row[0] != owner_id:
            raise ValueError(f"User {owner_id} is not the owner of synth group {synth_group_id}")

        target_user = self.user_repo.get_by_email(target_email)
        if target_user:
            query = text("""
                DELETE FROM synth_group_shares
                WHERE synth_group_id = :synth_group_id AND user_id = :user_id
            """)
            result = self.db.execute(query, {
                "synth_group_id": synth_group_id,
                "user_id": str(target_user.id),
            })
            self.db.commit()
            if result.rowcount > 0:
                return True

        return self.share_repo.revoke_pending_invite("synth_group", synth_group_id, target_email)

    def list_synth_group_shares(self, synth_group_id: str, requester_id: str) -> dict:
        """List all access for a synth_group."""
        query = text("SELECT owner_id FROM synth_groups WHERE id = :synth_group_id")
        result = self.db.execute(query, {"synth_group_id": synth_group_id})
        row = result.fetchone()
        if not row:
            raise ValueError(f"Synth group {synth_group_id} not found")
        if row[0] != requester_id:
            raise ValueError(
                f"User {requester_id} is not the owner of synth group {synth_group_id}"
            )

        shares = self.share_repo.get_synth_group_shares(synth_group_id)
        shares_list = []
        for share in shares:
            user = self.user_repo.get_by_id(share.user_id)
            if user:
                shares_list.append({
                    "share_id": str(share.id),
                    "user_id": str(share.user_id),
                    "email": user.email,
                    "display_name": user.display_name,
                    "profile_picture_url": user.profile_picture_url,
                    "permission_level": share.permission_level.value,
                    "granted_at": share.granted_at,
                    "status": "active",
                })

        invites = self.share_repo.get_pending_invites_for_resource("synth_group", synth_group_id)
        pending_list = [
            {
                "invite_id": inv.id,
                "email": inv.invited_email,
                "permission_level": "editor",
                "created_at": inv.created_at,
                "status": "pending",
            }
            for inv in invites
        ]

        return {
            "shares": shares_list,
            "pending": pending_list,
        }

    # ── Legacy methods (kept for backward compat with permission service) ──

    def share_experiment(
        self,
        experiment_id: str,
        owner_id: str,
        target_user_id: str,
        permission_level: PermissionLevel,
    ) -> ExperimentShare:
        """Share experiment with another user by user_id (legacy)."""
        query = text("SELECT owner_id, synth_group_id FROM experiments WHERE id = :experiment_id")
        result = self.db.execute(query, {"experiment_id": experiment_id})
        row = result.fetchone()
        if not row:
            raise ValueError(f"Experiment {experiment_id} not found")
        if row[0] != owner_id:
            raise ValueError(f"User {owner_id} is not the owner of experiment {experiment_id}")
        if owner_id == target_user_id:
            raise ValueError("Cannot share experiment with yourself")

        user_query = text("SELECT id FROM users WHERE id = :user_id")
        user_result = self.db.execute(user_query, {"user_id": target_user_id})
        if not user_result.fetchone():
            raise ValueError(f"Target user {target_user_id} not found")

        existing = self.share_repo.get_experiment_share(experiment_id, target_user_id)
        if existing:
            raise ValueError(
                f"Experiment {experiment_id} is already shared with user {target_user_id}"
            )

        share = self.share_repo.create_experiment_share(
            experiment_id=experiment_id,
            user_id=target_user_id,
            permission_level=permission_level,
            granted_by_id=owner_id,
        )

        synth_group_id = row[1]
        if synth_group_id:
            self._ensure_synth_group_shared(synth_group_id, target_user_id, owner_id)

        return share

    def share_synth_group(
        self,
        synth_group_id: str,
        owner_id: str,
        target_user_id: str,
        permission_level: PermissionLevel,
    ) -> SynthGroupShare:
        """Share synth_group with another user by user_id (legacy)."""
        query = text("SELECT owner_id FROM synth_groups WHERE id = :synth_group_id")
        result = self.db.execute(query, {"synth_group_id": synth_group_id})
        row = result.fetchone()
        if not row:
            raise ValueError(f"Synth group {synth_group_id} not found")
        if row[0] != owner_id:
            raise ValueError(f"User {owner_id} is not the owner of synth group {synth_group_id}")
        if owner_id == target_user_id:
            raise ValueError("Cannot share synth group with yourself")

        return self.share_repo.create_synth_group_share(
            synth_group_id=synth_group_id,
            user_id=target_user_id,
            permission_level=permission_level,
            granted_by_id=owner_id,
        )
