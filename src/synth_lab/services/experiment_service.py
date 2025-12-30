"""
ExperimentService for synth-lab.

Business logic layer for experiment operations with embedded scorecard support.

References:
    - Spec: specs/019-experiment-refactor/spec.md
    - Data model: specs/019-experiment-refactor/data-model.md
"""

from synth_lab.domain.entities.experiment import Experiment, ScorecardData
from synth_lab.models.pagination import PaginatedResponse, PaginationParams
from synth_lab.repositories.experiment_repository import (
    ExperimentRepository,
    ExperimentSummary,
)


class ExperimentService:
    """Service for experiment business logic."""

    # Validation constants
    NAME_MAX_LENGTH = 100
    HYPOTHESIS_MAX_LENGTH = 500
    DESCRIPTION_MAX_LENGTH = 2000

    def __init__(self, repository: ExperimentRepository | None = None):
        """
        Initialize service.

        Args:
            repository: Experiment repository. Defaults to new instance.
        """
        self.repository = repository or ExperimentRepository()

    def create_experiment(
        self,
        name: str,
        hypothesis: str,
        description: str | None = None,
        scorecard_data: ScorecardData | None = None,
    ) -> Experiment:
        """
        Create a new experiment.

        Args:
            name: Short name of the feature (max 100 chars).
            hypothesis: Description of hypothesis to test (max 500 chars).
            description: Additional context (max 2000 chars).
            scorecard_data: Optional embedded scorecard data.

        Returns:
            Created experiment.

        Raises:
            ValueError: If validation fails.
        """
        # Validate required fields
        if not name or not name.strip():
            raise ValueError("name is required and cannot be empty")
        if not hypothesis or not hypothesis.strip():
            raise ValueError("hypothesis is required and cannot be empty")

        # Validate max lengths
        if len(name) > self.NAME_MAX_LENGTH:
            raise ValueError(
                f"name must not exceed {self.NAME_MAX_LENGTH} characters (got {len(name)})"
            )
        if len(hypothesis) > self.HYPOTHESIS_MAX_LENGTH:
            raise ValueError(
                f"hypothesis must not exceed {self.HYPOTHESIS_MAX_LENGTH} characters (got {len(hypothesis)})"
            )
        if description and len(description) > self.DESCRIPTION_MAX_LENGTH:
            raise ValueError(
                f"description must not exceed {self.DESCRIPTION_MAX_LENGTH} characters"
            )

        # Create experiment entity
        experiment = Experiment(
            name=name.strip(),
            hypothesis=hypothesis.strip(),
            description=description.strip() if description else None,
            scorecard_data=scorecard_data,
        )

        return self.repository.create(experiment)

    def get_experiment(self, experiment_id: str) -> Experiment | None:
        """
        Get an experiment by ID.

        Args:
            experiment_id: Experiment ID.

        Returns:
            Experiment if found, None otherwise.
        """
        return self.repository.get_by_id(experiment_id)

    def get_experiment_detail(self, experiment_id: str) -> ExperimentSummary | None:
        """
        Get experiment detail with simulation and interview counts.

        Args:
            experiment_id: Experiment ID.

        Returns:
            ExperimentSummary with counts if found, None otherwise.
        """
        # List experiments and filter by ID to get counts
        params = PaginationParams(limit=200, offset=0)
        result = self.repository.list_experiments(params)

        for exp in result.data:
            if exp.id == experiment_id:
                return exp

        return None

    def list_experiments(
        self, params: PaginationParams | None = None
    ) -> PaginatedResponse[ExperimentSummary]:
        """
        List experiments with pagination.

        Args:
            params: Pagination parameters.

        Returns:
            Paginated list of experiment summaries.
        """
        params = params or PaginationParams()
        return self.repository.list_experiments(params)

    def update_experiment(
        self,
        experiment_id: str,
        name: str | None = None,
        hypothesis: str | None = None,
        description: str | None = None,
    ) -> Experiment | None:
        """
        Update an experiment.

        Args:
            experiment_id: ID of experiment to update.
            name: New name (optional).
            hypothesis: New hypothesis (optional).
            description: New description (optional).

        Returns:
            Updated experiment if found, None otherwise.

        Raises:
            ValueError: If validation fails.
        """
        # Validate max lengths if provided
        if name is not None:
            if len(name) > self.NAME_MAX_LENGTH:
                raise ValueError(f"name must not exceed {self.NAME_MAX_LENGTH} characters")
        if hypothesis is not None:
            if len(hypothesis) > self.HYPOTHESIS_MAX_LENGTH:
                raise ValueError(
                    f"hypothesis must not exceed {self.HYPOTHESIS_MAX_LENGTH} characters"
                )
        if description is not None:
            if len(description) > self.DESCRIPTION_MAX_LENGTH:
                raise ValueError(
                    f"description must not exceed {self.DESCRIPTION_MAX_LENGTH} characters"
                )

        return self.repository.update(
            experiment_id,
            name=name,
            hypothesis=hypothesis,
            description=description,
        )

    def delete_experiment(self, experiment_id: str) -> bool:
        """
        Delete an experiment.

        Args:
            experiment_id: ID of experiment to delete.

        Returns:
            True if deleted, False if not found.
        """
        return self.repository.delete(experiment_id)

    def update_scorecard(
        self,
        experiment_id: str,
        scorecard_data: ScorecardData,
    ) -> Experiment | None:
        """
        Update the scorecard data of an experiment.

        Args:
            experiment_id: ID of experiment to update.
            scorecard_data: New scorecard data.

        Returns:
            Updated experiment if found, None otherwise.
        """
        return self.repository.update_scorecard(experiment_id, scorecard_data)

    def get_experiment_with_scorecard(self, experiment_id: str) -> Experiment | None:
        """
        Get an experiment ensuring scorecard data is included.

        Args:
            experiment_id: Experiment ID.

        Returns:
            Experiment with scorecard_data if found, None otherwise.
        """
        experiment = self.repository.get_by_id(experiment_id)
        if experiment is None:
            return None

        return experiment

    def has_scorecard(self, experiment_id: str) -> bool:
        """
        Check if an experiment has a scorecard.

        Args:
            experiment_id: Experiment ID.

        Returns:
            True if experiment has scorecard, False otherwise.
        """
        experiment = self.repository.get_by_id(experiment_id)
        if experiment is None:
            return False

        return experiment.has_scorecard()


if __name__ == "__main__":
    import sys
    import tempfile
    from pathlib import Path

    from synth_lab.infrastructure.database import DatabaseManager, init_database

    # Validation
    all_validation_failures = []
    total_tests = 0

    # Use a temporary database for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db_path = Path(tmpdir) / "test.db"
        init_database(test_db_path)
        db = DatabaseManager(test_db_path)
        repo = ExperimentRepository(db)
        service = ExperimentService(repo)

        # Test 1: Create experiment
        total_tests += 1
        try:
            exp = service.create_experiment(
                name="Test Feature",
                hypothesis="Users will prefer this approach",
            )
            if not exp.id.startswith("exp_"):
                all_validation_failures.append(f"ID should start with exp_: {exp.id}")
        except Exception as e:
            all_validation_failures.append(f"Create experiment failed: {e}")

        # Test 2: Validate name required
        total_tests += 1
        try:
            service.create_experiment(name="", hypothesis="Valid")
            all_validation_failures.append("Should reject empty name")
        except ValueError:
            pass  # Expected

        # Test 3: Validate hypothesis required
        total_tests += 1
        try:
            service.create_experiment(name="Valid", hypothesis="")
            all_validation_failures.append("Should reject empty hypothesis")
        except ValueError:
            pass  # Expected

        # Test 4: Validate name max length
        total_tests += 1
        try:
            service.create_experiment(name="x" * 101, hypothesis="Valid")
            all_validation_failures.append("Should reject name > 100 chars")
        except ValueError:
            pass  # Expected

        # Test 5: Get experiment
        total_tests += 1
        try:
            retrieved = service.get_experiment(exp.id)
            if retrieved is None:
                all_validation_failures.append("Get experiment returned None")
            elif retrieved.name != "Test Feature":
                all_validation_failures.append(f"Name mismatch: {retrieved.name}")
        except Exception as e:
            all_validation_failures.append(f"Get experiment failed: {e}")

        # Test 6: List experiments
        total_tests += 1
        try:
            result = service.list_experiments()
            if len(result.data) < 1:
                all_validation_failures.append("Should have at least 1 experiment")
        except Exception as e:
            all_validation_failures.append(f"List experiments failed: {e}")

        # Test 7: Create experiment with scorecard
        total_tests += 1
        try:
            from synth_lab.domain.entities.experiment import ScorecardDimension

            scorecard = ScorecardData(
                feature_name="Test Feature",
                description_text="A test feature for validation",
                complexity=ScorecardDimension(score=0.3),
                initial_effort=ScorecardDimension(score=0.4),
                perceived_risk=ScorecardDimension(score=0.2),
                time_to_value=ScorecardDimension(score=0.5),
            )
            exp_with_sc = service.create_experiment(
                name="Feature with Scorecard",
                hypothesis="Test hypothesis",
                scorecard_data=scorecard,
            )
            if not exp_with_sc.has_scorecard():
                all_validation_failures.append("Experiment should have scorecard")
            elif exp_with_sc.scorecard_data.feature_name != "Test Feature":
                all_validation_failures.append("Scorecard feature_name mismatch")
        except Exception as e:
            all_validation_failures.append(f"Create with scorecard failed: {e}")

        # Test 8: Update scorecard
        total_tests += 1
        try:
            new_scorecard = ScorecardData(
                feature_name="Updated Feature",
                description_text="Updated description",
                complexity=ScorecardDimension(score=0.6),
                initial_effort=ScorecardDimension(score=0.5),
                perceived_risk=ScorecardDimension(score=0.4),
                time_to_value=ScorecardDimension(score=0.3),
            )
            updated = service.update_scorecard(exp.id, new_scorecard)
            if updated is None:
                all_validation_failures.append("Update scorecard returned None")
            elif not updated.has_scorecard():
                all_validation_failures.append("Updated exp should have scorecard")
            elif updated.scorecard_data.feature_name != "Updated Feature":
                all_validation_failures.append("Updated scorecard feature_name mismatch")
        except Exception as e:
            all_validation_failures.append(f"Update scorecard failed: {e}")

        # Test 9: has_scorecard method
        total_tests += 1
        try:
            has_sc = service.has_scorecard(exp.id)
            if not has_sc:
                all_validation_failures.append("has_scorecard should return True")
        except Exception as e:
            all_validation_failures.append(f"has_scorecard failed: {e}")

        # Test 10: get_experiment_with_scorecard
        total_tests += 1
        try:
            exp_sc = service.get_experiment_with_scorecard(exp.id)
            if exp_sc is None:
                all_validation_failures.append("get_experiment_with_scorecard returned None")
            elif not exp_sc.has_scorecard():
                all_validation_failures.append("Should have scorecard data")
        except Exception as e:
            all_validation_failures.append(f"get_experiment_with_scorecard failed: {e}")

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
