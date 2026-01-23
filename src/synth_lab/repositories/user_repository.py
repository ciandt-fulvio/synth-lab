"""User repository for database operations.

Handles CRUD operations for User entities using SQLAlchemy.
"""
from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from synth_lab.domain.entities.user import User
from synth_lab.models.orm.user import User as UserModel


class UserRepository:
    """Repository for User data access operations."""

    def __init__(self, db: Session):
        """Initialize repository with database session.

        Args:
            db: SQLAlchemy session
        """
        self.db = db

    def create(self, user: User) -> User:
        """Create new user in database.

        Args:
            user: User entity to create

        Returns:
            Created user entity

        Raises:
            ValueError: If user with same email or google_user_id already exists
        """
        try:
            # Convert entity to database model
            user_model = UserModel(
                id=str(user.id),
                google_user_id=user.google_user_id,
                email=user.email,
                display_name=user.display_name,
                profile_picture_url=user.profile_picture_url,
                created_at=user.created_at,
                updated_at=user.updated_at,
            )

            self.db.add(user_model)
            self.db.flush()
            self.db.refresh(user_model)

            return self._model_to_entity(user_model)

        except IntegrityError as e:
            self.db.rollback()
            error_msg = str(e)
            if "email" in error_msg or "uq_users_email" in error_msg:
                raise ValueError(f"User with email {user.email} already exists")
            elif "google_user_id" in error_msg or "uq_users_google_id" in error_msg:
                raise ValueError(f"User with google_user_id {user.google_user_id} already exists")
            else:
                raise ValueError(f"Failed to create user: {error_msg}")

    def get_by_id(self, user_id: UUID | str) -> Optional[User]:
        """Get user by ID.

        Args:
            user_id: User UUID

        Returns:
            User entity if found, None otherwise
        """
        query = select(UserModel).where(UserModel.id == str(user_id))
        result = self.db.execute(query)
        user_model = result.scalar_one_or_none()

        if user_model:
            return self._model_to_entity(user_model)
        return None

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email (case-insensitive).

        Args:
            email: User email

        Returns:
            User entity if found, None otherwise
        """
        email_lower = email.lower().strip()
        query = select(UserModel).where(UserModel.email == email_lower)
        result = self.db.execute(query)
        user_model = result.scalar_one_or_none()

        if user_model:
            return self._model_to_entity(user_model)
        return None

    def get_by_google_id(self, google_user_id: str) -> Optional[User]:
        """Get user by Google user ID.

        Args:
            google_user_id: Google's unique user identifier

        Returns:
            User entity if found, None otherwise
        """
        query = select(UserModel).where(UserModel.google_user_id == google_user_id)
        result = self.db.execute(query)
        user_model = result.scalar_one_or_none()

        if user_model:
            return self._model_to_entity(user_model)
        return None

    def update(self, user: User) -> User:
        """Update existing user.

        Args:
            user: User entity with updated data

        Returns:
            Updated user entity

        Raises:
            ValueError: If user doesn't exist
        """
        query = select(UserModel).where(UserModel.id == str(user.id))
        result = self.db.execute(query)
        user_model = result.scalar_one_or_none()

        if not user_model:
            raise ValueError(f"User with id {user.id} not found")

        # Update fields
        user_model.email = user.email
        user_model.display_name = user.display_name
        user_model.profile_picture_url = user.profile_picture_url
        user_model.updated_at = datetime.utcnow().isoformat()

        self.db.flush()
        self.db.refresh(user_model)

        return self._model_to_entity(user_model)

    def delete(self, user_id: UUID | str) -> bool:
        """Delete user by ID.

        Args:
            user_id: User UUID

        Returns:
            True if deleted, False if not found
        """
        query = select(UserModel).where(UserModel.id == str(user_id))
        result = self.db.execute(query)
        user_model = result.scalar_one_or_none()

        if user_model:
            self.db.delete(user_model)
            self.db.flush()
            return True

        return False

    def _model_to_entity(self, user_model: UserModel) -> User:
        """Convert database model to domain entity.

        Args:
            user_model: SQLAlchemy User model

        Returns:
            User entity
        """
        return User(
            id=user_model.id,
            google_user_id=user_model.google_user_id,
            email=user_model.email,
            display_name=user_model.display_name,
            profile_picture_url=user_model.profile_picture_url,
            created_at=user_model.created_at,
            updated_at=user_model.updated_at,
        )
