"""Permission service for resource access control.

Handles permission checks for experiments and synth_groups based on
ownership and sharing relationships.
"""
from typing import Optional
from uuid import UUID


class PermissionService:
    """Service for checking resource access permissions."""

    def __init__(self, db_session):
        """Initialize permission service.

        Args:
            db_session: Database session for queries
        """
        self.db = db_session

    def can_access_experiment(self, user_id: str, experiment_id: str) -> bool:
        """Check if user can access experiment.

        User can access if:
        - They own it (owner_id matches)
        - OR they have an ExperimentShare record

        Args:
            user_id: User UUID
            experiment_id: Experiment ID

        Returns:
            True if user can access, False otherwise
        """
        # Check ownership
        from sqlalchemy import text

        query = text("""
            SELECT owner_id::text FROM experiments WHERE id = :experiment_id
        """)
        result = self.db.execute(query, {"experiment_id": experiment_id})
        row = result.fetchone()

        if not row:
            return False

        if row[0] == user_id:
            return True

        # Check shares
        query = text("""
            SELECT id FROM experiment_shares
            WHERE experiment_id = :experiment_id AND user_id = :user_id
        """)
        result = self.db.execute(query, {
            "experiment_id": experiment_id,
            "user_id": user_id
        })
        row = result.fetchone()

        return row is not None

    def can_edit_experiment(self, user_id: str, experiment_id: str) -> bool:
        """Check if user can edit experiment.

        User can edit if:
        - They own it (owner_id matches)
        - OR they have an ExperimentShare with permission_level='editor'

        Args:
            user_id: User UUID
            experiment_id: Experiment ID

        Returns:
            True if user can edit, False otherwise
        """
        # Check ownership
        from sqlalchemy import text

        query = text("""
            SELECT owner_id::text FROM experiments WHERE id = :experiment_id
        """)
        result = self.db.execute(query, {"experiment_id": experiment_id})
        row = result.fetchone()

        if not row:
            return False

        if row[0] == user_id:
            return True

        # Check editor permission
        query = text("""
            SELECT permission_level FROM experiment_shares
            WHERE experiment_id = :experiment_id AND user_id = :user_id
        """)
        result = self.db.execute(query, {
            "experiment_id": experiment_id,
            "user_id": user_id
        })
        row = result.fetchone()

        if row and row[0] == "editor":
            return True

        return False

    def can_access_synth_group(self, user_id: str, synth_group_id: str) -> bool:
        """Check if user can access synth_group.

        User can access if:
        - They own it (owner_id matches)
        - OR they have a SynthGroupShare record

        Args:
            user_id: User UUID
            synth_group_id: Synth group ID

        Returns:
            True if user can access, False otherwise
        """
        from sqlalchemy import text

        # Check ownership
        query = text("""
            SELECT owner_id::text FROM synth_groups WHERE id = :synth_group_id
        """)
        result = self.db.execute(query, {"synth_group_id": synth_group_id})
        row = result.fetchone()

        if not row:
            return False

        if row[0] == user_id:
            return True

        # Check shares
        query = text("""
            SELECT id FROM synth_group_shares
            WHERE synth_group_id = :synth_group_id AND user_id = :user_id
        """)
        result = self.db.execute(query, {
            "synth_group_id": synth_group_id,
            "user_id": user_id
        })
        row = result.fetchone()

        return row is not None

    def can_edit_synth_group(self, user_id: str, synth_group_id: str) -> bool:
        """Check if user can edit synth_group.

        User can edit if:
        - They own it (owner_id matches)
        - OR they have a SynthGroupShare with permission_level='editor'

        Args:
            user_id: User UUID
            synth_group_id: Synth group ID

        Returns:
            True if user can edit, False otherwise
        """
        from sqlalchemy import text

        # Check ownership
        query = text("""
            SELECT owner_id::text FROM synth_groups WHERE id = :synth_group_id
        """)
        result = self.db.execute(query, {"synth_group_id": synth_group_id})
        row = result.fetchone()

        if not row:
            return False

        if row[0] == user_id:
            return True

        # Check editor permission
        query = text("""
            SELECT permission_level FROM synth_group_shares
            WHERE synth_group_id = :synth_group_id AND user_id = :user_id
        """)
        result = self.db.execute(query, {
            "synth_group_id": synth_group_id,
            "user_id": user_id
        })
        row = result.fetchone()

        if row and row[0] == "editor":
            return True

        return False
