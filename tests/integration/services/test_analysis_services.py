"""
Integration tests for analysis-related services.

Tests the full flow: Service → Repository → Database
Uses real database (isolated_db_session) and tests CRUD operations.

Executar: pytest -m integration tests/integration/services/test_analysis_services.py
"""

import pytest
from datetime import datetime

from synth_lab.services.analysis.analysis_service import AnalysisService
from synth_lab.services.analysis.analysis_cache_service import AnalysisCacheService
from synth_lab.models.orm.experiment import Experiment
from synth_lab.models.orm.analysis import AnalysisRun, SynthOutcome, AnalysisCache


@pytest.mark.integration
class TestAnalysisServiceIntegration:
    """Integration tests for analysis_service.py - Core analysis operations."""

    def test_create_analysis_persists_to_database(self, isolated_db_session):
        """Test that create_analysis saves AnalysisRun to database."""
        # Setup: Create experiment with scorecard
        experiment = Experiment(
            id="exp_analysis_001",
            name="Analysis Test Experiment",
            hypothesis="Testing analysis creation",
            status="active",
            created_at=datetime.now().isoformat(),
            scorecard_data={
                "features": [
                    {"name": "feature1", "data_type": "continuous"},
                    {"name": "feature2", "data_type": "categorical"},
                ]
            },
        )
        isolated_db_session.add(experiment)
        isolated_db_session.commit()

        # Execute: Create analysis
        service = AnalysisService()
        from synth_lab.domain.entities.analysis_run import AnalysisConfig

        config = AnalysisConfig(n_simulations=100, seed=42)
        analysis = service.create_analysis(
            experiment_id="exp_analysis_001", config=config
        )

        # Verify
        assert analysis.id is not None, "Analysis should have ID after creation"
        assert analysis.experiment_id == "exp_analysis_001"
        assert analysis.status == "pending"
        assert analysis.config.n_simulations == 100

        # Verify in database
        db_analysis = (
            isolated_db_session.query(AnalysisRun).filter_by(id=analysis.id).first()
        )
        assert db_analysis is not None
        assert db_analysis.experiment_id == "exp_analysis_001"

    def test_create_analysis_enforces_one_to_one_relationship(
        self, isolated_db_session
    ):
        """Test that only one analysis can exist per experiment (1:1 constraint)."""
        # Setup: Create experiment
        experiment = Experiment(
            id="exp_one_analysis",
            name="One Analysis Test",
            hypothesis="Testing 1:1 constraint",
            status="active",
            created_at=datetime.now().isoformat(),
            scorecard_data={
                "features": [{"name": "f1", "data_type": "continuous"}]
            },
        )
        isolated_db_session.add(experiment)
        isolated_db_session.commit()

        # Execute: Create first analysis
        service = AnalysisService()
        from synth_lab.domain.entities.analysis_run import AnalysisConfig

        config = AnalysisConfig(n_simulations=100)
        analysis1 = service.create_analysis(
            experiment_id="exp_one_analysis", config=config
        )
        assert analysis1.id is not None

        # Try to create second analysis (should fail)
        with pytest.raises(RuntimeError) as exc_info:
            service.create_analysis(experiment_id="exp_one_analysis", config=config)

        assert "already has an analysis" in str(exc_info.value)

    def test_create_analysis_validates_experiment_exists(self, isolated_db_session):
        """Test that create_analysis raises error for non-existent experiment."""
        service = AnalysisService()
        from synth_lab.domain.entities.analysis_run import AnalysisConfig

        config = AnalysisConfig(n_simulations=100)

        with pytest.raises(ValueError) as exc_info:
            service.create_analysis(
                experiment_id="non_existent_exp", config=config
            )

        assert "Experiment not found" in str(exc_info.value)

    def test_create_analysis_validates_scorecard_exists(self, isolated_db_session):
        """Test that create_analysis raises error when experiment has no scorecard."""
        # Setup: Experiment without scorecard
        experiment = Experiment(
            id="exp_no_scorecard",
            name="No Scorecard",
            hypothesis="Missing scorecard",
            status="active",
            created_at=datetime.now().isoformat(),
            scorecard_data=None,  # No scorecard
        )
        isolated_db_session.add(experiment)
        isolated_db_session.commit()

        service = AnalysisService()
        from synth_lab.domain.entities.analysis_run import AnalysisConfig

        config = AnalysisConfig(n_simulations=100)

        with pytest.raises(ValueError) as exc_info:
            service.create_analysis(experiment_id="exp_no_scorecard", config=config)

        assert "must have a scorecard" in str(exc_info.value)

    def test_get_analysis_retrieves_by_experiment_id(self, isolated_db_session):
        """Test that get_analysis retrieves analysis by experiment_id."""
        # Setup: Create analysis
        experiment = Experiment(
            id="exp_get_analysis",
            name="Get Analysis Test",
            hypothesis="Testing retrieval",
            status="active",
            created_at=datetime.now().isoformat(),
        )
        analysis = AnalysisRun(
            id="analysis_get_001",
            experiment_id="exp_get_analysis",
            config={"n_simulations": 100},
            status="completed",
            started_at=datetime.now().isoformat(),
            completed_at=datetime.now().isoformat(),
            total_synths=100,
        )
        isolated_db_session.add_all([experiment, analysis])
        isolated_db_session.commit()

        # Execute
        service = AnalysisService()
        result = service.get_analysis("exp_get_analysis")

        # Verify
        assert result is not None
        assert result.id == "analysis_get_001"
        assert result.experiment_id == "exp_get_analysis"
        assert result.status == "completed"

    def test_get_analysis_returns_none_when_not_found(self, isolated_db_session):
        """Test that get_analysis returns None when no analysis exists."""
        service = AnalysisService()
        result = service.get_analysis("non_existent_exp")
        assert result is None

    def test_get_analysis_by_id_retrieves_correctly(self, isolated_db_session):
        """Test that get_analysis_by_id retrieves by analysis ID."""
        # Setup
        experiment = Experiment(
            id="exp_get_by_id",
            name="Get By ID Test",
            hypothesis="Testing ID retrieval",
            status="active",
            created_at=datetime.now().isoformat(),
        )
        analysis = AnalysisRun(
            id="analysis_id_001",
            experiment_id="exp_get_by_id",
            config={"n_simulations": 100},
            status="running",
            started_at=datetime.now().isoformat(),
            total_synths=0,
        )
        isolated_db_session.add_all([experiment, analysis])
        isolated_db_session.commit()

        # Execute
        service = AnalysisService()
        result = service.get_analysis_by_id("analysis_id_001")

        # Verify
        assert result is not None
        assert result.id == "analysis_id_001"
        assert result.status == "running"


@pytest.mark.integration
class TestAnalysisCacheServiceIntegration:
    """Integration tests for analysis_cache_service.py - Cache management."""

    def test_pre_compute_all_creates_cache_entries(self, isolated_db_session):
        """Test that pre_compute_all creates AnalysisCache entries in database."""
        # Setup: Create analysis with outcomes
        experiment = Experiment(
            id="exp_cache_001",
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
            id="analysis_cache_001",
            experiment_id="exp_cache_001",
            config={"n_simulations": 100},
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
        isolated_db_session.add_all([experiment, analysis])

        # Create synth outcomes
        for i in range(10):
            outcome = SynthOutcome(
                id=f"outcome_cache_{i:03d}",
                analysis_run_id="analysis_cache_001",
                synth_id=f"synth_cache_{i:03d}",
                synth_name=f"Test Synth {i}",
                inputs={
                    "digital_literacy": 50.0 + i,
                    "domain_expertise": 60.0 + i,
                },
                outputs={
                    "success": i % 2 == 0,
                    "success_rate": 0.5 + (i * 0.05),
                },
                created_at=datetime.now().isoformat(),
            )
            isolated_db_session.add(outcome)

        isolated_db_session.commit()

        # Execute: Pre-compute cache
        service = AnalysisCacheService()
        results = service.pre_compute_all("analysis_cache_001")

        # Verify: Cache entries created
        cache_entries = (
            isolated_db_session.query(AnalysisCache)
            .filter_by(analysis_run_id="analysis_cache_001")
            .all()
        )

        # Should have created multiple cache entries
        assert len(cache_entries) > 0, "Should create cache entries"

        # Verify some standard cache keys exist
        cache_keys = {entry.cache_key for entry in cache_entries}

        # At least one cache entry should have been created successfully
        assert len(cache_keys) > 0, "Should have at least one cache entry"

    def test_get_cached_data_retrieves_stored_data(self, isolated_db_session):
        """Test that get_cached_data retrieves previously stored cache."""
        # Setup: Create cache entry
        experiment = Experiment(
            id="exp_get_cache",
            name="Get Cache Test",
            hypothesis="Testing cache retrieval",
            status="active",
            created_at=datetime.now().isoformat(),
        )
        analysis = AnalysisRun(
            id="analysis_get_cache",
            experiment_id="exp_get_cache",
            config={"n_simulations": 100},
            status="completed",
            started_at=datetime.now().isoformat(),
            total_synths=100,
        )
        cache = AnalysisCache(
            id="cache_get_001",
            analysis_run_id="analysis_get_cache",
            cache_key="distribution",
            data={
                "chart_data": [{"name": "Synth 1", "success_rate": 0.75}],
                "metadata": {"total": 100},
            },
            created_at=datetime.now().isoformat(),
        )
        isolated_db_session.add_all([experiment, analysis, cache])
        isolated_db_session.commit()

        # Execute
        service = AnalysisCacheService()
        result = service.get_cached_data("analysis_get_cache", "distribution")

        # Verify
        assert result is not None
        assert "chart_data" in result
        assert result["chart_data"][0]["success_rate"] == 0.75

    def test_invalidate_cache_removes_entries(self, isolated_db_session):
        """Test that invalidate_cache removes cache entries for analysis."""
        # Setup: Create cache entries
        experiment = Experiment(
            id="exp_invalidate",
            name="Invalidate Test",
            hypothesis="Testing cache invalidation",
            status="active",
            created_at=datetime.now().isoformat(),
        )
        analysis = AnalysisRun(
            id="analysis_invalidate",
            experiment_id="exp_invalidate",
            config={"n_simulations": 100},
            status="completed",
            started_at=datetime.now().isoformat(),
            total_synths=100,
        )
        cache1 = AnalysisCache(
            id="cache_inv_001",
            analysis_run_id="analysis_invalidate",
            cache_key="distribution",
            data={"test": "data1"},
            created_at=datetime.now().isoformat(),
        )
        cache2 = AnalysisCache(
            id="cache_inv_002",
            analysis_run_id="analysis_invalidate",
            cache_key="correlations",
            data={"test": "data2"},
            created_at=datetime.now().isoformat(),
        )
        isolated_db_session.add_all([experiment, analysis, cache1, cache2])
        isolated_db_session.commit()

        # Verify cache exists
        before = (
            isolated_db_session.query(AnalysisCache)
            .filter_by(analysis_run_id="analysis_invalidate")
            .count()
        )
        assert before == 2

        # Execute: Invalidate cache
        service = AnalysisCacheService()
        service.invalidate_cache("analysis_invalidate")

        # Verify: Cache removed
        after = (
            isolated_db_session.query(AnalysisCache)
            .filter_by(analysis_run_id="analysis_invalidate")
            .count()
        )
        assert after == 0


@pytest.mark.integration
class TestAnalysisServiceErrorHandling:
    """Integration tests for error handling in analysis services."""

    def test_get_analysis_handles_missing_analysis(self, isolated_db_session):
        """Test that get_analysis returns None gracefully for missing analysis."""
        service = AnalysisService()
        result = service.get_analysis("missing_experiment_id")
        assert result is None

    def test_create_analysis_validates_experiment_state(self, isolated_db_session):
        """Test that create_analysis validates experiment state before creation."""
        # Setup: Experiment with invalid state (no scorecard)
        experiment = Experiment(
            id="exp_invalid_state",
            name="Invalid State Test",
            hypothesis="Testing validation",
            status="active",
            created_at=datetime.now().isoformat(),
            scorecard_data=None,
        )
        isolated_db_session.add(experiment)
        isolated_db_session.commit()

        service = AnalysisService()
        from synth_lab.domain.entities.analysis_run import AnalysisConfig

        config = AnalysisConfig(n_simulations=100)

        # Should raise error for missing scorecard
        with pytest.raises(ValueError) as exc_info:
            service.create_analysis(experiment_id="exp_invalid_state", config=config)

        assert "scorecard" in str(exc_info.value).lower()
