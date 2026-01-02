"""
InterviewGuideRepository for synth-lab.

Data access layer for interview guide data in SQLite database.
Interview guides are 1:1 with experiments and contain the context for interviews.

References:
    - Database module: synth_lab.infrastructure.database
    - ORM models: synth_lab.models.orm.experiment
"""

from datetime import datetime, timezone

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from synth_lab.models.orm.experiment import InterviewGuide as InterviewGuideORM
from synth_lab.repositories.base import BaseRepository


class InterviewGuide(BaseModel):
    """Interview guide entity for an experiment."""

    experiment_id: str = Field(description="Experiment ID (primary key).")
    context_definition: str | None = Field(default=None, description="Context definition.")
    questions: str | None = Field(default=None, description="Interview questions.")
    context_examples: str | None = Field(default=None, description="Context examples.")
    created_at: datetime = Field(description="Creation timestamp.")
    updated_at: datetime | None = Field(default=None, description="Last update timestamp.")


class InterviewGuideRepository(BaseRepository):
    """Repository for interview guide data access.

    Uses SQLAlchemy ORM for database operations.
    """

    def __init__(
        self,
session: Session | None = None):
        super().__init__( session=session)

    def create(self, guide: InterviewGuide) -> InterviewGuide:
        """
        Create a new interview guide.

        Args:
            guide: InterviewGuide entity to create.

        Returns:
            Created interview guide.
        """
        orm_guide = InterviewGuideORM(
            experiment_id=guide.experiment_id,
            context_definition=guide.context_definition,
            questions=guide.questions,
            context_examples=guide.context_examples,
            created_at=guide.created_at.isoformat(),
            updated_at=guide.updated_at.isoformat() if guide.updated_at else None)
        self._add(orm_guide)
        self._flush()
        self._commit()
        return guide
    def get_by_experiment_id(self, experiment_id: str) -> InterviewGuide | None:
        """
        Get interview guide by experiment ID.

        Args:
            experiment_id: Experiment ID to retrieve guide for.

        Returns:
            InterviewGuide if found, None otherwise.
        """
        orm_guide = self.session.get(InterviewGuideORM, experiment_id)
        if orm_guide is None:
            return None
        return self._orm_to_guide(orm_guide)
    def exists(self, experiment_id: str) -> bool:
        """
        Check if interview guide exists for an experiment.

        Args:
            experiment_id: Experiment ID to check.

        Returns:
            True if guide exists, False otherwise.
        """
        orm_guide = self.session.get(InterviewGuideORM, experiment_id)
        return orm_guide is not None
    def update(
        self,
        experiment_id: str,
        context_definition: str | None = None,
        questions: str | None = None,
        context_examples: str | None = None) -> InterviewGuide | None:
        """
        Update an interview guide.

        Args:
            experiment_id: Experiment ID of the guide to update.
            context_definition: New context definition (optional).
            questions: New questions (optional).
            context_examples: New context examples (optional).

        Returns:
            Updated interview guide if found, None otherwise.
        """
        orm_guide = self.session.get(InterviewGuideORM, experiment_id)
        if orm_guide is None:
            return None

        if context_definition is not None:
            orm_guide.context_definition = context_definition
        if questions is not None:
            orm_guide.questions = questions
        if context_examples is not None:
            orm_guide.context_examples = context_examples

        orm_guide.updated_at = datetime.now(timezone.utc).isoformat()
        self._flush()
        self._commit()
        return self._orm_to_guide(orm_guide)
    def delete(self, experiment_id: str) -> bool:
        """
        Delete an interview guide.

        Args:
            experiment_id: Experiment ID of the guide to delete.

        Returns:
            True if deleted, False if not found.
        """
        orm_guide = self.session.get(InterviewGuideORM, experiment_id)
        if orm_guide is None:
            return False
        self.session.delete(orm_guide)
        self._flush()
        self._commit()
        return True
    def _row_to_guide(self, row) -> InterviewGuide:
        """Convert a database row to InterviewGuide entity."""
        created_at = row["created_at"]
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        updated_at = row["updated_at"]
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)

        return InterviewGuide(
            experiment_id=row["experiment_id"],
            context_definition=row["context_definition"],
            questions=row["questions"],
            context_examples=row["context_examples"],
            created_at=created_at,
            updated_at=updated_at)

    def _orm_to_guide(self, orm_guide: InterviewGuideORM) -> InterviewGuide:
        """Convert ORM model to InterviewGuide entity."""
        created_at = orm_guide.created_at
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        updated_at = orm_guide.updated_at
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)

        return InterviewGuide(
            experiment_id=orm_guide.experiment_id,
            context_definition=orm_guide.context_definition,
            questions=orm_guide.questions,
            context_examples=orm_guide.context_examples,
            created_at=created_at,
            updated_at=updated_at)


if __name__ == "__main__":
    import sys
    import tempfile
    from pathlib import Path


    # Validation
    all_validation_failures = []
    total_tests = 0

    with tempfile.TemporaryDirectory() as tmpdir:
        test_db_path = Path(tmpdir) / "test.db"
        init_database(test_db_path)
        db = DatabaseManager(test_db_path)
        repo = InterviewGuideRepository()

        # Create a test experiment first
        db.execute(
            """
            INSERT INTO experiments (id, name, hypothesis, created_at)
            VALUES ('exp_test1', 'Test Experiment', 'Test hypothesis', datetime('now'))
            """
        )

        # Test 1: Create interview guide
        total_tests += 1
        try:
            guide = InterviewGuide(
                experiment_id="exp_test1",
                context_definition="Test context definition",
                questions="Q1: Test question?",
                context_examples="Example 1",
                created_at=datetime.now(timezone.utc))
            result = repo.create(guide)
            if result.experiment_id != "exp_test1":
                all_validation_failures.append(f"ID mismatch: {result.experiment_id} != exp_test1")
        except Exception as e:
            all_validation_failures.append(f"Create guide failed: {e}")

        # Test 2: Get guide by experiment ID
        total_tests += 1
        try:
            retrieved = repo.get_by_experiment_id("exp_test1")
            if retrieved is None:
                all_validation_failures.append("Get by experiment ID returned None")
            elif retrieved.context_definition != "Test context definition":
                all_validation_failures.append(f"Context mismatch: {retrieved.context_definition}")
        except Exception as e:
            all_validation_failures.append(f"Get by experiment ID failed: {e}")

        # Test 3: Check exists
        total_tests += 1
        try:
            exists = repo.exists("exp_test1")
            if not exists:
                all_validation_failures.append("exists() should return True")

            not_exists = repo.exists("exp_nonexistent")
            if not_exists:
                all_validation_failures.append("exists() should return False for non-existent")
        except Exception as e:
            all_validation_failures.append(f"exists() test failed: {e}")

        # Test 4: Update guide
        total_tests += 1
        try:
            updated = repo.update("exp_test1", context_definition="Updated context")
            if updated is None:
                all_validation_failures.append("Update returned None")
            elif updated.context_definition != "Updated context":
                all_validation_failures.append(f"Context not updated: {updated.context_definition}")
            elif updated.updated_at is None:
                all_validation_failures.append("updated_at not set")
        except Exception as e:
            all_validation_failures.append(f"Update failed: {e}")

        # Test 5: Get non-existent guide
        total_tests += 1
        try:
            result = repo.get_by_experiment_id("exp_nonexistent")
            if result is not None:
                all_validation_failures.append("Should return None for non-existent guide")
        except Exception as e:
            all_validation_failures.append(f"Get non-existent failed: {e}")

        # Test 6: Delete guide
        total_tests += 1
        try:
            result = repo.delete("exp_test1")
            if not result:
                all_validation_failures.append("Delete returned False")
            if repo.exists("exp_test1"):
                all_validation_failures.append("Guide still exists after delete")
        except Exception as e:
            all_validation_failures.append(f"Delete failed: {e}")

        # Test 7: Delete non-existent
        total_tests += 1
        try:
            result = repo.delete("exp_nonexistent")
            if result:
                all_validation_failures.append("Delete non-existent should return False")
        except Exception as e:
            all_validation_failures.append(f"Delete non-existent failed: {e}")

        db.close()

    # Final validation result
    if all_validation_failures:
        print(f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
