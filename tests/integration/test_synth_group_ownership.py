"""Integration tests for synth_group ownership.

Tests ownership assignment and persistence with real database.
"""
import pytest
from uuid import uuid4

from synth_lab.services.synth_group_service import SynthGroupService
from synth_lab.repositories.synth_group_repository import SynthGroupRepository


@pytest.mark.slow
class TestSynthGroupOwnership:
    """Test synth_group ownership integration - T069."""

    def test_create_synth_group_with_owner(self, db_session, create_test_user):
        """Should create synth_group with owner_id and persist to database.

        Integration test covering:
        - Owner assignment during creation
        - Persistence to database
        - Retrieval with owner_id
        """
        # Setup
        repository = SynthGroupRepository(db_session)
        synth_group_service = SynthGroupService(repository)
        owner_id = create_test_user(email="owner_synth_group@example.com")

        # Create synth_group with owner using correct service method
        created_group = synth_group_service.create_group(
            name="Owned Group",
            owner_id=owner_id,
        )

        # Verify owner persisted to database
        # Note: SynthGroupSummary doesn't expose owner_id, so we query directly
        from sqlalchemy import text
        query = text("SELECT owner_id FROM synth_groups WHERE id = :id")
        result = db_session.execute(query, {"id": created_group.id})
        row = result.fetchone()

        assert row is not None
        assert row[0] == owner_id

    def test_retrieve_synth_groups_by_owner(self, db_session, create_test_user):
        """Should retrieve all synth_groups owned by a user.

        Integration test covering:
        - Multiple synth_groups with same owner
        - Filtering by owner_id
        """
        # Setup
        repository = SynthGroupRepository(db_session)
        synth_group_service = SynthGroupService(repository)
        owner_id = create_test_user(email="owner_retrieve@example.com")
        other_owner_id = create_test_user(email="other_owner_retrieve@example.com")

        # Create synth_groups for owner
        synth_group_service.create_group(
            name="Group 1",
            owner_id=owner_id,
        )
        synth_group_service.create_group(
            name="Group 2",
            owner_id=owner_id,
        )

        # Create synth_group for different owner
        synth_group_service.create_group(
            name="Other Group",
            owner_id=other_owner_id,
        )

        # Query synth_groups by owner
        from sqlalchemy import text
        query = text("SELECT id FROM synth_groups WHERE owner_id = :owner_id")
        result = db_session.execute(query, {"owner_id": owner_id})
        rows = result.fetchall()

        # Should have exactly 2 synth_groups
        assert len(rows) == 2
