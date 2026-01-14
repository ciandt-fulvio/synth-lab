#!/usr/bin/env python3
"""
Analisa gaps de cobertura de testes.

Detecta:
- Routers sem contract tests
- ORM models sem schema tests
- Services sem integration tests
- Fluxos críticos sem E2E tests

NOVO: Analisa commits específicos e sugere testes baseado nas mudanças.

Usage:
    # Análise geral do projeto
    python scripts/analyze_test_coverage.py
    python scripts/analyze_test_coverage.py --verbose
    python scripts/analyze_test_coverage.py --suggest-claude-prompts
    python scripts/analyze_test_coverage.py --check-goals  # Exit 0 if goals met, 1 otherwise

    # Análise de commit específico (NOVO)
    python scripts/analyze_test_coverage.py --commit HEAD
    python scripts/analyze_test_coverage.py --commit abc123
    python scripts/analyze_test_coverage.py --commit HEAD --show-templates
"""

import argparse
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Literal, Set

# Metas de cobertura de testes
COVERAGE_TARGETS = {
    "contract_tests": 0.80,  # 80% dos endpoints
    "schema_tests": 0.80,    # 80% dos models
    "integration_tests": 0.60  # 60% dos services
}


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


def check_coverage_goals(results: dict) -> tuple[bool, list[str], list[str]]:
    """
    Verifica se as metas de cobertura foram atingidas.

    Returns:
        Tuple de (goals_met: bool, goals_achieved: list[str], goals_missing: list[str])
    """
    endpoint_coverage = (
        (results["endpoints"]["tested"] / results["endpoints"]["total"])
        if results["endpoints"]["total"] > 0
        else 0
    )

    model_coverage = (
        (results["orm_models"]["tested"] / results["orm_models"]["total"])
        if results["orm_models"]["total"] > 0
        else 0
    )

    service_coverage = (
        (results["services"]["tested"] / results["services"]["total"])
        if results["services"]["total"] > 0
        else 0
    )

    current = {
        "contract_tests": endpoint_coverage,
        "schema_tests": model_coverage,
        "integration_tests": service_coverage
    }

    goals_achieved = []
    goals_missing = []

    for category, target in COVERAGE_TARGETS.items():
        actual = current[category]
        if actual >= target:
            goals_achieved.append(
                f"✅ {category}: {actual:.1%} (meta: {target:.1%})"
            )
        else:
            gap = target - actual
            goals_missing.append(
                f"⚠️  {category}: {actual:.1%} (faltam {gap:.1%} para atingir meta de {target:.1%})"
            )

    all_goals_met = len(goals_missing) == 0

    return all_goals_met, goals_achieved, goals_missing


def print_results(results: dict, suggest_prompts: bool = False, check_goals: bool = False):
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

    # Verificação de metas
    if check_goals:
        print("=" * 60)
        print("🎯 VERIFICAÇÃO DE METAS DE COBERTURA")
        print("=" * 60)
        print()

        all_goals_met, goals_achieved, goals_missing = check_coverage_goals(results)

        if goals_achieved:
            print("Metas atingidas:")
            for goal in goals_achieved:
                print(f"   {goal}")
            print()

        if goals_missing:
            print("Metas pendentes:")
            for goal in goals_missing:
                print(f"   {goal}")
            print()

        if all_goals_met:
            print("🎉 TODAS AS METAS DE COBERTURA FORAM ATINGIDAS!")
            print()
        else:
            print("⚠️  Algumas metas ainda não foram atingidas.")
            print(f"   Progresso: {len(goals_achieved)}/{len(COVERAGE_TARGETS)} categorias concluídas")
            print()

    print("=" * 60)


# ========================================
# COMMIT-BASED ANALYSIS (NEW)
# ========================================


@dataclass
class TestSuggestion:
    """Test suggestion based on code changes."""

    type: Literal["unit", "integration", "contract", "smoke", "e2e", "migration"]
    priority: Literal["OBRIGATÓRIO", "RECOMENDADO", "OPCIONAL"]
    file: str
    function: str | None = None
    reason: str = ""
    template: str | None = None


@dataclass
class CommitAnalysis:
    """Complete coverage analysis for a commit."""

    commit: str
    files_changed: list[str]
    tests_missing: list[TestSuggestion]
    coverage_status: Literal["COMPLETE", "INCOMPLETE", "UNKNOWN"]


def get_changed_files(commit: str = "HEAD") -> list[str]:
    """Get list of files changed in a commit."""
    try:
        result = subprocess.run(
            ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", commit],
            capture_output=True,
            text=True,
            check=True,
        )
        return [
            line.strip() for line in result.stdout.strip().split("\n") if line.strip()
        ]
    except subprocess.CalledProcessError as e:
        print(f"Error getting changed files: {e}", file=sys.stderr)
        return []


def analyze_router_changes(file_path: str) -> list[TestSuggestion]:
    """Analyze changes in API routers."""
    suggestions = []

    # Extract endpoint name from file path
    file_name = Path(file_path).stem
    endpoint = file_name.replace("_", "-")

    # Contract test is OBRIGATÓRIO
    suggestions.append(
        TestSuggestion(
            type="contract",
            priority="OBRIGATÓRIO",
            file="tests/contract/test_api_contracts.py",
            function=f"test_{file_name}_contract",
            reason=f"Endpoint público {endpoint} deve ter contract test",
            template=f'''def test_{file_name}_contract(client):
    """Valida schema da resposta de /{endpoint}."""
    response = client.get("/{endpoint}")

    assert response.status_code == 200
    body = response.json()

    # Campos obrigatórios (ajustar conforme schema real)
    assert "id" in body
    assert "name" in body
''',
        )
    )

    # E2E test is RECOMENDADO for public endpoints
    suggestions.append(
        TestSuggestion(
            type="e2e",
            priority="RECOMENDADO",
            file=f"frontend/tests/e2e/{file_name.replace('_', '-')}.spec.ts",
            function=f"test_{file_name}_user_flow",
            reason=f"Endpoint /{endpoint} pode ser usado por usuários",
            template=f'''test('{endpoint} user flow', async ({{ page }}) => {{
  // 1. Navega para página
  await page.goto('/');

  // 2. Interage com UI
  await page.click('text=Novo');

  // 3. Valida resultado
  await expect(page).toHaveURL(/{endpoint}/);
}});
''',
        )
    )

    return suggestions


def analyze_service_changes(file_path: str) -> list[TestSuggestion]:
    """Analyze changes in services."""
    suggestions = []

    file_name = Path(file_path).stem
    service_name = file_name.replace("_service", "")

    # Integration test is OBRIGATÓRIO
    suggestions.append(
        TestSuggestion(
            type="integration",
            priority="OBRIGATÓRIO",
            file=f"tests/integration/test_{service_name}_workflow.py",
            function=f"test_{service_name}_flow",
            reason=f"Serviço {service_name} precisa de teste de fluxo completo",
            template=f'''def test_{service_name}_flow(client, db_session):
    """Testa fluxo completo do serviço {service_name}."""
    # 1. Chama API
    response = client.post("/{service_name}", json={{"data": "value"}})
    resource_id = response.json()["id"]

    # 2. Valida no DB
    resource = db_session.query(Model).filter_by(id=resource_id).first()
    assert resource is not None
    assert resource.status == "expected"
''',
        )
    )

    return suggestions


def analyze_model_changes(file_path: str) -> list[TestSuggestion]:
    """Analyze changes in ORM models."""
    suggestions = []

    file_name = Path(file_path).stem

    # Migration is OBRIGATÓRIO
    suggestions.append(
        TestSuggestion(
            type="migration",
            priority="OBRIGATÓRIO",
            file="(criar via alembic)",
            function=None,
            reason=f"Model {file_name} mudou, precisa criar/atualizar migration",
            template=f'''# 1. Criar migration
DATABASE_URL="$DATABASE_TEST_URL" alembic revision --autogenerate -m "Update {file_name}"

# 2. Aplicar
DATABASE_URL="$DATABASE_TEST_URL" alembic upgrade head

# 3. Validar
pytest -m schema
''',
        )
    )

    return suggestions


def analyze_repository_changes(file_path: str) -> list[TestSuggestion]:
    """Analyze changes in repositories."""
    suggestions = []

    file_name = Path(file_path).stem
    repo_name = file_name.replace("_repository", "")

    # Integration test is OBRIGATÓRIO
    suggestions.append(
        TestSuggestion(
            type="integration",
            priority="OBRIGATÓRIO",
            file=f"tests/integration/test_{repo_name}_repository.py",
            function=f"test_{repo_name}_repository_queries",
            reason=f"Repository {repo_name} precisa validar queries SQL",
            template=f'''def test_{repo_name}_repository_queries(db_session):
    """Valida queries do repository {repo_name}."""
    repo = {repo_name.title()}Repository(db_session)

    # Teste de criação
    entity = repo.create(name="Test", data={{}})
    assert entity.id is not None

    # Teste de busca
    found = repo.get_by_id(entity.id)
    assert found is not None
    assert found.name == "Test"
''',
        )
    )

    return suggestions


def analyze_frontend_changes(file_path: str) -> list[TestSuggestion]:
    """Analyze changes in frontend."""
    suggestions = []

    # E2E test for pages
    if "frontend/src/pages" in file_path:
        page_name = Path(file_path).stem
        suggestions.append(
            TestSuggestion(
                type="e2e",
                priority="RECOMENDADO",
                file=f"frontend/tests/e2e/{page_name}.spec.ts",
                function=f"test_{page_name}_page",
                reason=f"Página {page_name} deve ter teste E2E",
                template=f'''test('{page_name} page', async ({{ page }}) => {{
  // 1. Navega para página
  await page.goto('/{page_name}');

  // 2. Valida que carregou
  await expect(page).toHaveTitle(/{page_name}/i);

  // 3. Testa interações principais
  // TODO: adicionar interações específicas
}});
''',
            )
        )

    return suggestions


def analyze_commit_changes(commit: str = "HEAD") -> CommitAnalysis:
    """Analyze changes in a commit and suggest tests."""
    changed_files = get_changed_files(commit)

    if not changed_files:
        return CommitAnalysis(
            commit=commit,
            files_changed=[],
            tests_missing=[],
            coverage_status="UNKNOWN",
        )

    all_suggestions: list[TestSuggestion] = []

    for file_path in changed_files:
        # Skip test files themselves
        if "/tests/" in file_path or ".spec." in file_path or ".test." in file_path:
            continue

        # Analyze based on file type
        if "api/routers" in file_path and file_path.endswith(".py"):
            all_suggestions.extend(analyze_router_changes(file_path))

        elif "services/" in file_path and file_path.endswith(".py"):
            all_suggestions.extend(analyze_service_changes(file_path))

        elif "models/orm" in file_path and file_path.endswith(".py"):
            all_suggestions.extend(analyze_model_changes(file_path))

        elif "repositories/" in file_path and file_path.endswith(".py"):
            all_suggestions.extend(analyze_repository_changes(file_path))

        elif "frontend/src/" in file_path:
            all_suggestions.extend(analyze_frontend_changes(file_path))

    # Determine coverage status
    has_obrigatorio = any(s.priority == "OBRIGATÓRIO" for s in all_suggestions)
    coverage_status = "INCOMPLETE" if has_obrigatorio else "COMPLETE"

    return CommitAnalysis(
        commit=commit,
        files_changed=changed_files,
        tests_missing=all_suggestions,
        coverage_status=coverage_status,
    )


def print_commit_analysis(analysis: CommitAnalysis, show_templates: bool = False) -> None:
    """Print commit coverage analysis to console."""
    print("\n📊 Análise de Cobertura de Testes (Commit)")
    print("━" * 60)
    print(f"Commit: {analysis.commit}")
    print(f"Arquivos modificados: {len(analysis.files_changed)}")
    print()

    if not analysis.tests_missing:
        print("✅ Nenhum teste adicional necessário para este commit")
        return

    # Group by priority
    obrigatorio = [s for s in analysis.tests_missing if s.priority == "OBRIGATÓRIO"]
    recomendado = [s for s in analysis.tests_missing if s.priority == "RECOMENDADO"]
    opcional = [s for s in analysis.tests_missing if s.priority == "OPCIONAL"]

    if obrigatorio:
        print("🔴 OBRIGATÓRIO ({})".format(len(obrigatorio)))
        for suggestion in obrigatorio:
            print(
                f"   ├─ {suggestion.type.upper()} Test: {suggestion.function or '(ver template)'}"
            )
            print(f"   │  Arquivo: {suggestion.file}")
            print(f"   │  Razão: {suggestion.reason}")
            if show_templates and suggestion.template:
                print("   │  Template:")
                for line in suggestion.template.split("\n"):
                    print(f"   │    {line}")
            print("   │")
        print()

    if recomendado:
        print("🟡 RECOMENDADO ({})".format(len(recomendado)))
        for suggestion in recomendado:
            print(
                f"   ├─ {suggestion.type.upper()} Test: {suggestion.function or '(ver template)'}"
            )
            print(f"   │  Arquivo: {suggestion.file}")
            print(f"   │  Razão: {suggestion.reason}")
            if show_templates and suggestion.template:
                print("   │  Template:")
                for line in suggestion.template.split("\n"):
                    print(f"   │    {line}")
            print("   │")
        print()

    if opcional:
        print("⚪ OPCIONAL ({})".format(len(opcional)))
        for suggestion in opcional:
            print(
                f"   └─ {suggestion.type.upper()} Test: {suggestion.function or '(ver template)'}"
            )
        print()

    print("💡 Próximos passos:")
    if obrigatorio:
        print("   1. Criar testes OBRIGATÓRIOS antes do push")
    if recomendado:
        print("   2. Considerar testes RECOMENDADOS para cobertura completa")
    if show_templates:
        print("   3. Copiar templates acima e ajustar conforme necessário")
    else:
        print("   3. Executar novamente com --show-templates para ver exemplos")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analisa gaps de cobertura de testes")
    parser.add_argument("-v", "--verbose", action="store_true", help="Modo verbose")
    parser.add_argument(
        "-s",
        "--suggest-claude-prompts",
        action="store_true",
        help="Sugere prompts para Claude Code",
    )
    parser.add_argument(
        "--check-goals",
        action="store_true",
        help="Verifica se metas de cobertura foram atingidas (exit 0 se sim, 1 se não)",
    )
    # NEW: Commit-based analysis
    parser.add_argument(
        "--commit",
        type=str,
        help="Analisa um commit específico (ex: HEAD, abc123)",
    )
    parser.add_argument(
        "--show-templates",
        action="store_true",
        help="Mostra templates de testes nas sugestões",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output em formato JSON",
    )

    args = parser.parse_args()

    # NEW: Commit-based analysis mode
    if args.commit:
        analysis = analyze_commit_changes(args.commit)

        if args.json:
            # Convert to dict and handle dataclasses
            output = {
                "commit": analysis.commit,
                "files_changed": analysis.files_changed,
                "tests_missing": [asdict(s) for s in analysis.tests_missing],
                "coverage_status": analysis.coverage_status,
            }
            print(json.dumps(output, indent=2))
        else:
            print_commit_analysis(analysis, show_templates=args.show_templates)

        # Exit with error if OBRIGATÓRIO tests missing
        has_obrigatorio = any(
            s.priority == "OBRIGATÓRIO" for s in analysis.tests_missing
        )
        sys.exit(1 if has_obrigatorio else 0)

    # Original: Project-wide analysis mode
    else:
        results = analyze_coverage(verbose=args.verbose)
        print_results(
            results,
            suggest_prompts=args.suggest_claude_prompts,
            check_goals=args.check_goals,
        )

        # Exit code based on goals check
        if args.check_goals:
            all_goals_met, _, _ = check_coverage_goals(results)
            sys.exit(0 if all_goals_met else 1)
