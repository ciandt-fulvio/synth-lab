"""
Unit tests for Sankey flow chart generation.

Tests the gap calculation functions and outcome aggregation
for the Sankey diagram visualization.

References:
    - Spec: specs/025-sankey-diagram/spec.md
    - Research: specs/025-sankey-diagram/research.md
"""

import pytest

from synth_lab.domain.entities import (
    FeatureScorecard,
    ScorecardDimension,
    ScorecardIdentification,
    SynthOutcome,
)
from synth_lab.domain.entities.simulation_attributes import (
    SimulationAttributes,
    SimulationLatentTraits,
    SimulationObservables,
)
from synth_lab.services.simulation.chart_data_service import ChartDataService


@pytest.fixture
def chart_service() -> ChartDataService:
    """Create chart data service instance."""
    return ChartDataService()


@pytest.fixture
def sample_scorecard() -> FeatureScorecard:
    """Create a sample scorecard for testing."""
    return FeatureScorecard(
        id="ab123456",  # 8-character alphanumeric ID (no underscores)
        identification=ScorecardIdentification(
            feature_name="Test Feature",
            use_scenario="Test scenario for unit tests",
        ),
        description_text="A test feature description for unit tests",
        perceived_risk=ScorecardDimension(
            score=0.6, min_uncertainty=0.5, max_uncertainty=0.7
        ),
        initial_effort=ScorecardDimension(
            score=0.7, min_uncertainty=0.6, max_uncertainty=0.8
        ),
        complexity=ScorecardDimension(
            score=0.5, min_uncertainty=0.4, max_uncertainty=0.6
        ),
        time_to_value=ScorecardDimension(
            score=0.6, min_uncertainty=0.5, max_uncertainty=0.7
        ),
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
        id=f"out_12345678",
        synth_id=synth_id,
        analysis_id="ana_12345678",
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


# =============================================================================
# Tests for get_dominant_outcome (T008)
# =============================================================================


class TestGetDominantOutcome:
    """Tests for determining dominant outcome from rates."""

    def test_highest_rate_wins(self, chart_service: ChartDataService) -> None:
        """Dominant outcome is the one with highest rate."""
        outcome = create_synth_outcome(
            synth_id="synth_001",
            did_not_try_rate=0.2,
            failed_rate=0.3,
            success_rate=0.5,  # Highest
        )
        result = chart_service.get_dominant_outcome(outcome)
        assert result == "success"

    def test_did_not_try_highest(self, chart_service: ChartDataService) -> None:
        """did_not_try wins when it has highest rate."""
        outcome = create_synth_outcome(
            synth_id="synth_002",
            did_not_try_rate=0.6,  # Highest
            failed_rate=0.3,
            success_rate=0.1,
        )
        result = chart_service.get_dominant_outcome(outcome)
        assert result == "did_not_try"

    def test_failed_highest(self, chart_service: ChartDataService) -> None:
        """failed wins when it has highest rate."""
        outcome = create_synth_outcome(
            synth_id="synth_003",
            did_not_try_rate=0.2,
            failed_rate=0.6,  # Highest
            success_rate=0.2,
        )
        result = chart_service.get_dominant_outcome(outcome)
        assert result == "failed"

    def test_tie_success_over_failed(self, chart_service: ChartDataService) -> None:
        """On tie, success has priority over failed."""
        outcome = create_synth_outcome(
            synth_id="synth_004",
            did_not_try_rate=0.0,
            failed_rate=0.5,  # Tie
            success_rate=0.5,  # Tie - but priority
        )
        result = chart_service.get_dominant_outcome(outcome)
        assert result == "success"

    def test_tie_failed_over_did_not_try(self, chart_service: ChartDataService) -> None:
        """On tie, failed has priority over did_not_try."""
        outcome = create_synth_outcome(
            synth_id="synth_005",
            did_not_try_rate=0.5,  # Tie
            failed_rate=0.5,  # Tie - but priority
            success_rate=0.0,
        )
        result = chart_service.get_dominant_outcome(outcome)
        assert result == "failed"

    def test_three_way_tie(self, chart_service: ChartDataService) -> None:
        """On three-way tie, success wins."""
        outcome = create_synth_outcome(
            synth_id="synth_006",
            did_not_try_rate=1 / 3,
            failed_rate=1 / 3,
            success_rate=1 / 3,
        )
        result = chart_service.get_dominant_outcome(outcome)
        assert result == "success"


# =============================================================================
# Tests for diagnose_did_not_try (T017-T020)
# =============================================================================


class TestDiagnoseDidNotTry:
    """Tests for root cause diagnosis of did_not_try outcome.

    Based on P(attempt) formula: 2.0*motivation + 1.5*trust - 2.0*risk - 1.5*effort

    Gaps (barrier - enabler):
    - effort_gap = 1.5*initial_effort - 2.0*motivation
    - risk_gap = 2.0*perceived_risk - 1.5*trust
    """

    def test_effort_gap_largest(
        self, chart_service: ChartDataService, sample_scorecard: FeatureScorecard
    ) -> None:
        """Returns effort_barrier when effort_gap is largest."""
        # initial_effort.score = 0.7, motivation = 0.5
        # effort_gap = 1.5*0.7 - 2.0*0.5 = 1.05 - 1.0 = 0.05
        # perceived_risk.score = 0.6, trust_mean = 0.8
        # risk_gap = 2.0*0.6 - 1.5*0.8 = 1.2 - 1.2 = 0.0
        # effort_gap > risk_gap → effort_barrier
        outcome = create_synth_outcome(
            synth_id="synth_010",
            did_not_try_rate=0.8,
            failed_rate=0.1,
            success_rate=0.1,
            trust_mean=0.8,  # High trust makes risk_gap small
            friction_tolerance_mean=0.9,
        )
        result = chart_service.diagnose_did_not_try(outcome, sample_scorecard)
        assert result == "effort_barrier"

    def test_risk_gap_largest(
        self, chart_service: ChartDataService, sample_scorecard: FeatureScorecard
    ) -> None:
        """Returns risk_barrier when risk_gap is largest."""
        # perceived_risk.score = 0.6, trust_mean = 0.2
        # risk_gap = 2.0*0.6 - 1.5*0.2 = 1.2 - 0.3 = 0.9
        # effort_gap = 1.5*0.7 - 2.0*0.5 = 0.05
        # risk_gap > effort_gap → risk_barrier
        outcome = create_synth_outcome(
            synth_id="synth_011",
            did_not_try_rate=0.8,
            failed_rate=0.1,
            success_rate=0.1,
            trust_mean=0.2,  # Low trust makes risk_gap large
            friction_tolerance_mean=0.9,
        )
        result = chart_service.diagnose_did_not_try(outcome, sample_scorecard)
        assert result == "risk_barrier"

    def test_tie_breaking_effort_over_risk(
        self, chart_service: ChartDataService, sample_scorecard: FeatureScorecard
    ) -> None:
        """On tie, effort_barrier wins over risk_barrier."""
        # Create roughly equal gaps
        # effort_gap = 1.5*0.7 - 2.0*0.5 = 0.05
        # risk_gap = 2.0*0.6 - 1.5*trust = 0.05 → trust = (1.2-0.05)/1.5 = 0.767
        outcome = create_synth_outcome(
            synth_id="synth_013",
            did_not_try_rate=0.8,
            failed_rate=0.1,
            success_rate=0.1,
            trust_mean=0.767,  # Makes risk_gap ≈ effort_gap
            friction_tolerance_mean=0.9,
        )
        result = chart_service.diagnose_did_not_try(outcome, sample_scorecard)
        assert result == "effort_barrier"  # effort has higher priority on tie


# =============================================================================
# Tests for diagnose_failed (T024-T026)
# =============================================================================


class TestDiagnoseFailed:
    """Tests for root cause diagnosis of failed outcome."""

    def test_capability_gap_largest(
        self, chart_service: ChartDataService, sample_scorecard: FeatureScorecard
    ) -> None:
        """Returns capability_barrier when capability_gap is largest."""
        # complexity.score = 0.5, capability_mean = 0.2
        # capability_gap = 0.5 - 0.2 = 0.3 (largest)
        outcome = create_synth_outcome(
            synth_id="synth_020",
            did_not_try_rate=0.1,
            failed_rate=0.7,
            success_rate=0.2,
            capability_mean=0.2,  # capability_gap = 0.5 - 0.2 = 0.3
            friction_tolerance_mean=0.9,  # patience_gap = 0.6 - 0.9 = -0.3
        )
        result = chart_service.diagnose_failed(outcome, sample_scorecard)
        assert result == "capability_barrier"

    def test_patience_gap_largest(
        self, chart_service: ChartDataService, sample_scorecard: FeatureScorecard
    ) -> None:
        """Returns patience_barrier when patience_gap is largest."""
        # time_to_value.score = 0.6, friction_tolerance_mean = 0.2
        # patience_gap = 0.6 - 0.2 = 0.4 (largest)
        outcome = create_synth_outcome(
            synth_id="synth_021",
            did_not_try_rate=0.1,
            failed_rate=0.7,
            success_rate=0.2,
            capability_mean=0.9,  # capability_gap = 0.5 - 0.9 = -0.4
            friction_tolerance_mean=0.2,  # patience_gap = 0.6 - 0.2 = 0.4
        )
        result = chart_service.diagnose_failed(outcome, sample_scorecard)
        assert result == "patience_barrier"

    def test_tie_breaking_capability_over_patience(
        self, chart_service: ChartDataService, sample_scorecard: FeatureScorecard
    ) -> None:
        """On tie, capability_gap (capability_barrier) wins over patience_gap."""
        # Create equal gaps
        # complexity.score = 0.5, capability_mean = 0.3 → gap = 0.2
        # time_to_value.score = 0.6, friction_tolerance_mean = 0.4 → gap = 0.2
        outcome = create_synth_outcome(
            synth_id="synth_022",
            did_not_try_rate=0.1,
            failed_rate=0.7,
            success_rate=0.2,
            capability_mean=0.3,  # capability_gap = 0.5 - 0.3 = 0.2
            friction_tolerance_mean=0.4,  # patience_gap = 0.6 - 0.4 = 0.2
        )
        result = chart_service.diagnose_failed(outcome, sample_scorecard)
        assert result == "capability_barrier"  # capability has higher priority


# =============================================================================
# Tests for get_sankey_flow (T009, T029)
# =============================================================================


class TestGetSankeyFlow:
    """Tests for Sankey flow chart generation."""

    def test_empty_outcomes(
        self, chart_service: ChartDataService, sample_scorecard: FeatureScorecard
    ) -> None:
        """Returns empty chart when no outcomes."""
        result = chart_service.get_sankey_flow(
            analysis_id="ana_test0000",
            outcomes=[],
            scorecard=sample_scorecard,
        )
        assert result.total_synths == 0
        assert len(result.nodes) == 0
        assert len(result.links) == 0
        assert result.outcome_counts.did_not_try == 0
        assert result.outcome_counts.failed == 0
        assert result.outcome_counts.success == 0

    def test_outcome_aggregation(
        self, chart_service: ChartDataService, sample_scorecard: FeatureScorecard
    ) -> None:
        """Correctly aggregates outcomes by dominant result."""
        outcomes = [
            create_synth_outcome("s1", 0.1, 0.2, 0.7),  # success
            create_synth_outcome("s2", 0.2, 0.1, 0.7),  # success
            create_synth_outcome("s3", 0.7, 0.2, 0.1),  # did_not_try
            create_synth_outcome("s4", 0.2, 0.7, 0.1),  # failed
            create_synth_outcome("s5", 0.2, 0.6, 0.2),  # failed
        ]
        result = chart_service.get_sankey_flow(
            analysis_id="ana_test0001",
            outcomes=outcomes,
            scorecard=sample_scorecard,
        )
        assert result.total_synths == 5
        assert result.outcome_counts.success == 2
        assert result.outcome_counts.did_not_try == 1
        assert result.outcome_counts.failed == 2

    def test_success_has_no_outgoing_links(
        self, chart_service: ChartDataService, sample_scorecard: FeatureScorecard
    ) -> None:
        """Success nodes should not have outgoing links (terminal)."""
        outcomes = [
            create_synth_outcome("s1", 0.0, 0.0, 1.0),  # 100% success
        ]
        result = chart_service.get_sankey_flow(
            analysis_id="ana_test0002",
            outcomes=outcomes,
            scorecard=sample_scorecard,
        )
        # Find links from success
        success_outgoing = [l for l in result.links if l.source == "success"]
        assert len(success_outgoing) == 0

    def test_all_synths_same_outcome(
        self, chart_service: ChartDataService, sample_scorecard: FeatureScorecard
    ) -> None:
        """Handles case where all synths have same dominant outcome."""
        outcomes = [
            create_synth_outcome("s1", 0.0, 0.0, 1.0),
            create_synth_outcome("s2", 0.0, 0.0, 1.0),
            create_synth_outcome("s3", 0.0, 0.0, 1.0),
        ]
        result = chart_service.get_sankey_flow(
            analysis_id="ana_test0003",
            outcomes=outcomes,
            scorecard=sample_scorecard,
        )
        assert result.outcome_counts.success == 3
        assert result.outcome_counts.did_not_try == 0
        assert result.outcome_counts.failed == 0
        # Should only have population and success nodes
        node_ids = [n.id for n in result.nodes]
        assert "population" in node_ids
        assert "success" in node_ids
        assert "did_not_try" not in node_ids
        assert "failed" not in node_ids

    def test_nodes_have_correct_levels(
        self, chart_service: ChartDataService, sample_scorecard: FeatureScorecard
    ) -> None:
        """Nodes should have correct hierarchy levels."""
        outcomes = [
            create_synth_outcome("s1", 0.7, 0.2, 0.1, trust_mean=0.1),  # did_not_try
            create_synth_outcome("s2", 0.1, 0.7, 0.2, capability_mean=0.1),  # failed
            create_synth_outcome("s3", 0.1, 0.2, 0.7),  # success
        ]
        result = chart_service.get_sankey_flow(
            analysis_id="ana_test0004",
            outcomes=outcomes,
            scorecard=sample_scorecard,
        )
        # Check levels
        for node in result.nodes:
            if node.id == "population":
                assert node.level == 1
            elif node.id in ["did_not_try", "failed", "success"]:
                assert node.level == 2
            else:
                # Root cause nodes
                assert node.level == 3

    def test_links_sum_correctly(
        self, chart_service: ChartDataService, sample_scorecard: FeatureScorecard
    ) -> None:
        """Links from population should sum to total synths."""
        outcomes = [
            create_synth_outcome("s1", 0.7, 0.2, 0.1),  # did_not_try
            create_synth_outcome("s2", 0.1, 0.7, 0.2),  # failed
            create_synth_outcome("s3", 0.1, 0.2, 0.7),  # success
            create_synth_outcome("s4", 0.1, 0.2, 0.7),  # success
        ]
        result = chart_service.get_sankey_flow(
            analysis_id="ana_test0005",
            outcomes=outcomes,
            scorecard=sample_scorecard,
        )
        # Sum of population outgoing links
        population_links = [l for l in result.links if l.source == "population"]
        total_from_population = sum(l.value for l in population_links)
        assert total_from_population == result.total_synths
