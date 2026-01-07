"""
Integration tests for analysis-related services.

Tests the full flow: Service → Repository → Database
Uses real database (db_session) and tests CRUD operations.

Executar: pytest -m integration tests/integration/services/test_analysis_services.py
"""

import pytest
from datetime import datetime

from synth_lab.services.analysis.analysis_service import AnalysisService
from synth_lab.services.analysis.analysis_cache_service import AnalysisCacheService
from synth_lab.repositories.analysis_repository import AnalysisRepository
from synth_lab.repositories.experiment_repository import ExperimentRepository
from synth_lab.models.orm.experiment import Experiment
from synth_lab.models.orm.analysis import AnalysisRun, SynthOutcome, AnalysisCache


def create_analysis_service(session) -> AnalysisService:
    """Create an AnalysisService with test session."""
    analysis_repo = AnalysisRepository(session=session)
    experiment_repo = ExperimentRepository(session=session)
    return AnalysisService(analysis_repo=analysis_repo, experiment_repo=experiment_repo)


@pytest.mark.integration
class TestAnalysisServiceIntegration:
    """Integration tests for analysis_service.py - Core analysis operations."""

    def test_create_analysis_persists_to_database(self, db_session):
        """Test that create_analysis saves AnalysisRun to database."""
        # Setup: Create experiment with valid scorecard
        experiment = Experiment(
            id="exp_b1c2d3e4",
            name="Analysis Test Experiment",
            hypothesis="Testing analysis creation",
            status="active",
            created_at=datetime.now().isoformat(),
            scorecard_data={
                "feature_name": "Test Feature",
                "scenario": "Test scenario",
                "description_text": "Test description",
                "complexity": {"score": 0.5, "reasoning": "Medium complexity"},
                "initial_effort": {"score": 0.6, "reasoning": "Medium effort"},
                "perceived_risk": {"score": 0.4, "reasoning": "Low risk"},
                "time_to_value": {"score": 0.7, "reasoning": "Fast value"},
            },
        )
        db_session.add(experiment)
        db_session.commit()

        # Execute: Create analysis with test session
        service = create_analysis_service(db_session)
        from synth_lab.domain.entities.analysis_run import AnalysisConfig

        config = AnalysisConfig(n_synths=100, seed=42)
        analysis = service.create_analysis(
            experiment_id="exp_b1c2d3e4", config=config
        )

        # Verify
        assert analysis.id is not None, "Analysis should have ID after creation"
        assert analysis.experiment_id == "exp_b1c2d3e4"
        assert analysis.status == "pending"
        assert analysis.config.n_synths == 100

        # Verify in database
        db_analysis = (
            db_session.query(AnalysisRun).filter_by(id=analysis.id).first()
        )
        assert db_analysis is not None
        assert db_analysis.experiment_id == "exp_b1c2d3e4"

    def test_create_analysis_enforces_one_to_one_relationship(
        self, db_session
    ):
        """Test that only one analysis can exist per experiment (1:1 constraint)."""
        # Setup: Create experiment with valid scorecard
        experiment = Experiment(
            id="exp_c2d3e4f5",
            name="One Analysis Test",
            hypothesis="Testing 1:1 constraint",
            status="active",
            created_at=datetime.now().isoformat(),
            scorecard_data={
                "feature_name": "Test Feature",
                "scenario": "Test scenario",
                "description_text": "Test description",
                "complexity": {"score": 0.5, "reasoning": "Medium"},
                "initial_effort": {"score": 0.6, "reasoning": "Medium"},
                "perceived_risk": {"score": 0.4, "reasoning": "Low"},
                "time_to_value": {"score": 0.7, "reasoning": "Fast"},
            },
        )
        db_session.add(experiment)
        db_session.commit()

        # Execute: Create first analysis
        service = create_analysis_service(db_session)
        from synth_lab.domain.entities.analysis_run import AnalysisConfig

        config = AnalysisConfig(n_synths=100)
        analysis1 = service.create_analysis(
            experiment_id="exp_c2d3e4f5", config=config
        )
        assert analysis1.id is not None

        # Try to create second analysis (should fail)
        with pytest.raises(RuntimeError) as exc_info:
            service.create_analysis(experiment_id="exp_c2d3e4f5", config=config)

        assert "already has an analysis" in str(exc_info.value)

    def test_create_analysis_validates_experiment_exists(self, db_session):
        """Test that create_analysis raises error for non-existent experiment."""
        service = create_analysis_service(db_session)
        from synth_lab.domain.entities.analysis_run import AnalysisConfig

        config = AnalysisConfig(n_synths=100)

        with pytest.raises(ValueError) as exc_info:
            service.create_analysis(
                experiment_id="non_existent_exp", config=config
            )

        assert "Experiment not found" in str(exc_info.value)

    def test_create_analysis_validates_scorecard_exists(self, db_session):
        """Test that create_analysis raises error when experiment has no scorecard."""
        # Setup: Experiment without scorecard
        experiment = Experiment(
            id="exp_d3e4f5a6",
            name="No Scorecard",
            hypothesis="Missing scorecard",
            status="active",
            created_at=datetime.now().isoformat(),
            scorecard_data=None,  # No scorecard
        )
        db_session.add(experiment)
        db_session.commit()

        service = create_analysis_service(db_session)
        from synth_lab.domain.entities.analysis_run import AnalysisConfig

        config = AnalysisConfig(n_synths=100)

        with pytest.raises(ValueError) as exc_info:
            service.create_analysis(experiment_id="exp_d3e4f5a6", config=config)

        assert "must have a scorecard" in str(exc_info.value)

    def test_get_analysis_retrieves_by_experiment_id(self, db_session):
        """Test that get_analysis retrieves analysis by experiment_id."""
        # Setup: Create analysis
        experiment = Experiment(
            id="exp_e4f5a6b7",
            name="Get Analysis Test",
            hypothesis="Testing retrieval",
            status="active",
            created_at=datetime.now().isoformat(),
        )
        analysis = AnalysisRun(
            id="ana_b1c2d3e4",
            experiment_id="exp_e4f5a6b7",
            config={"n_synths": 100},
            status="completed",
            started_at=datetime.now().isoformat(),
            completed_at=datetime.now().isoformat(),
            total_synths=100,
        )
        db_session.add_all([experiment, analysis])
        db_session.commit()

        # Execute
        service = create_analysis_service(db_session)
        result = service.get_analysis("exp_e4f5a6b7")

        # Verify
        assert result is not None
        assert result.id == "ana_b1c2d3e4"
        assert result.experiment_id == "exp_e4f5a6b7"
        assert result.status == "completed"

    def test_get_analysis_returns_none_when_not_found(self, db_session):
        """Test that get_analysis returns None when no analysis exists."""
        service = create_analysis_service(db_session)
        result = service.get_analysis("non_existent_exp")
        assert result is None

    def test_get_analysis_by_id_retrieves_correctly(self, db_session):
        """Test that get_analysis_by_id retrieves by analysis ID."""
        # Setup
        experiment = Experiment(
            id="exp_f5a6b7c8",
            name="Get By ID Test",
            hypothesis="Testing ID retrieval",
            status="active",
            created_at=datetime.now().isoformat(),
        )
        analysis = AnalysisRun(
            id="ana_c2d3e4f5",
            experiment_id="exp_f5a6b7c8",
            config={"n_synths": 100},
            status="running",
            started_at=datetime.now().isoformat(),
            total_synths=0,
        )
        db_session.add_all([experiment, analysis])
        db_session.commit()

        # Execute
        service = create_analysis_service(db_session)
        result = service.get_analysis_by_id("ana_c2d3e4f5")

        # Verify
        assert result is not None
        assert result.id == "ana_c2d3e4f5"
        assert result.status == "running"


def create_cache_service(session) -> AnalysisCacheService:
    """Create an AnalysisCacheService with test session."""
    from synth_lab.repositories.analysis_cache_repository import AnalysisCacheRepository
    from synth_lab.repositories.analysis_outcome_repository import AnalysisOutcomeRepository

    cache_repo = AnalysisCacheRepository(session=session)
    outcome_repo = AnalysisOutcomeRepository(session=session)
    return AnalysisCacheService(cache_repo=cache_repo, outcome_repo=outcome_repo)


@pytest.mark.integration
class TestAnalysisCacheServiceIntegration:
    """Integration tests for analysis_cache_service.py - Cache management."""

    def test_pre_compute_all_creates_cache_entries(self, db_session):
        """Test that pre_compute_all creates AnalysisCache entries in database."""
        # Setup: Create analysis with outcomes
        experiment = Experiment(
            id="exp_a6b7c8d9",
            name="Cache Test",
            hypothesis="Testing cache creation",
            status="active",
            created_at=datetime.now().isoformat(),
            scorecard_data={
                "features": [
                    {"name": "digital_literacy", "data_type": "continuous"},
                    {"name": "domain_expertise", "data_type": "continuous"},
                ]
            },
        )
        analysis = AnalysisRun(
            id="ana_d3e4f5a6",
            experiment_id="exp_a6b7c8d9",
            config={"n_synths": 100},
            status="completed",
            started_at=datetime.now().isoformat(),
            completed_at=datetime.now().isoformat(),
            total_synths=10,
            aggregated_outcomes={
                "success_rate": 0.65,
                "summary_stats": {
                    "digital_literacy": {"mean": 50.0, "std": 10.0},
                    "domain_expertise": {"mean": 60.0, "std": 15.0},
                },
            },
        )
        db_session.add_all([experiment, analysis])

        # Create synth outcomes with proper SimulationAttributes structure
        # Rates must sum to 1.0
        for i in range(10):
            success_rate = 0.5 + (i * 0.03)  # 0.50 to 0.77
            failed_rate = 0.3 - (i * 0.02)   # 0.30 to 0.12
            did_not_try_rate = 1.0 - success_rate - failed_rate  # ~0.20
            outcome = SynthOutcome(
                id=f"outcome_cache_{i:03d}",
                analysis_id="ana_d3e4f5a6",
                synth_id=f"synth_cache_{i:03d}",
                did_not_try_rate=round(did_not_try_rate, 3),
                failed_rate=round(failed_rate, 3),
                success_rate=round(success_rate, 3),
                synth_attributes={
                    "observables": {
                        "digital_literacy": min(0.5 + i * 0.04, 1.0),
                        "similar_tool_experience": min(0.6 + i * 0.03, 1.0),
                        "motor_ability": 0.9,
                        "time_availability": 0.5,
                        "domain_expertise": min(0.6 + i * 0.04, 1.0),
                    },
                    "latent_traits": {
                        "capability_mean": min(0.55 + i * 0.03, 1.0),
                        "trust_mean": min(0.58 + i * 0.03, 1.0),
                        "friction_tolerance_mean": min(0.5 + i * 0.03, 1.0),
                        "exploration_prob": 0.45,
                    },
                },
            )
            db_session.add(outcome)

        db_session.commit()

        # Execute: Pre-compute cache
        service = create_cache_service(db_session)
        results = service.pre_compute_all("ana_d3e4f5a6")

        # Verify: Cache entries created
        cache_entries = (
            db_session.query(AnalysisCache)
            .filter_by(analysis_id="ana_d3e4f5a6")
            .all()
        )

        # Should have created multiple cache entries
        assert len(cache_entries) > 0, "Should create cache entries"

        # Verify some standard cache keys exist
        cache_keys = {entry.cache_key for entry in cache_entries}

        # At least one cache entry should have been created successfully
        assert len(cache_keys) > 0, "Should have at least one cache entry"

    def test_get_cached_data_retrieves_stored_data(self, db_session):
        """Test that get_cached_data retrieves previously stored cache."""
        # Setup: Create cache entry
        experiment = Experiment(
            id="exp_b7c8d9e0",
            name="Get Cache Test",
            hypothesis="Testing cache retrieval",
            status="active",
            created_at=datetime.now().isoformat(),
        )
        analysis = AnalysisRun(
            id="ana_e4f5a6b7",
            experiment_id="exp_b7c8d9e0",
            config={"n_synths": 100},
            status="completed",
            started_at=datetime.now().isoformat(),
            total_synths=100,
        )
        cache = AnalysisCache(
            analysis_id="ana_e4f5a6b7",
            cache_key="distribution",
            data={
                "chart_data": [{"name": "Synth 1", "success_rate": 0.75}],
                "metadata": {"total": 100},
            },
            computed_at=datetime.now().isoformat(),
        )
        db_session.add_all([experiment, analysis, cache])
        db_session.commit()

        # Execute
        service = create_cache_service(db_session)
        result = service.get_cached(analysis_id="ana_e4f5a6b7", cache_key="distribution")

        # Verify
        assert result is not None
        assert "chart_data" in result
        assert result["chart_data"][0]["success_rate"] == 0.75

    def test_invalidate_cache_removes_entries(self, db_session):
        """Test that invalidate_cache removes cache entries for analysis."""
        # Setup: Create cache entries
        experiment = Experiment(
            id="exp_c8d9e0f1",
            name="Invalidate Test",
            hypothesis="Testing cache invalidation",
            status="active",
            created_at=datetime.now().isoformat(),
        )
        analysis = AnalysisRun(
            id="ana_f5a6b7c8",
            experiment_id="exp_c8d9e0f1",
            config={"n_synths": 100},
            status="completed",
            started_at=datetime.now().isoformat(),
            total_synths=100,
        )
        cache1 = AnalysisCache(
            analysis_id="ana_f5a6b7c8",
            cache_key="distribution",
            data={"test": "data1"},
            computed_at=datetime.now().isoformat(),
        )
        cache2 = AnalysisCache(
            analysis_id="ana_f5a6b7c8",
            cache_key="correlations",
            data={"test": "data2"},
            computed_at=datetime.now().isoformat(),
        )
        db_session.add_all([experiment, analysis, cache1, cache2])
        db_session.commit()

        # Verify cache exists
        before = (
            db_session.query(AnalysisCache)
            .filter_by(analysis_id="ana_f5a6b7c8")
            .count()
        )
        assert before == 2

        # Execute: Invalidate cache
        service = create_cache_service(db_session)
        service.invalidate("ana_f5a6b7c8")

        # Verify: Cache removed
        after = (
            db_session.query(AnalysisCache)
            .filter_by(analysis_id="ana_f5a6b7c8")
            .count()
        )
        assert after == 0


@pytest.mark.integration
class TestAnalysisServiceErrorHandling:
    """Integration tests for error handling in analysis services."""

    def test_get_analysis_handles_missing_analysis(self, db_session):
        """Test that get_analysis returns None gracefully for missing analysis."""
        service = create_analysis_service(db_session)
        result = service.get_analysis("missing_experiment_id")
        assert result is None

    def test_create_analysis_validates_experiment_state(self, db_session):
        """Test that create_analysis validates experiment state before creation."""
        # Setup: Experiment with invalid state (no scorecard)
        experiment = Experiment(
            id="exp_d9e0f1a2",
            name="Invalid State Test",
            hypothesis="Testing validation",
            status="active",
            created_at=datetime.now().isoformat(),
            scorecard_data=None,
        )
        db_session.add(experiment)
        db_session.commit()

        service = create_analysis_service(db_session)
        from synth_lab.domain.entities.analysis_run import AnalysisConfig

        config = AnalysisConfig(n_synths=100)

        # Should raise error for missing scorecard
        with pytest.raises(ValueError) as exc_info:
            service.create_analysis(experiment_id="exp_d9e0f1a2", config=config)

        assert "scorecard" in str(exc_info.value).lower()
