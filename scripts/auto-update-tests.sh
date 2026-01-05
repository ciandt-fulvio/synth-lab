#!/bin/bash
#
# Auto-atualiza testes usando Claude Code
# Detecta mudanças, gera prompts, roda Claude Code, valida
#
# Uso:
#   ./scripts/auto-update-tests.sh                    # Analisa staged files
#   ./scripts/auto-update-tests.sh --last-commit      # Analisa último commit
#   ./scripts/auto-update-tests.sh --file router.py   # Arquivo específico
#

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Flags
DRY_RUN=false
AUTO_COMMIT=false
LAST_COMMIT=false
SPECIFIC_FILE=""

# Parse argumentos
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --auto-commit)
            AUTO_COMMIT=true
            shift
            ;;
        --last-commit)
            LAST_COMMIT=true
            shift
            ;;
        --file)
            SPECIFIC_FILE="$2"
            shift 2
            ;;
        *)
            echo "Opção desconhecida: $1"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}🤖 Auto-Update Tests com Claude Code${NC}"
echo ""

# Detecta arquivos modificados
if [ -n "$SPECIFIC_FILE" ]; then
    CHANGED_FILES="$SPECIFIC_FILE"
elif [ "$LAST_COMMIT" = true ]; then
    CHANGED_FILES=$(git diff --name-only HEAD~1 HEAD)
else
    CHANGED_FILES=$(git diff --cached --name-only --diff-filter=ACM)
fi

if [ -z "$CHANGED_FILES" ]; then
    echo "Nenhum arquivo modificado encontrado."
    exit 0
fi

echo "Arquivos modificados:"
echo "$CHANGED_FILES" | sed 's/^/  - /'
echo ""

# Arrays para armazenar prompts
declare -a PROMPTS
declare -a PROMPT_TYPES

# Analisa routers modificados
ROUTERS=$(echo "$CHANGED_FILES" | grep "src/synth_lab/api/routers/.*\.py" || true)
if [ -n "$ROUTERS" ]; then
    echo -e "${YELLOW}📡 Routers modificados detectados${NC}"

    for router_file in $ROUTERS; do
        router_name=$(basename "$router_file" .py)

        # Extrai endpoints do router
        endpoints=$(grep -E '@router\.(get|post|put|delete|patch)\(' "$router_file" | \
                    sed -E 's/.*@router\.(get|post|put|delete|patch)\(["\']([^"\']+).*/\2/' | \
                    head -5)

        if [ -n "$endpoints" ]; then
            prompt="Atualizar tests para cobrir o router '$router_name'.

Endpoints encontrados:
$(echo "$endpoints" | sed 's/^/- /')

Para cada endpoint, crie/atualize contract test que valide:
- Status code esperado (200, 201, 404, etc)
- Estrutura de resposta (campos obrigatórios)
- Tipos de dados corretos
- Valores válidos para enums/constantes

Use o padrão existente em test_api_contracts.py como referência.
Adicione os testes na classe apropriada ou crie nova classe se necessário."

            PROMPTS+=("$prompt")
            PROMPT_TYPES+=("contract")
        fi
    done
fi

# Analisa ORM models modificados
MODELS=$(echo "$CHANGED_FILES" | grep "src/synth_lab/models/orm/.*\.py" | grep -v "__init__.py\|base.py" || true)
if [ -n "$MODELS" ]; then
    echo -e "${YELLOW}🗄️  ORM Models modificados detectados${NC}"

    for model_file in $MODELS; do
        model_name=$(basename "$model_file" .py)

        # Extrai classes do model
        classes=$(grep -E "^class \w+\(Base" "$model_file" | sed 's/class \(\w\+\)(.*/\1/' || true)

        if [ -n "$classes" ]; then
            prompt="IMPORTANTE: Mudança em ORM model detectada.

Arquivo: $model_file
Classes: $(echo "$classes" | tr '\n' ', ')

AÇÕES NECESSÁRIAS:

1. Se você ADICIONOU/MODIFICOU campos no model:
   - Rode: alembic revision --autogenerate -m 'Update $model_name schema'
   - Rode: alembic upgrade head

2. Atualize tests/schema/test_db_schema_validation.py:
   - Adicione/atualize validação para a tabela correspondente
   - Valide tipos de colunas
   - Valide constraints (nullable, FK)

Use o padrão existente em test_db_schema_validation.py como referência."

            PROMPTS+=("$prompt")
            PROMPT_TYPES+=("schema")
        fi
    done
fi

# Analisa services modificados
SERVICES=$(echo "$CHANGED_FILES" | grep "src/synth_lab/services/.*service\.py" || true)
if [ -n "$SERVICES" ]; then
    echo -e "${YELLOW}⚙️  Services modificados detectados${NC}"

    for service_file in $SERVICES; do
        service_name=$(basename "$service_file" .py)

        # Extrai classe do service
        service_class=$(grep -E "^class \w+Service" "$service_file" | head -1 | sed 's/class \(\w\+\)(.*/\1/' || true)

        if [ -n "$service_class" ]; then
            prompt="Criar/atualizar integration test para $service_class em tests/integration/.

Service: $service_file

Crie teste que valide:
1. Fluxo completo do serviço (happy path)
2. Interações com banco de dados (se houver)
3. Tratamento de erros principais
4. Side effects (dados persistidos corretamente)

Use o padrão existente em tests/integration/ como referência.
Nomeie o arquivo como test_${service_name}_flows.py"

            PROMPTS+=("$prompt")
            PROMPT_TYPES+=("integration")
        fi
    done
fi

# Se não há prompts, sai
if [ ${#PROMPTS[@]} -eq 0 ]; then
    echo -e "${GREEN}✅ Nenhuma atualização de teste necessária${NC}"
    exit 0
fi

echo ""
echo -e "${BLUE}📝 Prompts gerados: ${#PROMPTS[@]}${NC}"
echo ""

# Processa cada prompt
for i in "${!PROMPTS[@]}"; do
    prompt="${PROMPTS[$i]}"
    type="${PROMPT_TYPES[$i]}"

    echo -e "${BLUE}════════════════════════════════════════${NC}"
    echo -e "${BLUE}Prompt $((i+1))/${#PROMPTS[@]} - Tipo: $type${NC}"
    echo -e "${BLUE}════════════════════════════════════════${NC}"
    echo ""
    echo "$prompt"
    echo ""

    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}[DRY-RUN] Pulando execução${NC}"
        echo ""
        continue
    fi

    # Pergunta se deve executar (se não for auto)
    if [ "$AUTO_COMMIT" = false ]; then
        read -p "Executar este prompt com Claude Code? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Pulado."
            echo ""
            continue
        fi
    fi

    # Executa Claude Code
    echo -e "${BLUE}🤖 Executando Claude Code...${NC}"

    # Salva prompt em arquivo temporário
    PROMPT_FILE=$(mktemp)
    echo "$prompt" > "$PROMPT_FILE"

    # Chama Claude Code
    if claude code --prompt-file "$PROMPT_FILE"; then
        echo -e "${GREEN}✅ Claude Code executado com sucesso${NC}"
        rm "$PROMPT_FILE"
    else
        echo -e "${RED}❌ Claude Code falhou${NC}"
        rm "$PROMPT_FILE"
        continue
    fi

    # Valida que testes foram criados/atualizados
    echo ""
    echo -e "${BLUE}🧪 Validando testes...${NC}"

    case $type in
        contract)
            if make test-fast 2>&1 | grep -q "contract.*passed"; then
                echo -e "${GREEN}✅ Contract tests passaram${NC}"
            else
                echo -e "${RED}❌ Contract tests falharam. Revise manualmente.${NC}"
                continue
            fi
            ;;
        schema)
            if make test-fast 2>&1 | grep -q "schema.*passed"; then
                echo -e "${GREEN}✅ Schema tests passaram${NC}"
            else
                echo -e "${RED}❌ Schema tests falharam. Rode: alembic revision --autogenerate${NC}"
                continue
            fi
            ;;
        integration)
            if pytest tests/integration/ -q --tb=short; then
                echo -e "${GREEN}✅ Integration tests passaram${NC}"
            else
                echo -e "${RED}❌ Integration tests falharam. Revise manualmente.${NC}"
                continue
            fi
            ;;
    esac

    # Auto-commit se solicitado
    if [ "$AUTO_COMMIT" = true ]; then
        echo ""
        echo -e "${BLUE}📦 Auto-commit...${NC}"

        git add tests/

        case $type in
            contract)
                git commit -m "test: update contract tests (auto-generated)"
                ;;
            schema)
                git commit -m "test: update schema validation tests (auto-generated)"
                ;;
            integration)
                git commit -m "test: add integration tests (auto-generated)"
                ;;
        esac

        echo -e "${GREEN}✅ Commit criado${NC}"
    fi

    echo ""
done

echo ""
echo -e "${GREEN}🎉 Auto-update concluído!${NC}"
echo ""

# Resumo
echo "Próximos passos:"
if [ "$AUTO_COMMIT" = false ]; then
    echo "  1. Revise as mudanças em tests/"
    echo "  2. Rode: make test-fast"
    echo "  3. Commit: git commit -m 'test: update tests'"
else
    echo "  ✅ Testes já foram commitados automaticamente"
fi
