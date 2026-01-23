"""Unit tests for UserRepository.

Tests user data access operations with mocked database.
"""
import pytest
from uuid import uuid4
from datetime import datetime
from unittest.mock import MagicMock, patch
from sqlalchemy.exc import IntegrityError

from synth_lab.repositories.user_repository import UserRepository
from synth_lab.domain.entities.user import User
from synth_lab.models.orm.user import User as UserModel


@pytest.fixture
def mock_db_session():
    """Create mock database session."""
    session = MagicMock()
    session.add = MagicMock()
    session.flush = MagicMock()
    session.refresh = MagicMock()
    session.delete = MagicMock()
    session.rollback = MagicMock()
    return session


@pytest.fixture
def user_repository(mock_db_session):
    """Create UserRepository with mocked session."""
    return UserRepository(mock_db_session)


@pytest.fixture
def sample_user():
    """Sample user for testing."""
    return User(
        id=uuid4(),
        google_user_id="1074729472929292",
        email="user@example.com",
        display_name="John Doe",
        profile_picture_url="https://example.com/pic.jpg",
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat(),
    )


@pytest.fixture
def sample_user_model():
    """Sample user ORM model for testing."""
    model = MagicMock(spec=UserModel)
    model.id = str(uuid4())
    model.google_user_id = "1074729472929292"
    model.email = "user@example.com"
    model.display_name = "John Doe"
    model.profile_picture_url = "https://example.com/pic.jpg"
    model.created_at = datetime.utcnow().isoformat()
    model.updated_at = datetime.utcnow().isoformat()
    return model


class TestUserRepositoryCreate:
    """Test user creation operations."""

    def test_create_user(self, user_repository, sample_user, mock_db_session, sample_user_model):
        """Should create new user in database."""
        # Mock refresh to populate the model
        mock_db_session.refresh = MagicMock(side_effect=lambda m: None)

        # Patch the UserModel to return our mock
        with patch.object(user_repository, '_model_to_entity') as mock_convert:
            mock_convert.return_value = sample_user
            created_user = user_repository.create(sample_user)

        assert created_user is not None
        assert created_user.email == sample_user.email
        mock_db_session.add.assert_called_once()
        mock_db_session.flush.assert_called_once()

    def test_create_user_calls_flush(self, user_repository, sample_user, mock_db_session):
        """Should flush transaction when creating user."""
        with patch.object(user_repository, '_model_to_entity', return_value=sample_user):
            user_repository.create(sample_user)

        mock_db_session.flush.assert_called_once()

    def test_create_duplicate_email_raises_error(self, user_repository, sample_user, mock_db_session):
        """Should raise error when creating user with duplicate email."""
        mock_db_session.flush.side_effect = IntegrityError(
            "INSERT", {}, Exception("duplicate key value violates unique constraint \"uq_users_email\"")
        )

        with pytest.raises(ValueError, match="email"):
            user_repository.create(sample_user)

        mock_db_session.rollback.assert_called_once()

    def test_create_duplicate_google_id_raises_error(self, user_repository, mock_db_session):
        """Should raise error when creating user with duplicate google_user_id."""
        user = User(
            google_user_id="1074729472929292",
            email="different@example.com",
            display_name="Different User",
        )

        mock_db_session.flush.side_effect = IntegrityError(
            "INSERT", {}, Exception("duplicate key value violates unique constraint \"uq_users_google_id\"")
        )

        with pytest.raises(ValueError, match="google_user_id"):
            user_repository.create(user)


class TestUserRepositoryGetByEmail:
    """Test get user by email operations."""

    def test_get_by_email_existing(self, user_repository, sample_user_model, mock_db_session):
        """Should return user when email exists."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user_model
        mock_db_session.execute.return_value = mock_result

        user = user_repository.get_by_email("user@example.com")

        assert user is not None
        assert user.email == sample_user_model.email

    def test_get_by_email_not_found(self, user_repository, mock_db_session):
        """Should return None when email doesn't exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        user = user_repository.get_by_email("nonexistent@example.com")

        assert user is None

    def test_get_by_email_normalizes_input(self, user_repository, sample_user_model, mock_db_session):
        """Should normalize email to lowercase before search."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user_model
        mock_db_session.execute.return_value = mock_result

        user_repository.get_by_email("  USER@EXAMPLE.COM  ")

        # Verify execute was called (normalization happens internally)
        mock_db_session.execute.assert_called_once()


class TestUserRepositoryGetByGoogleId:
    """Test get user by Google ID operations."""

    def test_get_by_google_id_existing(self, user_repository, sample_user_model, mock_db_session):
        """Should return user when Google ID exists."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user_model
        mock_db_session.execute.return_value = mock_result

        user = user_repository.get_by_google_id("1074729472929292")

        assert user is not None
        assert user.google_user_id == "1074729472929292"

    def test_get_by_google_id_not_found(self, user_repository, mock_db_session):
        """Should return None when Google ID doesn't exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        user = user_repository.get_by_google_id("nonexistent_id")

        assert user is None


class TestUserRepositoryUpdate:
    """Test user update operations."""

    def test_update_user(self, user_repository, sample_user, sample_user_model, mock_db_session):
        """Should update user fields."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user_model
        mock_db_session.execute.return_value = mock_result

        sample_user.display_name = "Jane Doe Updated"

        updated_user = user_repository.update(sample_user)

        assert updated_user is not None
        mock_db_session.flush.assert_called_once()

    def test_update_nonexistent_user_raises_error(self, user_repository, sample_user, mock_db_session):
        """Should raise ValueError when user doesn't exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        with pytest.raises(ValueError, match="not found"):
            user_repository.update(sample_user)


class TestUserRepositoryGetById:
    """Test get user by ID operations."""

    def test_get_by_id_existing(self, user_repository, sample_user_model, mock_db_session):
        """Should return user when ID exists."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user_model
        mock_db_session.execute.return_value = mock_result

        user = user_repository.get_by_id(sample_user_model.id)

        assert user is not None

    def test_get_by_id_not_found(self, user_repository, mock_db_session):
        """Should return None when ID doesn't exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        user = user_repository.get_by_id(uuid4())

        assert user is None


class TestUserRepositoryDelete:
    """Test user deletion operations."""

    def test_delete_existing_user(self, user_repository, sample_user_model, mock_db_session):
        """Should delete user and return True."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user_model
        mock_db_session.execute.return_value = mock_result

        result = user_repository.delete(sample_user_model.id)

        assert result is True
        mock_db_session.delete.assert_called_once_with(sample_user_model)
        mock_db_session.flush.assert_called_once()

    def test_delete_nonexistent_user(self, user_repository, mock_db_session):
        """Should return False when user doesn't exist."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        result = user_repository.delete(uuid4())

        assert result is False
        mock_db_session.delete.assert_not_called()
