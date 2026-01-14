#!/bin/bash
#
# Configuration file for Claude Code Test Hooks
#
# Este arquivo permite customizar o comportamento dos hooks
# sem precisar editar os próprios hooks.
#

# =============================================================================
# MINIMUM TEST COVERAGE REQUIREMENTS
# =============================================================================

# Cobertura mínima para novo código (%)
export MIN_COVERAGE_NEW_CODE=80

# Cobertura mínima para código crítico (auth, payment, etc) (%)
export MIN_COVERAGE_CRITICAL=100

# Cobertura mínima para componentes UI (%)
export MIN_COVERAGE_UI=80

# Cobertura mínima para utils/helpers (%)
export MIN_COVERAGE_UTILS=100

# =============================================================================
# TEST EXECUTION SETTINGS
# =============================================================================

# Timeout para testes unitários (segundos)
export UNIT_TEST_TIMEOUT=30

# Timeout para testes de integração (segundos)
export INTEGRATION_TEST_TIMEOUT=120

# Timeout para testes E2E (segundos)
export E2E_TEST_TIMEOUT=300

# =============================================================================
# HOOK BEHAVIOR
# =============================================================================

# Mostrar avisos detalhados? (true/false)
export VERBOSE_WARNINGS=true

# Incluir exemplos de comandos nos prompts? (true/false)
export SHOW_COMMAND_EXAMPLES=true

# Incluir checklist no output? (true/false)
export SHOW_CHECKLIST=true

# =============================================================================
# FILE PATTERNS
# =============================================================================

# Arquivos de código backend (regex)
export BACKEND_CODE_PATTERN="^src/synth_lab/.*\.py$"

# Arquivos de código frontend (regex)
export FRONTEND_CODE_PATTERN="^frontend/src/.*\.(ts|tsx|js|jsx)$"

# Arquivos de teste backend (regex)
export BACKEND_TEST_PATTERN="^tests/.*\.py$"

# Arquivos de teste frontend (regex)
export FRONTEND_TEST_PATTERN="^frontend/.*\.(test|spec)\.(ts|tsx|js|jsx)$"

# =============================================================================
# GIT SETTINGS
# =============================================================================

# Branch padrão para comparação em PRs
export DEFAULT_BASE_BRANCH="main"

# Branch alternativa se main não existir
export FALLBACK_BASE_BRANCH="master"

# =============================================================================
# TEST COMMANDS
# =============================================================================

# Comando para testes unitários backend
export BACKEND_UNIT_TEST_CMD="pytest tests/unit/ -v"

# Comando para testes de integração backend
export BACKEND_INTEGRATION_TEST_CMD="pytest tests/integration/ -v"

# Comando para coverage backend
export BACKEND_COVERAGE_CMD="pytest --cov=src/synth_lab --cov-report=term-missing"

# Comando para testes frontend
export FRONTEND_TEST_CMD="cd frontend && npm test"

# Comando para testes E2E
export E2E_TEST_CMD="cd frontend && npm run test:e2e"

# Comando para lint frontend
export FRONTEND_LINT_CMD="cd frontend && npm run lint"

# =============================================================================
# NOTIFICATION SETTINGS
# =============================================================================

# Mostrar emoji nos prompts? (true/false)
export USE_EMOJI=true

# Cor dos avisos (none/red/yellow/green/blue)
export WARNING_COLOR="yellow"

# =============================================================================
# CRITICAL PATHS
# =============================================================================

# Paths considerados críticos (exigem coverage 100%)
# Separados por espaço
export CRITICAL_PATHS=(
    "src/synth_lab/services/auth_service.py"
    "src/synth_lab/services/payment_service.py"
    "src/synth_lab/security/"
)

# =============================================================================
# EXEMPTIONS
# =============================================================================

# Arquivos que não precisam de testes
# Separados por espaço
export TEST_EXEMPT_FILES=(
    "src/synth_lab/__init__.py"
    "src/synth_lab/cli.py"
    "frontend/src/vite-env.d.ts"
    "frontend/src/main.tsx"
)

# Patterns de arquivos que não precisam de testes (regex)
export TEST_EXEMPT_PATTERNS=(
    ".*__init__\.py$"
    ".*migrations/.*\.py$"
    ".*\.config\.(ts|js)$"
)

# =============================================================================
# HOOK SPECIFIC SETTINGS
# =============================================================================

# Pre-commit: Bloquear commit se não há testes? (true/false)
export PRECOMMIT_BLOCK_WITHOUT_TESTS=false

# Pre-push: Bloquear push se testes falharem? (true/false)
export PREPUSH_BLOCK_ON_FAILURE=false

# Pull-request: Requerer coverage report? (true/false)
export PR_REQUIRE_COVERAGE_REPORT=true

# =============================================================================
# ADVANCED SETTINGS
# =============================================================================

# Executar testes automaticamente no pre-commit? (true/false)
# ATENÇÃO: Pode tornar commits lentos
export AUTORUN_TESTS_ON_COMMIT=false

# Executar lint automaticamente? (true/false)
export AUTORUN_LINT=false

# Gerar coverage report HTML automaticamente? (true/false)
export AUTO_GENERATE_COVERAGE_HTML=false

# =============================================================================
# INTEGRATION WITH CI/CD
# =============================================================================

# URL do CI/CD (para incluir nos prompts)
export CI_URL="https://github.com/fulvio/synth-lab/actions"

# Nome do check de CI (para mencionar nos prompts)
export CI_CHECK_NAME="Tests"

# =============================================================================
# CUSTOM MESSAGES
# =============================================================================

# Mensagem customizada para pre-commit
export CUSTOM_PRECOMMIT_MESSAGE=""

# Mensagem customizada para pre-push
export CUSTOM_PREPUSH_MESSAGE=""

# Mensagem customizada para pull-request
export CUSTOM_PR_MESSAGE=""

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

# Função para checar se arquivo é crítico
is_critical_file() {
    local file="$1"
    for pattern in "${CRITICAL_PATHS[@]}"; do
        if [[ "$file" == *"$pattern"* ]]; then
            return 0
        fi
    done
    return 1
}

# Função para checar se arquivo está isento de testes
is_test_exempt() {
    local file="$1"

    # Checa lista de arquivos exatos
    for exempt_file in "${TEST_EXEMPT_FILES[@]}"; do
        if [[ "$file" == "$exempt_file" ]]; then
            return 0
        fi
    done

    # Checa patterns
    for pattern in "${TEST_EXEMPT_PATTERNS[@]}"; do
        if [[ "$file" =~ $pattern ]]; then
            return 0
        fi
    done

    return 1
}

# Função para obter nível de coverage requerido
get_required_coverage() {
    local file="$1"

    if is_critical_file "$file"; then
        echo "$MIN_COVERAGE_CRITICAL"
    elif [[ "$file" == *"/components/"* ]] || [[ "$file" == *"/pages/"* ]]; then
        echo "$MIN_COVERAGE_UI"
    elif [[ "$file" == *"/utils/"* ]] || [[ "$file" == *"/helpers/"* ]]; then
        echo "$MIN_COVERAGE_UTILS"
    else
        echo "$MIN_COVERAGE_NEW_CODE"
    fi
}

# =============================================================================
# NOTES
# =============================================================================

# Para usar estas configurações nos hooks, adicione no início do hook:
#
#   if [ -f .claude/hooks/config.sh ]; then
#       source .claude/hooks/config.sh
#   fi
#
# Então você pode usar as variáveis:
#
#   if [ "$VERBOSE_WARNINGS" = "true" ]; then
#       echo "Detailed warning..."
#   fi
