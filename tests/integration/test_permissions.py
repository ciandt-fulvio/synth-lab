"""Integration tests for permission checks.

Tests permission logic with real database interactions.
"""
from uuid import uuid4

import pytest

from synth_lab.domain.entities.share import PermissionLevel
from synth_lab.repositories.experiment_repository import ExperimentRepository
from synth_lab.repositories.synth_group_repository import SynthGroupRepository
from synth_lab.services.experiment_service import ExperimentService
from synth_lab.services.permission_service import PermissionService
from synth_lab.services.synth_group_service import SynthGroupService


@pytest.mark.slow
class TestPermissionChecksIntegration:
    """Test permission checks on owned resources - T070."""

    def test_owner_has_full_access_to_experiment(self, db_session, create_test_user):
        """Should grant full access to experiment owner.

        Integration test covering:
        - Owner can access experiment
        - Owner can edit experiment
        """
        # Setup
        exp_repository = ExperimentRepository(db_session)
        experiment_service = ExperimentService(exp_repository)
        permission_service = PermissionService(db_session)
        owner_id = create_test_user(email="owner_exp_access@example.com")

        # Create experiment with owner
        created_exp = experiment_service.create_experiment(
            name="Owned Experiment",
            hypothesis="Test",
            synth_group_id="grp_00000001",
            owner_id=owner_id,
        )

        # Verify owner can access
        can_access = permission_service.can_access_experiment(owner_id, created_exp.id)
        assert can_access is True

        # Verify owner can edit
        can_edit = permission_service.can_edit_experiment(owner_id, created_exp.id)
        assert can_edit is True

    def test_non_owner_cannot_access_experiment(self, db_session, create_test_user):
        """Should deny access to non-owner without share.

        Integration test covering:
        - Non-owner cannot access
        - Non-owner cannot edit
        """
        # Setup
        exp_repository = ExperimentRepository(db_session)
        experiment_service = ExperimentService(exp_repository)
        permission_service = PermissionService(db_session)
        owner_id = create_test_user(email="owner_exp_private@example.com")
        other_user_id = create_test_user(email="other_user_exp_private@example.com")

        # Create experiment
        created_exp = experiment_service.create_experiment(
            name="Private Experiment",
            hypothesis="Test",
            synth_group_id="grp_00000001",
            owner_id=owner_id,
        )

        # Verify other user cannot access
        can_access = permission_service.can_access_experiment(other_user_id, created_exp.id)
        assert can_access is False

        # Verify other user cannot edit
        can_edit = permission_service.can_edit_experiment(other_user_id, created_exp.id)
        assert can_edit is False

    def test_shared_user_can_access_experiment(self, db_session, create_test_user):
        """Should grant access to user with share.

        Integration test covering:
        - Shared user can access
        - Viewer cannot edit
        - Editor can edit
        """
        from sqlalchemy import text

        # Setup
        exp_repository = ExperimentRepository(db_session)
        experiment_service = ExperimentService(exp_repository)
        permission_service = PermissionService(db_session)
        owner_id = create_test_user(email="owner_exp_shared@example.com")
        viewer_id = create_test_user(email="viewer_exp_shared@example.com")
        editor_id = create_test_user(email="editor_exp_shared@example.com")

        # Create experiment
        created_exp = experiment_service.create_experiment(
            name="Shared Experiment",
            hypothesis="Test",
            synth_group_id="grp_00000001",
            owner_id=owner_id,
        )

        # Share with viewer - directly insert into shares table
        from datetime import UTC, datetime
        granted_at = datetime.now(UTC).isoformat()
        db_session.execute(
            text("""
                INSERT INTO experiment_shares (id, experiment_id, user_id, permission_level, granted_by_id, granted_at)
                VALUES (:id, :experiment_id, :user_id, :permission_level, :granted_by_id, :granted_at)
            """),
            {
                "id": str(uuid4()),
                "experiment_id": created_exp.id,
                "user_id": viewer_id,
                "permission_level": PermissionLevel.VIEWER.value,
                "granted_by_id": owner_id,
                "granted_at": granted_at,
            }
        )

        # Share with editor
        db_session.execute(
            text("""
                INSERT INTO experiment_shares (id, experiment_id, user_id, permission_level, granted_by_id, granted_at)
                VALUES (:id, :experiment_id, :user_id, :permission_level, :granted_by_id, :granted_at)
            """),
            {
                "id": str(uuid4()),
                "experiment_id": created_exp.id,
                "user_id": editor_id,
                "permission_level": PermissionLevel.EDITOR.value,
                "granted_by_id": owner_id,
                "granted_at": granted_at,
            }
        )
        db_session.flush()

        # Verify viewer can access but not edit
        can_access = permission_service.can_access_experiment(viewer_id, created_exp.id)
        assert can_access is True

        can_edit = permission_service.can_edit_experiment(viewer_id, created_exp.id)
        assert can_edit is False

        # Verify editor can access and edit
        can_access = permission_service.can_access_experiment(editor_id, created_exp.id)
        assert can_access is True

        can_edit = permission_service.can_edit_experiment(editor_id, created_exp.id)
        assert can_edit is True

    def test_owner_has_full_access_to_synth_group(self, db_session, create_test_user):
        """Should grant full access to synth_group owner.

        Integration test covering:
        - Owner can access synth_group
        - Owner can edit synth_group
        """
        # Setup
        sg_repository = SynthGroupRepository(db_session)
        synth_group_service = SynthGroupService(sg_repository)
        permission_service = PermissionService(db_session)
        owner_id = create_test_user(email="owner_sg_access@example.com")

        # Create synth_group with owner
        created_group = synth_group_service.create_group(
            name="Owned Group",
            owner_id=owner_id,
        )

        # Verify owner can access
        can_access = permission_service.can_access_synth_group(owner_id, created_group.id)
        assert can_access is True

        # Verify owner can edit
        can_edit = permission_service.can_edit_synth_group(owner_id, created_group.id)
        assert can_edit is True

    def test_non_owner_cannot_access_synth_group(self, db_session, create_test_user):
        """Should deny access to non-owner without share.

        Integration test covering:
        - Non-owner cannot access
        - Non-owner cannot edit
        """
        # Setup
        sg_repository = SynthGroupRepository(db_session)
        synth_group_service = SynthGroupService(sg_repository)
        permission_service = PermissionService(db_session)
        owner_id = create_test_user(email="owner_sg_private@example.com")
        other_user_id = create_test_user(email="other_user_sg_private@example.com")

        # Create synth_group
        created_group = synth_group_service.create_group(
            name="Private Group",
            owner_id=owner_id,
        )

        # Verify other user cannot access
        can_access = permission_service.can_access_synth_group(other_user_id, created_group.id)
        assert can_access is False

        # Verify other user cannot edit
        can_edit = permission_service.can_edit_synth_group(other_user_id, created_group.id)
        assert can_edit is False
