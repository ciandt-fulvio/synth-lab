"""
Contract tests - Valida que API mantém schemas esperados pelo frontend.

Estes testes garantem que mudanças na API não quebram o frontend validando:
- Estrutura de resposta (campos obrigatórios presentes)
- Tipos de dados corretos
- Valores válidos em enums/constantes
- Estruturas aninhadas mantidas

Executar: pytest -m contract

IMPORTANTE: Estes NÃO testam lógica de negócio, apenas contrato da API.
Se endpoint retorna 404 porque não há dados, isso é OK - teste passa.
O que importa é que SE retornar dados, o schema esteja correto.

Note: Uses shared 'client' fixture from tests/contract/conftest.py
      which ensures tests run against DATABASE_TEST_URL.
"""

import sys
from typing import Any

import pytest
from fastapi.testclient import TestClient


def validate_timestamp(value: str) -> bool:
    """Valida que string é timestamp ISO 8601."""
    from datetime import datetime

    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except (ValueError, AttributeError):
        return False


@pytest.mark.contract
class TestExperimentContracts:
    """Valida contratos dos endpoints de experiments."""

    def test_list_experiments_returns_valid_schema(self, client: TestClient):
        """GET /experiments/list retorna schema de lista esperado pelo frontend."""
        response = client.get("/experiments/list")

        # Aceita 200 (com dados) ou 200 (vazio)
        assert response.status_code == 200, "Endpoint deve estar disponível"

        data = response.json()
        assert "data" in data, "Resposta deve ter campo 'data'"
        assert "pagination" in data, "Resposta deve ter campo 'pagination'"

        experiments = data["data"]
        assert isinstance(experiments, list), "data deve ser lista"

        # Se há experimentos, valida schema do primeiro
        if len(experiments) > 0:
            exp = experiments[0]

            # Campos obrigatórios que frontend SEMPRE espera (ExperimentSummary)
            required_fields = ["id", "name", "hypothesis", "created_at"]
            for field in required_fields:
                assert field in exp, (
                    f"Experiment deve ter campo '{field}'. Frontend quebra sem ele!"
                )

            # Tipos corretos
            assert isinstance(exp["id"], str), "id deve ser string"
            assert isinstance(exp["name"], str), "name deve ser string"
            assert isinstance(exp["hypothesis"], str), "hypothesis deve ser string"

            # Campos booleanos de estado
            bool_fields = ["has_scorecard", "has_analysis", "has_interview_guide"]
            for field in bool_fields:
                if field in exp:
                    assert isinstance(exp[field], bool), f"{field} deve ser bool"

            # Timestamp válido
            assert validate_timestamp(exp["created_at"]), "created_at deve ser ISO 8601"

        # Valida metadata de paginação
        pagination = data["pagination"]
        pagination_fields = ["total", "limit", "offset"]
        for field in pagination_fields:
            assert field in pagination, f"pagination.{field} esperado pelo frontend"
            assert isinstance(pagination[field], int), f"pagination.{field} deve ser int"

    def test_list_experiments_with_search_parameter(self, client: TestClient):
        """GET /experiments/list?search=query aceita parametro de busca."""
        # Testa que parametro search é aceito (mesmo sem resultados)
        response = client.get("/experiments/list?search=test")
        assert response.status_code == 200, "Endpoint deve aceitar parametro search"

        data = response.json()
        assert "data" in data, "Resposta deve ter campo 'data'"
        assert "pagination" in data, "Resposta deve ter campo 'pagination'"

    def test_list_experiments_with_sort_parameters(self, client: TestClient):
        """GET /experiments/list?sort_by=name&sort_order=asc aceita parametros de sort."""
        # Testa sort by name ascending
        response = client.get("/experiments/list?sort_by=name&sort_order=asc")
        assert response.status_code == 200, "Endpoint deve aceitar sort_by=name"

        # Testa sort by created_at descending (default)
        response = client.get("/experiments/list?sort_by=created_at&sort_order=desc")
        assert response.status_code == 200, "Endpoint deve aceitar sort_by=created_at"

        # Verifica que schema permanece o mesmo
        data = response.json()
        assert "data" in data
        assert "pagination" in data

    def test_list_experiments_rejects_invalid_sort_field(self, client: TestClient):
        """GET /experiments/list?sort_by=invalid deve rejeitar campo invalido."""
        response = client.get("/experiments/list?sort_by=invalid_field")
        # FastAPI valida via regex pattern, deve retornar 422
        assert response.status_code == 422, "Deve rejeitar sort_by invalido"

    def test_get_experiment_detail_returns_valid_schema(self, client: TestClient):
        """GET /experiments/:id retorna schema detalhado esperado."""
        # Tenta pegar um experimento existente
        list_response = client.get("/experiments/list")
        experiments = list_response.json().get("data", [])

        if len(experiments) == 0:
            pytest.skip("Nenhum experimento disponível para testar")

        exp_id = experiments[0]["id"]
        response = client.get(f"/experiments/{exp_id}")

        assert response.status_code == 200, "Experimento existente deve retornar 200"

        exp = response.json()

        # Campos obrigatórios em detalhes (ExperimentDetail extends ExperimentResponse)
        required_fields = ["id", "name", "hypothesis", "created_at"]
        for field in required_fields:
            assert field in exp, f"ExperimentDetail deve ter '{field}'"

        # scorecard_data pode ou não existir (opcional)
        if "scorecard_data" in exp and exp["scorecard_data"] is not None:
            scorecard = exp["scorecard_data"]

            # Campos obrigatórios do scorecard
            scorecard_fields = [
                "feature_name",
                "scenario",
                "description_text",
                "complexity",
                "initial_effort",
                "perceived_risk",
                "time_to_value",
            ]
            for field in scorecard_fields:
                assert field in scorecard, f"scorecard_data deve ter '{field}'"

            # Valida estrutura de dimension
            for dimension in [
                "complexity",
                "initial_effort",
                "perceived_risk",
                "time_to_value",
            ]:
                dim = scorecard[dimension]
                assert "score" in dim, f"{dimension} deve ter 'score'"
                assert isinstance(
                    dim["score"], (int, float)
                ), f"{dimension}.score deve ser número"
                assert 0.0 <= dim["score"] <= 1.0, (
                    f"{dimension}.score deve estar entre 0 e 1"
                )

    def test_get_experiment_synths_returns_valid_schema(self, client: TestClient):
        """GET /synth-groups/:id/synths retorna lista de synths (endpoint separado)."""
        # Synths são acessados via /synth-groups/{group_id}/synths, não via experiment
        # Este teste valida o endpoint de synths correto
        response = client.get("/synth-groups/list")

        # Se não há grupos, skip
        if response.status_code != 200:
            pytest.skip("Endpoint de synth-groups não disponível")

        data = response.json()
        groups = data.get("data", [])

        if len(groups) == 0:
            pytest.skip("Nenhum synth group disponível")

        group_id = groups[0]["id"]
        response = client.get(f"/synth-groups/{group_id}/synths")

        # Aceita 200 (com ou sem synths)
        if response.status_code == 404:
            pytest.skip("Synths endpoint não disponível para este grupo")

        assert response.status_code == 200

        synths = response.json()
        assert isinstance(synths, list), "Deve retornar lista de synths"

        # Se há synths, valida schema
        if len(synths) > 0:
            synth = synths[0]

            required_fields = ["id", "nome"]
            for field in required_fields:
                assert field in synth, f"Synth deve ter campo '{field}'"


@pytest.mark.contract
class TestAnalysisContracts:
    """Valida contratos dos endpoints de análise."""

    def test_get_analysis_summary_returns_valid_schema(self, client: TestClient):
        """GET /experiments/:id/analysis retorna summary esperado."""
        # Pega primeiro experimento
        list_response = client.get("/experiments/list")
        experiments = list_response.json().get("data", [])

        if len(experiments) == 0:
            pytest.skip("Nenhum experimento disponível")

        exp_id = experiments[0]["id"]
        response = client.get(f"/experiments/{exp_id}/analysis")

        # Pode retornar 404 se não há análise ainda - OK
        if response.status_code == 404:
            pytest.skip("Nenhuma análise disponível ainda")

        assert response.status_code == 200

        analysis = response.json()

        # Campos que frontend espera
        if "simulation_runs" in analysis:
            assert isinstance(
                analysis["simulation_runs"], list
            ), "simulation_runs deve ser lista"


@pytest.mark.contract
class TestExplorationContracts:
    """Valida contratos dos endpoints de exploration."""

    def test_get_exploration_returns_valid_schema(self, client: TestClient):
        """GET /experiments/:id/exploration retorna árvore esperada."""
        # Pega primeiro experimento
        list_response = client.get("/experiments/list")
        experiments = list_response.json().get("data", [])

        if len(experiments) == 0:
            pytest.skip("Nenhum experimento disponível")

        exp_id = experiments[0]["id"]
        response = client.get(f"/experiments/{exp_id}/exploration")

        # Pode não ter exploration ainda
        if response.status_code == 404:
            pytest.skip("Nenhuma exploration disponível")

        assert response.status_code == 200

        exploration = response.json()

        # Campos que frontend espera na árvore
        if "nodes" in exploration:
            assert isinstance(exploration["nodes"], list), "nodes deve ser lista"

            # Se tem nós, valida schema
            if len(exploration["nodes"]) > 0:
                node = exploration["nodes"][0]
                node_fields = ["id", "question", "status"]
                for field in node_fields:
                    assert field in node, f"Exploration node deve ter '{field}'"


@pytest.mark.contract
class TestResearchContracts:
    """Valida contratos dos endpoints de research."""

    def test_list_research_returns_valid_schema(self, client: TestClient):
        """GET /research/list retorna lista de pesquisas."""
        response = client.get("/research/list")

        assert response.status_code == 200

        data = response.json()
        assert "data" in data, "Resposta deve ter campo 'data'"
        assert "pagination" in data, "Resposta deve ter campo 'pagination'"

        research_list = data["data"]
        assert isinstance(research_list, list), "data deve ser lista"

        if len(research_list) > 0:
            research = research_list[0]

            # Campos obrigatórios de ResearchExecutionSummary
            required_fields = ["exec_id", "topic_name", "status"]
            for field in required_fields:
                assert field in research, f"Research deve ter campo '{field}'"


# Validation block para executar standalone
if __name__ == "__main__":
    import subprocess

    all_validation_failures = []

    print("=" * 60)
    print("CONTRACT TESTS - Validação de API Schemas")
    print("=" * 60)

    # Executa os contract tests
    result = subprocess.run(
        ["pytest", "-m", "contract", "-v", __file__],
        capture_output=True,
        text=True,
    )

    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    if result.returncode != 0:
        all_validation_failures.append("Contract tests falharam")

    # Final validation result
    if all_validation_failures:
        print("\n" + "=" * 60)
        print("❌ VALIDATION FAILED - Contract tests falharam")
        print("=" * 60)
        print("ATENÇÃO: API mudou schemas que frontend espera!")
        print("Verifique se mudanças são breaking changes.")
        sys.exit(1)
    else:
        print("\n" + "=" * 60)
        print("✅ VALIDATION PASSED - Contratos da API mantidos")
        print("=" * 60)
        print("API não quebrou contratos com frontend")
        sys.exit(0)
