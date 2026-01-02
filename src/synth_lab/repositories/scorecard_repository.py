"""
Scorecard repository for synth-lab.

Provides data access layer for feature scorecards with PostgreSQL persistence.
Uses SQLAlchemy ORM for database operations.

Functions:
- create_scorecard(): Create a new scorecard
- get_scorecard(): Get scorecard by ID
- list_scorecards(): List scorecards with pagination
- update_scorecard(): Update an existing scorecard

References:
    - Spec: specs/016-feature-impact-simulation/spec.md
    - Database: src/synth_lab/infrastructure/database.py
    - ORM models: synth_lab.models.orm.legacy

Sample usage:
    from synth_lab.repositories.scorecard_repository import ScorecardRepository

    # ORM mode
    repo = ScorecardRepository(db=database_manager)
    scorecard_id = repo.create_scorecard(scorecard)
    scorecard = repo.get_scorecard(scorecard_id)

    # ORM mode (SQLAlchemy)
    repo = ScorecardRepository(session=session)

Expected output:
    FeatureScorecard instance or None if not found
"""

import json
from datetime import datetime, timezone

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from synth_lab.domain.entities import FeatureScorecard
from synth_lab.models.orm.legacy import FeatureScorecard as FeatureScorecardORM
from synth_lab.repositories.base import BaseRepository


class ScorecardRepository(BaseRepository):
    """Repository for feature scorecard persistence.

    Uses SQLAlchemy ORM for database operations.

    Usage:
        # ORM mode
        repo = ScorecardRepository(db=database_manager)

        # ORM mode (SQLAlchemy)
        repo = ScorecardRepository(session=session)
    """

    def __init__(
        self,
session: Session | None = None) -> None:
        """
        Initialize repository with database manager or session.

        Args:
            db: Legacy database manager instance.
            session: SQLAlchemy session for ORM operations.
        """
        super().__init__( session=session)
        self.logger = logger.bind(component="scorecard_repository")

    def create_scorecard(self, scorecard: FeatureScorecard) -> str:
        """
        Create a new scorecard in the database.

        Args:
            scorecard: FeatureScorecard instance to persist

        Returns:
            str: Created scorecard ID
        """
        return self._create_scorecard_orm(scorecard)

    def _create_scorecard_orm(self, scorecard: FeatureScorecard) -> str:
        """Create scorecard using ORM."""
        data = scorecard.model_dump(mode="json")
        created_at = scorecard.created_at.isoformat()
        updated_at = scorecard.updated_at.isoformat() if scorecard.updated_at else None

        orm_scorecard = FeatureScorecardORM(
            id=scorecard.id,
            experiment_id=scorecard.experiment_id,
            data=data,
            created_at=created_at,
            updated_at=updated_at)
        self._add(orm_scorecard)
        self._flush()
        self._commit()

        self.logger.info(
            f"Created scorecard {scorecard.id} for experiment {scorecard.experiment_id}"
        )
        return scorecard.id

    def get_scorecard(self, scorecard_id: str) -> FeatureScorecard | None:
        """
        Get a scorecard by ID.

        Args:
            scorecard_id: Scorecard ID to retrieve

        Returns:
            FeatureScorecard if found, None otherwise
        """
        return self._get_scorecard_orm(scorecard_id)

    def _get_scorecard_orm(self, scorecard_id: str) -> FeatureScorecard | None:
        """Get scorecard by ID using ORM."""
        stmt = select(FeatureScorecardORM).where(FeatureScorecardORM.id == scorecard_id)
        result = self.session.execute(stmt).scalar_one_or_none()
        if result is None:
            return None
        return self._orm_to_scorecard(result)

    def list_scorecards(
        self,
        limit: int = 20,
        offset: int = 0) -> tuple[list[FeatureScorecard], int]:
        """
        List scorecards with pagination.

        Args:
            limit: Maximum number of scorecards to return
            offset: Number of scorecards to skip

        Returns:
            Tuple of (list of scorecards, total count)
        """
        return self._list_scorecards_orm(limit, offset)

    def _list_scorecards_orm(
        self, limit: int, offset: int
    ) -> tuple[list[FeatureScorecard], int]:
        """List scorecards using ORM."""
        # Get total count
        count_stmt = select(func.count()).select_from(FeatureScorecardORM)
        total = self.session.execute(count_stmt).scalar() or 0

        # Get paginated results
        stmt = (
            select(FeatureScorecardORM)
            .order_by(FeatureScorecardORM.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        results = list(self.session.execute(stmt).scalars().all())

        scorecards = [self._orm_to_scorecard(orm_sc) for orm_sc in results]

        return scorecards, total

    def update_scorecard(self, scorecard: FeatureScorecard) -> bool:
        """
        Update an existing scorecard.

        Args:
            scorecard: FeatureScorecard with updated data

        Returns:
            bool: True if updated, False if not found
        """
        return self._update_scorecard_orm(scorecard)

    def _update_scorecard_orm(self, scorecard: FeatureScorecard) -> bool:
        """Update scorecard using ORM."""
        stmt = select(FeatureScorecardORM).where(FeatureScorecardORM.id == scorecard.id)
        orm_scorecard = self.session.execute(stmt).scalar_one_or_none()
        if orm_scorecard is None:
            self.logger.warning(f"Scorecard {scorecard.id} not found for update")
            return False

        # Set updated_at timestamp
        updated_scorecard = scorecard.model_copy(update={"updated_at": datetime.now(timezone.utc)})
        orm_scorecard.data = updated_scorecard.model_dump(mode="json")
        orm_scorecard.updated_at = updated_scorecard.updated_at.isoformat()
        self._flush()
        self._commit()

        self.logger.info(f"Updated scorecard {scorecard.id}")
        return True

    def delete_scorecard(self, scorecard_id: str) -> bool:
        """
        Delete a scorecard by ID.

        Args:
            scorecard_id: ID of scorecard to delete

        Returns:
            bool: True if deleted, False if not found
        """
        return self._delete_scorecard_orm(scorecard_id)

    def _delete_scorecard_orm(self, scorecard_id: str) -> bool:
        """Delete scorecard using ORM."""
        stmt = select(FeatureScorecardORM).where(FeatureScorecardORM.id == scorecard_id)
        orm_scorecard = self.session.execute(stmt).scalar_one_or_none()
        if orm_scorecard is None:
            self.logger.warning(f"Scorecard {scorecard_id} not found for deletion")
            return False

        self._delete(orm_scorecard)
        self._flush()
        self._commit()

        self.logger.info(f"Deleted scorecard {scorecard_id}")
        return True

    def list_by_experiment_id(
        self,
        experiment_id: str,
        limit: int = 20,
        offset: int = 0) -> tuple[list[FeatureScorecard], int]:
        """
        List scorecards for a specific experiment.

        Args:
            experiment_id: Experiment ID to filter by
            limit: Maximum number of scorecards to return
            offset: Number of scorecards to skip

        Returns:
            Tuple of (list of scorecards, total count)
        """
        return self._list_by_experiment_id_orm(experiment_id, limit, offset)

    def _list_by_experiment_id_orm(
        self, experiment_id: str, limit: int, offset: int
    ) -> tuple[list[FeatureScorecard], int]:
        """List scorecards by experiment ID using ORM."""
        # Get total count
        count_stmt = (
            select(func.count())
            .select_from(FeatureScorecardORM)
            .where(FeatureScorecardORM.experiment_id == experiment_id)
        )
        total = self.session.execute(count_stmt).scalar() or 0

        # Get paginated results
        stmt = (
            select(FeatureScorecardORM)
            .where(FeatureScorecardORM.experiment_id == experiment_id)
            .order_by(FeatureScorecardORM.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        results = list(self.session.execute(stmt).scalars().all())

        scorecards = [self._orm_to_scorecard(orm_sc) for orm_sc in results]

        return scorecards, total

    # =========================================================================
    # ORM conversion methods
    # =========================================================================

    def _orm_to_scorecard(self, orm_scorecard: FeatureScorecardORM) -> FeatureScorecard:
        """Convert ORM model to FeatureScorecard entity."""
        return FeatureScorecard.model_validate(orm_scorecard.data)


if __name__ == "__main__":
    import sys
    import tempfile
    from pathlib import Path

    from synth_lab.domain.entities import (
        ScorecardDimension,
        ScorecardIdentification)

    print("=== Scorecard Repository Validation ===\n")

    all_validation_failures = []
    total_tests = 0

    # Use temp database
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        init_database(db_path)
        db = DatabaseManager(db_path)
        repo = ScorecardRepository()

        # Create test scorecard
        test_scorecard = FeatureScorecard(
            identification=ScorecardIdentification(
                feature_name="Test Feature",
                use_scenario="First use"),
            description_text="Test description",
            complexity=ScorecardDimension(score=0.4),
            initial_effort=ScorecardDimension(score=0.3),
            perceived_risk=ScorecardDimension(score=0.2),
            time_to_value=ScorecardDimension(score=0.5))

        # Test 1: Create scorecard
        total_tests += 1
        try:
            scorecard_id = repo.create_scorecard(test_scorecard)
            if scorecard_id != test_scorecard.id:
                all_validation_failures.append(
                    f"Create: ID mismatch {scorecard_id} != {test_scorecard.id}"
                )
            else:
                print(f"Test 1 PASSED: Created scorecard {scorecard_id}")
        except Exception as e:
            all_validation_failures.append(f"Create failed: {e}")

        # Test 2: Get scorecard
        total_tests += 1
        try:
            retrieved = repo.get_scorecard(test_scorecard.id)
            if retrieved is None:
                all_validation_failures.append("Get: Scorecard not found")
            elif retrieved.identification.feature_name != "Test Feature":
                all_validation_failures.append(
                    f"Get: Feature name mismatch: {retrieved.identification.feature_name}"
                )
            else:
                print(f"Test 2 PASSED: Retrieved scorecard {retrieved.id}")
        except Exception as e:
            all_validation_failures.append(f"Get failed: {e}")

        # Test 3: Get non-existent scorecard
        total_tests += 1
        try:
            result = repo.get_scorecard("nonexistent123")
            if result is not None:
                all_validation_failures.append("Get non-existent: Should return None")
            else:
                print("Test 3 PASSED: Non-existent scorecard returns None")
        except Exception as e:
            all_validation_failures.append(f"Get non-existent failed: {e}")

        # Test 4: List scorecards
        total_tests += 1
        try:
            scorecards, total = repo.list_scorecards(limit=10, offset=0)
            if total != 1:
                all_validation_failures.append(f"List: Expected total=1, got {total}")
            elif len(scorecards) != 1:
                all_validation_failures.append(f"List: Expected 1 scorecard, got {len(scorecards)}")
            else:
                print(f"Test 4 PASSED: Listed {len(scorecards)} scorecards, total={total}")
        except Exception as e:
            all_validation_failures.append(f"List failed: {e}")

        # Test 5: Update scorecard
        total_tests += 1
        try:
            retrieved = repo.get_scorecard(test_scorecard.id)
            updated_scorecard = retrieved.model_copy(
                update={"description_text": "Updated description"}
            )
            updated = repo.update_scorecard(updated_scorecard)
            if not updated:
                all_validation_failures.append("Update: Should return True")
            else:
                # Verify update
                re_retrieved = repo.get_scorecard(test_scorecard.id)
                if re_retrieved.description_text != "Updated description":
                    all_validation_failures.append("Update: Description not updated")
                else:
                    print("Test 5 PASSED: Updated scorecard")
        except Exception as e:
            all_validation_failures.append(f"Update failed: {e}")

        # Test 6: Update non-existent scorecard
        total_tests += 1
        try:
            fake_scorecard = FeatureScorecard(
                id="fakefake",
                identification=ScorecardIdentification(
                    feature_name="Fake",
                    use_scenario="Fake"),
                description_text="Fake",
                complexity=ScorecardDimension(score=0.1),
                initial_effort=ScorecardDimension(score=0.1),
                perceived_risk=ScorecardDimension(score=0.1),
                time_to_value=ScorecardDimension(score=0.1))
            updated = repo.update_scorecard(fake_scorecard)
            if updated:
                all_validation_failures.append("Update non-existent: Should return False")
            else:
                print("Test 6 PASSED: Non-existent update returns False")
        except Exception as e:
            all_validation_failures.append(f"Update non-existent failed: {e}")

        # Test 7: Delete scorecard
        total_tests += 1
        try:
            deleted = repo.delete_scorecard(test_scorecard.id)
            if not deleted:
                all_validation_failures.append("Delete: Should return True")
            else:
                # Verify deletion
                result = repo.get_scorecard(test_scorecard.id)
                if result is not None:
                    all_validation_failures.append("Delete: Scorecard should be deleted")
                else:
                    print("Test 7 PASSED: Deleted scorecard")
        except Exception as e:
            all_validation_failures.append(f"Delete failed: {e}")

        # Test 8: List empty
        total_tests += 1
        try:
            scorecards, total = repo.list_scorecards()
            if total != 0:
                all_validation_failures.append(f"List empty: Expected total=0, got {total}")
            else:
                print("Test 8 PASSED: Empty list returns total=0")
        except Exception as e:
            all_validation_failures.append(f"List empty failed: {e}")

        db.close()

    # Final result
    print()
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
