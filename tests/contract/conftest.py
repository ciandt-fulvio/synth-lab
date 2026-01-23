"""
Shared fixtures for contract tests.

CRITICAL: All contract tests MUST use the test database to prevent
writing to production database during test runs.
"""

import os

import pytest
from fastapi.testclient import TestClient

from synth_lab.api.main import app
from synth_lab.infrastructure.auth.session_manager import SessionManager


# Test user constants
# IMPORTANT: Must be a valid UUID format for database FK constraints
TEST_USER_ID = "00000001-0000-0000-0000-000000000001"
TEST_USER_EMAIL = "testuser@example.com"
TEST_USER_GOOGLE_ID = "google-test-user-001"


@pytest.fixture
def auth_token() -> str:
    """Create a valid JWT token for testing."""
    session_manager = SessionManager()
    return session_manager.create_access_token(
        user_id=TEST_USER_ID,
        email=TEST_USER_EMAIL
    )


@pytest.fixture
def client(postgres_test_url: str, auth_token: str):
    """
    Create FastAPI test client using test database with authentication.

    CRITICAL: Sets DATABASE_URL to postgres_test_url to prevent
    writing to production database during tests.

    All contract tests should use this fixture instead of creating
    TestClient(app) directly.
    """
    # Store original DATABASE_URL
    original_db_url = os.environ.get("DATABASE_URL")

    # Set DATABASE_URL to test database
    os.environ["DATABASE_URL"] = postgres_test_url

    try:
        # Create client (will use test database)
        client = TestClient(app)
        # Set auth cookie for all requests
        client.cookies.set("auth_token", auth_token)
        yield client
    finally:
        # Restore original DATABASE_URL
        if original_db_url:
            os.environ["DATABASE_URL"] = original_db_url
        else:
            os.environ.pop("DATABASE_URL", None)
