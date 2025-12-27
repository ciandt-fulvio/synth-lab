"""
Unit tests for scorecard service.

Tests:
- Scorecard creation with validation
- Scorecard retrieval
- Scorecard listing with pagination
- Uncertainty interval validation
- Required field validation
"""

import tempfile
from pathlib import Path

import pytest

from synth_lab.domain.entities import (
    FeatureScorecard,
    ScorecardDimension,
    ScorecardIdentification,
)
from synth_lab.infrastructure.database import DatabaseManager, init_database
from synth_lab.repositories.scorecard_repository import ScorecardRepository
from synth_lab.services.simulation.scorecard_service import (
    ScorecardNotFoundError,
    ScorecardService,
    ValidationError,
)


@pytest.fixture
def db() -> DatabaseManager:
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        init_database(db_path)
        db = DatabaseManager(db_path)
        yield db
        db.close()


@pytest.fixture
def repository(db: DatabaseManager) -> ScorecardRepository:
    """Create a scorecard repository with temp database."""
    return ScorecardRepository(db)


@pytest.fixture
def service(repository: ScorecardRepository) -> ScorecardService:
    """Create a scorecard service with temp repository."""
    return ScorecardService(repository)


class TestScorecardCreation:
    """Tests for scorecard creation."""

    def test_create_valid_scorecard(self, service: ScorecardService) -> None:
        """Valid scorecard data creates a scorecard."""
        data = {
            "feature_name": "Test Feature",
            "use_scenario": "First use",
            "description_text": "Test description",
            "complexity": {"score": 0.4},
            "initial_effort": {"score": 0.3},
            "perceived_risk": {"score": 0.2},
            "time_to_value": {"score": 0.5},
        }

        scorecard = service.create_scorecard(data)

        assert len(scorecard.id) == 8
        assert scorecard.identification.feature_name == "Test Feature"
        assert scorecard.complexity.score == 0.4

    def test_create_scorecard_with_default_dimensions(
        self, service: ScorecardService
    ) -> None:
        """Missing dimensions get default score of 0.5."""
        data = {
            "feature_name": "Minimal",
            "use_scenario": "Test",
            "description_text": "Minimal description",
        }

        scorecard = service.create_scorecard(data)

        assert scorecard.complexity.score == 0.5
        assert scorecard.initial_effort.score == 0.5
        assert scorecard.perceived_risk.score == 0.5
        assert scorecard.time_to_value.score == 0.5

    def test_create_scorecard_with_rules(self, service: ScorecardService) -> None:
        """Scorecard preserves rules applied."""
        data = {
            "feature_name": "Feature with Rules",
            "use_scenario": "Complex scenario",
            "description_text": "Description",
            "complexity": {
                "score": 0.6,
                "rules_applied": ["2 conceitos novos", "estados invisíveis"],
            },
        }

        scorecard = service.create_scorecard(data)

        assert len(scorecard.complexity.rules_applied) == 2
        assert "2 conceitos novos" in scorecard.complexity.rules_applied

    def test_create_scorecard_with_uncertainty(self, service: ScorecardService) -> None:
        """Scorecard preserves uncertainty intervals."""
        data = {
            "feature_name": "Feature with Uncertainty",
            "use_scenario": "Uncertain scenario",
            "description_text": "Description",
            "perceived_risk": {
                "score": 0.3,
                "min_uncertainty": 0.2,
                "max_uncertainty": 0.4,
            },
        }

        scorecard = service.create_scorecard(data)

        assert scorecard.perceived_risk.min_uncertainty == 0.2
        assert scorecard.perceived_risk.max_uncertainty == 0.4


class TestScorecardValidation:
    """Tests for scorecard validation."""

    def test_missing_feature_name_raises_error(
        self, service: ScorecardService
    ) -> None:
        """Missing feature_name raises ValidationError."""
        data = {
            "use_scenario": "Test",
            "description_text": "Test description",
        }

        with pytest.raises(ValidationError) as exc_info:
            service.create_scorecard(data)

        assert "feature_name is required" in str(exc_info.value)

    def test_missing_use_scenario_raises_error(
        self, service: ScorecardService
    ) -> None:
        """Missing use_scenario raises ValidationError."""
        data = {
            "feature_name": "Test",
            "description_text": "Test description",
        }

        with pytest.raises(ValidationError) as exc_info:
            service.create_scorecard(data)

        assert "use_scenario is required" in str(exc_info.value)

    def test_missing_description_raises_error(
        self, service: ScorecardService
    ) -> None:
        """Missing description_text raises ValidationError."""
        data = {
            "feature_name": "Test",
            "use_scenario": "Test",
        }

        with pytest.raises(ValidationError) as exc_info:
            service.create_scorecard(data)

        assert "description_text is required" in str(exc_info.value)


class TestScorecardRetrieval:
    """Tests for scorecard retrieval."""

    def test_get_existing_scorecard(self, service: ScorecardService) -> None:
        """Existing scorecard is retrieved correctly."""
        data = {
            "feature_name": "Retrievable Feature",
            "use_scenario": "Test",
            "description_text": "Description",
        }
        created = service.create_scorecard(data)

        retrieved = service.get_scorecard(created.id)

        assert retrieved.id == created.id
        assert retrieved.identification.feature_name == "Retrievable Feature"

    def test_get_nonexistent_scorecard_raises_error(
        self, service: ScorecardService
    ) -> None:
        """Non-existent scorecard raises ScorecardNotFoundError."""
        with pytest.raises(ScorecardNotFoundError):
            service.get_scorecard("nonexistent_id")


class TestScorecardListing:
    """Tests for scorecard listing."""

    def test_list_empty(self, service: ScorecardService) -> None:
        """Empty database returns empty list."""
        result = service.list_scorecards()

        assert result["total"] == 0
        assert result["scorecards"] == []
        assert result["limit"] == 20
        assert result["offset"] == 0

    def test_list_with_scorecards(self, service: ScorecardService) -> None:
        """List returns all created scorecards."""
        for i in range(3):
            service.create_scorecard(
                {
                    "feature_name": f"Feature {i}",
                    "use_scenario": "Test",
                    "description_text": "Description",
                }
            )

        result = service.list_scorecards()

        assert result["total"] == 3
        assert len(result["scorecards"]) == 3

    def test_list_with_pagination(self, service: ScorecardService) -> None:
        """List respects pagination parameters."""
        for i in range(5):
            service.create_scorecard(
                {
                    "feature_name": f"Feature {i}",
                    "use_scenario": "Test",
                    "description_text": "Description",
                }
            )

        result = service.list_scorecards(limit=2, offset=0)

        assert result["total"] == 5
        assert len(result["scorecards"]) == 2
        assert result["limit"] == 2
        assert result["offset"] == 0


class TestScorecardInsights:
    """Tests for scorecard insights update."""

    def test_update_insights(self, service: ScorecardService) -> None:
        """Insights can be updated."""
        created = service.create_scorecard(
            {
                "feature_name": "Feature",
                "use_scenario": "Test",
                "description_text": "Description",
            }
        )

        updated = service.update_scorecard_insights(
            created.id,
            justification="Test justification",
            impact_hypotheses=["Hypothesis 1", "Hypothesis 2"],
        )

        assert updated.justification == "Test justification"
        assert len(updated.impact_hypotheses) == 2

    def test_update_partial_insights(self, service: ScorecardService) -> None:
        """Only provided insights are updated."""
        created = service.create_scorecard(
            {
                "feature_name": "Feature",
                "use_scenario": "Test",
                "description_text": "Description",
            }
        )

        updated = service.update_scorecard_insights(
            created.id,
            justification="Only justification",
        )

        assert updated.justification == "Only justification"
        assert updated.impact_hypotheses == []  # Unchanged

    def test_update_insights_nonexistent_raises_error(
        self, service: ScorecardService
    ) -> None:
        """Updating non-existent scorecard raises error."""
        with pytest.raises(ScorecardNotFoundError):
            service.update_scorecard_insights("nonexistent", justification="test")
