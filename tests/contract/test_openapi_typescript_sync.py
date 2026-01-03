"""
Contract test: Valida que tipos TypeScript do frontend batem com OpenAPI do backend.

Este teste NÃO usa LLM - compara schemas JSON diretamente.

Executar: pytest tests/contract/test_openapi_typescript_sync.py -v

Requer: Backend rodando em localhost:8000
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest
import requests


def get_openapi_schema() -> dict:
    """Fetch OpenAPI schema from running backend."""
    try:
        response = requests.get("http://localhost:8000/openapi.json", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        pytest.skip("Backend not running at localhost:8000")


def extract_schema_fields(schema: dict, schema_name: str) -> set[str]:
    """Extract field names from an OpenAPI component schema."""
    components = schema.get("components", {}).get("schemas", {})
    if schema_name not in components:
        return set()

    properties = components[schema_name].get("properties", {})
    return set(properties.keys())


def parse_typescript_interface(file_path: Path, interface_name: str) -> set[str]:
    """Extract field names from a TypeScript interface (simple parser)."""
    if not file_path.exists():
        return set()

    content = file_path.read_text()
    fields = set()

    # Find interface block
    import re
    pattern = rf"export interface {interface_name}\s*\{{"
    match = re.search(pattern, content)
    if not match:
        return set()

    # Extract fields until closing brace
    start = match.end()
    brace_count = 1
    i = start

    while i < len(content) and brace_count > 0:
        if content[i] == '{':
            brace_count += 1
        elif content[i] == '}':
            brace_count -= 1
        i += 1

    interface_body = content[start:i-1]

    # Parse field names (handles optional ? and type annotations)
    field_pattern = r"^\s*(\w+)\??\s*:"
    for line in interface_body.split('\n'):
        field_match = re.match(field_pattern, line)
        if field_match:
            fields.add(field_match.group(1))

    return fields


@pytest.mark.contract
class TestOpenAPITypeScriptSync:
    """Valida sincronização entre OpenAPI (backend) e TypeScript (frontend)."""

    def test_experiment_summary_fields_match(self):
        """ExperimentSummary: campos do TypeScript devem existir no OpenAPI."""
        openapi = get_openapi_schema()

        # Backend schema
        backend_fields = extract_schema_fields(openapi, "ExperimentSummary")

        # Frontend types
        frontend_path = Path("frontend/src/types/experiment.ts")
        frontend_fields = parse_typescript_interface(frontend_path, "ExperimentSummary")

        if not backend_fields:
            pytest.skip("ExperimentSummary not found in OpenAPI")
        if not frontend_fields:
            pytest.skip("ExperimentSummary not found in TypeScript")

        # Frontend fields should be subset of backend (backend can have more)
        missing_in_backend = frontend_fields - backend_fields

        assert not missing_in_backend, (
            f"Frontend ExperimentSummary has fields not in backend: {missing_in_backend}\n"
            f"Backend fields: {backend_fields}\n"
            f"Frontend fields: {frontend_fields}"
        )

    def test_experiment_detail_fields_match(self):
        """ExperimentDetail: campos do TypeScript devem existir no OpenAPI."""
        openapi = get_openapi_schema()

        backend_fields = extract_schema_fields(openapi, "ExperimentDetail")

        frontend_path = Path("frontend/src/types/experiment.ts")
        frontend_fields = parse_typescript_interface(frontend_path, "ExperimentDetail")

        if not backend_fields:
            pytest.skip("ExperimentDetail not found in OpenAPI")
        if not frontend_fields:
            pytest.skip("ExperimentDetail not found in TypeScript")

        missing_in_backend = frontend_fields - backend_fields

        assert not missing_in_backend, (
            f"Frontend ExperimentDetail has fields not in backend: {missing_in_backend}"
        )

    def test_research_execution_summary_fields_match(self):
        """ResearchExecutionSummary: campos devem bater."""
        openapi = get_openapi_schema()

        backend_fields = extract_schema_fields(openapi, "ResearchExecutionSummary")

        frontend_path = Path("frontend/src/types/research.ts")
        frontend_fields = parse_typescript_interface(frontend_path, "ResearchExecutionSummary")

        if not backend_fields:
            pytest.skip("ResearchExecutionSummary not found in OpenAPI")
        if not frontend_fields:
            pytest.skip("ResearchExecutionSummary not found in TypeScript")

        missing_in_backend = frontend_fields - backend_fields

        assert not missing_in_backend, (
            f"Frontend ResearchExecutionSummary has fields not in backend: {missing_in_backend}"
        )

    def test_pagination_meta_fields_match(self):
        """PaginationMeta: estrutura de paginação deve bater."""
        openapi = get_openapi_schema()

        backend_fields = extract_schema_fields(openapi, "PaginationMeta")

        frontend_path = Path("frontend/src/types/common.ts")
        frontend_fields = parse_typescript_interface(frontend_path, "PaginationMeta")

        if not backend_fields:
            pytest.skip("PaginationMeta not found in OpenAPI")
        if not frontend_fields:
            pytest.skip("PaginationMeta not found in TypeScript")

        missing_in_backend = frontend_fields - backend_fields

        assert not missing_in_backend, (
            f"Frontend PaginationMeta has fields not in backend: {missing_in_backend}"
        )

    def test_all_frontend_endpoints_exist_in_openapi(self):
        """Valida que todos os endpoints usados pelo frontend existem no OpenAPI."""
        openapi = get_openapi_schema()
        paths = set(openapi.get("paths", {}).keys())

        # Endpoints que o frontend usa (extraídos dos services)
        frontend_endpoints = [
            "/experiments/list",
            "/experiments/{experiment_id}",
            "/research/list",
            "/research/{exec_id}",
            "/research/{exec_id}/transcripts",
            "/synth-groups/list",
        ]

        for endpoint in frontend_endpoints:
            # Normalize path params
            normalized = endpoint.replace("{experiment_id}", "{id}").replace("{exec_id}", "{id}")

            # Check if endpoint exists (with any path param name)
            found = any(
                self._paths_match(endpoint, api_path)
                for api_path in paths
            )

            assert found, (
                f"Frontend uses endpoint '{endpoint}' but it's not in OpenAPI.\n"
                f"Available paths: {sorted(paths)}"
            )

    def _paths_match(self, frontend_path: str, api_path: str) -> bool:
        """Check if paths match, ignoring path parameter names."""
        import re
        # Replace {anything} with a placeholder
        frontend_normalized = re.sub(r'\{[^}]+\}', '{PARAM}', frontend_path)
        api_normalized = re.sub(r'\{[^}]+\}', '{PARAM}', api_path)
        return frontend_normalized == api_normalized


# Standalone validation
if __name__ == "__main__":
    print("=" * 60)
    print("OPENAPI vs TYPESCRIPT SYNC CHECK")
    print("=" * 60)

    result = subprocess.run(
        ["pytest", "-v", __file__],
        capture_output=False,
    )

    sys.exit(result.returncode)
