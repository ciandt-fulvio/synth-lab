"""Unit tests for User entity validation.

Tests user model validation rules and constraints.
Must FAIL before implementation.
"""
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from synth_lab.domain.entities.user import User


class TestUserEntityValidation:
    """Test User entity creation and validation."""

    def test_create_valid_user(self):
        """Should create user with valid fields."""
        user = User(
            id=uuid4(),
            google_user_id="1074729472929292",
            email="user@example.com",
            display_name="John Doe",
            profile_picture_url="https://lh3.googleusercontent.com/test",
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        assert user is not None
        assert user.email == "user@example.com"
        assert user.google_user_id == "1074729472929292"

    def test_user_requires_google_user_id(self):
        """Should require google_user_id."""
        with pytest.raises(ValueError, match="google_user_id"):
            User(
                id=uuid4(),
                google_user_id="",
                email="user@example.com",
                display_name="John Doe",
                profile_picture_url=None,
                created_at=datetime.now(UTC).isoformat(),
                updated_at=datetime.now(UTC).isoformat(),
            )

    def test_user_requires_email(self):
        """Should require email."""
        with pytest.raises(ValueError, match="email"):
            User(
                id=uuid4(),
                google_user_id="1074729472929292",
                email="",
                display_name="John Doe",
                profile_picture_url=None,
                created_at=datetime.now(UTC).isoformat(),
                updated_at=datetime.now(UTC).isoformat(),
            )

    def test_user_validates_email_format(self):
        """Should validate email format."""
        with pytest.raises(ValueError, match="email"):
            User(
                id=uuid4(),
                google_user_id="1074729472929292",
                email="not-an-email",
                display_name="John Doe",
                profile_picture_url=None,
                created_at=datetime.now(UTC).isoformat(),
                updated_at=datetime.now(UTC).isoformat(),
            )

    def test_user_display_name_optional(self):
        """Should allow None for optional display_name."""
        user = User(
            id=uuid4(),
            google_user_id="1074729472929292",
            email="user@example.com",
            display_name=None,
            profile_picture_url=None,
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        assert user.display_name is None

    def test_user_profile_picture_optional(self):
        """Should allow None for optional profile_picture_url."""
        user = User(
            id=uuid4(),
            google_user_id="1074729472929292",
            email="user@example.com",
            display_name="John Doe",
            profile_picture_url=None,
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )

        assert user.profile_picture_url is None

    def test_user_auto_generates_id(self):
        """Should auto-generate UUID if not provided."""
        user = User(
            google_user_id="1074729472929292",
            email="user@example.com",
            display_name="John Doe",
        )

        assert user.id is not None
        assert isinstance(user.id, str) or hasattr(user.id, "hex")

    def test_user_auto_sets_timestamps(self):
        """Should auto-set created_at and updated_at."""
        user = User(
            google_user_id="1074729472929292",
            email="user@example.com",
            display_name="John Doe",
        )

        assert user.created_at is not None
        assert user.updated_at is not None

    def test_user_normalizes_email(self):
        """Should normalize email to lowercase."""
        user = User(
            google_user_id="1074729472929292",
            email="User@EXAMPLE.COM",
            display_name="John Doe",
        )

        assert user.email == "user@example.com"

    def test_user_equality(self):
        """Should compare users by ID."""
        user_id = uuid4()
        user1 = User(
            id=user_id,
            google_user_id="1074729472929292",
            email="user@example.com",
            display_name="John Doe",
        )
        user2 = User(
            id=user_id,
            google_user_id="1074729472929292",
            email="user@example.com",
            display_name="John Doe",
        )

        assert user1 == user2

    def test_user_to_dict(self):
        """Should convert user to dict."""
        user = User(
            google_user_id="1074729472929292",
            email="user@example.com",
            display_name="John Doe",
            profile_picture_url="https://example.com/pic.jpg",
        )

        user_dict = user.to_dict()

        assert user_dict["email"] == "user@example.com"
        assert user_dict["google_user_id"] == "1074729472929292"
        assert user_dict["display_name"] == "John Doe"
        assert "id" in user_dict
        assert "created_at" in user_dict
