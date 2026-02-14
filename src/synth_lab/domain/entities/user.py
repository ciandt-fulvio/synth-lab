"""User domain entity.

Represents an authenticated user who has successfully logged in via Google OAuth.
"""
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Optional
from uuid import UUID, uuid4


@dataclass
class User:
    """User entity for authenticated users.

    Attributes:
        id: Unique user identifier (UUID)
        google_user_id: Google's unique user identifier (sub claim from JWT)
        email: User's email from Google account
        display_name: User's full name from Google profile (optional)
        profile_picture_url: URL to user's Google profile picture (optional)
        created_at: When user first logged in (ISO format timestamp)
        updated_at: Last profile update from Google (ISO format timestamp)
    """

    google_user_id: str
    email: str
    display_name: Optional[str] = None
    profile_picture_url: Optional[str] = None
    id: UUID = field(default_factory=uuid4)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def __post_init__(self):
        """Validate and normalize user data after initialization."""
        # Validate required fields
        if not self.google_user_id or not self.google_user_id.strip():
            raise ValueError("google_user_id is required")

        if not self.email or not self.email.strip():
            raise ValueError("email is required")

        # Normalize email to lowercase
        self.email = self.email.lower().strip()

        # Validate email format
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, self.email):
            raise ValueError(f"Invalid email format: {self.email}")

        # Convert UUID to string if needed
        if isinstance(self.id, UUID):
            self.id = str(self.id)

    def __eq__(self, other):
        """Compare users by ID."""
        if not isinstance(other, User):
            return False
        return self.id == other.id

    def __hash__(self):
        """Hash user by ID."""
        return hash(self.id)

    def to_dict(self) -> dict:
        """Convert user to dictionary representation.

        Returns:
            Dictionary with user data suitable for JSON serialization
        """
        return {
            "id": str(self.id),
            "google_user_id": self.google_user_id,
            "email": self.email,
            "display_name": self.display_name,
            "profile_picture_url": self.profile_picture_url,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        """Create User from dictionary.

        Args:
            data: Dictionary with user data

        Returns:
            User instance
        """
        return cls(
            id=data.get("id"),
            google_user_id=data["google_user_id"],
            email=data["email"],
            display_name=data.get("display_name"),
            profile_picture_url=data.get("profile_picture_url"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

    @classmethod
    def from_google_oauth(cls, google_user_info: dict) -> "User":
        """Create User from Google OAuth user info response.

        Args:
            google_user_info: User info from Google OAuth API

        Returns:
            User instance

        Raises:
            ValueError: If required fields are missing
        """
        if "sub" not in google_user_info:
            raise ValueError("Google user info missing 'sub' field")
        if "email" not in google_user_info:
            raise ValueError("Google user info missing 'email' field")

        return cls(
            google_user_id=google_user_info["sub"],
            email=google_user_info["email"],
            display_name=google_user_info.get("name"),
            profile_picture_url=google_user_info.get("picture"),
        )

    def update_from_google(self, google_user_info: dict) -> None:
        """Update user profile from Google OAuth data.

        Args:
            google_user_info: User info from Google OAuth API
        """
        if "name" in google_user_info:
            self.display_name = google_user_info["name"]
        if "picture" in google_user_info:
            self.profile_picture_url = google_user_info["picture"]
        if "email" in google_user_info:
            self.email = google_user_info["email"].lower().strip()

        self.updated_at = datetime.now(UTC).isoformat()
