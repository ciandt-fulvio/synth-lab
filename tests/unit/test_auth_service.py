"""Unit tests for AuthService.

Tests authentication business logic with mocked dependencies.
"""
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from synth_lab.domain.entities.user import User
from synth_lab.services.auth_service import AuthService


@pytest.fixture
def mock_user_repository():
    """Mock user repository (synchronous)."""
    repo = MagicMock()
    repo.get_by_email = MagicMock()
    repo.get_by_google_id = MagicMock()
    repo.get_by_id = MagicMock()
    repo.create = MagicMock()
    repo.update = MagicMock()
    return repo


@pytest.fixture
def mock_session_manager():
    """Mock session manager."""
    manager = MagicMock()
    manager.create_access_token = MagicMock(return_value="mock_access_token")
    manager.create_refresh_token = MagicMock(return_value="mock_refresh_token")
    manager.validate_token = MagicMock(return_value={"sub": "test-user-id"})
    manager.get_user_id_from_token = MagicMock(return_value="test-user-id")
    return manager


@pytest.fixture
def auth_service(mock_user_repository, mock_session_manager):
    """Create AuthService with mocked dependencies."""
    return AuthService(
        user_repository=mock_user_repository,
        session_manager=mock_session_manager
    )


@pytest.fixture
def google_user_info():
    """Sample Google user info response."""
    return {
        "sub": "1074729472929292",
        "email": "user@example.com",
        "email_verified": True,
        "name": "John Doe",
        "picture": "https://lh3.googleusercontent.com/test",
        "given_name": "John",
        "family_name": "Doe",
    }


class TestCreateUserFromGoogle:
    """Test user creation from Google OAuth data."""

    def test_create_new_user(self, auth_service, mock_user_repository, google_user_info):
        """Should create new user from Google data."""
        mock_user_repository.get_by_google_id.return_value = None
        # Make create return the created user
        mock_user_repository.create.side_effect = lambda u: u

        user = auth_service.create_user_from_google(google_user_info)

        assert user is not None
        assert user.email == "user@example.com"
        assert user.google_user_id == "1074729472929292"
        assert user.display_name == "John Doe"
        mock_user_repository.create.assert_called_once()

    def test_update_existing_user(self, auth_service, mock_user_repository, google_user_info):
        """Should update existing user if Google ID exists."""
        existing_user = User(
            id=uuid4(),
            google_user_id="1074729472929292",
            email="user@example.com",
            display_name="Old Name",
            profile_picture_url="https://old.com/pic.jpg",
        )
        mock_user_repository.get_by_google_id.return_value = existing_user
        mock_user_repository.update.side_effect = lambda u: u

        user = auth_service.create_user_from_google(google_user_info)

        assert user.display_name == "John Doe"
        assert user.profile_picture_url == google_user_info["picture"]
        mock_user_repository.update.assert_called_once()
        mock_user_repository.create.assert_not_called()

    def test_handles_missing_optional_fields(self, auth_service, mock_user_repository):
        """Should handle missing optional fields in Google response."""
        minimal_user_info = {
            "sub": "1074729472929292",
            "email": "user@example.com",
            "email_verified": True,
        }
        mock_user_repository.get_by_google_id.return_value = None
        mock_user_repository.create.side_effect = lambda u: u

        user = auth_service.create_user_from_google(minimal_user_info)

        assert user.email == "user@example.com"
        assert user.display_name is None
        assert user.profile_picture_url is None

    def test_requires_sub(self, auth_service, google_user_info):
        """Should raise error if 'sub' is missing."""
        del google_user_info["sub"]

        with pytest.raises(ValueError, match="sub"):
            auth_service.create_user_from_google(google_user_info)

    def test_requires_email(self, auth_service, google_user_info):
        """Should raise error if 'email' is missing."""
        del google_user_info["email"]

        with pytest.raises(ValueError, match="email"):
            auth_service.create_user_from_google(google_user_info)

    def test_requires_email_verified(self, auth_service, google_user_info):
        """Should raise error if email is not verified."""
        google_user_info["email_verified"] = False

        with pytest.raises(ValueError, match="verified"):
            auth_service.create_user_from_google(google_user_info)


class TestValidateWhitelist:
    """Test whitelist validation logic."""

    def test_whitelisted_email(self, auth_service):
        """Should return True for whitelisted email."""
        with patch("synth_lab.services.auth_service.is_whitelisted") as mock_is_whitelisted:
            mock_is_whitelisted.return_value = True

            result = auth_service.validate_whitelist("user@example.com")

            assert result is True

    def test_non_whitelisted_email(self, auth_service):
        """Should return False for non-whitelisted email."""
        with patch("synth_lab.services.auth_service.is_whitelisted") as mock_is_whitelisted:
            mock_is_whitelisted.return_value = False

            result = auth_service.validate_whitelist("hacker@evil.com")

            assert result is False

    def test_validates_email_format(self, auth_service):
        """Should handle invalid email format."""
        with patch("synth_lab.services.auth_service.is_whitelisted") as mock_is_whitelisted:
            mock_is_whitelisted.return_value = False

            result = auth_service.validate_whitelist("not-an-email")

            assert result is False


class TestHandleOAuthCallback:
    """Test OAuth callback handling."""

    def test_successful_callback(self, auth_service, mock_user_repository, google_user_info):
        """Should handle successful OAuth callback."""
        mock_user_repository.get_by_google_id.return_value = None
        mock_user_repository.create.side_effect = lambda u: u

        with patch("synth_lab.services.auth_service.is_whitelisted") as mock_whitelist:
            mock_whitelist.return_value = True

            user, session_token = auth_service.handle_oauth_callback(google_user_info)

            assert user is not None
            assert user.email == "user@example.com"
            assert session_token is not None
            assert len(session_token) > 0

    def test_callback_rejects_non_whitelisted(self, auth_service, google_user_info):
        """Should reject non-whitelisted users."""
        with patch("synth_lab.services.auth_service.is_whitelisted") as mock_whitelist:
            mock_whitelist.return_value = False

            with pytest.raises(ValueError, match="whitelist"):
                auth_service.handle_oauth_callback(google_user_info)

    def test_callback_creates_jwt_token(self, auth_service, mock_user_repository, google_user_info):
        """Should create valid JWT token for authenticated user."""
        mock_user_repository.get_by_google_id.return_value = None
        mock_user_repository.create.side_effect = lambda u: u

        with patch("synth_lab.services.auth_service.is_whitelisted") as mock_whitelist:
            mock_whitelist.return_value = True

            user, session_token = auth_service.handle_oauth_callback(google_user_info)

            # Token should be a non-empty string
            assert isinstance(session_token, str)
            assert len(session_token) > 10  # Mock token is "mock_access_token"

    def test_callback_for_existing_user(
        self, auth_service, mock_user_repository, google_user_info
    ):
        """Should handle callback for existing user."""
        existing_user = User(
            id=uuid4(),
            google_user_id=google_user_info["sub"],
            email=google_user_info["email"],
            display_name="Existing User",
        )
        mock_user_repository.get_by_google_id.return_value = existing_user
        mock_user_repository.update.side_effect = lambda u: u

        with patch("synth_lab.services.auth_service.is_whitelisted") as mock_whitelist:
            mock_whitelist.return_value = True

            user, session_token = auth_service.handle_oauth_callback(google_user_info)

            assert user.id == existing_user.id
            mock_user_repository.update.assert_called_once()
            mock_user_repository.create.assert_not_called()


class TestGetCurrentUser:
    """Test getting current user from token."""

    def test_get_user_from_valid_token(self, auth_service, mock_user_repository, mock_session_manager):
        """Should return user from valid token."""
        user_id = str(uuid4())
        user = User(
            id=user_id,
            google_user_id="1074729472929292",
            email="user@example.com",
            display_name="John Doe",
        )
        mock_user_repository.get_by_id.return_value = user
        mock_session_manager.get_user_id_from_token.return_value = user_id

        result = auth_service.get_current_user("valid_token")

        assert result is not None
        assert str(result.id) == user_id

    def test_get_user_from_invalid_token(self, auth_service, mock_session_manager):
        """Should return None for invalid token."""
        mock_session_manager.get_user_id_from_token.return_value = None

        result = auth_service.get_current_user("invalid_token")

        assert result is None


class TestLogout:
    """Test logout functionality."""

    def test_logout_clears_session(self, auth_service):
        """Should clear session on logout."""
        result = auth_service.logout()

        # Logout is stateless with JWT, just returns success
        assert result is True
