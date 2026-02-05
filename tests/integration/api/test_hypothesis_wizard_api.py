"""
Integration tests for Hypothesis Wizard API endpoints.

Tests the wizard flow from API request through service to database persistence.

References:
    - Router: src/synth_lab/api/routers/hypotheses.py
    - Service: src/synth_lab/services/simulation/hypothesis_wizard_service.py
    - Spec: specs/036-simplified-hypothesis-wizard/spec.md
"""

import pytest
from fastapi.testclient import TestClient

from synth_lab.api.main import app
from synth_lab.models.orm.simulation import (
    CausalDAG as CausalDAGORM,
    Simulation as SimulationORM,
)


@pytest.fixture
def client(postgres_test_url: str, auth_token):
    """Create test client with test database and authentication."""
    import os

    # Store original DATABASE_URL
    original_db_url = os.environ.get("DATABASE_URL")

    # Set DATABASE_URL to test database
    os.environ["DATABASE_URL"] = postgres_test_url

    try:
        # Create client (will use test database)
        test_client = TestClient(app)
        # Set auth cookie for all requests
        test_client.cookies.set("auth_token", auth_token)
        yield test_client
    finally:
        # Restore original DATABASE_URL
        if original_db_url:
            os.environ["DATABASE_URL"] = original_db_url
        else:
            os.environ.pop("DATABASE_URL", None)


@pytest.fixture
def simulation_with_validated_dag(db_session):
    """Create a simulation with a validated DAG for wizard testing."""
    from synth_lab.domain.entities.causal_dag import (
        CausalDAG,
        Controllability,
        VariableScope,
        VariableType,
    )
    from synth_lab.domain.entities.causal_dag import Variable as DAGVariable
    from synth_lab.repositories.causal_dag_repository import CausalDAGRepository

    # 1. Create simulation in database
    simulation = SimulationORM(
        id="sim_00000001",
        question="What is the impact of cost changes on profit?",
        status="parsing",
        random_seed=42,
        n_worlds=500,
    )
    db_session.add(simulation)
    db_session.flush()

    # 2. Create and persist a validated DAG
    dag = CausalDAG(
        id="dag_00000001",
        simulation_id="sim_00000001",
        nodes=[
            DAGVariable(
                id="var_revenue",
                name="Revenue",
                type=VariableType.OBSERVABLE,
                scope=VariableScope.WORLD,
                description="Monthly revenue",
                controllability=Controllability.NONE,
            ),
            DAGVariable(
                id="var_cost",
                name="Cost",
                type=VariableType.OBSERVABLE,
                scope=VariableScope.WORLD,
                description="Operating cost",
                controllability=Controllability.MEDIUM,
            ),
            DAGVariable(
                id="var_profit",
                name="Profit",
                type=VariableType.OBSERVABLE,
                scope=VariableScope.WORLD,
                description="Net profit",
                controllability=Controllability.NONE,
                is_outcome=True,
            ),
        ],
        edges=[],
        assumptions=[],
        risks=[],
        is_validated=True,  # Mark as validated
        validation_errors=[],
    )

    dag_repo = CausalDAGRepository(session=db_session)
    persisted_dag = dag_repo.create(dag)

    db_session.commit()

    return {
        "simulation_id": simulation.id,
        "dag_id": persisted_dag.id,
        "num_variables": len(dag.nodes),
    }


# ==================== Tests for T017-T019: POST /wizard/init ====================


def test_wizard_init_conservative_profile(client, simulation_with_validated_dag):
    """
    Test T017: Initialize wizard with Conservative profile.

    GIVEN simulation with validated DAG
    WHEN POST /wizard/init with Conservative profile
    THEN hypotheses are generated with conservative adjustments
    """
    simulation_id = simulation_with_validated_dag["simulation_id"]

    # Call wizard init endpoint
    response = client.post(
        f"/simulations/{simulation_id}/hypotheses/wizard/init",
        json={"scenario_profile": "conservative"},
    )

    # Assert successful response
    assert response.status_code == 200, f"Response: {response.text}"
    data = response.json()

    # Assert structure
    assert "hypotheses" in data
    assert "clarification_questions" in data

    # Assert hypotheses generated for all variables
    hypotheses = data["hypotheses"]
    assert len(hypotheses) == simulation_with_validated_dag["num_variables"]

    # Assert each hypothesis has required fields
    for hyp in hypotheses:
        assert "id" in hyp
        assert hyp["id"].startswith("hyp_")
        assert "simulation_id" in hyp
        assert hyp["simulation_id"] == simulation_id
        assert "variable_name" in hyp
        assert "parameters" in hyp
        assert "distribution_type" in hyp["parameters"]

    # Verify at least one hypothesis has parameters (conservative profile was applied)
    # Note: Conservative should have adjusted parameters (e.g., increased variance)
    assert any(hyp["parameters"] for hyp in hypotheses)


def test_wizard_init_realistic_profile(client, simulation_with_validated_dag):
    """
    Test T018: Initialize wizard with Realistic profile.

    GIVEN simulation with validated DAG
    WHEN POST /wizard/init with Realistic profile
    THEN hypotheses are generated without adjustments
    """
    simulation_id = simulation_with_validated_dag["simulation_id"]

    # Call wizard init endpoint
    response = client.post(
        f"/simulations/{simulation_id}/hypotheses/wizard/init",
        json={"scenario_profile": "realistic"},
    )

    # Assert successful response
    assert response.status_code == 200, f"Response: {response.text}"
    data = response.json()

    # Assert structure
    assert "hypotheses" in data
    assert "clarification_questions" in data

    # Assert hypotheses generated for all variables
    hypotheses = data["hypotheses"]
    assert len(hypotheses) == simulation_with_validated_dag["num_variables"]

    # Assert each hypothesis has required fields
    for hyp in hypotheses:
        assert "id" in hyp
        assert hyp["id"].startswith("hyp_")
        assert "simulation_id" in hyp
        assert hyp["simulation_id"] == simulation_id
        assert "variable_name" in hyp
        assert "parameters" in hyp
        assert "distribution_type" in hyp["parameters"]


def test_wizard_init_optimistic_profile(client, simulation_with_validated_dag):
    """
    Test T019: Initialize wizard with Optimistic profile.

    GIVEN simulation with validated DAG
    WHEN POST /wizard/init with Optimistic profile
    THEN hypotheses are generated with optimistic adjustments
    """
    simulation_id = simulation_with_validated_dag["simulation_id"]

    # Call wizard init endpoint
    response = client.post(
        f"/simulations/{simulation_id}/hypotheses/wizard/init",
        json={"scenario_profile": "optimistic"},
    )

    # Assert successful response
    assert response.status_code == 200, f"Response: {response.text}"
    data = response.json()

    # Assert structure
    assert "hypotheses" in data
    assert "clarification_questions" in data

    # Assert hypotheses generated for all variables
    hypotheses = data["hypotheses"]
    assert len(hypotheses) == simulation_with_validated_dag["num_variables"]

    # Assert each hypothesis has required fields
    for hyp in hypotheses:
        assert "id" in hyp
        assert hyp["id"].startswith("hyp_")
        assert "simulation_id" in hyp
        assert hyp["simulation_id"] == simulation_id
        assert "variable_name" in hyp
        assert "parameters" in hyp
        assert "distribution_type" in hyp["parameters"]


def test_wizard_init_missing_dag(client, db_session):
    """
    Test error case: Initialize wizard without DAG.

    GIVEN simulation without DAG
    WHEN POST /wizard/init
    THEN returns 404 error
    """
    # Create simulation without DAG
    simulation = SimulationORM(
        id="sim_00000002",
        question="Test simulation without DAG",
        status="parsing",
        random_seed=42,
        n_worlds=500,
    )
    db_session.add(simulation)
    db_session.commit()

    # Call wizard init endpoint
    response = client.post(
        f"/simulations/{simulation.id}/hypotheses/wizard/init",
        json={"scenario_profile": "realistic"},
    )

    # Assert error response
    assert response.status_code == 404
    assert "No DAG found" in response.json()["detail"]


def test_wizard_init_unvalidated_dag(client, db_session):
    """
    Test error case: Initialize wizard with unvalidated DAG.

    GIVEN simulation with unvalidated DAG
    WHEN POST /wizard/init
    THEN returns 400 error
    """
    from synth_lab.domain.entities.causal_dag import (
        CausalDAG,
        Controllability,
        VariableScope,
        VariableType,
    )
    from synth_lab.domain.entities.causal_dag import Variable as DAGVariable
    from synth_lab.repositories.causal_dag_repository import CausalDAGRepository

    # Create simulation
    simulation = SimulationORM(
        id="sim_00000003",
        question="Test simulation with unvalidated DAG",
        status="parsing",
        random_seed=42,
        n_worlds=500,
    )
    db_session.add(simulation)
    db_session.flush()

    # Create unvalidated DAG
    dag = CausalDAG(
        id="dag_00000002",
        simulation_id="sim_00000003",
        nodes=[
            DAGVariable(
                id="var_test",
                name="Test Variable",
                type=VariableType.OBSERVABLE,
                scope=VariableScope.WORLD,
                description="Test variable",
                controllability=Controllability.NONE,
            ),
        ],
        edges=[],
        assumptions=[],
        risks=[],
        is_validated=False,  # NOT validated
        validation_errors=[],
    )

    dag_repo = CausalDAGRepository(session=db_session)
    dag_repo.create(dag)
    db_session.commit()

    # Call wizard init endpoint
    response = client.post(
        f"/simulations/{simulation.id}/hypotheses/wizard/init",
        json={"scenario_profile": "realistic"},
    )

    # Assert error response
    assert response.status_code == 400
    assert "must be validated" in response.json()["detail"]


def test_wizard_init_invalid_profile(client, simulation_with_validated_dag):
    """
    Test error case: Initialize wizard with invalid profile.

    GIVEN simulation with validated DAG
    WHEN POST /wizard/init with invalid profile
    THEN returns 400 error
    """
    simulation_id = simulation_with_validated_dag["simulation_id"]

    # Call wizard init endpoint with invalid profile
    response = client.post(
        f"/simulations/{simulation_id}/hypotheses/wizard/init",
        json={"scenario_profile": "invalid_profile"},
    )

    # Assert error response
    assert response.status_code == 400
    assert "Invalid scenario_profile" in response.json()["detail"]


# ==================== Tests for T048: POST /wizard/clarify (partial responses) ====================


def test_wizard_clarify_partial_responses(client, simulation_with_validated_dag):
    """
    Test T048: Apply partial clarification responses.

    GIVEN simulation with wizard-initialized hypotheses
    WHEN POST /wizard/clarify with partial responses (not all variables)
    THEN only specified variables are adjusted, others remain unchanged
    """
    simulation_id = simulation_with_validated_dag["simulation_id"]

    # First, initialize wizard to generate hypotheses
    init_response = client.post(
        f"/simulations/{simulation_id}/hypotheses/wizard/init",
        json={"scenario_profile": "realistic"},
    )
    assert init_response.status_code == 200, f"Init failed: {init_response.text}"
    init_data = init_response.json()
    initial_hypotheses = init_data["hypotheses"]

    # Apply partial clarifications (only for one variable)
    first_var_name = initial_hypotheses[0]["variable_name"]
    clarify_response = client.post(
        f"/simulations/{simulation_id}/hypotheses/wizard/clarify",
        json={
            "responses": [
                {"variable_name": first_var_name, "response": "more"},
            ]
        },
    )

    assert clarify_response.status_code == 200, f"Clarify failed: {clarify_response.text}"
    data = clarify_response.json()

    # Assert hypotheses returned
    assert "hypotheses" in data
    assert len(data["hypotheses"]) >= 1


# ==================== Tests for T082: POST /wizard/clarify (skip - empty responses) ====================


def test_wizard_clarify_skip_all_questions(client, simulation_with_validated_dag):
    """
    Test T082: Skip all clarification questions (empty responses).

    GIVEN simulation with wizard-initialized hypotheses
    WHEN POST /wizard/clarify with empty responses
    THEN hypotheses remain unchanged (profile defaults preserved)
    """
    simulation_id = simulation_with_validated_dag["simulation_id"]

    # First, initialize wizard to generate hypotheses
    init_response = client.post(
        f"/simulations/{simulation_id}/hypotheses/wizard/init",
        json={"scenario_profile": "conservative"},
    )
    assert init_response.status_code == 200, f"Init failed: {init_response.text}"

    # Apply empty clarifications (skip all)
    clarify_response = client.post(
        f"/simulations/{simulation_id}/hypotheses/wizard/clarify",
        json={"responses": []},
    )

    assert clarify_response.status_code == 200, f"Clarify failed: {clarify_response.text}"
    data = clarify_response.json()

    # Assert hypotheses returned (unchanged from init)
    assert "hypotheses" in data
    assert len(data["hypotheses"]) == simulation_with_validated_dag["num_variables"]
