"""
T019 [TEST] [BDD] Integration tests for Experiments API.

Tests based on BDD acceptance scenarios from spec.md:
- US2 Scenario 2: Create experiment with valid data
- US2 Scenario 3: Validation errors on create
- US1 Scenario 1: List experiments with counters
- US3 Scenario 1: Get experiment details with simulations and interviews

References:
    - Spec: specs/018-experiment-hub/spec.md
    - OpenAPI: specs/018-experiment-hub/contracts/openapi.yaml
"""

import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from synth_lab.api.main import app
from synth_lab.infrastructure.database import DatabaseManager, init_database


@pytest.fixture
def test_db(tmp_path):
    """Create a test database with schema."""
    db_path = tmp_path / "test.db"
    init_database(db_path)
    db = DatabaseManager(db_path)
    yield db
    db.close()


@pytest.fixture
def client(test_db, monkeypatch):
    """Create test client with test database."""
    import synth_lab.infrastructure.database as db_module

    # Reset global database instance to None
    monkeypatch.setattr(db_module, "_db", None)

    # Create a patched get_database that always returns test_db
    def get_test_database(db_path=None):
        return test_db

    monkeypatch.setattr(db_module, "get_database", get_test_database)

    # Also patch in repositories that import get_database directly
    import synth_lab.repositories.base as base_repo
    monkeypatch.setattr(base_repo, "get_database", get_test_database)

    # Patch in experiments router that imports get_database directly
    import synth_lab.api.routers.experiments as experiments_router
    monkeypatch.setattr(experiments_router, "get_database", get_test_database)

    return TestClient(app)


class TestCreateExperiment:
    """Tests for POST /experiments - US2 scenarios."""

    def test_create_experiment_with_valid_data(self, client) -> None:
        """
        US2 Scenario 2: Given formulário, When preenche nome e hipótese,
        Then experimento é criado.
        """
        response = client.post(
            "/experiments",
            json={
                "name": "Checkout Simplificado",
                "hypothesis": "Usuários completam mais compras com checkout de uma página",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["id"].startswith("exp_")
        assert data["name"] == "Checkout Simplificado"
        assert data["hypothesis"] == "Usuários completam mais compras com checkout de uma página"

    def test_create_experiment_with_description(self, client) -> None:
        """Verify experiment can be created with optional description."""
        response = client.post(
            "/experiments",
            json={
                "name": "Feature X",
                "hypothesis": "Hypothesis Y",
                "description": "Additional context and links",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["description"] == "Additional context and links"

    def test_create_experiment_without_name_returns_422(self, client) -> None:
        """
        US2 Scenario 3: Given formulário, When tenta salvar sem nome,
        Then mostra validação.
        """
        response = client.post(
            "/experiments",
            json={
                "hypothesis": "Valid hypothesis",
            },
        )

        assert response.status_code == 422

    def test_create_experiment_without_hypothesis_returns_422(self, client) -> None:
        """Verify hypothesis is required."""
        response = client.post(
            "/experiments",
            json={
                "name": "Valid name",
            },
        )

        assert response.status_code == 422

    def test_create_experiment_with_empty_name_returns_422(self, client) -> None:
        """Verify empty name is rejected."""
        response = client.post(
            "/experiments",
            json={
                "name": "",
                "hypothesis": "Valid hypothesis",
            },
        )

        assert response.status_code == 422

    def test_create_experiment_name_max_100_chars(self, client) -> None:
        """Verify name max length is enforced."""
        response = client.post(
            "/experiments",
            json={
                "name": "x" * 101,
                "hypothesis": "Valid hypothesis",
            },
        )

        assert response.status_code == 422


class TestListExperiments:
    """Tests for GET /experiments/list - US1 scenarios."""

    def test_list_experiments_includes_counters(self, client, test_db) -> None:
        """
        US1 Scenario 1: Given home + existem experimentos,
        Then vê lista com nome, hipótese, contadores, data.
        """
        # Create experiment
        response = client.post(
            "/experiments",
            json={
                "name": "Test Feature",
                "hypothesis": "Test hypothesis",
            },
        )
        exp_id = response.json()["id"]

        # Add analysis run
        test_db.execute(
            """
            INSERT INTO analysis_runs
            (id, experiment_id, config, status, started_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "ana_12345678",
                exp_id,
                '{"scenario": "baseline"}',
                "completed",
                datetime.now(timezone.utc).isoformat(),
            ),
        )

        # Add interview (research_execution)
        test_db.execute(
            """
            INSERT INTO research_executions
            (exec_id, experiment_id, topic_name, status, synth_count, started_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "exec_001",
                exp_id,
                "Test Topic",
                "completed",
                5,
                datetime.now(timezone.utc).isoformat(),
            ),
        )

        # List experiments
        response = client.get("/experiments/list")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["has_analysis"] is True
        assert data["data"][0]["interview_count"] == 1

    def test_list_experiments_empty_returns_empty_list(self, client) -> None:
        """Verify empty list is returned when no experiments exist."""
        response = client.get("/experiments/list")

        assert response.status_code == 200
        data = response.json()
        assert data["data"] == []
        assert data["pagination"]["total"] == 0

    def test_list_experiments_with_pagination(self, client) -> None:
        """Verify pagination parameters work."""
        # Create 5 experiments
        for i in range(5):
            client.post(
                "/experiments",
                json={
                    "name": f"Feature {i}",
                    "hypothesis": f"Hypothesis {i}",
                },
            )

        # Get first page
        response = client.get("/experiments/list?limit=3&offset=0")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 3
        assert data["pagination"]["total"] == 5
        assert data["pagination"]["has_next"] is True


class TestGetExperiment:
    """Tests for GET /experiments/{id} - US3 scenarios."""

    def test_get_experiment_includes_simulations_and_interviews(
        self, client, test_db
    ) -> None:
        """
        US3 Scenario 1: Given home + clica experimento,
        Then navega para /experiments/:id com detalhes completos.
        """
        # Create experiment
        response = client.post(
            "/experiments",
            json={
                "name": "Test Feature",
                "hypothesis": "Test hypothesis",
                "description": "Test description",
            },
        )
        exp_id = response.json()["id"]

        # Add analysis run
        test_db.execute(
            """
            INSERT INTO analysis_runs
            (id, experiment_id, config, status, started_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "ana_12345678",
                exp_id,
                '{"scenario": "baseline"}',
                "completed",
                datetime.now(timezone.utc).isoformat(),
            ),
        )

        # Add interview
        test_db.execute(
            """
            INSERT INTO research_executions
            (exec_id, experiment_id, topic_name, status, synth_count, started_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "exec_001",
                exp_id,
                "User Feedback",
                "completed",
                10,
                datetime.now(timezone.utc).isoformat(),
            ),
        )

        # Get experiment details
        response = client.get(f"/experiments/{exp_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == exp_id
        assert data["name"] == "Test Feature"
        assert data["description"] == "Test description"
        assert "analysis" in data or data.get("has_analysis") is not None
        assert "interviews" in data

    def test_get_experiment_not_found_returns_404(self, client) -> None:
        """Verify 404 for non-existent experiment."""
        response = client.get("/experiments/exp_nonexist")

        assert response.status_code == 404


class TestUpdateExperiment:
    """Tests for PUT /experiments/{id}."""

    def test_update_experiment_name(self, client) -> None:
        """Verify experiment name can be updated."""
        # Create experiment
        response = client.post(
            "/experiments",
            json={
                "name": "Original Name",
                "hypothesis": "Original hypothesis",
            },
        )
        exp_id = response.json()["id"]

        # Update name
        response = client.put(
            f"/experiments/{exp_id}",
            json={"name": "Updated Name"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["hypothesis"] == "Original hypothesis"

    def test_update_experiment_sets_updated_at(self, client) -> None:
        """Verify updated_at is set on update."""
        # Create experiment
        response = client.post(
            "/experiments",
            json={
                "name": "Test",
                "hypothesis": "Test hypothesis",
            },
        )
        exp_id = response.json()["id"]

        # Update
        response = client.put(
            f"/experiments/{exp_id}",
            json={"name": "Updated"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["updated_at"] is not None

    def test_update_nonexistent_experiment_returns_404(self, client) -> None:
        """Verify 404 for non-existent experiment."""
        response = client.put(
            "/experiments/exp_nonexist",
            json={"name": "Updated"},
        )

        assert response.status_code == 404


class TestExperimentScorecard:
    """Tests for scorecard functionality (now embedded in experiment)."""

    def test_experiment_has_scorecard_flag(self, client) -> None:
        """Verify experiment has has_scorecard flag."""
        # Create experiment
        response = client.post(
            "/experiments",
            json={
                "name": "Checkout Flow",
                "hypothesis": "Simplify checkout increases conversions",
            },
        )

        assert response.status_code == 201
        data = response.json()
        # New experiment should not have scorecard yet
        assert data["has_scorecard"] is False

    def test_update_experiment_with_scorecard(self, client) -> None:
        """Verify experiment can be updated with scorecard data via dedicated endpoint."""
        # Create experiment
        exp_response = client.post(
            "/experiments",
            json={
                "name": "Feature X",
                "hypothesis": "Hypothesis Y",
            },
        )
        exp_id = exp_response.json()["id"]

        # Update scorecard via dedicated endpoint
        response = client.put(
            f"/experiments/{exp_id}/scorecard",
            json={
                "feature_name": "Feature X",
                "scenario": "baseline",
                "description_text": "Description of the feature",
                "description_media_urls": [],
                "complexity": {"score": 0.3, "rules_applied": ["rule1"]},
                "initial_effort": {"score": 0.4, "rules_applied": []},
                "perceived_risk": {"score": 0.2, "rules_applied": []},
                "time_to_value": {"score": 0.8, "rules_applied": []},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["has_scorecard"] is True


class TestCreateInterviewFromExperiment:
    """Tests for POST /experiments/{id}/interviews - US5 scenarios."""

    def test_create_interview_nonexistent_experiment_returns_404(self, client) -> None:
        """Verify 404 for non-existent experiment."""
        response = client.post(
            "/experiments/exp_nonexist/interviews",
            json={
                "topic_name": "test-topic",
                "synth_count": 3,
            },
        )

        assert response.status_code == 404
