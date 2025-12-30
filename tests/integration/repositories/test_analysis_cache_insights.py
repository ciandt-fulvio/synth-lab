"""
Integration tests for AnalysisCacheRepository insight methods.

Tests storage and retrieval of chart insights and executive summaries.

References:
    - Repository: src/synth_lab/repositories/analysis_cache_repository.py
    - Entities: src/synth_lab/domain/entities/chart_insight.py, executive_summary.py
    - Spec: specs/023-quantitative-ai-insights/spec.md
"""

import tempfile
from pathlib import Path

import pytest

from synth_lab.domain.entities.analysis_run import AnalysisRun
from synth_lab.domain.entities.chart_insight import ChartInsight
from synth_lab.domain.entities.executive_summary import ExecutiveSummary
from synth_lab.domain.entities.experiment import Experiment
from synth_lab.infrastructure.database import DatabaseManager, init_database
from synth_lab.repositories.analysis_cache_repository import AnalysisCacheRepository
from synth_lab.repositories.analysis_repository import AnalysisRepository
from synth_lab.repositories.experiment_repository import ExperimentRepository


@pytest.fixture
def test_db():
    """Create a temporary test database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        init_database(db_path)
        db = DatabaseManager(db_path)
        yield db
        db.close()


@pytest.fixture
def cache_repo(test_db):
    """Create cache repository with test database."""
    return AnalysisCacheRepository(test_db)


@pytest.fixture
def analysis_id(test_db):
    """Create a test analysis and return its ID."""
    exp_repo = ExperimentRepository(test_db)
    ana_repo = AnalysisRepository(test_db)

    exp = Experiment(name="Test Experiment", hypothesis="Test hypothesis")
    exp_repo.create(exp)

    analysis = AnalysisRun(experiment_id=exp.id, status="completed")
    ana_repo.create(analysis)

    return analysis.id


class TestStoreAndGetChartInsight:
    """Test storing and retrieving chart insights."""

    def test_stores_and_retrieves_insight(self, cache_repo, analysis_id):
        """Should store insight and retrieve it by chart_type."""
        insight = ChartInsight(
            analysis_id=analysis_id,
            chart_type="try_vs_success",
            summary="Checkout tem boa taxa de engajamento mas precisa melhorar conversão",
            status="completed",
        )

        # Store
        stored = cache_repo.store_chart_insight(insight)
        assert stored.analysis_id == analysis_id

        # Retrieve
        retrieved = cache_repo.get_chart_insight(analysis_id, "try_vs_success")
        assert retrieved is not None
        assert retrieved.chart_type == "try_vs_success"
        assert "engajamento" in retrieved.summary
        assert retrieved.status == "completed"

    def test_returns_none_for_missing_insight(self, cache_repo, analysis_id):
        """Should return None if insight doesn't exist."""
        result = cache_repo.get_chart_insight(analysis_id, "nonexistent_chart")
        assert result is None

    def test_updates_existing_insight(self, cache_repo, analysis_id):
        """Should update insight if already exists."""
        insight_v1 = ChartInsight(
            analysis_id=analysis_id,
            chart_type="shap_summary",
            summary="Version 1 - Insight inicial",
            status="completed",
        )
        cache_repo.store_chart_insight(insight_v1)

        # Update with new data
        insight_v2 = ChartInsight(
            analysis_id=analysis_id,
            chart_type="shap_summary",
            summary="Version 2 - Insight atualizado",
            status="completed",
        )
        cache_repo.store_chart_insight(insight_v2)

        # Should retrieve latest version
        retrieved = cache_repo.get_chart_insight(analysis_id, "shap_summary")
        assert "Version 2" in retrieved.summary


class TestGetAllChartInsights:
    """Test retrieving all insights for an analysis."""

    def test_retrieves_all_insights(self, cache_repo, analysis_id):
        """Should retrieve all insights for an analysis."""
        insights = [
            ChartInsight(
                analysis_id=analysis_id,
                chart_type=f"chart_{i}",
                summary=f"Summary para chart {i}",
                status="completed",
            )
            for i in range(3)
        ]

        # Store all
        for insight in insights:
            cache_repo.store_chart_insight(insight)

        # Retrieve all
        all_insights = cache_repo.get_all_chart_insights(analysis_id)
        assert len(all_insights) == 3
        chart_types = [i.chart_type for i in all_insights]
        assert "chart_0" in chart_types
        assert "chart_1" in chart_types
        assert "chart_2" in chart_types

    def test_returns_empty_list_for_no_insights(self, cache_repo, analysis_id):
        """Should return empty list if no insights exist."""
        all_insights = cache_repo.get_all_chart_insights(analysis_id)
        assert all_insights == []


class TestStoreAndGetExecutiveSummary:
    """Test storing and retrieving executive summary."""

    def test_stores_and_retrieves_summary(self, cache_repo, analysis_id):
        """Should store and retrieve executive summary."""
        summary = ExecutiveSummary(
            analysis_id=analysis_id,
            overview="Tested checkout with 500 synths",
            explainability="Trust and capability are main drivers",
            segmentation="3 distinct user groups",
            edge_cases="High-capability users failing",
            recommendations=["Add trust signals", "Simplify flow"],
            included_chart_types=["try_vs_success", "shap_summary", "pca_scatter"],
            status="completed",
        )

        # Store
        stored = cache_repo.store_executive_summary(summary)
        assert stored.analysis_id == analysis_id

        # Retrieve
        retrieved = cache_repo.get_executive_summary(analysis_id)
        assert retrieved is not None
        assert retrieved.overview == "Tested checkout with 500 synths"
        assert len(retrieved.recommendations) == 2
        assert len(retrieved.included_chart_types) == 3
        assert retrieved.status == "completed"

    def test_returns_none_for_missing_summary(self, cache_repo, analysis_id):
        """Should return None if summary doesn't exist."""
        result = cache_repo.get_executive_summary(analysis_id)
        assert result is None

    def test_updates_existing_summary(self, cache_repo, analysis_id):
        """Should update summary if already exists."""
        summary_v1 = ExecutiveSummary(
            analysis_id=analysis_id,
            overview="Version 1",
            explainability="V1",
            segmentation="V1",
            edge_cases="V1",
            recommendations=["R1", "R2"],
            included_chart_types=["chart1", "chart2", "chart3"],
            status="completed",
        )
        cache_repo.store_executive_summary(summary_v1)

        # Update
        summary_v2 = ExecutiveSummary(
            analysis_id=analysis_id,
            overview="Version 2 - Updated",
            explainability="V2",
            segmentation="V2",
            edge_cases="V2",
            recommendations=["R1 updated", "R2 updated"],
            included_chart_types=["chart1", "chart2", "chart3", "chart4"],
            status="completed",
        )
        cache_repo.store_executive_summary(summary_v2)

        # Should retrieve latest
        retrieved = cache_repo.get_executive_summary(analysis_id)
        assert retrieved.overview == "Version 2 - Updated"
        assert len(retrieved.included_chart_types) == 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
