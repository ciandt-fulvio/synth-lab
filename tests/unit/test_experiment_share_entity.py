"""Unit tests for ExperimentShare entity.

Tests share entity validation and data structure.
Must FAIL before implementation.
"""
from uuid import uuid4

import pytest

from synth_lab.domain.entities.share import ExperimentShare, PermissionLevel


class TestExperimentShareEntity:
    """Test ExperimentShare entity validation - T084."""

    def test_create_valid_experiment_share(self):
        """Should create valid experiment share with required fields."""
        experiment_id = "exp_12345678"
        user_id = uuid4()
        granted_by_id = uuid4()

        share = ExperimentShare(
            experiment_id=experiment_id,
            user_id=user_id,
            permission_level=PermissionLevel.VIEWER,
            granted_by_id=granted_by_id,
        )

        assert share.experiment_id == experiment_id
        assert share.user_id == str(user_id)  # Converted to string
        assert share.permission_level == PermissionLevel.VIEWER
        assert share.granted_by_id == str(granted_by_id)
        assert share.id is not None
        assert share.granted_at is not None

    def test_experiment_share_with_editor_permission(self):
        """Should create share with editor permission level."""
        share = ExperimentShare(
            experiment_id="exp_12345678",
            user_id=uuid4(),
            permission_level=PermissionLevel.EDITOR,
            granted_by_id=uuid4(),
        )

        assert share.permission_level == PermissionLevel.EDITOR

    def test_experiment_share_requires_experiment_id(self):
        """Should raise error if experiment_id is missing."""
        with pytest.raises(ValueError, match="experiment_id"):
            ExperimentShare(
                experiment_id="",
                user_id=uuid4(),
                permission_level=PermissionLevel.VIEWER,
                granted_by_id=uuid4(),
            )

    def test_experiment_share_requires_user_id(self):
        """Should raise error if user_id is invalid."""
        with pytest.raises((ValueError, TypeError)):
            ExperimentShare(
                experiment_id="exp_12345678",
                user_id=None,
                permission_level=PermissionLevel.VIEWER,
                granted_by_id=uuid4(),
            )

    def test_experiment_share_converts_string_permission_level(self):
        """Should convert string permission level to enum."""
        share = ExperimentShare(
            experiment_id="exp_12345678",
            user_id=uuid4(),
            permission_level="viewer",  # String instead of enum
            granted_by_id=uuid4(),
        )

        assert share.permission_level == PermissionLevel.VIEWER
        assert isinstance(share.permission_level, PermissionLevel)

    def test_experiment_share_to_dict(self):
        """Should convert share to dictionary."""
        experiment_id = "exp_12345678"
        user_id = uuid4()
        granted_by_id = uuid4()

        share = ExperimentShare(
            experiment_id=experiment_id,
            user_id=user_id,
            permission_level=PermissionLevel.EDITOR,
            granted_by_id=granted_by_id,
        )

        data = share.to_dict()

        assert data["experiment_id"] == experiment_id
        assert data["user_id"] == str(user_id)
        assert data["permission_level"] == "editor"
        assert data["granted_by_id"] == str(granted_by_id)
        assert "id" in data
        assert "granted_at" in data

    def test_experiment_share_uuid_conversion(self):
        """Should convert UUIDs to strings internally."""
        share = ExperimentShare(
            experiment_id="exp_12345678",
            user_id=uuid4(),
            permission_level=PermissionLevel.VIEWER,
            granted_by_id=uuid4(),
        )

        # All IDs should be strings
        assert isinstance(share.id, str)
        assert isinstance(share.user_id, str)
        assert isinstance(share.granted_by_id, str)
