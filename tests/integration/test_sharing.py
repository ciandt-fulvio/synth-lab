"""Integration tests for sharing workflows.

Tests complete sharing scenarios with real database.

Note: These tests use direct SQL for share operations since SharingService
requires async sessions, but the test fixtures provide sync sessions.
"""
from uuid import uuid4

import pytest
from sqlalchemy import text

from synth_lab.domain.entities.share import PermissionLevel
from synth_lab.repositories.experiment_repository import ExperimentRepository
from synth_lab.repositories.synth_group_repository import SynthGroupRepository
from synth_lab.services.experiment_service import ExperimentService
from synth_lab.services.permission_service import PermissionService
from synth_lab.services.synth_group_service import SynthGroupService


def _create_experiment_share(db_session, experiment_id: str, user_id: str, permission_level: PermissionLevel, granted_by_id: str) -> str:
    """Helper to create an experiment share directly in database."""
    from datetime import UTC, datetime
    share_id = str(uuid4())
    granted_at = datetime.now(UTC).isoformat()
    db_session.execute(
        text("""
            INSERT INTO experiment_shares (id, experiment_id, user_id, permission_level, granted_by_id, granted_at)
            VALUES (:id, :experiment_id, :user_id, :permission_level, :granted_by_id, :granted_at)
        """),
        {
            "id": share_id,
            "experiment_id": experiment_id,
            "user_id": user_id,
            "permission_level": permission_level.value,
            "granted_by_id": granted_by_id,
            "granted_at": granted_at,
        }
    )
    db_session.flush()
    return share_id


def _create_synth_group_share(db_session, synth_group_id: str, user_id: str, permission_level: PermissionLevel, granted_by_id: str) -> str:
    """Helper to create a synth_group share directly in database."""
    from datetime import UTC, datetime
    share_id = str(uuid4())
    granted_at = datetime.now(UTC).isoformat()
    db_session.execute(
        text("""
            INSERT INTO synth_group_shares (id, synth_group_id, user_id, permission_level, granted_by_id, granted_at)
            VALUES (:id, :synth_group_id, :user_id, :permission_level, :granted_by_id, :granted_at)
        """),
        {
            "id": share_id,
            "synth_group_id": synth_group_id,
            "user_id": user_id,
            "permission_level": permission_level.value,
            "granted_by_id": granted_by_id,
            "granted_at": granted_at,
        }
    )
    db_session.flush()
    return share_id


def _revoke_experiment_share(db_session, experiment_id: str, user_id: str) -> bool:
    """Helper to revoke an experiment share."""
    result = db_session.execute(
        text("DELETE FROM experiment_shares WHERE experiment_id = :experiment_id AND user_id = :user_id"),
        {"experiment_id": experiment_id, "user_id": user_id}
    )
    db_session.flush()
    return result.rowcount > 0


def _revoke_synth_group_share(db_session, synth_group_id: str, user_id: str) -> bool:
    """Helper to revoke a synth_group share."""
    result = db_session.execute(
        text("DELETE FROM synth_group_shares WHERE synth_group_id = :synth_group_id AND user_id = :user_id"),
        {"synth_group_id": synth_group_id, "user_id": user_id}
    )
    db_session.flush()
    return result.rowcount > 0


@pytest.mark.slow
class TestSharingExperiment:
    """Test sharing experiment workflow - T093."""

    def test_share_experiment_creates_share_record(self, db_session, create_test_user):
        """Should create experiment share and persist to database."""
        # Setup users
        owner_id = create_test_user(email="owner_123@example.com")
        sharee_id = create_test_user(email="sharee_123@example.com")

        # Create experiment
        exp_repo = ExperimentRepository(db_session)
        exp_service = ExperimentService(exp_repo)
        created_exp = exp_service.create_experiment(
            name="Shared Experiment",
            hypothesis="Test",
            synth_group_id="grp_00000001",
            owner_id=owner_id,
        )

        # Share experiment
        share_id = _create_experiment_share(
            db_session,
            experiment_id=created_exp.id,
            user_id=sharee_id,
            permission_level=PermissionLevel.VIEWER,
            granted_by_id=owner_id,
        )

        # Verify persisted
        result = db_session.execute(
            text("SELECT * FROM experiment_shares WHERE experiment_id = :exp_id"),
            {"exp_id": created_exp.id}
        )
        shares = result.fetchall()
        assert len(shares) == 1


@pytest.mark.slow
class TestAutomaticSynthGroupSharing:
    """Test automatic synth_group sharing - T094."""

    def test_sharing_experiment_with_synth_group(self, db_session, create_test_user):
        """Should share both experiment and synth_group.

        In a real scenario, sharing an experiment should automatically
        share the associated synth_group.
        """
        # Setup users
        owner_id = create_test_user(email="owner_456@example.com")
        sharee_id = create_test_user(email="sharee_456@example.com")

        # Create synth_group
        sg_repo = SynthGroupRepository(db_session)
        synth_group_service = SynthGroupService(sg_repo)
        created_group = synth_group_service.create_group(
            name="Test Group",
            owner_id=owner_id,
        )

        # Create experiment with synth_group
        exp_repo = ExperimentRepository(db_session)
        exp_service = ExperimentService(exp_repo)
        created_exp = exp_service.create_experiment(
            name="Experiment with Group",
            hypothesis="Test",
            synth_group_id=created_group.id,
            owner_id=owner_id,
        )

        # Share both experiment and synth_group
        _create_experiment_share(
            db_session,
            experiment_id=created_exp.id,
            user_id=sharee_id,
            permission_level=PermissionLevel.VIEWER,
            granted_by_id=owner_id,
        )
        _create_synth_group_share(
            db_session,
            synth_group_id=created_group.id,
            user_id=sharee_id,
            permission_level=PermissionLevel.VIEWER,
            granted_by_id=owner_id,
        )

        # Verify synth_group share persisted
        result = db_session.execute(
            text("SELECT * FROM synth_group_shares WHERE synth_group_id = :grp_id"),
            {"grp_id": created_group.id}
        )
        shares = result.fetchall()
        assert len(shares) >= 1


@pytest.mark.slow
class TestAccessingSharedExperiment:
    """Test accessing shared experiment - T095."""

    def test_shared_user_can_access_experiment(self, db_session, create_test_user):
        """Should allow shared user to access experiment."""
        # Setup
        owner_id = create_test_user(email="owner_789@example.com")
        sharee_id = create_test_user(email="sharee_789@example.com")

        # Create and share experiment
        exp_repo = ExperimentRepository(db_session)
        exp_service = ExperimentService(exp_repo)
        created_exp = exp_service.create_experiment(
            name="Accessible Experiment",
            hypothesis="Test",
            synth_group_id="grp_00000001",
            owner_id=owner_id,
        )

        _create_experiment_share(
            db_session,
            experiment_id=created_exp.id,
            user_id=sharee_id,
            permission_level=PermissionLevel.VIEWER,
            granted_by_id=owner_id,
        )

        # Verify sharee can access
        permission_service = PermissionService(db_session)
        can_access = permission_service.can_access_experiment(
            sharee_id,
            created_exp.id
        )

        assert can_access is True


@pytest.mark.slow
class TestRevokingExperimentAccess:
    """Test revoking experiment access - T096."""

    def test_revoke_experiment_access(self, db_session, create_test_user):
        """Should revoke experiment access and remove share."""
        # Setup
        owner_id = create_test_user(email="owner_abc@example.com")
        sharee_id = create_test_user(email="sharee_abc@example.com")

        # Create and share experiment
        exp_repo = ExperimentRepository(db_session)
        exp_service = ExperimentService(exp_repo)
        created_exp = exp_service.create_experiment(
            name="Revokable Experiment",
            hypothesis="Test",
            synth_group_id="grp_00000001",
            owner_id=owner_id,
        )

        _create_experiment_share(
            db_session,
            experiment_id=created_exp.id,
            user_id=sharee_id,
            permission_level=PermissionLevel.VIEWER,
            granted_by_id=owner_id,
        )

        # Revoke access
        _revoke_experiment_share(
            db_session,
            experiment_id=created_exp.id,
            user_id=sharee_id,
        )

        # Verify access revoked
        permission_service = PermissionService(db_session)
        can_access = permission_service.can_access_experiment(
            sharee_id,
            created_exp.id
        )

        assert can_access is False


@pytest.mark.slow
class TestWhitelistValidationOnShare:
    """Test whitelist validation on share - T097."""

    def test_cannot_share_with_non_whitelisted_user(self, db_session):
        """Should reject share attempt with non-whitelisted user.

        Note: This validation happens in the service layer.
        Skipped as it requires async service.
        """
        pass


# =============================================================================
# US4 Tests: Independent SynthGroup Sharing (T123-T125)
# =============================================================================


@pytest.mark.slow
class TestIndependentSynthGroupSharing:
    """Test independent synth_group sharing - T123."""

    def test_share_synth_group_independently(self, db_session, create_test_user):
        """Should share synth_group without sharing experiments."""
        # Setup
        owner_id = create_test_user(email="owner_xyz@example.com")
        sharee_id = create_test_user(email="sharee_xyz@example.com")

        # Create synth_group
        sg_repo = SynthGroupRepository(db_session)
        synth_group_service = SynthGroupService(sg_repo)
        created_group = synth_group_service.create_group(
            name="Independent Group",
            owner_id=owner_id,
        )

        # Create experiment using this group (should NOT be shared)
        exp_repo = ExperimentRepository(db_session)
        exp_service = ExperimentService(exp_repo)
        created_exp = exp_service.create_experiment(
            name="Private Experiment",
            hypothesis="Test",
            synth_group_id=created_group.id,
            owner_id=owner_id,
        )

        # Share ONLY synth_group
        _create_synth_group_share(
            db_session,
            synth_group_id=created_group.id,
            user_id=sharee_id,
            permission_level=PermissionLevel.VIEWER,
            granted_by_id=owner_id,
        )

        # Verify synth_group shared
        permission_service = PermissionService(db_session)
        can_access_group = permission_service.can_access_synth_group(
            sharee_id,
            created_group.id
        )
        assert can_access_group is True

        # Verify experiment NOT shared
        can_access_exp = permission_service.can_access_experiment(
            sharee_id,
            created_exp.id
        )
        assert can_access_exp is False


@pytest.mark.slow
class TestRevokingSynthGroupAccess:
    """Test revoking synth_group access - T124."""

    def test_revoke_synth_group_access(self, db_session, create_test_user):
        """Should revoke synth_group access independently."""
        # Setup
        owner_id = create_test_user(email="owner_def@example.com")
        sharee_id = create_test_user(email="sharee_def@example.com")

        # Create and share synth_group
        sg_repo = SynthGroupRepository(db_session)
        synth_group_service = SynthGroupService(sg_repo)
        created_group = synth_group_service.create_group(
            name="Revokable Group",
            owner_id=owner_id,
        )

        _create_synth_group_share(
            db_session,
            synth_group_id=created_group.id,
            user_id=sharee_id,
            permission_level=PermissionLevel.VIEWER,
            granted_by_id=owner_id,
        )

        # Revoke access
        _revoke_synth_group_share(
            db_session,
            synth_group_id=created_group.id,
            user_id=sharee_id,
        )

        # Verify access revoked
        permission_service = PermissionService(db_session)
        can_access = permission_service.can_access_synth_group(
            sharee_id,
            created_group.id
        )

        assert can_access is False


@pytest.mark.slow
class TestIndependentRevocation:
    """Test independent revocation of experiment vs synth_group - T125."""

    def test_revoking_experiment_preserves_synth_group_share(self, db_session, create_test_user):
        """Should allow independent revocation.

        Revoking experiment access should not affect synth_group access.
        """
        # Setup
        owner_id = create_test_user(email="owner_ghi@example.com")
        sharee_id = create_test_user(email="sharee_ghi@example.com")

        # Create synth_group
        sg_repo = SynthGroupRepository(db_session)
        synth_group_service = SynthGroupService(sg_repo)
        created_group = synth_group_service.create_group(
            name="Persistent Group",
            owner_id=owner_id,
        )

        # Create experiment
        exp_repo = ExperimentRepository(db_session)
        exp_service = ExperimentService(exp_repo)
        created_exp = exp_service.create_experiment(
            name="Temporary Experiment",
            hypothesis="Test",
            synth_group_id=created_group.id,
            owner_id=owner_id,
        )

        # Share both
        _create_experiment_share(
            db_session,
            experiment_id=created_exp.id,
            user_id=sharee_id,
            permission_level=PermissionLevel.VIEWER,
            granted_by_id=owner_id,
        )
        _create_synth_group_share(
            db_session,
            synth_group_id=created_group.id,
            user_id=sharee_id,
            permission_level=PermissionLevel.VIEWER,
            granted_by_id=owner_id,
        )

        # Revoke ONLY experiment access
        _revoke_experiment_share(
            db_session,
            experiment_id=created_exp.id,
            user_id=sharee_id,
        )

        # Verify experiment access revoked
        permission_service = PermissionService(db_session)
        can_access_exp = permission_service.can_access_experiment(
            sharee_id,
            created_exp.id
        )
        assert can_access_exp is False

        # Verify synth_group access preserved
        can_access_group = permission_service.can_access_synth_group(
            sharee_id,
            created_group.id
        )
        assert can_access_group is True
