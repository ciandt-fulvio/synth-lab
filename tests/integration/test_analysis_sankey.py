"""
Integration tests for Sankey flow chart API endpoint.

Tests the full flow from API request to response for the Sankey endpoint.

References:
    - Spec: specs/025-sankey-diagram/spec.md
    - Analysis Router: src/synth_lab/api/routers/analysis.py
    - Chart Data Service: src/synth_lab/services/simulation/chart_data_service.py
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from synth_lab.api.main import app
from synth_lab.domain.entities import (
    SynthOutcome,
)
from synth_lab.domain.entities.analysis_run import (
    AggregatedOutcomes,
    AnalysisConfig,
    AnalysisRun,
)
from synth_lab.domain.entities.experiment import (
    Experiment,
    ScorecardData,
    ScorecardDimension,
)
from synth_lab.domain.entities.simulation_attributes import (
    SimulationAttributes,
    SimulationLatentTraits,
    SimulationObservables,
)


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_completed_analysis():
    """Create a mock completed analysis."""
    return AnalysisRun(
        id="ana_12345678",  # 8 hex chars after ana_
        experiment_id="exp_12345678",  # 8 hex chars after exp_
        config=AnalysisConfig(n_synths=50, n_executions=10),
        status="completed",
        total_synths=50,
        aggregated_outcomes=AggregatedOutcomes(
            did_not_try_rate=0.3,
            failed_rate=0.2,
            success_rate=0.5,
        ),
    )


@pytest.fixture
def mock_running_analysis():
    """Create a mock running analysis."""
    return AnalysisRun(
        id="ana_abcdef12",  # 8 hex chars after ana_
        experiment_id="exp_abcdef12",  # 8 hex chars after exp_
        config=AnalysisConfig(n_synths=50, n_executions=10),
        status="running",
        total_synths=0,
    )


@pytest.fixture
def mock_scorecard():
    """Create a mock scorecard for testing."""
    return ScorecardData(
        feature_name="Test Feature",
        scenario="Test scenario",
        description_text="Test feature description",
        perceived_risk=ScorecardDimension(score=0.5),
        initial_effort=ScorecardDimension(score=0.6),
        complexity=ScorecardDimension(score=0.4),
        time_to_value=ScorecardDimension(score=0.5),
    )


@pytest.fixture
def mock_experiment(mock_scorecard):
    """Create a mock experiment with scorecard."""
    return Experiment(
        id="exp_12345678",  # 8 hex chars after exp_
        name="Test Experiment",
        hypothesis="Test hypothesis for the experiment",
        scorecard_data=mock_scorecard,
    )


@pytest.fixture
def mock_experiment_no_scorecard():
    """Create a mock experiment without scorecard."""
    return Experiment(
        id="exp_98765432",  # 8 hex chars after exp_
        name="Test Experiment No Scorecard",
        hypothesis="Test hypothesis for the experiment without scorecard",
        scorecard_data=None,
    )


def create_synth_outcome(
    synth_id: str,
    did_not_try_rate: float,
    failed_rate: float,
    success_rate: float,
    capability_mean: float = 0.5,
    trust_mean: float = 0.5,
    friction_tolerance_mean: float = 0.5,
) -> SynthOutcome:
    """Helper to create SynthOutcome with simulation attributes."""
    return SynthOutcome(
        id="out_12345678",  # Pattern: out_[a-f0-9]{8}
        synth_id=synth_id,
        analysis_id="ana_12345678",  # Pattern: ana_[a-f0-9]{8}
        did_not_try_rate=did_not_try_rate,
        failed_rate=failed_rate,
        success_rate=success_rate,
        synth_attributes=SimulationAttributes(
            latent_traits=SimulationLatentTraits(
                capability_mean=capability_mean,
                trust_mean=trust_mean,
                friction_tolerance_mean=friction_tolerance_mean,
                exploration_prob=0.5,
            ),
            observables=SimulationObservables(
                digital_literacy=0.5,
                similar_tool_experience=0.5,
                motor_ability=0.5,
                time_availability=0.5,
                domain_expertise=0.5,
            ),
        ),
    )


@pytest.fixture
def mock_outcomes():
    """Create a list of mock outcomes for testing."""
    return [
        create_synth_outcome("s1", 0.1, 0.2, 0.7),  # success
        create_synth_outcome("s2", 0.1, 0.2, 0.7),  # success
        create_synth_outcome("s3", 0.7, 0.2, 0.1, trust_mean=0.1),  # did_not_try
        create_synth_outcome("s4", 0.2, 0.7, 0.1, capability_mean=0.1),  # failed
        create_synth_outcome("s5", 0.2, 0.6, 0.2, capability_mean=0.1),  # failed
    ]


class TestSankeyFlowEndpoint:
    """Integration tests for GET /experiments/{id}/analysis/charts/sankey-flow."""

    def test_sankey_flow_returns_valid_data(
        self,
        client,
        mock_completed_analysis,
        mock_experiment,
        mock_outcomes,
    ):
        """Test that endpoint returns valid Sankey flow data for completed analysis."""
        with (
            patch(
                "synth_lab.api.routers.analysis.get_analysis_service"
            ) as mock_analysis_svc,
            patch(
                "synth_lab.api.routers.analysis.get_experiment_service"
            ) as mock_exp_svc,
            patch(
                "synth_lab.api.routers.analysis.get_outcome_repository"
            ) as mock_outcome_repo,
        ):
            # Setup mocks
            mock_analysis_svc.return_value.get_analysis.return_value = mock_completed_analysis
            mock_exp_svc.return_value.get_experiment.return_value = mock_experiment
            mock_outcome_repo.return_value.get_outcomes.return_value = (mock_outcomes, 5)

            response = client.get("/experiments/exp_12345678/analysis/charts/sankey-flow")

            assert response.status_code == 200
            data = response.json()

            # Verify structure
            assert "analysis_id" in data
            assert "nodes" in data
            assert "links" in data
            assert "total_synths" in data
            assert "outcome_counts" in data

            # Verify counts
            assert data["total_synths"] == 5
            assert data["outcome_counts"]["success"] == 2
            assert data["outcome_counts"]["did_not_try"] == 1
            assert data["outcome_counts"]["failed"] == 2

            # Verify nodes structure
            for node in data["nodes"]:
                assert "id" in node
                assert "label" in node
                assert "level" in node
                assert "color" in node
                assert "value" in node
                assert node["level"] in [1, 2, 3]

            # Verify links structure
            for link in data["links"]:
                assert "source" in link
                assert "target" in link
                assert "value" in link
                assert link["value"] > 0

    def test_sankey_flow_404_no_analysis(self, client):
        """Test that endpoint returns 404 when no analysis exists."""
        with patch(
            "synth_lab.api.routers.analysis.get_analysis_service"
        ) as mock_analysis_svc:
            mock_analysis_svc.return_value.get_analysis.return_value = None

            response = client.get("/experiments/exp_nonexistent/analysis/charts/sankey-flow")

            assert response.status_code == 404
            assert "no analysis found" in response.json()["detail"].lower()

    def test_sankey_flow_400_analysis_not_completed(
        self,
        client,
        mock_running_analysis,
    ):
        """Test that endpoint returns 400 when analysis is not completed."""
        with patch(
            "synth_lab.api.routers.analysis.get_analysis_service"
        ) as mock_analysis_svc:
            mock_analysis_svc.return_value.get_analysis.return_value = mock_running_analysis

            response = client.get("/experiments/exp_abcdef12/analysis/charts/sankey-flow")

            assert response.status_code == 400
            assert "completed" in response.json()["detail"].lower()

    def test_sankey_flow_404_experiment_not_found(
        self,
        client,
        mock_completed_analysis,
    ):
        """Test that endpoint returns 404 when experiment is not found."""
        with (
            patch(
                "synth_lab.api.routers.analysis.get_analysis_service"
            ) as mock_analysis_svc,
            patch(
                "synth_lab.api.routers.analysis.get_experiment_service"
            ) as mock_exp_svc,
        ):
            mock_analysis_svc.return_value.get_analysis.return_value = mock_completed_analysis
            mock_exp_svc.return_value.get_experiment.return_value = None

            response = client.get("/experiments/exp_12345678/analysis/charts/sankey-flow")

            assert response.status_code == 404
            # The error message is "Experiment {exp_id} not found"
            assert "experiment" in response.json()["detail"].lower()

    def test_sankey_flow_400_no_scorecard(
        self,
        client,
        mock_completed_analysis,
        mock_experiment_no_scorecard,
    ):
        """Test that endpoint returns 400 when experiment has no scorecard."""
        with (
            patch(
                "synth_lab.api.routers.analysis.get_analysis_service"
            ) as mock_analysis_svc,
            patch(
                "synth_lab.api.routers.analysis.get_experiment_service"
            ) as mock_exp_svc,
        ):
            mock_analysis_svc.return_value.get_analysis.return_value = mock_completed_analysis
            mock_exp_svc.return_value.get_experiment.return_value = mock_experiment_no_scorecard

            response = client.get("/experiments/exp_98765432/analysis/charts/sankey-flow")

            assert response.status_code == 400
            assert "scorecard" in response.json()["detail"].lower()

    def test_sankey_flow_400_no_outcomes(
        self,
        client,
        mock_completed_analysis,
        mock_experiment,
    ):
        """Test that endpoint returns 400 when no outcomes exist."""
        with (
            patch(
                "synth_lab.api.routers.analysis.get_analysis_service"
            ) as mock_analysis_svc,
            patch(
                "synth_lab.api.routers.analysis.get_experiment_service"
            ) as mock_exp_svc,
            patch(
                "synth_lab.api.routers.analysis.get_outcome_repository"
            ) as mock_outcome_repo,
        ):
            mock_analysis_svc.return_value.get_analysis.return_value = mock_completed_analysis
            mock_exp_svc.return_value.get_experiment.return_value = mock_experiment
            mock_outcome_repo.return_value.get_outcomes.return_value = ([], 0)

            response = client.get("/experiments/exp_12345678/analysis/charts/sankey-flow")

            assert response.status_code == 400
            assert "outcome" in response.json()["detail"].lower()

    def test_sankey_flow_success_is_terminal(
        self,
        client,
        mock_completed_analysis,
        mock_experiment,
    ):
        """Test that success node has no outgoing links (is terminal)."""
        # All synths have 100% success
        all_success_outcomes = [
            create_synth_outcome("s1", 0.0, 0.0, 1.0),
            create_synth_outcome("s2", 0.0, 0.0, 1.0),
            create_synth_outcome("s3", 0.0, 0.0, 1.0),
        ]

        with (
            patch(
                "synth_lab.api.routers.analysis.get_analysis_service"
            ) as mock_analysis_svc,
            patch(
                "synth_lab.api.routers.analysis.get_experiment_service"
            ) as mock_exp_svc,
            patch(
                "synth_lab.api.routers.analysis.get_outcome_repository"
            ) as mock_outcome_repo,
        ):
            mock_analysis_svc.return_value.get_analysis.return_value = mock_completed_analysis
            mock_exp_svc.return_value.get_experiment.return_value = mock_experiment
            mock_outcome_repo.return_value.get_outcomes.return_value = (all_success_outcomes, 3)

            response = client.get("/experiments/exp_12345678/analysis/charts/sankey-flow")

            assert response.status_code == 200
            data = response.json()

            # Verify success has no outgoing links
            success_links = [l for l in data["links"] if l["source"] == "success"]
            assert len(success_links) == 0

            # Verify counts are correct
            assert data["outcome_counts"]["success"] == 3
            assert data["outcome_counts"]["did_not_try"] == 0
            assert data["outcome_counts"]["failed"] == 0

    def test_sankey_flow_has_root_cause_nodes(
        self,
        client,
        mock_completed_analysis,
        mock_experiment,
    ):
        """Test that failed and did_not_try outcomes have root cause nodes."""
        # Mix of outcomes to trigger root cause diagnosis
        mixed_outcomes = [
            create_synth_outcome("s1", 0.7, 0.2, 0.1, trust_mean=0.1),  # did_not_try - risk
            create_synth_outcome("s2", 0.2, 0.7, 0.1, capability_mean=0.1),  # failed - cap
        ]

        with (
            patch(
                "synth_lab.api.routers.analysis.get_analysis_service"
            ) as mock_analysis_svc,
            patch(
                "synth_lab.api.routers.analysis.get_experiment_service"
            ) as mock_exp_svc,
            patch(
                "synth_lab.api.routers.analysis.get_outcome_repository"
            ) as mock_outcome_repo,
        ):
            mock_analysis_svc.return_value.get_analysis.return_value = mock_completed_analysis
            mock_exp_svc.return_value.get_experiment.return_value = mock_experiment
            mock_outcome_repo.return_value.get_outcomes.return_value = (mixed_outcomes, 2)

            response = client.get("/experiments/exp_12345678/analysis/charts/sankey-flow")

            assert response.status_code == 200
            data = response.json()

            # Check that level 3 nodes exist
            level_3_nodes = [n for n in data["nodes"] if n["level"] == 3]
            assert len(level_3_nodes) > 0

            # Check that did_not_try and failed have outgoing links to root causes
            did_not_try_links = [l for l in data["links"] if l["source"] == "did_not_try"]
            failed_links = [l for l in data["links"] if l["source"] == "failed"]

            assert len(did_not_try_links) > 0
            assert len(failed_links) > 0
