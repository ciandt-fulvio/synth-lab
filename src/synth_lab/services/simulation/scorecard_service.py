"""
Scorecard service for synth-lab.

Business logic layer for feature scorecards, coordinating between
API layer and repository.

Functions:
- create_scorecard(): Create a new scorecard with validation
- get_scorecard(): Get scorecard by ID
- list_scorecards(): List scorecards with pagination
- update_scorecard(): Update scorecard with insights

References:
    - Spec: specs/016-feature-impact-simulation/spec.md
    - Repository: src/synth_lab/repositories/scorecard_repository.py

Sample usage:
    from synth_lab.services.simulation.scorecard_service import ScorecardService

    service = ScorecardService(repository)
    scorecard = service.create_scorecard(data)

Expected output:
    FeatureScorecard instance with generated ID
"""

from typing import Any

from loguru import logger

from synth_lab.domain.entities import (
    FeatureScorecard,
    ScorecardDimension,
    ScorecardIdentification,
)
from synth_lab.repositories.scorecard_repository import ScorecardRepository


class ScorecardNotFoundError(Exception):
    """Raised when a scorecard is not found."""

    pass


class ValidationError(Exception):
    """Raised when scorecard data is invalid."""

    pass


class ScorecardService:
    """Service for feature scorecard operations."""

    def __init__(self, repository: ScorecardRepository) -> None:
        """
        Initialize service with repository.

        Args:
            repository: Scorecard repository instance
        """
        self.repository = repository
        self.logger = logger.bind(component="scorecard_service")

    def create_scorecard(self, data: dict[str, Any]) -> FeatureScorecard:
        """
        Create a new scorecard from provided data.

        Args:
            data: Dictionary with scorecard data

        Returns:
            FeatureScorecard: Created scorecard with generated ID

        Raises:
            ValidationError: If data is invalid
        """
        try:
            scorecard = self._build_scorecard(data)
            self._validate_scorecard(scorecard)
            self.repository.create_scorecard(scorecard)
            self.logger.info(f"Created scorecard {scorecard.id}")
            return scorecard
        except ValueError as e:
            raise ValidationError(str(e)) from e

    def get_scorecard(self, scorecard_id: str) -> FeatureScorecard:
        """
        Get a scorecard by ID.

        Args:
            scorecard_id: Scorecard ID to retrieve

        Returns:
            FeatureScorecard: Retrieved scorecard

        Raises:
            ScorecardNotFoundError: If scorecard not found
        """
        scorecard = self.repository.get_scorecard(scorecard_id)
        if scorecard is None:
            raise ScorecardNotFoundError(f"Scorecard {scorecard_id} not found")
        return scorecard

    def list_scorecards(
        self,
        limit: int = 20,
        offset: int = 0,
    ) -> dict[str, Any]:
        """
        List scorecards with pagination.

        Args:
            limit: Maximum number of scorecards to return
            offset: Number of scorecards to skip

        Returns:
            dict: {"scorecards": [...], "total": int, "limit": int, "offset": int}
        """
        scorecards, total = self.repository.list_scorecards(limit, offset)
        return {
            "scorecards": scorecards,
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    def update_scorecard_insights(
        self,
        scorecard_id: str,
        justification: str | None = None,
        impact_hypotheses: list[str] | None = None,
    ) -> FeatureScorecard:
        """
        Update a scorecard with LLM-generated insights.

        Args:
            scorecard_id: Scorecard ID to update
            justification: LLM-generated justification
            impact_hypotheses: LLM-generated hypotheses

        Returns:
            FeatureScorecard: Updated scorecard

        Raises:
            ScorecardNotFoundError: If scorecard not found
        """
        scorecard = self.get_scorecard(scorecard_id)

        updates: dict[str, Any] = {}
        if justification is not None:
            updates["justification"] = justification
        if impact_hypotheses is not None:
            updates["impact_hypotheses"] = impact_hypotheses

        updated_scorecard = scorecard.model_copy(update=updates)
        self.repository.update_scorecard(updated_scorecard)

        self.logger.info(f"Updated insights for scorecard {scorecard_id}")
        return updated_scorecard

    def _build_scorecard(self, data: dict[str, Any]) -> FeatureScorecard:
        """
        Build a FeatureScorecard from raw data.

        Args:
            data: Dictionary with scorecard fields

        Returns:
            FeatureScorecard: Built scorecard instance
        """
        # Build identification
        identification = ScorecardIdentification(
            feature_name=data.get("feature_name", ""),
            use_scenario=data.get("use_scenario", ""),
            evaluators=data.get("evaluators", []),
        )

        # Build dimensions
        def build_dimension(dim_data: dict[str, Any] | None) -> ScorecardDimension:
            if dim_data is None:
                return ScorecardDimension(score=0.5)
            return ScorecardDimension(
                score=dim_data.get("score", 0.5),
                rules_applied=dim_data.get("rules_applied", []),
                min_uncertainty=dim_data.get("min_uncertainty", 0.0),
                max_uncertainty=dim_data.get("max_uncertainty", 0.0),
            )

        return FeatureScorecard(
            identification=identification,
            description_text=data.get("description_text", ""),
            description_media_urls=data.get("description_media_urls", []),
            complexity=build_dimension(data.get("complexity")),
            initial_effort=build_dimension(data.get("initial_effort")),
            perceived_risk=build_dimension(data.get("perceived_risk")),
            time_to_value=build_dimension(data.get("time_to_value")),
            justification=data.get("justification"),
            impact_hypotheses=data.get("impact_hypotheses", []),
        )

    def _validate_scorecard(self, scorecard: FeatureScorecard) -> None:
        """
        Validate scorecard data.

        Args:
            scorecard: Scorecard to validate

        Raises:
            ValidationError: If validation fails
        """
        errors = []

        # Validate feature name
        if not scorecard.identification.feature_name:
            errors.append("feature_name is required")

        # Validate use scenario
        if not scorecard.identification.use_scenario:
            errors.append("use_scenario is required")

        # Validate description
        if not scorecard.description_text:
            errors.append("description_text is required")

        # Validate dimension scores
        dimensions = [
            ("complexity", scorecard.complexity),
            ("initial_effort", scorecard.initial_effort),
            ("perceived_risk", scorecard.perceived_risk),
            ("time_to_value", scorecard.time_to_value),
        ]

        for name, dim in dimensions:
            if not 0.0 <= dim.score <= 1.0:
                errors.append(f"{name}.score must be in [0, 1]")
            if dim.min_uncertainty > dim.max_uncertainty:
                errors.append(
                    f"{name}.min_uncertainty must be <= max_uncertainty"
                )

        if errors:
            raise ValidationError("; ".join(errors))


if __name__ == "__main__":
    import sys
    import tempfile
    from pathlib import Path

    from synth_lab.infrastructure.database import DatabaseManager, init_database
    from synth_lab.repositories.scorecard_repository import ScorecardRepository

    print("=== Scorecard Service Validation ===\n")

    all_validation_failures = []
    total_tests = 0

    # Use temp database
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        init_database(db_path)
        db = DatabaseManager(db_path)
        repo = ScorecardRepository(db)
        service = ScorecardService(repo)

        # Test 1: Create valid scorecard
        total_tests += 1
        try:
            data = {
                "feature_name": "Novo Onboarding",
                "use_scenario": "Primeiro acesso",
                "description_text": "Fluxo de onboarding simplificado com 3 passos",
                "evaluators": ["PM: Joao", "UX: Maria"],
                "complexity": {"score": 0.4, "rules_applied": ["2 conceitos novos"]},
                "initial_effort": {"score": 0.3},
                "perceived_risk": {"score": 0.2, "min_uncertainty": 0.1, "max_uncertainty": 0.3},
                "time_to_value": {"score": 0.5},
            }
            scorecard = service.create_scorecard(data)
            if scorecard.identification.feature_name != "Novo Onboarding":
                all_validation_failures.append(
                    f"Create: Feature name mismatch: {scorecard.identification.feature_name}"
                )
            elif len(scorecard.id) != 8:
                all_validation_failures.append(f"Create: ID should be 8 chars: {scorecard.id}")
            else:
                print(f"Test 1 PASSED: Created scorecard {scorecard.id}")
        except Exception as e:
            all_validation_failures.append(f"Create failed: {e}")

        # Test 2: Get scorecard
        total_tests += 1
        try:
            retrieved = service.get_scorecard(scorecard.id)
            if retrieved.complexity.score != 0.4:
                all_validation_failures.append(
                    f"Get: Complexity score mismatch: {retrieved.complexity.score}"
                )
            else:
                print(f"Test 2 PASSED: Retrieved scorecard with complexity={retrieved.complexity.score}")
        except Exception as e:
            all_validation_failures.append(f"Get failed: {e}")

        # Test 3: Get non-existent scorecard
        total_tests += 1
        try:
            service.get_scorecard("nonexistent")
            all_validation_failures.append("Get non-existent: Should raise ScorecardNotFoundError")
        except ScorecardNotFoundError:
            print("Test 3 PASSED: Non-existent scorecard raises ScorecardNotFoundError")
        except Exception as e:
            all_validation_failures.append(f"Get non-existent: Unexpected error {e}")

        # Test 4: List scorecards
        total_tests += 1
        try:
            result = service.list_scorecards(limit=10, offset=0)
            if result["total"] != 1:
                all_validation_failures.append(f"List: Expected total=1, got {result['total']}")
            elif len(result["scorecards"]) != 1:
                all_validation_failures.append(
                    f"List: Expected 1 scorecard, got {len(result['scorecards'])}"
                )
            else:
                print(f"Test 4 PASSED: Listed {result['total']} scorecards")
        except Exception as e:
            all_validation_failures.append(f"List failed: {e}")

        # Test 5: Update insights
        total_tests += 1
        try:
            updated = service.update_scorecard_insights(
                scorecard.id,
                justification="LLM generated justification",
                impact_hypotheses=["Hypothesis 1", "Hypothesis 2"],
            )
            if updated.justification != "LLM generated justification":
                all_validation_failures.append(
                    f"Update insights: Justification mismatch: {updated.justification}"
                )
            elif len(updated.impact_hypotheses) != 2:
                all_validation_failures.append(
                    f"Update insights: Expected 2 hypotheses, got {len(updated.impact_hypotheses)}"
                )
            else:
                print("Test 5 PASSED: Updated scorecard insights")
        except Exception as e:
            all_validation_failures.append(f"Update insights failed: {e}")

        # Test 6: Create with missing required field
        total_tests += 1
        try:
            invalid_data = {
                "use_scenario": "Test",
                "description_text": "Test",
                # missing feature_name
            }
            service.create_scorecard(invalid_data)
            all_validation_failures.append("Create invalid: Should raise ValidationError")
        except ValidationError as e:
            if "feature_name is required" in str(e):
                print("Test 6 PASSED: Missing feature_name raises ValidationError")
            else:
                all_validation_failures.append(
                    f"Create invalid: Wrong error message: {e}"
                )
        except Exception as e:
            all_validation_failures.append(f"Create invalid: Unexpected error {e}")

        # Test 7: Build scorecard with defaults
        total_tests += 1
        try:
            minimal_data = {
                "feature_name": "Minimal",
                "use_scenario": "Test",
                "description_text": "Minimal description",
            }
            scorecard2 = service.create_scorecard(minimal_data)
            # Should have default dimension scores of 0.5
            if scorecard2.complexity.score != 0.5:
                all_validation_failures.append(
                    f"Defaults: Expected default score 0.5, got {scorecard2.complexity.score}"
                )
            else:
                print("Test 7 PASSED: Created scorecard with default dimension scores")
        except Exception as e:
            all_validation_failures.append(f"Defaults test failed: {e}")

        db.close()

    # Final result
    print()
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
