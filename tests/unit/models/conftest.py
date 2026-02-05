"""
Shared test fixtures for ORM model unit tests.

Provides isolated database engine and session fixtures for each test.
Each test gets a fresh database with minimal seed data (test user only).
"""

import os
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from synth_lab.models.orm.base import Base
from synth_lab.models.orm.user import User
from synth_lab.models.orm.synth import SynthGroup

# Test constants
TEST_USER_ID = "00000001-0000-0000-0000-000000000001"
TEST_USER_GOOGLE_ID = "google-test-user-001"
TEST_USER_EMAIL = "testuser@example.com"
DEFAULT_SYNTH_GROUP_ID = "grp_00000001"


def _seed_minimal_data(engine):
    """Seed minimal test data (user + default synth group) for FK constraints."""
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    session = SessionLocal()
    try:
        user = User(
            id=TEST_USER_ID,
            google_user_id=TEST_USER_GOOGLE_ID,
            email=TEST_USER_EMAIL,
            display_name="Test User",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )
        session.add(user)

        # Default synth group (required by Experiment FK with default="grp_00000001")
        default_group = SynthGroup(
            id=DEFAULT_SYNTH_GROUP_ID,
            name="Default Group",
            description="Default group for tests",
            owner_id=TEST_USER_ID,
            created_at=datetime.now().isoformat(),
        )
        session.add(default_group)

        session.commit()
    finally:
        session.close()


@pytest.fixture(scope="function")
def engine():
    """Create isolated test database engine for each test."""
    database_url = os.getenv(
        "DATABASE_URL", "postgresql://synthlab:synthlab@localhost:5433/synthlab"
    )
    engine = create_engine(database_url, echo=False)

    # Drop all tables to ensure clean state
    Base.metadata.drop_all(engine)
    
    # Create all tables
    Base.metadata.create_all(engine)

    # Seed minimal test data (user only)
    _seed_minimal_data(engine)

    yield engine

    # Cleanup: drop all tables
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture(scope="function")
def session(engine) -> Session:
    """Create test database session."""
    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
    session = SessionLocal()

    yield session

    session.close()
