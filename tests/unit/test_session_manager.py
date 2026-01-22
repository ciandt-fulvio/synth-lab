"""Unit tests for JWT Session Manager.

Following Test-First Development:
- Tests are written BEFORE implementation
- Tests MUST fail initially (no implementation exists yet)
- Implementation in src/synth_lab/infrastructure/auth/session_manager.py

The SessionManager handles JWT token creation, validation, and expiration.
"""

import pytest
from datetime import datetime, timedelta, UTC
from uuid import uuid4


class TestJWTTokenCreation:
    """Test JWT token creation (T014)."""

    def test_create_access_token_returns_valid_jwt(self):
        """Test that create_access_token returns a JWT string."""
        from synth_lab.infrastructure.auth.session_manager import SessionManager

        manager = SessionManager(secret_key="test-secret-key", algorithm="HS256")
        user_id = str(uuid4())
        token = manager.create_access_token(user_id=user_id, email="alice@example.com")

        # Token should be a non-empty string with 3 parts (header.payload.signature)
        assert isinstance(token, str)
        assert len(token) > 0
        assert token.count(".") == 2

    def test_create_access_token_includes_user_data(self):
        """Test that the token includes user ID and email in the payload."""
        from synth_lab.infrastructure.auth.session_manager import SessionManager

        manager = SessionManager(secret_key="test-secret-key", algorithm="HS256")
        user_id = str(uuid4())
        email = "alice@example.com"

        token = manager.create_access_token(user_id=user_id, email=email)

        # Decode token to verify payload (without verification for testing)
        import jwt
        payload = jwt.decode(token, options={"verify_signature": False})

        assert payload["sub"] == user_id
        assert payload["email"] == email

    def test_create_access_token_includes_expiration(self):
        """Test that the token includes an expiration timestamp."""
        from synth_lab.infrastructure.auth.session_manager import SessionManager

        manager = SessionManager(
            secret_key="test-secret-key", algorithm="HS256", access_token_expire_minutes=30
        )
        token = manager.create_access_token(user_id=str(uuid4()), email="alice@example.com")

        # Decode token to verify expiration
        import jwt
        payload = jwt.decode(token, options={"verify_signature": False})

        assert "exp" in payload
        assert isinstance(payload["exp"], int)


class TestJWTTokenValidation:
    """Test JWT token validation (T015)."""

    def test_validate_token_returns_payload_for_valid_token(self):
        """Test that validate_token returns the payload for a valid token."""
        from synth_lab.infrastructure.auth.session_manager import SessionManager

        manager = SessionManager(secret_key="test-secret-key", algorithm="HS256")
        user_id = str(uuid4())
        email = "alice@example.com"

        # Create token
        token = manager.create_access_token(user_id=user_id, email=email)

        # Validate token
        payload = manager.validate_token(token)

        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["email"] == email

    def test_validate_token_raises_for_invalid_signature(self):
        """Test that validate_token raises an exception for tampered tokens."""
        from synth_lab.infrastructure.auth.session_manager import SessionManager
        from jose import JWTError

        manager = SessionManager(secret_key="test-secret-key", algorithm="HS256")
        token = manager.create_access_token(user_id=str(uuid4()), email="alice@example.com")

        # Tamper with the token (change last character)
        tampered_token = token[:-1] + ("x" if token[-1] != "x" else "y")

        # Validation should raise an exception
        with pytest.raises(JWTError):
            manager.validate_token(tampered_token)

    def test_validate_token_raises_for_wrong_secret(self):
        """Test that validate_token fails if secret key is different."""
        from synth_lab.infrastructure.auth.session_manager import SessionManager
        from jose import JWTError

        manager1 = SessionManager(secret_key="secret-key-1", algorithm="HS256")
        manager2 = SessionManager(secret_key="secret-key-2", algorithm="HS256")

        # Create token with manager1
        token = manager1.create_access_token(user_id=str(uuid4()), email="alice@example.com")

        # Try to validate with manager2 (different secret)
        with pytest.raises(JWTError):
            manager2.validate_token(token)


class TestJWTTokenExpiration:
    """Test JWT token expiration (T016)."""

    def test_expired_token_raises_exception(self):
        """Test that validate_token raises an exception for expired tokens."""
        from synth_lab.infrastructure.auth.session_manager import SessionManager
        from jose import JWTError

        # Create manager with very short expiration (negative to make it expire immediately)
        manager = SessionManager(
            secret_key="test-secret-key", algorithm="HS256", access_token_expire_minutes=-1
        )

        # Create token (already expired)
        token = manager.create_access_token(user_id=str(uuid4()), email="alice@example.com")

        # Validation should raise an exception
        with pytest.raises(JWTError):
            manager.validate_token(token)

    def test_token_expiration_time_is_configurable(self):
        """Test that expiration time can be configured."""
        from synth_lab.infrastructure.auth.session_manager import SessionManager
        import jwt

        # Create token with 60 minute expiration
        manager = SessionManager(
            secret_key="test-secret-key", algorithm="HS256", access_token_expire_minutes=60
        )
        token = manager.create_access_token(user_id=str(uuid4()), email="alice@example.com")

        # Decode and check expiration is approximately 60 minutes from now
        payload = jwt.decode(token, options={"verify_signature": False})
        exp_time = datetime.fromtimestamp(payload["exp"], UTC)
        expected_exp = datetime.now(UTC) + timedelta(minutes=60)

        # Allow 5 second tolerance for test execution time
        time_diff = abs((exp_time - expected_exp).total_seconds())
        assert time_diff < 5

    def test_non_expired_token_validates_successfully(self):
        """Test that tokens within expiration time validate successfully."""
        from synth_lab.infrastructure.auth.session_manager import SessionManager

        # Create token with reasonable expiration
        manager = SessionManager(
            secret_key="test-secret-key", algorithm="HS256", access_token_expire_minutes=30
        )
        user_id = str(uuid4())
        token = manager.create_access_token(user_id=user_id, email="alice@example.com")

        # Should validate successfully
        payload = manager.validate_token(token)
        assert payload["sub"] == user_id
