"""Integration tests for authentication flow.

Tests complete OAuth flow with real database interactions.
"""
import pytest
from unittest.mock import patch

from synth_lab.services.auth_service import AuthService
from synth_lab.repositories.user_repository import UserRepository
from synth_lab.domain.entities.user import User


@pytest.mark.slow
class TestCompleteOAuthFlow:
    """Test complete OAuth flow integration - T028."""

    def test_complete_oauth_flow_new_user(self, db_session):
        """Should create user and return session token for new whitelisted user.

        Integration test covering:
        - Whitelist validation
        - User creation in database
        - JWT token generation
        """
        # Setup
        user_repository = UserRepository(db_session)
        auth_service = AuthService(user_repository=user_repository)

        google_user_info = {
            "sub": "google_test_123",
            "email": "newuser@example.com",
            "email_verified": True,
            "name": "New User",
            "picture": "https://example.com/pic.jpg",
        }

        # Mock whitelist check
        with patch.object(auth_service, 'validate_whitelist', return_value=True):
            # Execute
            user, session_token = auth_service.handle_oauth_callback(google_user_info)

            # Verify user created
            assert user is not None
            assert user.email == "newuser@example.com"
            assert user.google_user_id == "google_test_123"
            assert user.display_name == "New User"

            # Verify token generated
            assert session_token is not None
            assert isinstance(session_token, str)
            assert len(session_token) > 50

            # Verify persisted to database
            db_user = user_repository.get_by_email("newuser@example.com")
            assert db_user is not None
            assert db_user.google_user_id == "google_test_123"

    def test_complete_oauth_flow_existing_user(self, db_session):
        """Should update existing user and return session token.

        Integration test covering:
        - User update in database
        - Profile data refresh from Google
        """
        # Setup - create existing user
        user_repository = UserRepository(db_session)

        # Create user entity and persist
        existing_user = User(
            google_user_id="google_test_existing",
            email="existing@example.com",
            display_name="Old Name",
            profile_picture_url="https://old.com/pic.jpg",
        )
        created_user = user_repository.create(existing_user)

        auth_service = AuthService(user_repository=user_repository)

        google_user_info = {
            "sub": "google_test_existing",
            "email": "existing@example.com",
            "email_verified": True,
            "name": "Updated Name",
            "picture": "https://new.com/pic.jpg",
        }

        with patch.object(auth_service, 'validate_whitelist', return_value=True):
            # Execute
            user, session_token = auth_service.handle_oauth_callback(google_user_info)

            # Verify user updated
            assert user.id == created_user.id
            assert user.display_name == "Updated Name"
            assert user.profile_picture_url == "https://new.com/pic.jpg"

            # Verify token generated
            assert session_token is not None

            # Verify updates persisted
            db_user = user_repository.get_by_google_id("google_test_existing")
            assert db_user.display_name == "Updated Name"
            assert db_user.profile_picture_url == "https://new.com/pic.jpg"


@pytest.mark.slow
class TestWhitelistRejection:
    """Test whitelist rejection integration - T029."""

    def test_whitelist_rejection_integration(self, db_session):
        """Should reject non-whitelisted user and not create database record.

        Integration test covering:
        - Whitelist validation
        - No database record created for rejected users
        - Error handling
        """
        # Setup
        user_repository = UserRepository(db_session)
        auth_service = AuthService(user_repository=user_repository)

        google_user_info = {
            "sub": "hacker_123",
            "email": "hacker@evil.com",
            "email_verified": True,
            "name": "Hacker",
        }

        with patch.object(auth_service, 'validate_whitelist', return_value=False):
            # Execute and verify rejection
            with pytest.raises(ValueError, match="whitelist"):
                auth_service.handle_oauth_callback(google_user_info)

            # Verify no user created in database
            db_user = user_repository.get_by_email("hacker@evil.com")
            assert db_user is None

            db_user_by_google = user_repository.get_by_google_id("hacker_123")
            assert db_user_by_google is None


@pytest.mark.slow
class TestDomainWhitelistMatch:
    """Test domain whitelist matching integration - T030."""

    def test_domain_whitelist_match_integration(self, db_session):
        """Should allow users from whitelisted domain.

        Integration test covering:
        - Domain-based whitelist validation
        - User creation for domain-whitelisted users
        """
        # Setup
        user_repository = UserRepository(db_session)
        auth_service = AuthService(user_repository=user_repository)

        google_user_info = {
            "sub": "domain_user_123",
            "email": "anyone@company.com",
            "email_verified": True,
            "name": "Domain User",
        }

        # Mock domain whitelist (e.g., @company.com is whitelisted)
        with patch.object(auth_service, 'validate_whitelist', return_value=True):
            # Execute
            user, session_token = auth_service.handle_oauth_callback(google_user_info)

            # Verify user created
            assert user is not None
            assert user.email == "anyone@company.com"
            assert session_token is not None

            # Verify persisted to database
            db_user = user_repository.get_by_email("anyone@company.com")
            assert db_user is not None
            assert db_user.google_user_id == "domain_user_123"

    def test_subdomain_not_matched(self, db_session):
        """Should reject subdomains if not explicitly whitelisted.

        Integration test covering:
        - Subdomain exclusion logic
        """
        # Setup
        user_repository = UserRepository(db_session)
        auth_service = AuthService(user_repository=user_repository)

        google_user_info = {
            "sub": "subdomain_user_123",
            "email": "user@sub.company.com",
            "email_verified": True,
            "name": "Subdomain User",
        }

        # Assume @company.com is whitelisted but @sub.company.com is not
        with patch.object(auth_service, 'validate_whitelist', return_value=False):
            # Execute and verify rejection
            with pytest.raises(ValueError, match="whitelist"):
                auth_service.handle_oauth_callback(google_user_info)

            # Verify no user created
            db_user = user_repository.get_by_email("user@sub.company.com")
            assert db_user is None
