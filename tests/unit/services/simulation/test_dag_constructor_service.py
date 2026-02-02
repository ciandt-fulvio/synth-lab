"""
Unit tests for DAGConstructorService unified generation.

Tests the UnifiedDAGResponse schema, hypothesis conversion,
and fallback logic for missing hypotheses.

References:
    - Spec: specs/037-unified-dag-hypotheses/spec.md
    - Implementation: synth_lab/services/simulation/dag_constructor_service.py
"""

import pytest

from synth_lab.domain.entities.hypothesis import (
    DistributionType,
    Hypothesis,
    Relevance,
)
from synth_lab.services.simulation.dag_constructor_service import (
    DAGResponse,
    LLMAssumption,
    LLMEdge,
    LLMRisk,
    LLMVariable,
)


# ============================================================================
# Fixtures
# ============================================================================

def _make_llm_variables() -> list[LLMVariable]:
    """Create sample LLM variables for testing."""
    return [
        LLMVariable(
            id="var_001",
            name="preco",
            type="observable",
            scope="world",
            description="Preço do produto",
            controllability="high",
            is_intervention=True,
            is_outcome=False,
        ),
        LLMVariable(
            id="var_002",
            name="demanda",
            type="observable",
            scope="user",
            description="Demanda do mercado",
            controllability="none",
            is_intervention=False,
            is_outcome=True,
        ),
        LLMVariable(
            id="var_003",
            name="satisfacao",
            type="latent",
            scope="user",
            description="Satisfação do cliente",
            controllability="low",
            is_intervention=False,
            is_outcome=False,
        ),
    ]


def _make_llm_edges() -> list[LLMEdge]:
    return [
        LLMEdge(**{"from": "var_001", "to": "var_002", "relationship_type": "causal", "strength_estimated": "high"}),
        LLMEdge(**{"from": "var_001", "to": "var_003", "relationship_type": "causal", "strength_estimated": "low"}),
    ]


def _make_llm_assumptions() -> list[LLMAssumption]:
    return [
        LLMAssumption(assumption="Mercado estável", rationale="Sem crise", confidence="medium"),
    ]


def _make_llm_risks() -> list[LLMRisk]:
    return [
        LLMRisk(risk="Concorrência", impact="medium", mitigation="Monitorar"),
    ]


# ============================================================================
# T014: UnifiedDAGResponse schema parsing
# ============================================================================

class TestUnifiedDAGResponseParsing:
    """T014: Test UnifiedDAGResponse Pydantic schema parsing."""

    def test_parse_valid_response_with_hypotheses(self):
        """UnifiedDAGResponse parses correctly with hypotheses included."""
        from synth_lab.services.simulation.dag_constructor_service import (
            LLMHypothesis,
            UnifiedDAGResponse,
        )

        hypotheses = [
            LLMHypothesis(
                variable_name="preco",
                distribution_type="normal",
                parameters={"mean": 50.0, "std": 10.0},
                relevance="high",
                range_min=10.0,
                range_max=100.0,
            ),
            LLMHypothesis(
                variable_name="demanda",
                distribution_type="beta",
                parameters={"alpha": 2.0, "beta": 8.0},
                relevance="medium",
            ),
        ]

        response = UnifiedDAGResponse(
            variables=_make_llm_variables(),
            edges=_make_llm_edges(),
            assumptions=_make_llm_assumptions(),
            risks=_make_llm_risks(),
            hypotheses=hypotheses,
        )

        assert len(response.hypotheses) == 2
        assert response.hypotheses[0].variable_name == "preco"
        assert response.hypotheses[0].relevance == "high"
        assert response.hypotheses[0].range_min == 10.0
        assert response.hypotheses[1].range_min is None

    def test_parse_response_without_hypotheses_uses_default(self):
        """UnifiedDAGResponse defaults to empty list when hypotheses not provided."""
        from synth_lab.services.simulation.dag_constructor_service import UnifiedDAGResponse

        response = UnifiedDAGResponse(
            variables=_make_llm_variables(),
            edges=_make_llm_edges(),
            assumptions=_make_llm_assumptions(),
            risks=_make_llm_risks(),
        )

        assert response.hypotheses == []


# ============================================================================
# T015: Fallback for missing hypotheses
# ============================================================================

class TestFallbackMissingHypotheses:
    """T015: Fallback when LLM response is missing hypotheses for some variables."""

    def test_fallback_creates_uniform_medium_for_missing_vars(self):
        """Variables without LLM hypotheses get uniform, medium relevance, no range."""
        from loguru import logger as _logger

        from synth_lab.services.simulation.dag_constructor_service import (
            DAGConstructorService,
            LLMHypothesis,
        )

        service = DAGConstructorService.__new__(DAGConstructorService)
        service.logger = _logger.bind(component="test")

        # Only provide hypothesis for var_001 (preco), missing var_002 and var_003
        llm_hypotheses = [
            LLMHypothesis(
                variable_name="preco",
                distribution_type="normal",
                parameters={"mean": 50.0, "std": 10.0},
                relevance="high",
            ),
        ]

        variables = _make_llm_variables()
        var_names = [v.name for v in variables]

        hypotheses = service._convert_llm_hypotheses_to_entities(
            simulation_id="sim_00000001",
            llm_hypotheses=llm_hypotheses,
            variable_names=var_names,
            variable_id_map={"preco": "dag_001_var_001", "demanda": "dag_001_var_002", "satisfacao": "dag_001_var_003"},
        )

        assert len(hypotheses) == 3

        # First should be from LLM
        preco_hyp = next(h for h in hypotheses if h.variable_name == "preco")
        assert preco_hyp.distribution_type == DistributionType.NORMAL
        assert preco_hyp.relevance == Relevance.HIGH

        # Missing ones should be fallback
        demanda_hyp = next(h for h in hypotheses if h.variable_name == "demanda")
        assert demanda_hyp.distribution_type == DistributionType.UNIFORM
        assert demanda_hyp.relevance == Relevance.MEDIUM
        assert demanda_hyp.range_min is None
        assert demanda_hyp.range_max is None


# ============================================================================
# T016: _convert_llm_hypotheses_to_entities mapping
# ============================================================================

class TestConvertLLMHypotheses:
    """T016: Test mapping LLMHypothesis → Hypothesis domain entity."""

    def test_maps_all_fields_correctly(self):
        """LLMHypothesis fields are mapped to Hypothesis entity."""
        from synth_lab.services.simulation.dag_constructor_service import (
            DAGConstructorService,
            LLMHypothesis,
        )

        service = DAGConstructorService.__new__(DAGConstructorService)

        llm_hypotheses = [
            LLMHypothesis(
                variable_name="preco",
                distribution_type="lognormal",
                parameters={"mean": 4.0, "sigma": 0.6},
                relevance="low",
                range_min=5.0,
                range_max=500.0,
            ),
        ]

        hypotheses = service._convert_llm_hypotheses_to_entities(
            simulation_id="sim_00000001",
            llm_hypotheses=llm_hypotheses,
            variable_names=["preco"],
            variable_id_map={"preco": "dag_001_var_001"},
        )

        assert len(hypotheses) == 1
        hyp = hypotheses[0]
        assert hyp.simulation_id == "sim_00000001"
        assert hyp.variable_id == "dag_001_var_001"
        assert hyp.variable_name == "preco"
        assert hyp.distribution_type == DistributionType.LOGNORMAL
        assert hyp.relevance == Relevance.LOW
        assert hyp.range_min == 5.0
        assert hyp.range_max == 500.0
        assert hyp.parameters.mean == 4.0
        assert hyp.parameters.sigma == 0.6

    def test_maps_beta_distribution(self):
        """Beta distribution parameters are correctly mapped."""
        from synth_lab.services.simulation.dag_constructor_service import (
            DAGConstructorService,
            LLMHypothesis,
        )

        service = DAGConstructorService.__new__(DAGConstructorService)

        llm_hypotheses = [
            LLMHypothesis(
                variable_name="taxa",
                distribution_type="beta",
                parameters={"alpha": 2.0, "beta": 8.0},
                relevance="medium",
            ),
        ]

        hypotheses = service._convert_llm_hypotheses_to_entities(
            simulation_id="sim_00000001",
            llm_hypotheses=llm_hypotheses,
            variable_names=["taxa"],
            variable_id_map={"taxa": "dag_001_var_001"},
        )

        hyp = hypotheses[0]
        assert hyp.distribution_type == DistributionType.BETA
        assert hyp.parameters.alpha == 2.0
        assert hyp.parameters.beta == 8.0

    def test_unsupported_distribution_falls_back_to_uniform(self):
        """Unknown distribution type falls back to uniform."""
        from synth_lab.services.simulation.dag_constructor_service import (
            DAGConstructorService,
            LLMHypothesis,
        )

        service = DAGConstructorService.__new__(DAGConstructorService)
        import logging
        service.logger = logging.getLogger("test")

        llm_hypotheses = [
            LLMHypothesis(
                variable_name="x",
                distribution_type="gamma",  # unsupported
                parameters={"shape": 2.0, "scale": 1.0},
                relevance="medium",
            ),
        ]

        hypotheses = service._convert_llm_hypotheses_to_entities(
            simulation_id="sim_00000001",
            llm_hypotheses=llm_hypotheses,
            variable_names=["x"],
            variable_id_map={"x": "dag_001_var_001"},
        )

        hyp = hypotheses[0]
        assert hyp.distribution_type == DistributionType.UNIFORM
