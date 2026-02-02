"""
Unit tests for HypothesisWizardService.

Tests for scenario profile adjustments, decision context classification,
and wizard initialization flow.

References:
    - Service: src/synth_lab/services/simulation/hypothesis_wizard_service.py
    - Research: specs/036-simplified-hypothesis-wizard/research.md
"""

from unittest.mock import Mock, patch

import pytest

from synth_lab.domain.entities.causal_dag import (
    CausalDAG,
    Controllability,
    Edge,
    VariableScope,
    VariableType,
)
from synth_lab.domain.entities.causal_dag import Variable as DAGVariable
from synth_lab.domain.entities.hypothesis import (
    BernoulliParams,
    BetaParams,
    DistributionType,
    Hypothesis,
    LogNormalParams,
    NormalParams,
    ScenarioProfile,
    TriangularParams,
    UniformParams,
)
from synth_lab.services.simulation.hypothesis_wizard_service import (
    HypothesisWizardService,
)


@pytest.fixture
def service():
    """Create HypothesisWizardService instance for testing."""
    return HypothesisWizardService()


# ==================== Tests for T009: _classify_decision_context() ====================


def test_classify_decision_context_simple_small_dag():
    """GIVEN small DAG (≤5 nodes) WHEN classifying THEN returns simple."""
    service = HypothesisWizardService()

    dag = CausalDAG(
        id="dag_12345678",
        simulation_id="sim_12345678",
        nodes=[
            DAGVariable(
                id=f"var_{i}",
                name=f"Variable {i}",
                type=VariableType.OBSERVABLE,
                scope=VariableScope.WORLD,
                description=f"Test variable {i}",
                controllability=Controllability.NONE,
            )
            for i in range(5)
        ],
        edges=[],
        assumptions=[],
        risks=[],
    )

    result = service._classify_decision_context(dag)
    assert result == "simple", "DAG with ≤5 nodes should be simple"


def test_classify_decision_context_complex_large_dag():
    """GIVEN large DAG (>10 nodes) WHEN classifying THEN returns complex."""
    service = HypothesisWizardService()

    dag = CausalDAG(
        id="dag_12345678",
        simulation_id="sim_12345678",
        nodes=[
            DAGVariable(
                id=f"var_{i}",
                name=f"Variable {i}",
                type=VariableType.OBSERVABLE,
                scope=VariableScope.WORLD,
                description=f"Test variable {i}",
                controllability=Controllability.NONE,
            )
            for i in range(12)
        ],
        edges=[],
        assumptions=[],
        risks=[],
    )

    result = service._classify_decision_context(dag)
    assert result == "complex", "DAG with >10 nodes should be complex"


def test_classify_decision_context_complex_many_outcomes():
    """GIVEN DAG with >3 outcomes WHEN classifying THEN returns complex."""
    service = HypothesisWizardService()

    dag = CausalDAG(
        id="dag_12345678",
        simulation_id="sim_12345678",
        nodes=[
            DAGVariable(
                id=f"var_{i}",
                name=f"Outcome {i}",
                type=VariableType.OBSERVABLE,
                scope=VariableScope.WORLD,
                description=f"Test outcome {i}",
                controllability=Controllability.NONE,
                is_outcome=True,
            )
            for i in range(4)
        ],
        edges=[],
        assumptions=[],
        risks=[],
    )

    result = service._classify_decision_context(dag)
    assert result == "complex", "DAG with >3 outcomes should be complex"


def test_classify_decision_context_complex_many_controllable():
    """GIVEN DAG with >4 controllable vars WHEN classifying THEN returns complex."""
    service = HypothesisWizardService()

    dag = CausalDAG(
        id="dag_12345678",
        simulation_id="sim_12345678",
        nodes=[
            DAGVariable(
                id=f"var_{i}",
                name=f"Control {i}",
                type=VariableType.OBSERVABLE,
                scope=VariableScope.WORLD,
                description=f"Test controllable {i}",
                controllability=Controllability.HIGH,
            )
            for i in range(5)
        ],
        edges=[],
        assumptions=[],
        risks=[],
    )

    result = service._classify_decision_context(dag)
    assert result == "complex", "DAG with >4 controllable vars should be complex"


# ==================== Tests for T010-T015: _apply_profile_adjustments() ====================


def test_apply_profile_adjustments_normal_conservative():
    """GIVEN Normal distribution hypothesis WHEN applying Conservative profile THEN mean decreases, std increases."""
    service = HypothesisWizardService()

    hypothesis = Hypothesis(
        id="hyp_12345678",
        simulation_id="sim_12345678",
        variable_id="var_0",
        variable_name="test_var",
        distribution_type=DistributionType.NORMAL,
        parameters=NormalParams(mean=10.0, std=2.0),
    )

    adjusted = service._apply_profile_adjustments(
        hypothesis, ScenarioProfile.CONSERVATIVE
    )

    # Conservative: μ - 0.5σ, σ × 1.5
    assert adjusted.parameters.mean == pytest.approx(
        9.0
    ), "Conservative should decrease mean by 0.5 * std"
    assert adjusted.parameters.std == pytest.approx(
        3.0
    ), "Conservative should increase std by 1.5x"


def test_apply_profile_adjustments_normal_realistic():
    """GIVEN Normal distribution hypothesis WHEN applying Realistic profile THEN no change."""
    service = HypothesisWizardService()

    hypothesis = Hypothesis(
        id="hyp_12345678",
        simulation_id="sim_12345678",
        variable_id="var_0",
        variable_name="test_var",
        distribution_type=DistributionType.NORMAL,
        parameters=NormalParams(mean=10.0, std=2.0),
    )

    adjusted = service._apply_profile_adjustments(hypothesis, ScenarioProfile.REALISTIC)

    # Realistic: no change
    assert adjusted.parameters.mean == 10.0, "Realistic should not change mean"
    assert adjusted.parameters.std == 2.0, "Realistic should not change std"


def test_apply_profile_adjustments_normal_optimistic():
    """GIVEN Normal distribution hypothesis WHEN applying Optimistic profile THEN mean increases, std decreases."""
    service = HypothesisWizardService()

    hypothesis = Hypothesis(
        id="hyp_12345678",
        simulation_id="sim_12345678",
        variable_id="var_0",
        variable_name="test_var",
        distribution_type=DistributionType.NORMAL,
        parameters=NormalParams(mean=10.0, std=2.0),
    )

    adjusted = service._apply_profile_adjustments(hypothesis, ScenarioProfile.OPTIMISTIC)

    # Optimistic: μ + 0.5σ, σ × 0.75
    assert adjusted.parameters.mean == pytest.approx(
        11.0
    ), "Optimistic should increase mean by 0.5 * std"
    assert adjusted.parameters.std == pytest.approx(
        1.5
    ), "Optimistic should decrease std by 0.75x"


def test_apply_profile_adjustments_beta_conservative():
    """GIVEN Beta distribution hypothesis WHEN applying Conservative profile THEN shifts toward failure."""
    service = HypothesisWizardService()

    hypothesis = Hypothesis(
        id="hyp_12345678",
        simulation_id="sim_12345678",
        variable_id="var_0",
        variable_name="test_var",
        distribution_type=DistributionType.BETA,
        parameters=BetaParams(alpha=10.0, beta=20.0),
    )

    adjusted = service._apply_profile_adjustments(
        hypothesis, ScenarioProfile.CONSERVATIVE
    )

    # Conservative: α × 0.7, β × 1.3
    assert adjusted.parameters.alpha == pytest.approx(
        7.0
    ), "Conservative should decrease alpha by 0.7x"
    assert adjusted.parameters.beta == pytest.approx(
        26.0
    ), "Conservative should increase beta by 1.3x"


def test_apply_profile_adjustments_beta_optimistic():
    """GIVEN Beta distribution hypothesis WHEN applying Optimistic profile THEN shifts toward success."""
    service = HypothesisWizardService()

    hypothesis = Hypothesis(
        id="hyp_12345678",
        simulation_id="sim_12345678",
        variable_id="var_0",
        variable_name="test_var",
        distribution_type=DistributionType.BETA,
        parameters=BetaParams(alpha=10.0, beta=20.0),
    )

    adjusted = service._apply_profile_adjustments(hypothesis, ScenarioProfile.OPTIMISTIC)

    # Optimistic: α × 1.3, β × 0.7
    assert adjusted.parameters.alpha == pytest.approx(
        13.0
    ), "Optimistic should increase alpha by 1.3x"
    assert adjusted.parameters.beta == pytest.approx(
        14.0
    ), "Optimistic should decrease beta by 0.7x"


def test_apply_profile_adjustments_uniform_conservative():
    """GIVEN Uniform distribution hypothesis WHEN applying Conservative profile THEN shifts toward worse range."""
    service = HypothesisWizardService()

    hypothesis = Hypothesis(
        id="hyp_12345678",
        simulation_id="sim_12345678",
        variable_id="var_0",
        variable_name="test_var",
        distribution_type=DistributionType.UNIFORM,
        parameters=UniformParams(low=0.0, high=10.0),
    )

    adjusted = service._apply_profile_adjustments(
        hypothesis, ScenarioProfile.CONSERVATIVE
    )

    # Conservative: low - 0.2×range, high - 0.1×range
    # range = 10, so low - 2, high - 1
    assert adjusted.parameters.low == pytest.approx(
        -2.0
    ), "Conservative should decrease low by 0.2 * range"
    assert adjusted.parameters.high == pytest.approx(
        9.0
    ), "Conservative should decrease high by 0.1 * range"


def test_apply_profile_adjustments_uniform_optimistic():
    """GIVEN Uniform distribution hypothesis WHEN applying Optimistic profile THEN shifts toward better range."""
    service = HypothesisWizardService()

    hypothesis = Hypothesis(
        id="hyp_12345678",
        simulation_id="sim_12345678",
        variable_id="var_0",
        variable_name="test_var",
        distribution_type=DistributionType.UNIFORM,
        parameters=UniformParams(low=0.0, high=10.0),
    )

    adjusted = service._apply_profile_adjustments(hypothesis, ScenarioProfile.OPTIMISTIC)

    # Optimistic: low + 0.1×range, high + 0.2×range
    # range = 10, so low + 1, high + 2
    assert adjusted.parameters.low == pytest.approx(
        1.0
    ), "Optimistic should increase low by 0.1 * range"
    assert adjusted.parameters.high == pytest.approx(
        12.0
    ), "Optimistic should increase high by 0.2 * range"


def test_apply_profile_adjustments_lognormal_conservative():
    """GIVEN LogNormal distribution hypothesis WHEN applying Conservative profile THEN shifts toward worse outcomes."""
    service = HypothesisWizardService()

    hypothesis = Hypothesis(
        id="hyp_12345678",
        simulation_id="sim_12345678",
        variable_id="var_0",
        variable_name="test_var",
        distribution_type=DistributionType.LOGNORMAL,
        parameters=LogNormalParams(mean=1.0, sigma=0.5),
    )

    adjusted = service._apply_profile_adjustments(
        hypothesis, ScenarioProfile.CONSERVATIVE
    )

    # Conservative: μ - 0.3, σ × 1.4
    assert adjusted.parameters.mean == pytest.approx(
        0.7
    ), "Conservative should decrease mean by 0.3"
    assert adjusted.parameters.sigma == pytest.approx(
        0.7
    ), "Conservative should increase sigma by 1.4x"


def test_apply_profile_adjustments_lognormal_optimistic():
    """GIVEN LogNormal distribution hypothesis WHEN applying Optimistic profile THEN shifts toward better outcomes."""
    service = HypothesisWizardService()

    hypothesis = Hypothesis(
        id="hyp_12345678",
        simulation_id="sim_12345678",
        variable_id="var_0",
        variable_name="test_var",
        distribution_type=DistributionType.LOGNORMAL,
        parameters=LogNormalParams(mean=1.0, sigma=0.5),
    )

    adjusted = service._apply_profile_adjustments(hypothesis, ScenarioProfile.OPTIMISTIC)

    # Optimistic: μ + 0.3, σ × 0.8
    assert adjusted.parameters.mean == pytest.approx(
        1.3
    ), "Optimistic should increase mean by 0.3"
    assert adjusted.parameters.sigma == pytest.approx(
        0.4
    ), "Optimistic should decrease sigma by 0.8x"


def test_apply_profile_adjustments_bernoulli_conservative():
    """GIVEN Bernoulli distribution hypothesis WHEN applying Conservative profile THEN probability decreases."""
    service = HypothesisWizardService()

    hypothesis = Hypothesis(
        id="hyp_12345678",
        simulation_id="sim_12345678",
        variable_id="var_0",
        variable_name="test_var",
        distribution_type=DistributionType.BERNOULLI,
        parameters=BernoulliParams(p=0.7),
    )

    adjusted = service._apply_profile_adjustments(
        hypothesis, ScenarioProfile.CONSERVATIVE
    )

    # Conservative: p × 0.8
    assert adjusted.parameters.p == pytest.approx(
        0.56
    ), "Conservative should decrease p by 0.8x"


def test_apply_profile_adjustments_bernoulli_optimistic():
    """GIVEN Bernoulli distribution hypothesis WHEN applying Optimistic profile THEN probability increases."""
    service = HypothesisWizardService()

    hypothesis = Hypothesis(
        id="hyp_12345678",
        simulation_id="sim_12345678",
        variable_id="var_0",
        variable_name="test_var",
        distribution_type=DistributionType.BERNOULLI,
        parameters=BernoulliParams(p=0.7),
    )

    adjusted = service._apply_profile_adjustments(hypothesis, ScenarioProfile.OPTIMISTIC)

    # Optimistic: p × 1.2
    assert adjusted.parameters.p == pytest.approx(
        0.84
    ), "Optimistic should increase p by 1.2x"


def test_apply_profile_adjustments_bernoulli_optimistic_capped():
    """GIVEN Bernoulli with high p WHEN applying Optimistic profile THEN probability capped at 1.0."""
    service = HypothesisWizardService()

    hypothesis = Hypothesis(
        id="hyp_12345678",
        simulation_id="sim_12345678",
        variable_id="var_0",
        variable_name="test_var",
        distribution_type=DistributionType.BERNOULLI,
        parameters=BernoulliParams(p=0.9),
    )

    adjusted = service._apply_profile_adjustments(hypothesis, ScenarioProfile.OPTIMISTIC)

    # Optimistic: p × 1.2 = 1.08, capped at 1.0
    assert adjusted.parameters.p == pytest.approx(
        1.0
    ), "Optimistic should cap p at 1.0"


def test_apply_profile_adjustments_triangular_conservative():
    """GIVEN Triangular distribution hypothesis WHEN applying Conservative profile THEN shifts toward worse outcomes."""
    service = HypothesisWizardService()

    hypothesis = Hypothesis(
        id="hyp_12345678",
        simulation_id="sim_12345678",
        variable_id="var_0",
        variable_name="test_var",
        distribution_type=DistributionType.TRIANGULAR,
        parameters=TriangularParams(min_value=0.0, mode=5.0, max_value=10.0),
    )

    adjusted = service._apply_profile_adjustments(
        hypothesis, ScenarioProfile.CONSERVATIVE
    )

    # Conservative: min - 0.15×range, mode - 0.1×range, max - 0.1×range
    # range = 10, so min - 1.5, mode - 1, max - 1
    assert adjusted.parameters.min_value == pytest.approx(
        -1.5
    ), "Conservative should decrease min by 0.15 * range"
    assert adjusted.parameters.mode == pytest.approx(
        4.0
    ), "Conservative should decrease mode by 0.1 * range"
    assert adjusted.parameters.max_value == pytest.approx(
        9.0
    ), "Conservative should decrease max by 0.1 * range"


def test_apply_profile_adjustments_triangular_optimistic():
    """GIVEN Triangular distribution hypothesis WHEN applying Optimistic profile THEN shifts toward better outcomes."""
    service = HypothesisWizardService()

    hypothesis = Hypothesis(
        id="hyp_12345678",
        simulation_id="sim_12345678",
        variable_id="var_0",
        variable_name="test_var",
        distribution_type=DistributionType.TRIANGULAR,
        parameters=TriangularParams(min_value=0.0, mode=5.0, max_value=10.0),
    )

    adjusted = service._apply_profile_adjustments(hypothesis, ScenarioProfile.OPTIMISTIC)

    # Optimistic: min + 0.1×range, mode + 0.1×range, max + 0.15×range
    # range = 10, so min + 1, mode + 1, max + 1.5
    assert adjusted.parameters.min_value == pytest.approx(
        1.0
    ), "Optimistic should increase min by 0.1 * range"
    assert adjusted.parameters.mode == pytest.approx(
        6.0
    ), "Optimistic should increase mode by 0.1 * range"
    assert adjusted.parameters.max_value == pytest.approx(
        11.5
    ), "Optimistic should increase max by 0.15 * range"


# ==================== Tests for T016: init_wizard() ====================


def test_init_wizard_creates_and_adjusts_hypotheses():
    """GIVEN simulation and DAG WHEN calling init_wizard THEN hypotheses are generated, adjusted, persisted, and returned."""

    # Setup mocks
    mock_parametrizer = Mock()
    mock_repository = Mock()

    # Create baseline hypotheses that will be returned by parametrizer
    baseline_hypotheses = [
        Hypothesis(
            id="hyp_12345678",
            simulation_id="sim_12345678",
            variable_id="var_0",
            variable_name="Revenue",
            distribution_type=DistributionType.NORMAL,
            parameters=NormalParams(mean=100.0, std=10.0),
        ),
        Hypothesis(
            id="hyp_87654321",
            simulation_id="sim_12345678",
            variable_id="var_1",
            variable_name="Cost",
            distribution_type=DistributionType.UNIFORM,
            parameters=UniformParams(low=50.0, high=150.0),
        ),
    ]

    mock_parametrizer.quantify.return_value = baseline_hypotheses
    mock_repository.create_batch.return_value = baseline_hypotheses
    mock_repository.update_batch.return_value = baseline_hypotheses

    # Create service with mocked dependencies
    service = HypothesisWizardService()

    # Create a simple DAG
    dag = CausalDAG(
        id="dag_12345678",
        simulation_id="sim_12345678",
        nodes=[
            DAGVariable(
                id="var_0",
                name="Revenue",
                type=VariableType.OBSERVABLE,
                scope=VariableScope.WORLD,
                description="Monthly revenue",
                controllability=Controllability.NONE,
            ),
            DAGVariable(
                id="var_1",
                name="Cost",
                type=VariableType.OBSERVABLE,
                scope=VariableScope.WORLD,
                description="Operating cost",
                controllability=Controllability.MEDIUM,
            ),
        ],
        edges=[],
        assumptions=[],
        risks=[],
    )

    # Patch the dependencies
    with patch.object(service, '_parametrizer', mock_parametrizer):
        with patch.object(service, '_repository', mock_repository):
            # Call init_wizard with Conservative profile
            result = service.init_wizard(
                simulation_id="sim_12345678",
                dag=dag,
                scenario_profile=ScenarioProfile.CONSERVATIVE
            )

    # Verify parametrizer was called
    mock_parametrizer.quantify.assert_called_once_with("sim_12345678", dag)

    # Verify hypotheses were persisted (create_batch should be called)
    mock_repository.create_batch.assert_called_once()
    persisted_hypotheses = mock_repository.create_batch.call_args[0][0]

    # Verify adjustments were applied (Conservative profile should decrease mean)
    # Normal: mean should be 100 - 0.5*10 = 95
    assert persisted_hypotheses[0].parameters.mean == pytest.approx(95.0)
    # Normal: std should be 10 * 1.5 = 15
    assert persisted_hypotheses[0].parameters.std == pytest.approx(15.0)

    # Uniform: low should be 50 - 0.2*100 = 30, high should be 150 - 0.1*100 = 140
    # range = 150 - 50 = 100
    assert persisted_hypotheses[1].parameters.low == pytest.approx(30.0)
    assert persisted_hypotheses[1].parameters.high == pytest.approx(140.0)

    # Verify result contains hypotheses
    assert len(result["hypotheses"]) == 2

    # Verify result contains clarification_questions (empty for now)
    assert "clarification_questions" in result
    assert isinstance(result["clarification_questions"], list)


# ==================== Tests for T036-T042: Criticality Ranking & Question Generation ====================


def test_calculate_impact_score_outcome_variable():
    """
    Test T036: Calculate impact score for outcome variable.

    GIVEN outcome variable with controllability=NONE and out_degree=2
    WHEN calculating impact_score
    THEN score = 3.0 (outcome) + 2.0 (out_degree) = 5.0
    """
    service = HypothesisWizardService()

    variable = DAGVariable(
        id="var_outcome",
        name="Profit",
        type=VariableType.OBSERVABLE,
        scope=VariableScope.WORLD,
        description="Net profit",
        controllability=Controllability.NONE,
        is_outcome=True,
    )

    # Mock DAG with edges to calculate out_degree
    dag = CausalDAG(
        id="dag_12345678",
        simulation_id="sim_12345678",
        nodes=[variable],
        edges=[
            # 2 edges FROM outcome variable (out_degree=2)
            Edge(from_var="var_outcome", to_var="var_other1"),
            Edge(from_var="var_outcome", to_var="var_other2"),
        ],
        assumptions=[],
        risks=[],
    )

    impact_score = service._calculate_impact_score(variable, dag)

    # is_outcome=3.0, out_degree=2.0
    assert impact_score == pytest.approx(5.0)


def test_calculate_impact_score_high_controllability():
    """
    Test T036: Calculate impact score for high controllability variable.

    GIVEN variable with controllability=HIGH and out_degree=1
    WHEN calculating impact_score
    THEN score = 2.5 (high controllability) + 1.0 (out_degree) = 3.5
    """
    service = HypothesisWizardService()

    variable = DAGVariable(
        id="var_control",
        name="Price",
        type=VariableType.OBSERVABLE,
        scope=VariableScope.WORLD,
        description="Product price",
        controllability=Controllability.HIGH,
    )

    dag = CausalDAG(
        id="dag_12345678",
        simulation_id="sim_12345678",
        nodes=[variable],
        edges=[
            Edge(from_var="var_control", to_var="var_revenue"),
        ],
        assumptions=[],
        risks=[],
    )

    impact_score = service._calculate_impact_score(variable, dag)

    # controllability=HIGH gives 2.5, out_degree=1.0
    assert impact_score == pytest.approx(3.5)


def test_calculate_uncertainty_score_normal():
    """
    Test T037: Calculate uncertainty score for Normal distribution.

    GIVEN Normal distribution with mean=10, std=2
    WHEN calculating uncertainty_score
    THEN coefficient of variation = std/mean = 2/10 = 0.2
    """
    service = HypothesisWizardService()

    hypothesis = Hypothesis(
        id="hyp_12345678",
        simulation_id="sim_12345678",
        variable_id="var_0",
        variable_name="test_var",
        distribution_type=DistributionType.NORMAL,
        parameters=NormalParams(mean=10.0, std=2.0),
    )

    uncertainty_score = service._calculate_uncertainty_score(hypothesis)

    # Coefficient of variation: σ / μ = 2 / 10 = 0.2
    assert uncertainty_score == pytest.approx(0.2)


def test_calculate_uncertainty_score_beta():
    """
    Test T038: Calculate uncertainty score for Beta distribution.

    GIVEN Beta distribution with alpha=2, beta=5
    WHEN calculating uncertainty_score
    THEN standard deviation = sqrt(αβ / ((α+β)²(α+β+1)))
    """
    service = HypothesisWizardService()

    hypothesis = Hypothesis(
        id="hyp_12345678",
        simulation_id="sim_12345678",
        variable_id="var_0",
        variable_name="test_var",
        distribution_type=DistributionType.BETA,
        parameters=BetaParams(alpha=2.0, beta=5.0),
    )

    uncertainty_score = service._calculate_uncertainty_score(hypothesis)

    # sqrt(2*5 / ((2+5)^2 * (2+5+1))) = sqrt(10 / (49*8)) = sqrt(10/392) ≈ 0.1597
    import math
    expected = math.sqrt((2.0 * 5.0) / ((2.0 + 5.0) ** 2 * (2.0 + 5.0 + 1)))
    assert uncertainty_score == pytest.approx(expected)


def test_rank_critical_variables():
    """
    Test T039: Rank critical variables by criticality score.

    GIVEN DAG with 5 variables
    WHEN ranking by criticality (impact × uncertainty)
    THEN top 3-5 variables with highest scores are selected
    """
    service = HypothesisWizardService()

    # Create DAG with 5 variables
    dag = CausalDAG(
        id="dag_12345678",
        simulation_id="sim_12345678",
        nodes=[
            DAGVariable(
                id="var_outcome",
                name="Profit",
                type=VariableType.OBSERVABLE,
                scope=VariableScope.WORLD,
                description="Net profit",
                controllability=Controllability.NONE,
                is_outcome=True,
            ),
            DAGVariable(
                id="var_high_control",
                name="Price",
                type=VariableType.OBSERVABLE,
                scope=VariableScope.WORLD,
                description="Product price",
                controllability=Controllability.HIGH,
            ),
            DAGVariable(
                id="var_medium_control",
                name="Marketing",
                type=VariableType.OBSERVABLE,
                scope=VariableScope.WORLD,
                description="Marketing spend",
                controllability=Controllability.MEDIUM,
            ),
            DAGVariable(
                id="var_low_impact",
                name="Color",
                type=VariableType.OBSERVABLE,
                scope=VariableScope.WORLD,
                description="Product color",
                controllability=Controllability.NONE,
            ),
            DAGVariable(
                id="var_medium_impact",
                name="Quality",
                type=VariableType.OBSERVABLE,
                scope=VariableScope.WORLD,
                description="Product quality",
                controllability=Controllability.MEDIUM,
            ),
        ],
        edges=[
            Edge(from_var="var_high_control", to_var="var_outcome"),
            Edge(from_var="var_medium_control", to_var="var_outcome"),
            Edge(from_var="var_medium_impact", to_var="var_outcome"),
        ],
        assumptions=[],
        risks=[],
    )

    # Create hypotheses with varying uncertainty (CV >= 0.3 to pass filter)
    hypotheses = [
        Hypothesis(
            id="hyp_00000001",
            simulation_id="sim_12345678",
            variable_id="var_outcome",
            variable_name="Profit",
            distribution_type=DistributionType.NORMAL,
            parameters=NormalParams(mean=100.0, std=40.0),  # High uncertainty (CV=0.4)
        ),
        Hypothesis(
            id="hyp_00000002",
            simulation_id="sim_12345678",
            variable_id="var_high_control",
            variable_name="Price",
            distribution_type=DistributionType.NORMAL,
            parameters=NormalParams(mean=50.0, std=20.0),  # High uncertainty (CV=0.4)
        ),
        Hypothesis(
            id="hyp_00000003",
            simulation_id="sim_12345678",
            variable_id="var_medium_control",
            variable_name="Marketing",
            distribution_type=DistributionType.NORMAL,
            parameters=NormalParams(mean=1000.0, std=400.0),  # High uncertainty (CV=0.4)
        ),
        Hypothesis(
            id="hyp_00000004",
            simulation_id="sim_12345678",
            variable_id="var_low_impact",
            variable_name="Color",
            distribution_type=DistributionType.NORMAL,
            parameters=NormalParams(mean=5.0, std=1.0),  # Low uncertainty (CV=0.2, will be filtered)
        ),
        Hypothesis(
            id="hyp_00000005",
            simulation_id="sim_12345678",
            variable_id="var_medium_impact",
            variable_name="Quality",
            distribution_type=DistributionType.NORMAL,
            parameters=NormalParams(mean=8.0, std=3.0),  # Medium uncertainty (CV=0.375)
        ),
    ]

    critical_vars = service._rank_critical_variables(dag, hypotheses)

    # Should return 3-5 variables
    assert 3 <= len(critical_vars) <= 5

    # Outcome variable should be in top (high impact score)
    critical_var_ids = [v["variable_id"] for v in critical_vars]
    assert "var_outcome" in critical_var_ids

    # Each critical variable should have required fields
    for var_info in critical_vars:
        assert "variable_id" in var_info
        assert "variable_name" in var_info
        assert "criticality_score" in var_info
        assert var_info["criticality_score"] > 0


def test_generate_clarification_question_event():
    """
    Test T040: Generate clarification question for EVENT variable.

    GIVEN variable with type=EVENT
    WHEN generating clarification question
    THEN question asks about frequency
    """
    service = HypothesisWizardService()

    # Note: VariableType doesn't have EVENT, using OBSERVABLE as fallback
    # The actual implementation will need to check variable metadata or use different logic
    variable = DAGVariable(
        id="var_event",
        name="Customer Churn",
        type=VariableType.OBSERVABLE,
        scope=VariableScope.WORLD,
        description="Customers leaving",
        controllability=Controllability.NONE,
    )

    question = service._generate_clarification_question(variable)

    # Question should ask about frequency/magnitude
    assert "Customer Churn" in question
    assert len(question) > 10  # Non-trivial question


def test_generate_clarification_question_metric():
    """
    Test T041: Generate clarification question for METRIC variable.

    GIVEN variable with type=METRIC (using OBSERVABLE)
    WHEN generating clarification question
    THEN question asks about magnitude
    """
    service = HypothesisWizardService()

    variable = DAGVariable(
        id="var_metric",
        name="Revenue",
        type=VariableType.OBSERVABLE,
        scope=VariableScope.WORLD,
        description="Monthly revenue",
        controllability=Controllability.NONE,
    )

    question = service._generate_clarification_question(variable)

    # Question should mention the variable name
    assert "Revenue" in question
    assert len(question) > 10


def test_generate_clarification_question_rate():
    """
    Test T042: Generate clarification question for RATE variable.

    GIVEN variable with type=RATE (using OBSERVABLE)
    WHEN generating clarification question
    THEN question asks about magnitude
    """
    service = HypothesisWizardService()

    variable = DAGVariable(
        id="var_rate",
        name="Conversion Rate",
        type=VariableType.OBSERVABLE,
        scope=VariableScope.WORLD,
        description="Visitor to customer conversion",
        controllability=Controllability.NONE,
    )

    question = service._generate_clarification_question(variable)

    # Question should mention the variable name
    assert "Conversion Rate" in question
    assert len(question) > 10


def test_apply_response_adjustment_more_normal():
    """
    Test T043: Apply "more" response adjustment on Normal distribution.

    GIVEN hypothesis with Normal(μ=100, σ=20)
    WHEN applying "more" response
    THEN μ += 0.5σ (μ=110), σ ×= 0.8 (σ=16)
    """
    service = HypothesisWizardService()

    hypothesis = Hypothesis(
        id="hyp_12345678",
        simulation_id="sim_12345678",
        variable_id="var_revenue",
        variable_name="Revenue",
        distribution_type=DistributionType.NORMAL,
        parameters=NormalParams(mean=100.0, std=20.0),
    )

    adjusted = service._apply_response_adjustment(hypothesis, "more")

    # μ += 0.5σ = 100 + 10 = 110
    # σ ×= 0.8 = 20 × 0.8 = 16
    assert adjusted.parameters.mean == pytest.approx(110.0)
    assert adjusted.parameters.std == pytest.approx(16.0)


def test_apply_response_adjustment_less_beta():
    """
    Test T044: Apply "less" response adjustment on Beta distribution.

    GIVEN hypothesis with Beta(α=4, β=2)
    WHEN applying "less" response
    THEN α ×= 0.8 (α=3.2), β ×= 1.3 (β=2.6) - shift toward failure
    """
    service = HypothesisWizardService()

    hypothesis = Hypothesis(
        id="hyp_12345678",
        simulation_id="sim_12345678",
        variable_id="var_success",
        variable_name="Success Rate",
        distribution_type=DistributionType.BETA,
        parameters=BetaParams(alpha=4.0, beta=2.0),
    )

    adjusted = service._apply_response_adjustment(hypothesis, "less")

    # α ×= 0.8 = 4.0 × 0.8 = 3.2
    # β ×= 1.3 = 2.0 × 1.3 = 2.6
    assert adjusted.parameters.alpha == pytest.approx(3.2)
    assert adjusted.parameters.beta == pytest.approx(2.6)


def test_apply_response_adjustment_equal():
    """
    Test T045: Apply "equal" response (no adjustment).

    GIVEN hypothesis with Normal(μ=50, σ=10)
    WHEN applying "equal" response
    THEN parameters remain unchanged
    """
    service = HypothesisWizardService()

    hypothesis = Hypothesis(
        id="hyp_12345678",
        simulation_id="sim_12345678",
        variable_id="var_price",
        variable_name="Price",
        distribution_type=DistributionType.NORMAL,
        parameters=NormalParams(mean=50.0, std=10.0),
    )

    adjusted = service._apply_response_adjustment(hypothesis, "equal")

    # No change
    assert adjusted.parameters.mean == pytest.approx(50.0)
    assert adjusted.parameters.std == pytest.approx(10.0)


def test_apply_response_adjustment_dont_know():
    """
    Test T046: Apply "dont_know" response (increase variance).

    GIVEN hypothesis with Normal(μ=100, σ=20)
    WHEN applying "dont_know" response
    THEN μ unchanged (μ=100), σ ×= 1.5 (σ=30)
    """
    service = HypothesisWizardService()

    hypothesis = Hypothesis(
        id="hyp_12345678",
        simulation_id="sim_12345678",
        variable_id="var_cost",
        variable_name="Cost",
        distribution_type=DistributionType.NORMAL,
        parameters=NormalParams(mean=100.0, std=20.0),
    )

    adjusted = service._apply_response_adjustment(hypothesis, "dont_know")

    # μ unchanged = 100
    # σ ×= 1.5 = 20 × 1.5 = 30
    assert adjusted.parameters.mean == pytest.approx(100.0)
    assert adjusted.parameters.std == pytest.approx(30.0)


def test_apply_clarifications():
    """
    Test T047: Apply clarification responses to hypotheses.

    GIVEN simulation with 3 hypotheses
    WHEN applying 2 clarification responses
    THEN 2 hypotheses are updated with response adjustments
    """
    from unittest.mock import Mock

    service = HypothesisWizardService()

    # Mock repository to return hypotheses
    mock_repo = Mock()
    service._repository = mock_repo

    # Create hypotheses
    hypotheses = [
        Hypothesis(
            id="hyp_00000001",
            simulation_id="sim_12345678",
            variable_id="var_revenue",
            variable_name="Revenue",
            distribution_type=DistributionType.NORMAL,
            parameters=NormalParams(mean=100.0, std=20.0),
        ),
        Hypothesis(
            id="hyp_00000002",
            simulation_id="sim_12345678",
            variable_id="var_cost",
            variable_name="Cost",
            distribution_type=DistributionType.NORMAL,
            parameters=NormalParams(mean=50.0, std=10.0),
        ),
        Hypothesis(
            id="hyp_00000003",
            simulation_id="sim_12345678",
            variable_id="var_profit",
            variable_name="Profit",
            distribution_type=DistributionType.NORMAL,
            parameters=NormalParams(mean=50.0, std=15.0),
        ),
    ]

    mock_repo.get_by_simulation.return_value = hypotheses

    # Mock update_batch to return updated hypotheses
    def mock_update(updated_hyps):
        return updated_hyps

    mock_repo.update_batch.side_effect = mock_update

    # Apply clarifications
    clarifications = [
        {"variable_name": "Revenue", "response": "more"},
        {"variable_name": "Cost", "response": "less"},
    ]

    result = service.apply_clarifications("sim_12345678", clarifications)

    # Verify repository was called
    mock_repo.get_by_simulation.assert_called_once_with("sim_12345678")
    assert mock_repo.update_batch.called

    # Verify 2 hypotheses were updated
    updated = result["hypotheses"]
    assert len(updated) == 2

    # Verify Revenue was adjusted for "more"
    revenue_hyp = next(h for h in updated if h.variable_name == "Revenue")
    # μ += 0.5σ = 100 + 10 = 110, σ ×= 0.8 = 16
    assert revenue_hyp.parameters.mean == pytest.approx(110.0)
    assert revenue_hyp.parameters.std == pytest.approx(16.0)

    # Verify Cost was adjusted for "less"
    cost_hyp = next(h for h in updated if h.variable_name == "Cost")
    # μ -= 0.5σ = 50 - 5 = 45, σ ×= 0.8 = 8
    assert cost_hyp.parameters.mean == pytest.approx(45.0)
    assert cost_hyp.parameters.std == pytest.approx(8.0)


def test_apply_clarifications_empty_responses():
    """
    Test T049: Apply clarifications with empty responses (skip all).

    GIVEN simulation with hypotheses
    WHEN applying empty clarifications list
    THEN hypotheses are returned unchanged
    """
    from unittest.mock import Mock

    service = HypothesisWizardService()

    # Mock repository
    mock_repo = Mock()
    service._repository = mock_repo

    hypotheses = [
        Hypothesis(
            id="hyp_00000001",
            simulation_id="sim_12345678",
            variable_id="var_revenue",
            variable_name="Revenue",
            distribution_type=DistributionType.NORMAL,
            parameters=NormalParams(mean=100.0, std=20.0),
        ),
    ]

    mock_repo.get_by_simulation.return_value = hypotheses

    # Apply empty clarifications
    result = service.apply_clarifications("sim_12345678", [])

    # Verify repository was called
    mock_repo.get_by_simulation.assert_called_once_with("sim_12345678")

    # Verify no updates were made (update_batch not called)
    assert not mock_repo.update_batch.called

    # Verify original hypotheses returned
    assert result["hypotheses"] == hypotheses


def test_identify_high_uncertainty_variables():
    """
    Test T081: Identify variables with high uncertainty.

    GIVEN hypotheses with varying uncertainty scores
    WHEN identifying high uncertainty variables (threshold=0.5)
    THEN only variables with uncertainty >= 0.5 are returned
    """
    service = HypothesisWizardService()

    hypotheses = [
        Hypothesis(
            id="hyp_00000001",
            simulation_id="sim_12345678",
            variable_id="var_high",
            variable_name="HighUncertainty",
            distribution_type=DistributionType.NORMAL,
            parameters=NormalParams(mean=100.0, std=60.0),  # CV = 0.6
        ),
        Hypothesis(
            id="hyp_00000002",
            simulation_id="sim_12345678",
            variable_id="var_medium",
            variable_name="MediumUncertainty",
            distribution_type=DistributionType.NORMAL,
            parameters=NormalParams(mean=100.0, std=40.0),  # CV = 0.4 (below threshold)
        ),
        Hypothesis(
            id="hyp_00000003",
            simulation_id="sim_12345678",
            variable_id="var_low",
            variable_name="LowUncertainty",
            distribution_type=DistributionType.NORMAL,
            parameters=NormalParams(mean=100.0, std=10.0),  # CV = 0.1 (below threshold)
        ),
    ]

    high_uncertainty = service._identify_high_uncertainty_variables(
        hypotheses, threshold=0.5
    )

    # Only HighUncertainty should be returned (CV = 0.6 >= 0.5)
    assert len(high_uncertainty) == 1
    assert high_uncertainty[0]["variable_name"] == "HighUncertainty"
    assert high_uncertainty[0]["uncertainty_score"] == pytest.approx(0.6)
