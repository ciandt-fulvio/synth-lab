"""JWT-based session management for user authentication.

Handles creation, validation, and decoding of JWT tokens for stateless
authentication. Supports access tokens (short-lived) and refresh tokens
(long-lived) for secure session management.
"""
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Any

from jose import jwt, JWTError


class SessionManager:
    """Manages JWT token creation and validation for user sessions."""

    def __init__(
        self,
        secret_key: Optional[str] = None,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 480,  # 8 hours
        refresh_token_expire_days: int = 30,
    ):
        """Initialize SessionManager with JWT configuration.

        Args:
            secret_key: Secret key for JWT signing. If None, reads from JWT_SECRET_KEY env var.
            algorithm: JWT algorithm (default: HS256)
            access_token_expire_minutes: Access token lifetime in minutes (default: 30)
            refresh_token_expire_days: Refresh token lifetime in days (default: 30)

        Raises:
            ValueError: If secret_key is not provided and JWT_SECRET_KEY env var is not set
        """
        self.secret_key = secret_key or os.getenv("JWT_SECRET_KEY")
        if not self.secret_key:
            raise ValueError(
                "JWT secret key is required. Set JWT_SECRET_KEY environment variable "
                "or pass secret_key parameter."
            )

        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days

    def create_access_token(
        self,
        user_id: str,
        email: str,
        expires_delta: Optional[timedelta] = None,
        additional_claims: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create a JWT access token.

        Args:
            user_id: User's unique identifier
            email: User's email address
            expires_delta: Custom expiration time (overrides default)
            additional_claims: Optional additional JWT claims

        Returns:
            Encoded JWT token string

        Raises:
            ValueError: If user_id or email is empty

        Example:
            >>> manager = SessionManager(secret_key="secret")
            >>> token = manager.create_access_token("user-123", "user@example.com")
            >>> print(token)
            eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
        """
        if not user_id or not user_id.strip():
            raise ValueError("user_id cannot be empty")
        if not email or not email.strip():
            raise ValueError("email cannot be empty")

        # Calculate expiration
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)

        # Build payload
        to_encode = {
            "sub": user_id,  # Subject (user ID)
            "email": email,
            "exp": expire,  # Expiration time
            "iat": datetime.utcnow(),  # Issued at
        }

        # Add additional claims if provided
        if additional_claims:
            to_encode.update(additional_claims)

        # Encode token
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def create_refresh_token(
        self,
        user_id: str,
        email: str,
        additional_claims: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create a JWT refresh token with longer expiration.

        Args:
            user_id: User's unique identifier
            email: User's email address
            additional_claims: Optional additional JWT claims

        Returns:
            Encoded JWT refresh token string

        Example:
            >>> manager = SessionManager(secret_key="secret")
            >>> refresh_token = manager.create_refresh_token("user-123", "user@example.com")
        """
        expires_delta = timedelta(days=self.refresh_token_expire_days)
        claims = {"token_type": "refresh"}
        if additional_claims:
            claims.update(additional_claims)

        return self.create_access_token(
            user_id=user_id,
            email=email,
            expires_delta=expires_delta,
            additional_claims=claims,
        )

    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Decode JWT token WITHOUT validating expiration.

        Use this when you need to inspect token contents regardless of expiration.
        For validation with expiration check, use validate_token().

        Args:
            token: JWT token string

        Returns:
            Decoded payload dict, or None if token is invalid

        Example:
            >>> manager = SessionManager(secret_key="secret")
            >>> token = manager.create_access_token("user-123", "user@example.com")
            >>> payload = manager.decode_token(token)
            >>> print(payload["sub"])
            user-123
        """
        if not token:
            return None

        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": False},  # Don't check expiration
            )
            return payload
        except JWTError:
            return None

    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate JWT token including expiration check.

        Args:
            token: JWT token string

        Returns:
            Decoded payload dict if valid and not expired, None otherwise

        Example:
            >>> manager = SessionManager(secret_key="secret")
            >>> token = manager.create_access_token("user-123", "user@example.com")
            >>> payload = manager.validate_token(token)
            >>> if payload:
            ...     print(f"Valid token for user {payload['sub']}")
            ... else:
            ...     print("Invalid or expired token")
        """
        if not token:
            return None

        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": True},  # Check expiration
            )
            return payload
        except JWTError:
            return None

    def get_user_id_from_token(self, token: str) -> Optional[str]:
        """Extract user_id from token (convenience method).

        Args:
            token: JWT token string

        Returns:
            User ID if token is valid, None otherwise

        Example:
            >>> manager = SessionManager(secret_key="secret")
            >>> token = manager.create_access_token("user-123", "user@example.com")
            >>> user_id = manager.get_user_id_from_token(token)
            >>> print(user_id)
            user-123
        """
        payload = self.validate_token(token)
        if payload:
            return payload.get("sub")
        return None

    def get_email_from_token(self, token: str) -> Optional[str]:
        """Extract email from token (convenience method).

        Args:
            token: JWT token string

        Returns:
            Email if token is valid, None otherwise

        Example:
            >>> manager = SessionManager(secret_key="secret")
            >>> token = manager.create_access_token("user-123", "user@example.com")
            >>> email = manager.get_email_from_token(token)
            >>> print(email)
            user@example.com
        """
        payload = self.validate_token(token)
        if payload:
            return payload.get("email")
        return None


def get_session_manager() -> SessionManager:
    """Get SessionManager instance with configuration from environment.

    Returns:
        Configured SessionManager instance

    Environment Variables:
        JWT_SECRET_KEY: Required secret key for JWT signing
        JWT_ALGORITHM: Algorithm (default: HS256)
        JWT_ACCESS_TOKEN_EXPIRE_MINUTES: Access token lifetime (default: 480 = 8 hours)
        JWT_REFRESH_TOKEN_EXPIRE_DAYS: Refresh token lifetime (default: 30)

    Example:
        >>> manager = get_session_manager()
        >>> token = manager.create_access_token("user-123", "user@example.com")
    """
    return SessionManager(
        secret_key=os.getenv("JWT_SECRET_KEY"),
        algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
        access_token_expire_minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "480")),
        refresh_token_expire_days=int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "30")),
    )
