"""Unit tests for JWT session management.

Tests token creation, validation, and expiration logic.
Must FAIL before implementation.
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from synth_lab.infrastructure.auth.session_manager import SessionManager


@pytest.fixture
def session_manager():
    """Create SessionManager with test configuration."""
    return SessionManager(
        secret_key="test_secret_key_32_characters_long_for_testing",
        algorithm="HS256",
        access_token_expire_minutes=30
    )


class TestJWTTokenCreation:
    """Test JWT token creation."""

    def test_create_access_token(self, session_manager):
        """Should create valid JWT access token."""
        user_id = str(uuid4())
        email = "user@example.com"

        token = session_manager.create_access_token(
            user_id=user_id,
            email=email
        )

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_token_contains_user_data(self, session_manager):
        """Token payload should contain user_id and email."""
        user_id = str(uuid4())
        email = "user@example.com"

        token = session_manager.create_access_token(user_id=user_id, email=email)
        payload = session_manager.decode_token(token)

        assert payload["sub"] == user_id
        assert payload["email"] == email

    def test_token_contains_expiration(self, session_manager):
        """Token payload should contain expiration time."""
        user_id = str(uuid4())
        email = "user@example.com"

        token = session_manager.create_access_token(user_id=user_id, email=email)
        payload = session_manager.decode_token(token)

        assert "exp" in payload
        assert isinstance(payload["exp"], int)

    def test_token_expiration_is_correct(self, session_manager):
        """Token expiration should match configured time."""
        user_id = str(uuid4())
        email = "user@example.com"

        before_creation = datetime.utcnow()
        token = session_manager.create_access_token(user_id=user_id, email=email)
        after_creation = datetime.utcnow()

        payload = session_manager.decode_token(token)
        exp_timestamp = payload["exp"]
        exp_datetime = datetime.utcfromtimestamp(exp_timestamp)

        # Should expire 30 minutes from now (allow 1 second tolerance for timestamp rounding)
        expected_min = before_creation + timedelta(minutes=30) - timedelta(seconds=1)
        expected_max = after_creation + timedelta(minutes=30) + timedelta(seconds=1)

        assert expected_min <= exp_datetime <= expected_max

    def test_custom_expiration_time(self, session_manager):
        """Should allow custom expiration time."""
        user_id = str(uuid4())
        email = "user@example.com"
        custom_expires = timedelta(minutes=60)

        token = session_manager.create_access_token(
            user_id=user_id,
            email=email,
            expires_delta=custom_expires
        )
        payload = session_manager.decode_token(token)
        exp_datetime = datetime.utcfromtimestamp(payload["exp"])

        # Should expire ~60 minutes from now
        now = datetime.utcnow()
        expected = now + custom_expires
        delta = abs((exp_datetime - expected).total_seconds())

        assert delta < 2  # Within 2 seconds


class TestJWTTokenValidation:
    """Test JWT token validation."""

    def test_validate_valid_token(self, session_manager):
        """Should validate correctly formed token."""
        user_id = str(uuid4())
        email = "user@example.com"

        token = session_manager.create_access_token(user_id=user_id, email=email)
        payload = session_manager.validate_token(token)

        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["email"] == email

    def test_validate_invalid_signature(self, session_manager):
        """Should reject token with invalid signature."""
        # Create token with different secret
        other_manager = SessionManager(
            secret_key="different_secret_key_32_chars_test",
            algorithm="HS256",
            access_token_expire_minutes=30
        )
        token = other_manager.create_access_token(
            user_id=str(uuid4()),
            email="user@example.com"
        )

        # Try to validate with original manager
        payload = session_manager.validate_token(token)
        assert payload is None

    def test_validate_malformed_token(self, session_manager):
        """Should reject malformed token."""
        malformed_tokens = [
            "not.a.jwt",
            "invalid",
            "",
            "header.payload",  # Missing signature
        ]

        for token in malformed_tokens:
            payload = session_manager.validate_token(token)
            assert payload is None

    def test_decode_vs_validate(self, session_manager):
        """decode_token should not check expiration, validate_token should."""
        user_id = str(uuid4())
        email = "user@example.com"

        # Create expired token
        token = session_manager.create_access_token(
            user_id=user_id,
            email=email,
            expires_delta=timedelta(seconds=-1)  # Expired 1 second ago
        )

        # decode_token should work (no expiration check)
        decoded = session_manager.decode_token(token)
        assert decoded is not None
        assert decoded["sub"] == user_id

        # validate_token should fail (checks expiration)
        validated = session_manager.validate_token(token)
        assert validated is None


class TestJWTTokenExpiration:
    """Test JWT token expiration handling."""

    def test_expired_token_rejected(self, session_manager):
        """Should reject expired token."""
        user_id = str(uuid4())
        email = "user@example.com"

        # Create token that expires immediately
        token = session_manager.create_access_token(
            user_id=user_id,
            email=email,
            expires_delta=timedelta(seconds=-10)  # Expired 10 seconds ago
        )

        payload = session_manager.validate_token(token)
        assert payload is None

    def test_token_not_yet_expired(self, session_manager):
        """Should accept token that hasn't expired yet."""
        user_id = str(uuid4())
        email = "user@example.com"

        # Create token that expires in 1 hour
        token = session_manager.create_access_token(
            user_id=user_id,
            email=email,
            expires_delta=timedelta(hours=1)
        )

        payload = session_manager.validate_token(token)
        assert payload is not None
        assert payload["sub"] == user_id

    def test_token_boundary_expiration(self, session_manager):
        """Should handle token expiring right now."""
        user_id = str(uuid4())
        email = "user@example.com"

        # Create token that expires in 1 second
        token = session_manager.create_access_token(
            user_id=user_id,
            email=email,
            expires_delta=timedelta(seconds=1)
        )

        # Should be valid immediately
        payload = session_manager.validate_token(token)
        assert payload is not None

        # Wait for expiration
        import time
        time.sleep(2)

        # Should now be invalid
        payload = session_manager.validate_token(token)
        assert payload is None


class TestSessionManagerEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_user_id(self, session_manager):
        """Should handle empty user_id."""
        with pytest.raises(ValueError):
            session_manager.create_access_token(user_id="", email="user@example.com")

    def test_empty_email(self, session_manager):
        """Should handle empty email."""
        with pytest.raises(ValueError):
            session_manager.create_access_token(user_id=str(uuid4()), email="")

    def test_none_token_validation(self, session_manager):
        """Should handle None token gracefully."""
        payload = session_manager.validate_token(None)
        assert payload is None

    def test_refresh_token_creation(self, session_manager):
        """Should create refresh token with longer expiration."""
        user_id = str(uuid4())
        email = "user@example.com"

        refresh_token = session_manager.create_refresh_token(
            user_id=user_id,
            email=email
        )

        payload = session_manager.decode_token(refresh_token)
        exp_datetime = datetime.utcfromtimestamp(payload["exp"])
        now = datetime.utcnow()

        # Refresh token should expire in ~30 days
        delta_days = (exp_datetime - now).days
        assert 29 <= delta_days <= 31
