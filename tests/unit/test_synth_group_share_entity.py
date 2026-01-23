"""Unit tests for SynthGroupShare entity.

Tests share entity validation and data structure.
Must FAIL before implementation.
"""
import pytest
from uuid import uuid4
from synth_lab.domain.entities.share import SynthGroupShare, PermissionLevel


class TestSynthGroupShareEntity:
    """Test SynthGroupShare entity validation - T085."""

    def test_create_valid_synth_group_share(self):
        """Should create valid synth_group share with required fields."""
        synth_group_id = "grp_abcd1234"
        user_id = uuid4()
        granted_by_id = uuid4()

        share = SynthGroupShare(
            synth_group_id=synth_group_id,
            user_id=user_id,
            permission_level=PermissionLevel.VIEWER,
            granted_by_id=granted_by_id,
        )

        assert share.synth_group_id == synth_group_id
        assert share.user_id == str(user_id)
        assert share.permission_level == PermissionLevel.VIEWER
        assert share.granted_by_id == str(granted_by_id)
        assert share.id is not None
        assert share.granted_at is not None

    def test_synth_group_share_with_editor_permission(self):
        """Should create share with editor permission level."""
        share = SynthGroupShare(
            synth_group_id="grp_abcd1234",
            user_id=uuid4(),
            permission_level=PermissionLevel.EDITOR,
            granted_by_id=uuid4(),
        )

        assert share.permission_level == PermissionLevel.EDITOR

    def test_synth_group_share_requires_synth_group_id(self):
        """Should raise error if synth_group_id is missing."""
        with pytest.raises(ValueError, match="synth_group_id"):
            SynthGroupShare(
                synth_group_id="",
                user_id=uuid4(),
                permission_level=PermissionLevel.VIEWER,
                granted_by_id=uuid4(),
            )

    def test_synth_group_share_requires_user_id(self):
        """Should raise error if user_id is invalid."""
        with pytest.raises((ValueError, TypeError)):
            SynthGroupShare(
                synth_group_id="grp_abcd1234",
                user_id=None,
                permission_level=PermissionLevel.VIEWER,
                granted_by_id=uuid4(),
            )

    def test_synth_group_share_converts_string_permission_level(self):
        """Should convert string permission level to enum."""
        share = SynthGroupShare(
            synth_group_id="grp_abcd1234",
            user_id=uuid4(),
            permission_level="viewer",  # String instead of enum
            granted_by_id=uuid4(),
        )

        assert share.permission_level == PermissionLevel.VIEWER
        assert isinstance(share.permission_level, PermissionLevel)

    def test_synth_group_share_to_dict(self):
        """Should convert share to dictionary."""
        synth_group_id = "grp_abcd1234"
        user_id = uuid4()
        granted_by_id = uuid4()

        share = SynthGroupShare(
            synth_group_id=synth_group_id,
            user_id=user_id,
            permission_level=PermissionLevel.EDITOR,
            granted_by_id=granted_by_id,
        )

        data = share.to_dict()

        assert data["synth_group_id"] == synth_group_id
        assert data["user_id"] == str(user_id)
        assert data["permission_level"] == "editor"
        assert data["granted_by_id"] == str(granted_by_id)
        assert "id" in data
        assert "granted_at" in data

    def test_synth_group_share_uuid_conversion(self):
        """Should convert UUIDs to strings internally."""
        share = SynthGroupShare(
            synth_group_id="grp_abcd1234",
            user_id=uuid4(),
            permission_level=PermissionLevel.VIEWER,
            granted_by_id=uuid4(),
        )

        # All IDs should be strings
        assert isinstance(share.id, str)
        assert isinstance(share.user_id, str)
        assert isinstance(share.granted_by_id, str)
