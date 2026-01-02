"""
Base repository class for synth-lab.

Provides common patterns for data access including pagination and error handling.
Uses SQLAlchemy ORM for all database operations.

References:
    - SQLAlchemy ORM: https://docs.sqlalchemy.org/en/20/orm/
    - Database module: synth_lab.infrastructure.database_v2
"""

from typing import TypeVar

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from synth_lab.infrastructure.database_v2 import get_session_factory
from synth_lab.models.pagination import PaginationMeta, PaginationParams

T = TypeVar("T")


class BaseRepository:
    """Base class for all repositories with SQLAlchemy ORM.

    Usage:
        # With explicit session (preferred for FastAPI dependency injection):
        repo = MyRepository(session=db_session)

        # Without session (creates new session from global factory):
        repo = MyRepository()
    """

    def __init__(self, session: Session | None = None):
        """
        Initialize repository.

        Args:
            session: SQLAlchemy session. If not provided, uses global session factory.
        """
        self._session = session
        self._owns_session = session is None

    @property
    def session(self) -> Session:
        """Get the SQLAlchemy session.

        If no session was provided at init, creates one from the global factory.
        The session is properly closed when the repository is garbage collected
        or explicitly closed.
        """
        if self._session is None:
            # Create session from global factory directly (not via context manager)
            factory = get_session_factory()
            self._session = factory()
        return self._session

    def close(self) -> None:
        """Close the session if this repository owns it.

        Call this when done with the repository if you didn't provide a session.
        """
        if self._owns_session and self._session is not None:
            self._session.close()
            self._session = None

    def __del__(self) -> None:
        """Ensure session is closed when repository is garbage collected."""
        try:
            self.close()
        except Exception:
            pass  # Ignore errors during cleanup

    def __enter__(self) -> "BaseRepository":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - closes session."""
        self.close()

    def _paginate_orm(
        self,
        query,
        params: PaginationParams,
        count_query=None) -> tuple[list, PaginationMeta]:
        """
        Execute a paginated ORM query.

        Args:
            query: SQLAlchemy Select statement
            params: Pagination parameters
            count_query: Optional count query. If None, uses func.count()

        Returns:
            Tuple of (models_list, pagination_meta)
        """
        # Get total count
        if count_query is not None:
            total = self.session.execute(count_query).scalar() or 0
        else:
            # Create count query from select
            count_stmt = select(func.count()).select_from(query.subquery())
            total = self.session.execute(count_stmt).scalar() or 0

        # Apply sorting if specified and if query supports it
        if params.sort_by:
            # Get the first entity from the query to find the column
            # This is a simplified approach - more complex sorting may need custom handling
            pass  # Sorting should be applied to query before calling this method

        # Apply pagination
        paginated = query.limit(params.limit).offset(params.offset)
        result = self.session.execute(paginated)
        rows = list(result.scalars().all())

        meta = PaginationMeta.from_params(total, params)
        return rows, meta

    def _get_by_id(self, model_class, entity_id: str):
        """
        Get a single entity by ID using ORM.

        Args:
            model_class: SQLAlchemy model class
            entity_id: ID of the entity

        Returns:
            Model instance or None
        """
        return self.session.get(model_class, entity_id)

    def _add(self, entity) -> None:
        """
        Add an entity to the session.

        Args:
            entity: SQLAlchemy model instance
        """
        self.session.add(entity)

    def _flush(self) -> None:
        """Flush pending changes to the database."""
        self.session.flush()

    def _commit(self) -> None:
        """Commit the current transaction."""
        self.session.commit()

    def _delete(self, entity) -> None:
        """
        Delete an entity from the session.

        Args:
            entity: SQLAlchemy model instance
        """
        self.session.delete(entity)


if __name__ == "__main__":
    import sys

    # Validation
    all_validation_failures = []
    total_tests = 0

    # Test 1: BaseRepository initialization without session
    total_tests += 1
    try:
        repo = BaseRepository()
        if repo._session is not None:
            all_validation_failures.append("Session should be None initially")
        if repo._owns_session is not True:
            all_validation_failures.append("Should own session when none provided")
    except Exception as e:
        all_validation_failures.append(f"Init without session failed: {e}")

    # Test 2: BaseRepository initialization with session
    total_tests += 1
    try:
        from sqlalchemy.orm import Session as MockSession
        from unittest.mock import MagicMock

        mock_session = MagicMock(spec=MockSession)
        repo = BaseRepository(session=mock_session)
        if repo._session is not mock_session:
            all_validation_failures.append("Session should be the provided one")
        if repo._owns_session is not False:
            all_validation_failures.append("Should not own session when provided")
    except Exception as e:
        all_validation_failures.append(f"Init with session failed: {e}")

    # Test 3: Helper methods exist
    total_tests += 1
    try:
        repo = BaseRepository()
        methods = ["_paginate_orm", "_get_by_id", "_add", "_flush", "_delete"]
        for method in methods:
            if not hasattr(repo, method):
                all_validation_failures.append(f"Missing method: {method}")
    except Exception as e:
        all_validation_failures.append(f"Method check failed: {e}")

    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
