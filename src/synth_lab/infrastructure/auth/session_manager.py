"""JWT Session Manager for user authentication.

This module provides JWT-based session management for authenticated users.
Uses python-jose for JWT encoding/decoding.

Documentation:
- python-jose: https://python-jose.readthedocs.io/
- JWT standard: https://datatracker.ietf.org/doc/html/rfc7519

Example:
    >>> from synth_lab.infrastructure.auth.session_manager import SessionManager
    >>> manager = SessionManager(secret_key="my-secret", algorithm="HS256")
    >>> token = manager.create_access_token(user_id="123", email="user@example.com")
    >>> payload = manager.validate_token(token)
    >>> print(payload["sub"])  # "123"
"""

from datetime import datetime, timedelta, UTC
from jose import jwt, JWTError


class SessionManager:
    """Manages JWT-based user sessions.

    Handles creation and validation of JWT access tokens for authenticated users.

    Attributes:
        secret_key: Secret key for signing JWTs
        algorithm: JWT signing algorithm (default: HS256)
        access_token_expire_minutes: Token expiration time in minutes (default: 30)
    """

    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
    ):
        """Initialize the SessionManager.

        Args:
            secret_key: Secret key for signing JWTs
            algorithm: JWT signing algorithm (default: HS256)
            access_token_expire_minutes: Token expiration time in minutes (default: 30)
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes

    def create_access_token(self, user_id: str, email: str) -> str:
        """Create a JWT access token for a user.

        Args:
            user_id: User's unique identifier (UUID string)
            email: User's email address

        Returns:
            JWT access token as a string

        Example:
            >>> manager = SessionManager(secret_key="secret")
            >>> token = manager.create_access_token("user-123", "alice@example.com")
            >>> print(token)  # eyJ0eXAiOiJKV1QiLCJhbGc...
        """
        # Calculate expiration time
        expire = datetime.now(UTC) + timedelta(minutes=self.access_token_expire_minutes)

        # Create payload
        payload = {
            "sub": user_id,  # Subject (user ID)
            "email": email,
            "exp": expire,  # Expiration time
        }

        # Encode and return JWT
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def validate_token(self, token: str) -> dict:
        """Validate a JWT access token and return its payload.

        Args:
            token: JWT access token string

        Returns:
            Token payload as a dictionary

        Raises:
            JWTError: If token is invalid, expired, or tampered with

        Example:
            >>> manager = SessionManager(secret_key="secret")
            >>> token = manager.create_access_token("user-123", "alice@example.com")
            >>> payload = manager.validate_token(token)
            >>> print(payload["sub"])  # "user-123"
        """
        # Decode and validate JWT
        # This will raise JWTError if:
        # - Token is expired
        # - Signature is invalid
        # - Token is malformed
        payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        return payload
