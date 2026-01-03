#!/usr/bin/env python3
"""
Analisa gaps de cobertura de testes.

Detecta:
- Routers sem contract tests
- ORM models sem schema tests
- Services sem integration tests
- Fluxos críticos sem E2E tests

Usage:
    python scripts/analyze_test_coverage.py
    python scripts/analyze_test_coverage.py --verbose
    python scripts/analyze_test_coverage.py --suggest-claude-prompts
"""

import argparse
import re
from pathlib import Path
from typing import List, Set


def find_routers() -> Set[str]:
    """Encontra todos os routers definidos."""
    routers = set()
    routers_dir = Path("src/synth_lab/api/routers")

    if not routers_dir.exists():
        return routers

    for file in routers_dir.glob("*.py"):
        if file.name == "__init__.py":
            continue
        routers.add(file.stem)

    return routers


def find_router_endpoints(router_file: Path) -> List[str]:
    """Extrai endpoints de um router."""
    endpoints = []

    if not router_file.exists():
        return endpoints

    content = router_file.read_text()

    # Busca por @router.get, @router.post, etc
    patterns = [
        r'@router\.get\(["\']([^"\']+)',
        r'@router\.post\(["\']([^"\']+)',
        r'@router\.put\(["\']([^"\']+)',
        r'@router\.delete\(["\']([^"\']+)',
        r'@router\.patch\(["\']([^"\']+)',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, content)
        endpoints.extend(matches)

    return endpoints


def find_contract_test_endpoints() -> Set[str]:
    """Encontra endpoints testados em contract tests."""
    tested_endpoints = set()
    contract_tests = Path("tests/contract")

    if not contract_tests.exists():
        return tested_endpoints

    for file in contract_tests.glob("*.py"):
        content = file.read_text()

        # Busca por client.get("/api/...", client.post, etc
        patterns = [
            r'client\.get\(["\']([^"\']+)',
            r'client\.post\(["\']([^"\']+)',
            r'client\.put\(["\']([^"\']+)',
            r'client\.delete\(["\']([^"\']+)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content)
            tested_endpoints.update(matches)

    return tested_endpoints


def find_orm_models() -> Set[str]:
    """Encontra todos os ORM models."""
    models = set()
    models_dir = Path("src/synth_lab/models/orm")

    if not models_dir.exists():
        return models

    for file in models_dir.glob("*.py"):
        if file.name in ["__init__.py", "base.py"]:
            continue

        content = file.read_text()

        # Busca por class X(Base):
        matches = re.findall(r"class (\w+)\(Base", content)
        models.update(matches)

    return models


def find_schema_test_tables() -> Set[str]:
    """Encontra tabelas testadas em schema tests."""
    tested_tables = set()
    schema_tests = Path("tests/schema")

    if not schema_tests.exists():
        return tested_tables

    for file in schema_tests.glob("*.py"):
        content = file.read_text()

        # Busca por get_columns("table_name")
        matches = re.findall(r'get_columns\(["\'](\w+)', content)
        tested_tables.update(matches)

    return tested_tables


def find_services() -> Set[str]:
    """Encontra todos os services."""
    services = set()
    services_dir = Path("src/synth_lab/services")

    if not services_dir.exists():
        return services

    for file in services_dir.rglob("*_service.py"):
        services.add(file.stem)

    return services


def find_integration_test_services() -> Set[str]:
    """Encontra services testados em integration tests."""
    tested_services = set()
    integration_dir = Path("tests/integration")

    if not integration_dir.exists():
        return tested_services

    for file in integration_dir.rglob("*.py"):
        content = file.read_text()

        # Busca por imports de services
        matches = re.findall(r"from synth_lab\.services\.\S+ import (\w+Service)", content)
        tested_services.update(matches)

    return tested_services


def analyze_coverage(verbose: bool = False) -> dict:
    """Analisa gaps de cobertura."""
    results = {
        "routers": {"total": 0, "tested": 0, "missing": []},
        "endpoints": {"total": 0, "tested": 0, "missing": []},
        "orm_models": {"total": 0, "tested": 0, "missing": []},
        "services": {"total": 0, "tested": 0, "missing": []},
    }

    # Analisa routers/endpoints
    all_routers = find_routers()
    results["routers"]["total"] = len(all_routers)

    all_endpoints = []
    for router in all_routers:
        router_file = Path(f"src/synth_lab/api/routers/{router}.py")
        endpoints = find_router_endpoints(router_file)
        all_endpoints.extend(endpoints)

    tested_endpoints = find_contract_test_endpoints()

    results["endpoints"]["total"] = len(all_endpoints)
    results["endpoints"]["tested"] = len(
        [e for e in all_endpoints if any(e in t for t in tested_endpoints)]
    )

    missing_endpoints = [e for e in all_endpoints if not any(e in t for t in tested_endpoints)]
    results["endpoints"]["missing"] = missing_endpoints

    # Analisa ORM models
    all_models = find_orm_models()
    tested_tables = find_schema_test_tables()

    results["orm_models"]["total"] = len(all_models)
    results["orm_models"]["tested"] = len(tested_tables)

    # Converte model names para table names (CamelCase → snake_case)
    def to_table_name(model: str) -> str:
        return re.sub(r"(?<!^)(?=[A-Z])", "_", model).lower()

    missing_models = [m for m in all_models if to_table_name(m) not in tested_tables]
    results["orm_models"]["missing"] = missing_models

    # Analisa services
    all_services = find_services()
    tested_services = find_integration_test_services()

    results["services"]["total"] = len(all_services)
    results["services"]["tested"] = len(tested_services)

    missing_services = [s for s in all_services if s not in tested_services]
    results["services"]["missing"] = missing_services

    return results


def print_results(results: dict, suggest_prompts: bool = False):
    """Imprime resultados da análise."""
    print("=" * 60)
    print("📊 ANÁLISE DE COBERTURA DE TESTES")
    print("=" * 60)
    print()

    # Endpoints
    endpoint_coverage = (
        (results["endpoints"]["tested"] / results["endpoints"]["total"] * 100)
        if results["endpoints"]["total"] > 0
        else 0
    )
    print(f"📡 Endpoints (Contract Tests)")
    print(
        f"   {results['endpoints']['tested']}/{results['endpoints']['total']} testados ({endpoint_coverage:.1f}%)"
    )

    if results["endpoints"]["missing"]:
        print(f"   ⚠️  {len(results['endpoints']['missing'])} endpoints sem contract tests:")
        for endpoint in results["endpoints"]["missing"][:5]:
            print(f"      - {endpoint}")
        if len(results["endpoints"]["missing"]) > 5:
            print(f"      ... e mais {len(results['endpoints']['missing']) - 5}")
    print()

    # ORM Models
    model_coverage = (
        (results["orm_models"]["tested"] / results["orm_models"]["total"] * 100)
        if results["orm_models"]["total"] > 0
        else 0
    )
    print(f"🗄️  ORM Models (Schema Tests)")
    print(
        f"   {results['orm_models']['tested']}/{results['orm_models']['total']} testados ({model_coverage:.1f}%)"
    )

    if results["orm_models"]["missing"]:
        print(f"   ⚠️  {len(results['orm_models']['missing'])} models sem schema tests:")
        for model in results["orm_models"]["missing"][:5]:
            print(f"      - {model}")
        if len(results["orm_models"]["missing"]) > 5:
            print(f"      ... e mais {len(results['orm_models']['missing']) - 5}")
    print()

    # Services
    service_coverage = (
        (results["services"]["tested"] / results["services"]["total"] * 100)
        if results["services"]["total"] > 0
        else 0
    )
    print(f"⚙️  Services (Integration Tests)")
    print(
        f"   {results['services']['tested']}/{results['services']['total']} testados ({service_coverage:.1f}%)"
    )

    if results["services"]["missing"]:
        print(f"   ⚠️  {len(results['services']['missing'])} services sem integration tests:")
        for service in results["services"]["missing"][:5]:
            print(f"      - {service}")
        if len(results["services"]["missing"]) > 5:
            print(f"      ... e mais {len(results['services']['missing']) - 5}")
    print()

    # Sugestões de prompts para Claude Code
    if suggest_prompts:
        print("=" * 60)
        print("💡 SUGESTÕES DE PROMPTS PARA CLAUDE CODE")
        print("=" * 60)
        print()

        if results["endpoints"]["missing"]:
            print("📝 Para Contract Tests:")
            print(f'   claude code --prompt "Criar contract tests para os endpoints: {", ".join(results["endpoints"]["missing"][:3])}"')
            print()

        if results["orm_models"]["missing"]:
            print("📝 Para Schema Tests:")
            print(
                f'   claude code --prompt "Adicionar validação de schema para os models: {", ".join(results["orm_models"]["missing"][:3])}"'
            )
            print()

        if results["services"]["missing"]:
            print("📝 Para Integration Tests:")
            print(
                f'   claude code --prompt "Criar integration tests para os services: {", ".join(results["services"]["missing"][:3])}"'
            )
            print()

    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analisa gaps de cobertura de testes")
    parser.add_argument("-v", "--verbose", action="store_true", help="Modo verbose")
    parser.add_argument(
        "-s",
        "--suggest-claude-prompts",
        action="store_true",
        help="Sugere prompts para Claude Code",
    )

    args = parser.parse_args()

    results = analyze_coverage(verbose=args.verbose)
    print_results(results, suggest_prompts=args.suggest_claude_prompts)
