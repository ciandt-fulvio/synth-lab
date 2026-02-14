"""Unit tests for PermissionService.

Tests permission checking logic with mocked dependencies.
"""
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from synth_lab.services.permission_service import PermissionService


@pytest.fixture
def mock_db_session():
    """Mock database session (synchronous)."""
    session = MagicMock()
    return session


@pytest.fixture
def permission_service(mock_db_session):
    """Create PermissionService with mocked database."""
    return PermissionService(mock_db_session)


# =============================================================================
# US2 Tests: Permission Checks (T065-T067)
# =============================================================================


class TestCanAccessExperiment:
    """Test can_access_experiment permission check - T065."""

    def test_owner_can_access(self, permission_service, mock_db_session):
        """Should return True when user is the owner."""
        user_id = str(uuid4())
        experiment_id = "exp_12345678"

        # Mock database to return owner_id matching user_id
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (user_id,)  # owner_id
        mock_db_session.execute.return_value = mock_result

        can_access = permission_service.can_access_experiment(user_id, experiment_id)

        assert can_access is True

    def test_non_owner_without_share_cannot_access(self, permission_service, mock_db_session):
        """Should return False when user is not owner and has no share."""
        user_id = str(uuid4())
        other_user_id = str(uuid4())
        experiment_id = "exp_12345678"

        # Mock: experiment owned by other_user, no share exists
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock_result = MagicMock()
            if call_count == 1:  # First call: check ownership
                mock_result.fetchone.return_value = (other_user_id,)
            else:  # Second call: check shares
                mock_result.fetchone.return_value = None
            return mock_result

        mock_db_session.execute.side_effect = side_effect

        can_access = permission_service.can_access_experiment(user_id, experiment_id)

        assert can_access is False

    def test_user_with_share_can_access(self, permission_service, mock_db_session):
        """Should return True when user has a share (even if not owner)."""
        user_id = str(uuid4())
        other_user_id = str(uuid4())
        experiment_id = "exp_12345678"

        # Mock: experiment owned by other_user, but share exists for user_id
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock_result = MagicMock()
            if call_count == 1:  # First call: check ownership
                mock_result.fetchone.return_value = (other_user_id,)
            else:  # Second call: check shares
                share_id = str(uuid4())
                mock_result.fetchone.return_value = (share_id,)  # Share exists
            return mock_result

        mock_db_session.execute.side_effect = side_effect

        can_access = permission_service.can_access_experiment(user_id, experiment_id)

        assert can_access is True

    def test_experiment_not_found_returns_false(self, permission_service, mock_db_session):
        """Should return False when experiment doesn't exist."""
        user_id = str(uuid4())
        experiment_id = "exp_nonexistent"

        # Mock database to return no results
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_db_session.execute.return_value = mock_result

        can_access = permission_service.can_access_experiment(user_id, experiment_id)

        assert can_access is False


class TestCanEditExperiment:
    """Test can_edit_experiment permission check - T066."""

    def test_owner_can_edit(self, permission_service, mock_db_session):
        """Should return True when user is the owner."""
        user_id = str(uuid4())
        experiment_id = "exp_12345678"

        # Mock database to return owner_id matching user_id
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (user_id,)
        mock_db_session.execute.return_value = mock_result

        can_edit = permission_service.can_edit_experiment(user_id, experiment_id)

        assert can_edit is True

    def test_viewer_cannot_edit(self, permission_service, mock_db_session):
        """Should return False when user has viewer permission."""
        user_id = str(uuid4())
        other_user_id = str(uuid4())
        experiment_id = "exp_12345678"

        # Mock: experiment owned by other_user, user has viewer permission
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock_result = MagicMock()
            if call_count == 1:  # First call: check ownership
                mock_result.fetchone.return_value = (other_user_id,)
            else:  # Second call: check editor permission
                mock_result.fetchone.return_value = ("viewer",)
            return mock_result

        mock_db_session.execute.side_effect = side_effect

        can_edit = permission_service.can_edit_experiment(user_id, experiment_id)

        assert can_edit is False

    def test_editor_can_edit(self, permission_service, mock_db_session):
        """Should return True when user has editor permission."""
        user_id = str(uuid4())
        other_user_id = str(uuid4())
        experiment_id = "exp_12345678"

        # Mock: experiment owned by other_user, user has editor permission
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock_result = MagicMock()
            if call_count == 1:  # First call: check ownership
                mock_result.fetchone.return_value = (other_user_id,)
            else:  # Second call: check editor permission
                mock_result.fetchone.return_value = ("editor",)
            return mock_result

        mock_db_session.execute.side_effect = side_effect

        can_edit = permission_service.can_edit_experiment(user_id, experiment_id)

        assert can_edit is True

    def test_no_permission_cannot_edit(self, permission_service, mock_db_session):
        """Should return False when user has no share."""
        user_id = str(uuid4())
        other_user_id = str(uuid4())
        experiment_id = "exp_12345678"

        # Mock: experiment owned by other_user, no share
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock_result = MagicMock()
            if call_count == 1:  # First call: check ownership
                mock_result.fetchone.return_value = (other_user_id,)
            else:  # Second call: check editor permission
                mock_result.fetchone.return_value = None
            return mock_result

        mock_db_session.execute.side_effect = side_effect

        can_edit = permission_service.can_edit_experiment(user_id, experiment_id)

        assert can_edit is False


class TestCanAccessSynthGroup:
    """Test can_access_synth_group permission check - T067."""

    def test_owner_can_access(self, permission_service, mock_db_session):
        """Should return True when user is the owner."""
        user_id = str(uuid4())
        synth_group_id = "grp_abcd1234"

        # Mock database to return owner_id matching user_id
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (user_id,)
        mock_db_session.execute.return_value = mock_result

        can_access = permission_service.can_access_synth_group(user_id, synth_group_id)

        assert can_access is True

    def test_non_owner_without_share_cannot_access(self, permission_service, mock_db_session):
        """Should return False when user is not owner and has no share."""
        user_id = str(uuid4())
        other_user_id = str(uuid4())
        synth_group_id = "grp_abcd1234"

        # Mock: synth_group owned by other_user, no share exists
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock_result = MagicMock()
            if call_count == 1:  # First call: check ownership
                mock_result.fetchone.return_value = (other_user_id,)
            else:  # Second call: check shares
                mock_result.fetchone.return_value = None
            return mock_result

        mock_db_session.execute.side_effect = side_effect

        can_access = permission_service.can_access_synth_group(user_id, synth_group_id)

        assert can_access is False

    def test_user_with_share_can_access(self, permission_service, mock_db_session):
        """Should return True when user has a share."""
        user_id = str(uuid4())
        other_user_id = str(uuid4())
        synth_group_id = "grp_abcd1234"

        # Mock: synth_group owned by other_user, but share exists
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock_result = MagicMock()
            if call_count == 1:  # First call: check ownership
                mock_result.fetchone.return_value = (other_user_id,)
            else:  # Second call: check shares
                share_id = str(uuid4())
                mock_result.fetchone.return_value = (share_id,)
            return mock_result

        mock_db_session.execute.side_effect = side_effect

        can_access = permission_service.can_access_synth_group(user_id, synth_group_id)

        assert can_access is True


# =============================================================================
# US4 Tests: Independent SynthGroup Sharing (T122)
# =============================================================================


class TestCanEditSynthGroup:
    """Test can_edit_synth_group permission check - T122."""

    def test_owner_can_edit(self, permission_service, mock_db_session):
        """Should return True when user is the owner."""
        user_id = str(uuid4())
        synth_group_id = "grp_abcd1234"

        # Mock database to return owner_id matching user_id
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (user_id,)
        mock_db_session.execute.return_value = mock_result

        can_edit = permission_service.can_edit_synth_group(user_id, synth_group_id)

        assert can_edit is True

    def test_viewer_cannot_edit(self, permission_service, mock_db_session):
        """Should return False when user has viewer permission."""
        user_id = str(uuid4())
        other_user_id = str(uuid4())
        synth_group_id = "grp_abcd1234"

        # Mock: synth_group owned by other_user, user has viewer permission
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock_result = MagicMock()
            if call_count == 1:  # First call: check ownership
                mock_result.fetchone.return_value = (other_user_id,)
            else:  # Second call: check editor permission
                mock_result.fetchone.return_value = ("viewer",)
            return mock_result

        mock_db_session.execute.side_effect = side_effect

        can_edit = permission_service.can_edit_synth_group(user_id, synth_group_id)

        assert can_edit is False

    def test_editor_can_edit(self, permission_service, mock_db_session):
        """Should return True when user has editor permission."""
        user_id = str(uuid4())
        other_user_id = str(uuid4())
        synth_group_id = "grp_abcd1234"

        # Mock: synth_group owned by other_user, user has editor permission
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock_result = MagicMock()
            if call_count == 1:  # First call: check ownership
                mock_result.fetchone.return_value = (other_user_id,)
            else:  # Second call: check editor permission
                mock_result.fetchone.return_value = ("editor",)
            return mock_result

        mock_db_session.execute.side_effect = side_effect

        can_edit = permission_service.can_edit_synth_group(user_id, synth_group_id)

        assert can_edit is True
