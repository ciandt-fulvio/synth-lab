"""Authentication service for user authentication and session management.

Handles Google OAuth flow, user creation, whitelist validation, and session management.
"""
from typing import Optional, Tuple

from loguru import logger

from synth_lab.domain.entities.user import User
from synth_lab.infrastructure.auth.session_manager import SessionManager
from synth_lab.infrastructure.auth.whitelist import is_whitelisted, load_whitelist_from_env
from synth_lab.repositories.user_repository import UserRepository


class AuthService:
    """Service for authentication operations."""

    def __init__(
        self,
        user_repository: UserRepository,
        session_manager: Optional[SessionManager] = None,
    ):
        """Initialize AuthService.

        Args:
            user_repository: Repository for user data access
            session_manager: Optional session manager (uses default if not provided)
        """
        self.user_repository = user_repository
        self.session_manager = session_manager or SessionManager()

        # Load whitelist on initialization
        try:
            self.whitelist_emails, self.whitelist_domains = load_whitelist_from_env()
        except ValueError:
            # Whitelist not configured - will reject all users
            self.whitelist_emails = set()
            self.whitelist_domains = set()

    def create_user_from_google(self, google_user_info: dict) -> User:
        """Create or update user from Google OAuth data.

        Args:
            google_user_info: User info from Google OAuth API

        Returns:
            Created or updated User entity

        Raises:
            ValueError: If required fields are missing or email not verified
        """
        if "sub" not in google_user_info:
            raise ValueError("Google user info missing 'sub' field")
        if "email" not in google_user_info:
            raise ValueError("Google user info missing 'email' field")
        if not google_user_info.get("email_verified", False):
            raise ValueError("Email must be verified by Google")

        google_user_id = google_user_info["sub"]

        # Check if user already exists
        existing_user = self.user_repository.get_by_google_id(google_user_id)

        if existing_user:
            # Update existing user with latest Google data
            existing_user.update_from_google(google_user_info)
            return self.user_repository.update(existing_user)
        else:
            # Create new user
            new_user = User.from_google_oauth(google_user_info)
            return self.user_repository.create(new_user)

    def validate_whitelist(self, email: str) -> bool:
        """Check if email is whitelisted.

        Args:
            email: Email address to validate

        Returns:
            True if whitelisted, False otherwise
        """
        if not email:
            return False

        return is_whitelisted(email, self.whitelist_emails, self.whitelist_domains)

    def handle_oauth_callback(self, google_user_info: dict) -> Tuple[User, str]:
        """Handle OAuth callback and create session.

        Args:
            google_user_info: User info from Google OAuth API

        Returns:
            Tuple of (User, session_token)

        Raises:
            ValueError: If user not whitelisted or validation fails
        """
        # Validate email is whitelisted
        email = google_user_info.get("email", "")
        if not self.validate_whitelist(email):
            logger.warning(f"Authentication failed: email {email} is not whitelisted")
            raise ValueError(
                f"Email {email} is not whitelisted. Contact administrator for access."
            )

        # Create or update user
        user = self.create_user_from_google(google_user_info)

        # Create session token
        session_token = self.session_manager.create_access_token(
            user_id=str(user.id),
            email=user.email,
        )

        logger.info(f"Authentication successful for user {user.id} ({email})")

        return (user, session_token)

    def get_current_user(self, token: str) -> Optional[User]:
        """Get current user from session token.

        Args:
            token: JWT session token

        Returns:
            User entity if token is valid, None otherwise
        """
        if not token:
            return None

        # Validate token and extract user_id
        user_id = self.session_manager.get_user_id_from_token(token)
        if not user_id:
            return None

        # Fetch user from database
        return self.user_repository.get_by_id(user_id)

    def logout(self) -> bool:
        """Logout current user.

        With JWT tokens, logout is handled client-side by clearing the cookie.
        Server-side logout would require token blacklisting (not implemented).

        Returns:
            True to indicate success
        """
        # JWT tokens are stateless - logout is handled client-side
        return True

    def refresh_token(self, refresh_token: str) -> Optional[str]:
        """Refresh access token using refresh token.

        Args:
            refresh_token: JWT refresh token

        Returns:
            New access token if refresh token is valid, None otherwise
        """
        # Validate refresh token
        payload = self.session_manager.validate_token(refresh_token)
        if not payload:
            return None

        # Check if it's actually a refresh token
        if payload.get("token_type") != "refresh":
            return None

        user_id = payload.get("sub")
        email = payload.get("email")

        if not user_id or not email:
            return None

        # Verify user still exists
        user = self.user_repository.get_by_id(user_id)
        if not user:
            return None

        # Create new access token
        new_token = self.session_manager.create_access_token(
            user_id=user_id,
            email=email,
        )

        return new_token
