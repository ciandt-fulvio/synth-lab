"""
Unit tests for Sankey flow chart generation.

Tests the 2-outcome (adopted / not_adopted) Sankey diagram visualization.

References:
    - Spec: specs/025-sankey-diagram/spec.md
    - Research: specs/025-sankey-diagram/research.md
"""

import pytest

from synth_lab.domain.entities import (
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


def create_synth_outcome(
    synth_id: str,
    adopted_rate: float,
    not_adopted_rate: float,
    capability_mean: float = 0.5,
    trust_mean: float = 0.5,
    friction_tolerance_mean: float = 0.5,
) -> SynthOutcome:
    """Helper to create SynthOutcome with simulation attributes."""
    return SynthOutcome(
        id="out_12345678",
        synth_id=synth_id,
        analysis_id="ana_12345678",
        adopted_rate=adopted_rate,
        not_adopted_rate=not_adopted_rate,
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
# Tests for get_sankey_flow
# =============================================================================


class TestGetSankeyFlow:
    """Tests for Sankey flow chart generation with 2-outcome model."""

    def test_empty_outcomes(self, chart_service: ChartDataService) -> None:
        """Returns empty chart when no outcomes."""
        result = chart_service.get_sankey_flow(
            analysis_id="ana_test0000",
            outcomes=[],
        )
        assert result.total_synths == 0
        assert len(result.nodes) == 0
        assert len(result.links) == 0
        assert result.outcome_counts.adopted == 0
        assert result.outcome_counts.not_adopted == 0

    def test_outcome_aggregation(self, chart_service: ChartDataService) -> None:
        """Correctly aggregates outcomes into adopted and not_adopted."""
        outcomes = [
            create_synth_outcome("s1", adopted_rate=0.70, not_adopted_rate=0.30),
            create_synth_outcome("s2", adopted_rate=0.80, not_adopted_rate=0.20),
            create_synth_outcome("s3", adopted_rate=0.30, not_adopted_rate=0.70),
            create_synth_outcome("s4", adopted_rate=0.50, not_adopted_rate=0.50),
            create_synth_outcome("s5", adopted_rate=0.60, not_adopted_rate=0.40),
        ]
        result = chart_service.get_sankey_flow(
            analysis_id="ana_test0001",
            outcomes=outcomes,
        )
        assert result.total_synths == 5
        # adopted + not_adopted should sum to total_synths
        assert result.outcome_counts.adopted + result.outcome_counts.not_adopted == 5

    def test_all_synths_adopted(self, chart_service: ChartDataService) -> None:
        """Handles case where all synths are fully adopted."""
        outcomes = [
            create_synth_outcome("s1", adopted_rate=1.0, not_adopted_rate=0.0),
            create_synth_outcome("s2", adopted_rate=1.0, not_adopted_rate=0.0),
            create_synth_outcome("s3", adopted_rate=1.0, not_adopted_rate=0.0),
        ]
        result = chart_service.get_sankey_flow(
            analysis_id="ana_test0003",
            outcomes=outcomes,
        )
        assert result.outcome_counts.adopted == 3
        assert result.outcome_counts.not_adopted == 0
        # Should only have population and adopted nodes
        node_ids = [n.id for n in result.nodes]
        assert "population" in node_ids
        assert "adopted" in node_ids
        assert "not_adopted" not in node_ids

    def test_nodes_have_correct_levels(self, chart_service: ChartDataService) -> None:
        """Nodes should have correct hierarchy levels (1=Population, 2=Outcome)."""
        outcomes = [
            create_synth_outcome("s1", adopted_rate=0.70, not_adopted_rate=0.30),
            create_synth_outcome("s2", adopted_rate=0.30, not_adopted_rate=0.70),
            create_synth_outcome("s3", adopted_rate=0.50, not_adopted_rate=0.50),
        ]
        result = chart_service.get_sankey_flow(
            analysis_id="ana_test0004",
            outcomes=outcomes,
        )
        # Check levels
        for node in result.nodes:
            if node.id == "population":
                assert node.level == 1
            elif node.id in ["adopted", "not_adopted"]:
                assert node.level == 2

    def test_links_sum_correctly(self, chart_service: ChartDataService) -> None:
        """Links from population should sum to total synths."""
        outcomes = [
            create_synth_outcome("s1", adopted_rate=0.70, not_adopted_rate=0.30),
            create_synth_outcome("s2", adopted_rate=0.30, not_adopted_rate=0.70),
            create_synth_outcome("s3", adopted_rate=0.80, not_adopted_rate=0.20),
            create_synth_outcome("s4", adopted_rate=0.50, not_adopted_rate=0.50),
        ]
        result = chart_service.get_sankey_flow(
            analysis_id="ana_test0005",
            outcomes=outcomes,
        )
        # Sum of population outgoing links
        population_links = [link for link in result.links if link.source == "population"]
        total_from_population = sum(link.value for link in population_links)
        assert total_from_population == result.total_synths

    def test_no_level_3_nodes(self, chart_service: ChartDataService) -> None:
        """2-outcome model should only have level 1 and level 2 nodes."""
        outcomes = [
            create_synth_outcome("s1", adopted_rate=0.60, not_adopted_rate=0.40),
            create_synth_outcome("s2", adopted_rate=0.40, not_adopted_rate=0.60),
        ]
        result = chart_service.get_sankey_flow(
            analysis_id="ana_test0006",
            outcomes=outcomes,
        )
        for node in result.nodes:
            assert node.level in [1, 2]
