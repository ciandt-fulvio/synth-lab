"""
Shared fixtures for contract tests.

CRITICAL: All contract tests MUST use the test database to prevent
writing to production database during test runs.
"""

import os

import pytest
from fastapi.testclient import TestClient

from synth_lab.api.main import app


@pytest.fixture
def client(postgres_test_url: str):
    """
    Create FastAPI test client using test database.

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
        yield client
    finally:
        # Restore original DATABASE_URL
        if original_db_url:
            os.environ["DATABASE_URL"] = original_db_url
        else:
            os.environ.pop("DATABASE_URL", None)
