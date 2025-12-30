"""
AnalysisService for synth-lab.

Business logic layer for quantitative analysis operations.
Supports 1:1 relationship with experiments.

References:
    - Spec: specs/019-experiment-refactor/spec.md
    - Data model: specs/019-experiment-refactor/data-model.md
"""

from datetime import datetime, timezone

from loguru import logger

from synth_lab.domain.entities.analysis_run import (
    AggregatedOutcomes,
    AnalysisConfig,
    AnalysisRun,
)
from synth_lab.infrastructure.database import DatabaseManager, get_database
from synth_lab.repositories.analysis_repository import AnalysisRepository
from synth_lab.repositories.experiment_repository import ExperimentRepository


class AnalysisService:
    """Service for quantitative analysis business logic."""

    def __init__(
        self,
        db: DatabaseManager | None = None,
        analysis_repo: AnalysisRepository | None = None,
        experiment_repo: ExperimentRepository | None = None,
    ):
        """
        Initialize analysis service.

        Args:
            db: Database manager. Defaults to global instance.
            analysis_repo: Analysis repository. Defaults to new instance.
            experiment_repo: Experiment repository. Defaults to new instance.
        """
        self.db = db or get_database()
        self.analysis_repo = analysis_repo or AnalysisRepository(self.db)
        self.experiment_repo = experiment_repo or ExperimentRepository(self.db)
        self.logger = logger.bind(component="analysis_service")

    def get_analysis(self, experiment_id: str) -> AnalysisRun | None:
        """
        Get the analysis for an experiment.

        Since it's a 1:1 relationship, returns single analysis or None.

        Args:
            experiment_id: Parent experiment ID.

        Returns:
            AnalysisRun if found, None otherwise.
        """
        return self.analysis_repo.get_by_experiment_id(experiment_id)

    def get_analysis_by_id(self, analysis_id: str) -> AnalysisRun | None:
        """
        Get an analysis by its ID.

        Args:
            analysis_id: Analysis run ID.

        Returns:
            AnalysisRun if found, None otherwise.
        """
        return self.analysis_repo.get_by_id(analysis_id)

    def create_analysis(
        self,
        experiment_id: str,
        config: AnalysisConfig | None = None,
    ) -> AnalysisRun:
        """
        Create a new analysis run for an experiment.

        Validates that the experiment exists and has a scorecard.
        Enforces 1:1 relationship (only one analysis per experiment).

        Args:
            experiment_id: Parent experiment ID.
            config: Analysis configuration. Defaults to standard config.

        Returns:
            Created analysis run.

        Raises:
            ValueError: If experiment not found or doesn't have scorecard.
            RuntimeError: If experiment already has an analysis.
        """
        # Validate experiment exists
        experiment = self.experiment_repo.get_by_id(experiment_id)
        if experiment is None:
            raise ValueError(f"Experiment not found: {experiment_id}")

        # Validate experiment has scorecard
        if not experiment.has_scorecard():
            raise ValueError(
                f"Experiment {experiment_id} must have a scorecard before running analysis"
            )

        # Check for existing analysis (1:1 constraint)
        existing = self.analysis_repo.get_by_experiment_id(experiment_id)
        if existing is not None:
            raise RuntimeError(f"Experiment {experiment_id} already has an analysis: {existing.id}")

        # Create analysis with default or provided config
        analysis = AnalysisRun(
            experiment_id=experiment_id,
            config=config or AnalysisConfig(),
            status="pending",
            started_at=datetime.now(timezone.utc),
        )

        return self.analysis_repo.create(analysis)

    def start_analysis(self, analysis_id: str) -> AnalysisRun | None:
        """
        Mark an analysis as running.

        Args:
            analysis_id: Analysis ID to start.

        Returns:
            Updated analysis if found, None otherwise.

        Raises:
            RuntimeError: If analysis is already running or completed.
        """
        analysis = self.analysis_repo.get_by_id(analysis_id)
        if analysis is None:
            return None

        if analysis.status == "running":
            raise RuntimeError(f"Analysis {analysis_id} is already running")
        if analysis.status == "completed":
            raise RuntimeError(f"Analysis {analysis_id} is already completed")

        return self.analysis_repo.update_status(analysis_id, status="running")

    def complete_analysis(
        self,
        analysis_id: str,
        total_synths: int,
        aggregated_outcomes: AggregatedOutcomes,
        execution_time_seconds: float,
    ) -> AnalysisRun | None:
        """
        Mark an analysis as completed with results.

        Args:
            analysis_id: Analysis ID to complete.
            total_synths: Total synths processed.
            aggregated_outcomes: Aggregated results.
            execution_time_seconds: Execution time.

        Returns:
            Updated analysis if found, None otherwise.
        """
        return self.analysis_repo.update_status(
            analysis_id=analysis_id,
            status="completed",
            completed_at=datetime.now(timezone.utc),
            total_synths=total_synths,
            aggregated_outcomes=aggregated_outcomes,
            execution_time_seconds=execution_time_seconds,
        )

    def fail_analysis(self, analysis_id: str) -> AnalysisRun | None:
        """
        Mark an analysis as failed.

        Args:
            analysis_id: Analysis ID to mark as failed.

        Returns:
            Updated analysis if found, None otherwise.
        """
        return self.analysis_repo.update_status(
            analysis_id=analysis_id,
            status="failed",
            completed_at=datetime.now(timezone.utc),
        )

    def delete_analysis(self, experiment_id: str) -> bool:
        """
        Delete the analysis for an experiment.

        Args:
            experiment_id: Parent experiment ID.

        Returns:
            True if deleted, False if not found.
        """
        return self.analysis_repo.delete_by_experiment_id(experiment_id)

    def rerun_analysis(
        self,
        experiment_id: str,
        config: AnalysisConfig | None = None,
    ) -> AnalysisRun:
        """
        Delete existing analysis and create a new one.

        Args:
            experiment_id: Parent experiment ID.
            config: New analysis configuration.

        Returns:
            New analysis run.

        Raises:
            ValueError: If experiment not found or doesn't have scorecard.
        """
        # Delete existing if present
        self.delete_analysis(experiment_id)

        # Create new analysis
        return self.create_analysis(experiment_id, config)

    def has_analysis(self, experiment_id: str) -> bool:
        """
        Check if an experiment has an analysis.

        Args:
            experiment_id: Experiment ID.

        Returns:
            True if analysis exists, False otherwise.
        """
        return self.analysis_repo.get_by_experiment_id(experiment_id) is not None


if __name__ == "__main__":
    import sys
    import tempfile
    from pathlib import Path

    from synth_lab.domain.entities.experiment import (
        Experiment,
        ScorecardData,
        ScorecardDimension,
    )
    from synth_lab.infrastructure.database import init_database

    all_validation_failures: list[str] = []
    total_tests = 0

    # Use a temporary database for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db_path = Path(tmpdir) / "test.db"
        init_database(test_db_path)
        db = DatabaseManager(test_db_path)
        exp_repo = ExperimentRepository(db)
        ana_repo = AnalysisRepository(db)
        service = AnalysisService(db, ana_repo, exp_repo)

        # Create experiment with scorecard
        scorecard = ScorecardData(
            feature_name="Test Feature",
            description_text="Test description",
            complexity=ScorecardDimension(score=0.3),
            initial_effort=ScorecardDimension(score=0.4),
            perceived_risk=ScorecardDimension(score=0.2),
            time_to_value=ScorecardDimension(score=0.5),
        )
        exp = Experiment(name="Test", hypothesis="Test", scorecard_data=scorecard)
        exp_repo.create(exp)

        # Create experiment without scorecard
        exp_no_sc = Experiment(name="No Scorecard", hypothesis="Test")
        exp_repo.create(exp_no_sc)

        # Test 1: Create analysis
        total_tests += 1
        try:
            analysis = service.create_analysis(exp.id)
            if not analysis.id.startswith("ana_"):
                all_validation_failures.append(f"ID should start with ana_: {analysis.id}")
            if analysis.status != "pending":
                all_validation_failures.append(f"Status should be pending: {analysis.status}")
        except Exception as e:
            all_validation_failures.append(f"Create analysis failed: {e}")

        # Test 2: Reject analysis for experiment without scorecard
        total_tests += 1
        try:
            service.create_analysis(exp_no_sc.id)
            all_validation_failures.append("Should reject experiment without scorecard")
        except ValueError:
            pass  # Expected
        except Exception as e:
            all_validation_failures.append(f"Unexpected error for no scorecard: {e}")

        # Test 3: Get analysis
        total_tests += 1
        try:
            retrieved = service.get_analysis(exp.id)
            if retrieved is None:
                all_validation_failures.append("Get analysis returned None")
            elif retrieved.id != analysis.id:
                all_validation_failures.append("Analysis ID mismatch")
        except Exception as e:
            all_validation_failures.append(f"Get analysis failed: {e}")

        # Test 4: Start analysis
        total_tests += 1
        try:
            started = service.start_analysis(analysis.id)
            if started is None:
                all_validation_failures.append("Start analysis returned None")
            elif started.status != "running":
                all_validation_failures.append(f"Status should be running: {started.status}")
        except Exception as e:
            all_validation_failures.append(f"Start analysis failed: {e}")

        # Test 5: Reject starting already running analysis
        total_tests += 1
        try:
            service.start_analysis(analysis.id)
            all_validation_failures.append("Should reject starting running analysis")
        except RuntimeError:
            pass  # Expected
        except Exception as e:
            all_validation_failures.append(f"Unexpected error for already running: {e}")

        # Test 6: Complete analysis
        total_tests += 1
        try:
            outcomes = AggregatedOutcomes(
                did_not_try_rate=0.2,
                failed_rate=0.3,
                success_rate=0.5,
            )
            completed = service.complete_analysis(
                analysis_id=analysis.id,
                total_synths=100,
                aggregated_outcomes=outcomes,
                execution_time_seconds=5.5,
            )
            if completed is None:
                all_validation_failures.append("Complete analysis returned None")
            elif completed.status != "completed":
                all_validation_failures.append(f"Status should be completed: {completed.status}")
            elif not completed.has_results():
                all_validation_failures.append("Should have results after completion")
        except Exception as e:
            all_validation_failures.append(f"Complete analysis failed: {e}")

        # Test 7: 1:1 constraint - reject second analysis
        total_tests += 1
        try:
            service.create_analysis(exp.id)
            all_validation_failures.append("Should reject second analysis for same experiment")
        except RuntimeError:
            pass  # Expected
        except Exception as e:
            all_validation_failures.append(f"Unexpected error for duplicate analysis: {e}")

        # Test 8: has_analysis
        total_tests += 1
        try:
            has = service.has_analysis(exp.id)
            if not has:
                all_validation_failures.append("has_analysis should return True")
            has_no = service.has_analysis(exp_no_sc.id)
            if has_no:
                all_validation_failures.append("has_analysis should return False for no analysis")
        except Exception as e:
            all_validation_failures.append(f"has_analysis failed: {e}")

        # Test 9: Rerun analysis
        total_tests += 1
        try:
            new_config = AnalysisConfig(n_synths=200)
            new_analysis = service.rerun_analysis(exp.id, new_config)
            if new_analysis.id == analysis.id:
                all_validation_failures.append("Rerun should create new analysis")
            if new_analysis.config.n_synths != 200:
                all_validation_failures.append("Rerun should use new config")
        except Exception as e:
            all_validation_failures.append(f"Rerun analysis failed: {e}")

        # Test 10: Delete analysis
        total_tests += 1
        try:
            deleted = service.delete_analysis(exp.id)
            if not deleted:
                all_validation_failures.append("Delete should return True")
            if service.has_analysis(exp.id):
                all_validation_failures.append("Analysis should be deleted")
        except Exception as e:
            all_validation_failures.append(f"Delete analysis failed: {e}")

        db.close()

    # Final validation result
    if all_validation_failures:
        failed = len(all_validation_failures)
        print(f"VALIDATION FAILED - {failed} of {total_tests} tests failed:")
        for failure in all_validation_failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print(f"VALIDATION PASSED - All {total_tests} tests produced expected results")
        sys.exit(0)
