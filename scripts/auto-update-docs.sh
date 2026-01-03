#!/bin/bash
#
# Auto-atualiza documentação usando Claude Code
# Detecta mudanças, gera prompts, roda Claude Code, valida
#
# Uso:
#   ./scripts/auto-update-docs.sh                    # Analisa staged files
#   ./scripts/auto-update-docs.sh --last-commit      # Analisa último commit
#   ./scripts/auto-update-docs.sh --file router.py   # Arquivo específico
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

echo -e "${BLUE}📚 Auto-Update Docs com Claude Code${NC}"
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
declare -a DOC_FILES

# Função: detecta mudanças em routers
detect_router_changes() {
    local router_file=$1
    local router_name=$(basename "$router_file" .py)

    # Extrai endpoints (novos e existentes)
    local endpoints=$(grep -E '@router\.(get|post|put|delete|patch)\(' "$router_file" | \
                     sed -E 's/.*@router\.([a-z]+)\(["'\'']([^"'\'']+).*/\1 \2/' | \
                     awk '{print toupper($1) " " $2}' | \
                     head -10)

    if [ -n "$endpoints" ]; then
        local prompt
        prompt=$(cat <<EOF
Atualizar docs/api.md para refletir mudanças no router '$router_name' ($router_file).

Endpoints encontrados:
$(echo "$endpoints" | sed 's/^/- /')

Para cada endpoint novo/modificado:
1. Adicione/atualize descrição do que faz
2. Liste parâmetros (query, path, body) com tipos
3. Exemplo de request (curl ou httpie)
4. Exemplo de response (JSON)
5. Códigos de status possíveis (200, 201, 404, etc.)

IMPORTANTE:
- Mantenha formato existente em docs/api.md
- NÃO remova outros endpoints já documentados
- Apenas adicione/atualize seção do router '$router_name'
- Use exemplos reais baseados nos schemas Pydantic do router
- Se router tem novos endpoints, adicione na seção apropriada
- Se endpoint foi removido do código, remova da doc também
EOF
)

        PROMPTS+=("$prompt")
        PROMPT_TYPES+=("api")
        DOC_FILES+=("docs/api.md")
    fi
}

# Função: detecta mudanças em services
detect_service_changes() {
    local service_file=$1
    local service_name=$(basename "$service_file" .py)

    # Extrai classe do service
    local service_class=$(grep -E "^class \w+Service" "$service_file" | head -1 | sed 's/class \(\w\+\)(.*/\1/' || true)

    if [ -n "$service_class" ]; then
        local prompt
        prompt=$(cat <<EOF
Atualizar docs/arquitetura.md para refletir mudanças no service '$service_class' ($service_file).

Verifique e atualize:
1. O service está listado na seção 'Service Layer'?
2. Responsabilidades estão documentadas corretamente?
3. Dependências (repositories, infra clients) estão corretas?
4. Fluxo de dados está atualizado?

Se necessário:
- Atualize diagramas ASCII-art mostrando fluxo
- Adicione service à tabela de services
- Documente novos métodos principais públicos

IMPORTANTE:
- Preserve estrutura e conteúdo existente
- Apenas adicione/atualize seção relacionada a '$service_class'
- Mantenha consistência com outros services documentados
- NÃO documente métodos privados (com _)
EOF
)

        PROMPTS+=("$prompt")
        PROMPT_TYPES+=("architecture")
        DOC_FILES+=("docs/arquitetura.md")
    fi
}

# Função: detecta mudanças em models ORM
detect_model_changes() {
    local model_file=$1
    local model_name=$(basename "$model_file" .py)

    # Extrai classes do model
    local classes=$(grep -E "^class \w+\(Base" "$model_file" | sed 's/class \(\w\+\)(.*/\1/' || true)

    if [ -n "$classes" ]; then
        local prompt
        prompt=$(cat <<EOF
Atualizar docs/database_model.md para refletir mudanças no model ORM ($model_file).

Classes detectadas: $(echo "$classes" | tr '\n' ', ')

Para cada tabela:
1. Atualize schema (colunas, tipos, constraints)
2. Documente relacionamentos (FK, One-to-Many, Many-to-Many)
3. Adicione índices se houver
4. Marque campos obrigatórios (NOT NULL) vs opcionais

IMPORTANTE:
- Use schema REAL do banco (analise o código SQLAlchemy Column())
- Mantenha formato de tabela markdown existente
- NÃO remova outras tabelas já documentadas
- Se campos foram removidos do código, remova da doc também
- Documente tipos Python E tipos PostgreSQL (ex: str -> VARCHAR)
EOF
)

        PROMPTS+=("$prompt")
        PROMPT_TYPES+=("database")
        DOC_FILES+=("docs/database_model.md")
    fi
}

# Função: detecta mudanças em frontend pages
detect_page_changes() {
    local page_file=$1
    local page_name=$(basename "$page_file" .tsx)

    # Extrai rota (procura por path no arquivo ou infere do nome)
    local route=$(echo "$page_name" | sed 's/Page$//' | sed 's/\([A-Z]\)/-\L\1/g' | sed 's/^-//')

    local prompt
    prompt=$(cat <<EOF
Atualizar docs/arquitetura_front.md para refletir mudanças na página '$page_name' ($page_file).

Página: $page_name
Rota inferida: /$route (verifique no código se está correta)

Verifique e atualize:
1. Tabela de rotas (path, componente, descrição)
2. Componentes principais usados pela página
3. Hooks utilizados (useQuery, useMutation, custom hooks)
4. Fluxo de dados (API calls, state management)

IMPORTANTE:
- Mantenha formato existente
- NÃO remova outras páginas
- Se for nova página, adicione descrição clara do propósito
- Liste integrações com backend (endpoints chamados)
EOF
)

    PROMPTS+=("$prompt")
    PROMPT_TYPES+=("frontend")
    DOC_FILES+=("docs/arquitetura_front.md")
}

# Função: detecta mudanças em hooks do frontend
detect_hook_changes() {
    local hook_file=$1
    local hook_name=$(basename "$hook_file" .ts)

    local prompt
    prompt=$(cat <<EOF
Atualizar docs/arquitetura_front.md para refletir mudanças no hook '$hook_name' ($hook_file).

Hook: $hook_name

Adicione/atualize na seção 'Custom Hooks':
1. Nome e propósito do hook
2. Parâmetros aceitos (com tipos TypeScript)
3. Retorno (com tipos TypeScript)
4. Exemplo de uso em componente
5. Dependências (outros hooks usados internamente)

IMPORTANTE:
- Mantenha lista de hooks organizada (por categoria ou alfabética)
- Use formato consistente com hooks existentes
- Se hook foi removido do código, remova da doc
EOF
)

    PROMPTS+=("$prompt")
    PROMPT_TYPES+=("frontend")
    DOC_FILES+=("docs/arquitetura_front.md")
}

# Analisa arquivos e gera prompts
echo -e "${BLUE}🔍 Analisando mudanças...${NC}"
echo ""

# Routers
ROUTERS=$(echo "$CHANGED_FILES" | grep "src/synth_lab/api/routers/.*\.py" || true)
if [ -n "$ROUTERS" ]; then
    echo -e "${YELLOW}📡 Routers modificados detectados${NC}"
    for router in $ROUTERS; do
        if [ -f "$router" ]; then
            detect_router_changes "$router"
        fi
    done
fi

# Services
SERVICES=$(echo "$CHANGED_FILES" | grep "src/synth_lab/services/.*\.py" | grep -v "__init__.py" || true)
if [ -n "$SERVICES" ]; then
    echo -e "${YELLOW}⚙️  Services modificados detectados${NC}"
    for service in $SERVICES; do
        if [ -f "$service" ]; then
            detect_service_changes "$service"
        fi
    done
fi

# Models ORM
MODELS=$(echo "$CHANGED_FILES" | grep "src/synth_lab/models/orm/.*\.py" | grep -v "__init__.py\|base.py" || true)
if [ -n "$MODELS" ]; then
    echo -e "${YELLOW}🗄️  Models ORM modificados detectados${NC}"
    for model in $MODELS; do
        if [ -f "$model" ]; then
            detect_model_changes "$model"
        fi
    done
fi

# Frontend Pages
PAGES=$(echo "$CHANGED_FILES" | grep "frontend/src/pages/.*\\.tsx" || true)
if [ -n "$PAGES" ]; then
    echo -e "${YELLOW}🎨 Páginas frontend modificadas detectadas${NC}"
    for page in $PAGES; do
        if [ -f "$page" ]; then
            detect_page_changes "$page"
        fi
    done
fi

# Frontend Hooks
HOOKS=$(echo "$CHANGED_FILES" | grep "frontend/src/hooks/.*\\.ts" | grep -v "\.test\.ts" || true)
if [ -n "$HOOKS" ]; then
    echo -e "${YELLOW}🪝 Hooks frontend modificados detectados${NC}"
    for hook in $HOOKS; do
        if [ -f "$hook" ]; then
            detect_hook_changes "$hook"
        fi
    done
fi

# Se não há prompts, sai
if [ ${#PROMPTS[@]} -eq 0 ]; then
    echo -e "${GREEN}✅ Nenhuma atualização de documentação necessária${NC}"
    exit 0
fi

echo ""
echo -e "${BLUE}📝 Prompts gerados: ${#PROMPTS[@]}${NC}"
echo ""

# Processa cada prompt
for i in "${!PROMPTS[@]}"; do
    prompt="${PROMPTS[$i]}"
    type="${PROMPT_TYPES[$i]}"
    doc_file="${DOC_FILES[$i]}"

    echo -e "${BLUE}════════════════════════════════════════${NC}"
    echo -e "${BLUE}Prompt $((i+1))/${#PROMPTS[@]} - Tipo: $type${NC}"
    echo -e "${BLUE}Doc: $doc_file${NC}"
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

    # Valida que doc foi atualizada
    echo ""
    echo -e "${BLUE}📖 Validando atualização de doc...${NC}"

    # 1. Verifica que arquivo foi modificado
    if ! git diff --name-only | grep -q "$doc_file"; then
        echo -e "${RED}❌ $doc_file não foi atualizado${NC}"
        continue
    fi

    # 2. Verifica tamanho razoável
    line_count=$(wc -l < "$doc_file")
    if [ "$line_count" -lt 10 ]; then
        echo -e "${RED}❌ $doc_file parece vazio ou corrompido ($line_count linhas)${NC}"
        continue
    fi

    # 3. Verifica sintaxe markdown (se markdownlint disponível)
    if command -v markdownlint &> /dev/null; then
        if markdownlint "$doc_file" --config .markdownlint.json 2>/dev/null; then
            echo -e "${GREEN}✅ Sintaxe markdown válida${NC}"
        else
            echo -e "${YELLOW}⚠️  Avisos de formatação markdown (não bloqueante)${NC}"
        fi
    fi

    echo -e "${GREEN}✅ $doc_file atualizado com sucesso${NC}"

    # Auto-commit se solicitado
    if [ "$AUTO_COMMIT" = true ]; then
        echo ""
        echo -e "${BLUE}📦 Auto-commit...${NC}"

        git add "$doc_file"

        case $type in
            api)
                git commit -m "docs: update API documentation (auto-generated)"
                ;;
            architecture)
                git commit -m "docs: update architecture documentation (auto-generated)"
                ;;
            database)
                git commit -m "docs: update database model documentation (auto-generated)"
                ;;
            frontend)
                git commit -m "docs: update frontend documentation (auto-generated)"
                ;;
        esac

        echo -e "${GREEN}✅ Commit criado${NC}"
    fi

    echo ""
done

echo ""
echo -e "${GREEN}🎉 Auto-update de docs concluído!${NC}"
echo ""

# Resumo
echo "Próximos passos:"
if [ "$AUTO_COMMIT" = false ]; then
    echo "  1. Revise as mudanças em docs/"
    echo "  2. Verifique se tudo faz sentido"
    echo "  3. Commit: git commit -m 'docs: update documentation'"
else
    echo "  ✅ Docs já foram commitadas automaticamente"
fi
echo ""
