"""
SQLAlchemy ORM base classes and utilities for synth-lab.

Provides types and mixins for all ORM models using PostgreSQL.

References:
    - SQLAlchemy 2.0 ORM: https://docs.sqlalchemy.org/en/20/orm/
    - JSON type variants: https://docs.sqlalchemy.org/en/20/core/type_basics.html#sqlalchemy.types.JSON
    - Mutable tracking: https://docs.sqlalchemy.org/en/20/orm/extensions/mutable.html
"""

from typing import Any

from sqlalchemy import JSON, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# JSON type: Uses JSONB on PostgreSQL for better indexing and performance
JSONVariant = JSON().with_variant(JSONB(), "postgresql")

# Mutable JSON types for in-place change detection
# Use these when you need the ORM to detect nested dict/list modifications
MutableJSON = MutableDict.as_mutable(JSONVariant)
MutableJSONList = MutableList.as_mutable(JSONVariant)


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.

    All models should inherit from this class to be part of the same
    metadata and support automatic table creation via Alembic migrations.

    Example:
        class Experiment(Base):
            __tablename__ = "experiments"
            id: Mapped[str] = mapped_column(primary_key=True)
            name: Mapped[str] = mapped_column(String(100))
    """

    pass


class TimestampMixin:
    """
    Mixin for models that need created_at and updated_at timestamps.

    Timestamps are stored as ISO 8601 strings (TEXT) for cross-database
    compatibility. Use datetime.now().isoformat() when setting values.

    Example:
        class Experiment(Base, TimestampMixin):
            __tablename__ = "experiments"
            id: Mapped[str] = mapped_column(primary_key=True)
            # created_at and updated_at inherited from mixin
    """

    created_at: Mapped[str] = mapped_column(String(50), nullable=False)
    updated_at: Mapped[str | None] = mapped_column(String(50), nullable=True)


class SoftDeleteMixin:
    """
    Mixin for models that support soft delete via status field.

    Instead of physically deleting records, sets status to 'deleted'.
    Queries should filter by status='active' to exclude deleted records.

    Example:
        class Experiment(Base, SoftDeleteMixin):
            __tablename__ = "experiments"
            id: Mapped[str] = mapped_column(primary_key=True)
            # status inherited from mixin, defaults to 'active'
    """

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")


def to_dict(model: Base, exclude: set[str] | None = None) -> dict[str, Any]:
    """
    Convert a SQLAlchemy model instance to a dictionary.

    Args:
        model: SQLAlchemy model instance
        exclude: Set of column names to exclude from output

    Returns:
        Dictionary with column names as keys and values

    Example:
        experiment = session.query(Experiment).first()
        data = to_dict(experiment, exclude={"updated_at"})
    """
    exclude = exclude or set()
    return {
        column.name: getattr(model, column.name)
        for column in model.__table__.columns
        if column.name not in exclude
    }


if __name__ == "__main__":
    import sys

    # Validation
    all_validation_failures = []
    total_tests = 0

    # Test 1: JSONVariant type
    total_tests += 1
    try:
        assert JSONVariant is not None
        assert hasattr(JSONVariant, "with_variant")
    except AssertionError as e:
        all_validation_failures.append(f"JSONVariant type check failed: {e}")

    # Test 2: MutableJSON type
    total_tests += 1
    try:
        assert MutableJSON is not None
    except AssertionError as e:
        all_validation_failures.append(f"MutableJSON type check failed: {e}")

    # Test 3: Base class inheritance
    total_tests += 1
    try:
        assert issubclass(Base, DeclarativeBase)
    except AssertionError as e:
        all_validation_failures.append(f"Base class inheritance failed: {e}")

    # Test 4: TimestampMixin has required attributes
    total_tests += 1
    try:
        assert hasattr(TimestampMixin, "created_at")
        assert hasattr(TimestampMixin, "updated_at")
    except AssertionError as e:
        all_validation_failures.append(f"TimestampMixin attributes failed: {e}")

    # Test 5: SoftDeleteMixin has status attribute
    total_tests += 1
    try:
        assert hasattr(SoftDeleteMixin, "status")
    except AssertionError as e:
        all_validation_failures.append(f"SoftDeleteMixin attributes failed: {e}")

    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
