"""
InterviewGuideRepository for synth-lab.

Data access layer for interview guide data in SQLite database.
Interview guides are 1:1 with experiments and contain the context for interviews.

References:
    - Database module: synth_lab.infrastructure.database
"""

from datetime import datetime, timezone

from pydantic import BaseModel, Field

from synth_lab.infrastructure.database import DatabaseManager
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
    """Repository for interview guide data access."""

    def __init__(self, db: DatabaseManager | None = None):
        super().__init__(db)

    def create(self, guide: InterviewGuide) -> InterviewGuide:
        """
        Create a new interview guide.

        Args:
            guide: InterviewGuide entity to create.

        Returns:
            Created interview guide.
        """
        self.db.execute(
            """
            INSERT INTO interview_guide (
                experiment_id, context_definition, questions,
                context_examples, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                guide.experiment_id,
                guide.context_definition,
                guide.questions,
                guide.context_examples,
                guide.created_at.isoformat(),
                guide.updated_at.isoformat() if guide.updated_at else None,
            ),
        )
        return guide

    def get_by_experiment_id(self, experiment_id: str) -> InterviewGuide | None:
        """
        Get interview guide by experiment ID.

        Args:
            experiment_id: Experiment ID to retrieve guide for.

        Returns:
            InterviewGuide if found, None otherwise.
        """
        row = self.db.fetchone(
            "SELECT * FROM interview_guide WHERE experiment_id = ?",
            (experiment_id,),
        )
        if row is None:
            return None
        return self._row_to_guide(row)

    def exists(self, experiment_id: str) -> bool:
        """
        Check if interview guide exists for an experiment.

        Args:
            experiment_id: Experiment ID to check.

        Returns:
            True if guide exists, False otherwise.
        """
        row = self.db.fetchone(
            "SELECT 1 FROM interview_guide WHERE experiment_id = ?",
            (experiment_id,),
        )
        return row is not None

    def update(
        self,
        experiment_id: str,
        context_definition: str | None = None,
        questions: str | None = None,
        context_examples: str | None = None,
    ) -> InterviewGuide | None:
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
        existing = self.get_by_experiment_id(experiment_id)
        if existing is None:
            return None

        updates = []
        params = []

        if context_definition is not None:
            updates.append("context_definition = ?")
            params.append(context_definition)
        if questions is not None:
            updates.append("questions = ?")
            params.append(questions)
        if context_examples is not None:
            updates.append("context_examples = ?")
            params.append(context_examples)

        # Always set updated_at
        updated_at = datetime.now(timezone.utc)
        updates.append("updated_at = ?")
        params.append(updated_at.isoformat())

        params.append(experiment_id)

        if updates:
            query = f"UPDATE interview_guide SET {', '.join(updates)} WHERE experiment_id = ?"
            self.db.execute(query, tuple(params))

        return self.get_by_experiment_id(experiment_id)

    def delete(self, experiment_id: str) -> bool:
        """
        Delete an interview guide.

        Args:
            experiment_id: Experiment ID of the guide to delete.

        Returns:
            True if deleted, False if not found.
        """
        existing = self.get_by_experiment_id(experiment_id)
        if existing is None:
            return False

        self.db.execute(
            "DELETE FROM interview_guide WHERE experiment_id = ?",
            (experiment_id,),
        )
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
            updated_at=updated_at,
        )


if __name__ == "__main__":
    import sys
    import tempfile
    from pathlib import Path

    from synth_lab.infrastructure.database import DatabaseManager, init_database

    # Validation
    all_validation_failures = []
    total_tests = 0

    with tempfile.TemporaryDirectory() as tmpdir:
        test_db_path = Path(tmpdir) / "test.db"
        init_database(test_db_path)
        db = DatabaseManager(test_db_path)
        repo = InterviewGuideRepository(db)

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
                created_at=datetime.now(timezone.utc),
            )
            result = repo.create(guide)
            if result.experiment_id != "exp_test1":
                all_validation_failures.append(
                    f"ID mismatch: {result.experiment_id} != exp_test1"
                )
        except Exception as e:
            all_validation_failures.append(f"Create guide failed: {e}")

        # Test 2: Get guide by experiment ID
        total_tests += 1
        try:
            retrieved = repo.get_by_experiment_id("exp_test1")
            if retrieved is None:
                all_validation_failures.append("Get by experiment ID returned None")
            elif retrieved.context_definition != "Test context definition":
                all_validation_failures.append(
                    f"Context mismatch: {retrieved.context_definition}"
                )
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
                all_validation_failures.append(
                    "exists() should return False for non-existent"
                )
        except Exception as e:
            all_validation_failures.append(f"exists() test failed: {e}")

        # Test 4: Update guide
        total_tests += 1
        try:
            updated = repo.update("exp_test1", context_definition="Updated context")
            if updated is None:
                all_validation_failures.append("Update returned None")
            elif updated.context_definition != "Updated context":
                all_validation_failures.append(
                    f"Context not updated: {updated.context_definition}"
                )
            elif updated.updated_at is None:
                all_validation_failures.append("updated_at not set")
        except Exception as e:
            all_validation_failures.append(f"Update failed: {e}")

        # Test 5: Get non-existent guide
        total_tests += 1
        try:
            result = repo.get_by_experiment_id("exp_nonexistent")
            if result is not None:
                all_validation_failures.append(
                    "Should return None for non-existent guide"
                )
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
                all_validation_failures.append(
                    "Delete non-existent should return False"
                )
        except Exception as e:
            all_validation_failures.append(f"Delete non-existent failed: {e}")

        db.close()

    # Final validation result
    if all_validation_failures:
        print(
            f"VALIDATION FAILED - {len(all_validation_failures)} of {total_tests} tests failed:"
        )
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
