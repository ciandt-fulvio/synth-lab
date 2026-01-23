"""E2E test authentication helpers.

Provides utilities for generating test JWT tokens and managing authenticated sessions
in E2E tests using cookie injection (bypasses OAuth flow).
"""
import os
from datetime import datetime, timedelta


# Test user constants - must match tests/conftest.py and seed data
TEST_USER = {
    "id": "00000001-0000-0000-0000-000000000001",
    "email": "testuser@example.com",
    "google_id": "google-test-user-001",
    "display_name": "Test User",
}

# Second test user for sharing tests
TEST_USER_2 = {
    "id": "00000002-0000-0000-0000-000000000002",
    "email": "testuser2@example.com",
    "google_id": "google-test-user-002",
    "display_name": "Test User 2",
}


def get_jwt_secret() -> str:
    """Get JWT secret key from environment or use default for tests.

    In test environments, uses a predictable secret for reproducible tokens.
    """
    return os.getenv("JWT_SECRET_KEY", "test-secret-key-for-e2e-testing")


def create_test_auth_token(
    user_id: str,
    email: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT token for testing.

    Uses PyJWT to create a valid JWT token that can be used in E2E tests
    to bypass the OAuth flow.

    Args:
        user_id: User UUID
        email: User email
        expires_delta: Token expiration time (default: 1 hour)

    Returns:
        JWT token string
    """
    try:
        import jwt
    except ImportError:
        raise ImportError(
            "PyJWT is required for E2E auth helpers. "
            "Install with: pip install PyJWT"
        )

    if expires_delta is None:
        expires_delta = timedelta(hours=1)

    now = datetime.utcnow()
    payload = {
        "sub": user_id,
        "email": email,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        "token_type": "access",
    }

    secret = get_jwt_secret()
    return jwt.encode(payload, secret, algorithm="HS256")


def create_test_user_token() -> str:
    """Create a token for the default test user."""
    return create_test_auth_token(TEST_USER["id"], TEST_USER["email"])


def create_test_user_2_token() -> str:
    """Create a token for the second test user."""
    return create_test_auth_token(TEST_USER_2["id"], TEST_USER_2["email"])


def get_auth_cookie(token: str) -> dict:
    """Get auth cookie configuration for Playwright.

    Args:
        token: JWT token

    Returns:
        Cookie configuration dict for browser context
    """
    return {
        "name": "auth_token",
        "value": token,
        "domain": "localhost",
        "path": "/",
        "httpOnly": True,
        "secure": False,  # False for localhost
        "sameSite": "Lax",
    }


def get_default_auth_cookie() -> dict:
    """Get auth cookie for default test user."""
    return get_auth_cookie(create_test_user_token())


def get_second_user_auth_cookie() -> dict:
    """Get auth cookie for second test user."""
    return get_auth_cookie(create_test_user_2_token())
