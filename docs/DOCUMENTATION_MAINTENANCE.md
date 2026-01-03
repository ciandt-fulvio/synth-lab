# Sistema de Documentação Auto-Atualizada

**Data:** 2026-01-03
**Status:** ✅ Implementado (Fases 1-3)
**Objetivo:** Manter documentações do projeto sincronizadas com código usando Claude Code, git hooks e automação

---

## 🎯 Visão Geral

Sistema inspirado no `auto-update-tests.sh` existente, mas focado em manter documentação atualizada quando código muda.

---

## 📋 Arquitetura Proposta

### 1. Script Principal: `auto-update-docs.sh`

Similar ao `auto-update-tests.sh`, detecta mudanças que afetam documentação:

**Localização:** `scripts/auto-update-docs.sh`

**Lógica de detecção:**

| Arquivo Mudou | Doc Afetada | Ação |
|---------------|-------------|------|
| `src/synth_lab/api/routers/*.py` | `docs/api.md` | Atualizar lista de endpoints, schemas |
| `src/synth_lab/services/*.py` | `docs/arquitetura.md` | Atualizar diagrama de services |
| `src/synth_lab/models/orm/*.py` | `docs/database_model.md` | Atualizar schema do banco |
| `frontend/src/pages/*.tsx` | `docs/arquitetura_front.md` | Atualizar rotas e páginas |
| `frontend/src/hooks/*.ts` | `docs/arquitetura_front.md` | Atualizar lista de hooks |
| `.claude/skills/*/SKILL.md` | `README.md` | Atualizar seção de skills |

**Uso:**
```bash
# Analisa staged files
./scripts/auto-update-docs.sh

# Analisa último commit
./scripts/auto-update-docs.sh --last-commit

# Arquivo específico
./scripts/auto-update-docs.sh --file router.py

# Com auto-commit
./scripts/auto-update-docs.sh --last-commit --auto-commit

# Dry run (só mostra prompts)
./scripts/auto-update-docs.sh --dry-run
```

---

### 2. Git Hooks

**Arquivo:** `.githooks/post-commit`

Adicionar após a seção de testes:

```bash
#!/bin/bash
#
# Git post-commit hook: Sugere atualizar docs com Claude Code
# Não bloqueia - apenas oferece ajuda
#

# Verifica se mudou arquivos críticos
CHANGED_FILES=$(git diff --name-only HEAD~1 HEAD)

NEEDS_DOCS_UPDATE=false

# Detecta mudanças que afetam docs
if echo "$CHANGED_FILES" | grep -qE "src/synth_lab/(api|services|models)/"; then
    NEEDS_DOCS_UPDATE=true
fi

if echo "$CHANGED_FILES" | grep -qE "frontend/src/(pages|hooks)/"; then
    NEEDS_DOCS_UPDATE=true
fi

if echo "$CHANGED_FILES" | grep -q ".claude/skills/.*\.md"; then
    NEEDS_DOCS_UPDATE=true
fi

if [ "$NEEDS_DOCS_UPDATE" = true ]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📚 SUGESTÃO: Atualizar documentação"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Você modificou arquivos que podem afetar a documentação."
    echo "Quer que Claude Code atualize as docs automaticamente?"
    echo ""
    echo "Opções:"
    echo "  1) Sim, executar agora (interativo)"
    echo "  2) Sim, executar e auto-commit"
    echo "  3) Não, farei manualmente"
    echo ""
    read -p "Escolha (1/2/3): " -n 1 -r
    echo ""

    case $REPLY in
        1)
            echo "Executando auto-update docs (interativo)..."
            ./scripts/auto-update-docs.sh --last-commit
            ;;
        2)
            echo "Executando auto-update docs (auto-commit)..."
            ./scripts/auto-update-docs.sh --last-commit --auto-commit
            ;;
        3)
            echo "OK. Para rodar depois: ./scripts/auto-update-docs.sh --last-commit"
            ;;
        *)
            echo "Opção inválida. Pulando."
            ;;
    esac

    echo ""
fi

exit 0
```

---

### 3. Skill: `update-docs`

**Localização:** `.claude/skills/update-docs/SKILL.md`

```markdown
# Update Docs Skill

**Trigger:** Mudanças em código core (api, services, models, frontend)

**Objetivo:** Manter docs sincronizadas com código.

## Uso

```bash
# Automático (via git hook)
git commit -m "Add endpoint"
# Hook pergunta se quer atualizar docs

# Manual
./scripts/auto-update-docs.sh --last-commit
```

## O que faz

**Router mudou** → Atualiza `docs/api.md`
**Service mudou** → Atualiza `docs/arquitetura.md`
**Model mudou** → Atualiza `docs/database_model.md`
**Frontend mudou** → Atualiza `docs/arquitetura_front.md`

## Templates de Prompts

### API Docs Update
```
Atualizar docs/api.md para refletir mudanças em {router_file}.

Endpoints detectados:
{endpoints_list}

Para cada endpoint novo/modificado, adicione/atualize:
1. Descrição do que faz
2. Parâmetros (query, path, body)
3. Exemplo de request
4. Exemplo de response
5. Códigos de status possíveis

Mantenha o formato existente em docs/api.md.
NÃO remova seções existentes, apenas adicione/atualize.
```

### Architecture Docs Update
```
Atualizar docs/arquitetura.md para refletir mudanças em {service_file}.

Service modificado: {ServiceClass}

Verifique se:
1. O service está listado na seção "Services"
2. Responsabilidades estão documentadas
3. Dependências estão corretas
4. Fluxo de dados está atualizado

Se necessário, atualize diagramas ASCII-art.
Preserve todo conteúdo existente.
```

### Database Model Docs Update
```
Atualizar docs/database_model.md para refletir mudanças em {model_file}.

Model modificado: {ModelClass}

Atualize:
1. Tabela na seção "Schema"
2. Relacionamentos (se houver)
3. Constraints e índices
4. Campos novos/modificados/removidos

Use o schema real do banco (rode consulta SQL se necessário).
```

### Frontend Docs Update
```
Atualizar docs/arquitetura_front.md para refletir mudanças em {frontend_file}.

Tipo de mudança: {change_type}  # page, hook, component

Se página:
- Atualizar tabela de rotas
- Adicionar componentes usados

Se hook:
- Adicionar à lista de hooks
- Documentar propósito e parâmetros

Se componente principal:
- Adicionar à seção de componentes
- Documentar props principais
```

## Regras

- SEMPRE preserve conteúdo existente
- Apenas adicione/atualize seções relacionadas à mudança
- Use formato markdown consistente
- Valide links internos
- Mantenha exemplos de código atualizados

## Validação

Após atualização:
```bash
# Verifica sintaxe markdown
markdownlint docs/**/*.md

# Verifica que arquivo foi modificado
git diff docs/
```

## Guia Completo

Ver [docs/DOCUMENTATION_MAINTENANCE.md](../../docs/DOCUMENTATION_MAINTENANCE.md)
```

---

### 4. GitHub Actions Workflow

**Arquivo:** `.github/workflows/docs-validation.yml`

```yaml
name: Docs Validation

on:
  pull_request:
    paths:
      - 'src/**/*.py'
      - 'frontend/src/**/*.{ts,tsx}'
      - 'docs/**/*.md'

jobs:
  check-docs-sync:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 2  # Precisa de 2 commits para diff

      - name: Check if docs need update
        run: |
          echo "Verificando se mudanças em código requerem atualização de docs..."

          # Detecta mudanças em código que devem ter docs atualizadas
          CHANGED_CODE=$(git diff origin/main --name-only | grep -E "src/synth_lab/(api|services|models)/" || true)

          if [ -n "$CHANGED_CODE" ]; then
            echo "Código mudou:"
            echo "$CHANGED_CODE"

            CHANGED_DOCS=$(git diff origin/main --name-only | grep "docs/" || true)

            if [ -z "$CHANGED_DOCS" ]; then
              echo "::warning::⚠️  Código mudou mas docs não foram atualizadas"
              echo "::warning::Arquivos modificados que podem afetar docs:"
              echo "$CHANGED_CODE" | sed 's/^/::warning::  - /'
              echo "::warning::Considere rodar: ./scripts/auto-update-docs.sh"
              # Não falha, apenas avisa
            else
              echo "✅ Docs foram atualizadas junto com código"
              echo "$CHANGED_DOCS"
            fi
          else
            echo "✅ Nenhuma mudança em código crítico"
          fi

      - name: Validate markdown syntax
        run: |
          npm install -g markdownlint-cli

          # Cria config se não existir
          cat > .markdownlint.json << 'EOF'
          {
            "default": true,
            "MD013": false,
            "MD033": false,
            "MD041": false
          }
          EOF

          markdownlint docs/**/*.md --config .markdownlint.json || {
            echo "::error::Problemas de formatação encontrados em arquivos markdown"
            exit 1
          }

      - name: Check for broken internal links
        run: |
          echo "Verificando links internos quebrados..."

          # Procura por links markdown internos
          find docs -name "*.md" -exec grep -H "\[.*\](\.\.*/.*\.md)" {} \; > /tmp/doc_links.txt || true

          if [ -s /tmp/doc_links.txt ]; then
            while IFS=: read -r file link; do
              # Extrai path do link
              link_path=$(echo "$link" | sed -E 's/.*\((.*\.md)\).*/\1/')

              # Resolve path relativo
              dir=$(dirname "$file")
              full_path="$dir/$link_path"

              if [ ! -f "$full_path" ]; then
                echo "::warning::Link quebrado em $file: $link_path"
              fi
            done < /tmp/doc_links.txt
          fi

          echo "✅ Verificação de links concluída"

  check-api-docs-coverage:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'

      - name: Check API endpoints documentation
        run: |
          echo "Verificando se todos os endpoints estão documentados..."

          # Extrai endpoints dos routers
          ENDPOINTS=$(find src/synth_lab/api/routers -name "*.py" -exec grep -h "@router\." {} \; | \
                      grep -E "@router\.(get|post|put|delete|patch)" | \
                      sed -E 's/.*@router\.(get|post|put|delete|patch)\(["\']([^"\']+).*/\2/' | \
                      sort -u)

          # Conta total
          TOTAL=$(echo "$ENDPOINTS" | wc -l)

          # Verifica quantos estão em docs/api.md
          DOCUMENTED=0
          while IFS= read -r endpoint; do
            if grep -q "$endpoint" docs/api.md; then
              DOCUMENTED=$((DOCUMENTED + 1))
            else
              echo "::warning::Endpoint não documentado: $endpoint"
            fi
          done <<< "$ENDPOINTS"

          COVERAGE=$((DOCUMENTED * 100 / TOTAL))

          echo "📊 API Docs Coverage: $DOCUMENTED/$TOTAL endpoints ($COVERAGE%)"

          if [ $COVERAGE -lt 80 ]; then
            echo "::warning::Cobertura de docs de API abaixo de 80%"
          fi
```

---

### 5. CLI Command

**Arquivo:** `src/synth_lab/__main__.py`

Adicionar command ao Typer app:

```python
@app.command()
def update_docs(
    file: Optional[str] = typer.Option(None, help="Arquivo específico para atualizar docs"),
    auto: bool = typer.Option(False, help="Auto-commit após atualização"),
    last_commit: bool = typer.Option(False, help="Analisar último commit"),
    dry_run: bool = typer.Option(False, help="Apenas mostrar prompts sem executar"),
):
    """Atualiza documentação usando Claude Code.

    Detecta mudanças em código e gera prompts para Claude Code
    atualizar documentação correspondente.

    Examples:
        # Analisa staged files
        synth-lab update-docs

        # Analisa último commit
        synth-lab update-docs --last-commit

        # Arquivo específico
        synth-lab update-docs --file src/synth_lab/api/routers/research.py

        # Com auto-commit
        synth-lab update-docs --last-commit --auto
    """
    import subprocess
    from pathlib import Path

    # Verifica se script existe
    script_path = Path("scripts/auto-update-docs.sh")
    if not script_path.exists():
        typer.echo("❌ Script auto-update-docs.sh não encontrado", err=True)
        raise typer.Exit(1)

    # Monta comando
    cmd = ["./scripts/auto-update-docs.sh"]

    if file:
        cmd.extend(["--file", file])
    if auto:
        cmd.append("--auto-commit")
    if last_commit:
        cmd.append("--last-commit")
    if dry_run:
        cmd.append("--dry-run")

    # Executa
    try:
        result = subprocess.run(cmd, check=True)
        raise typer.Exit(result.returncode)
    except subprocess.CalledProcessError as e:
        typer.echo(f"❌ Erro ao executar auto-update-docs: {e}", err=True)
        raise typer.Exit(e.returncode)
```

**Por que isso é útil:**
- Permite rodar atualização de docs via CLI (`synth-lab update-docs`)
- Mais conveniente que lembrar path do script
- Integra com workflow do projeto (similar a `synth-lab research`, etc.)
- Suporta todas as flags do script bash

---

### 6. Detecção Inteligente de Mudanças

**Implementação no `auto-update-docs.sh`:**

```bash
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
                     sed -E 's/.*@router\.(get|post|put|delete|patch)\(["\']([^"\']+).*/\2/' | \
                     head -10)

    if [ -n "$endpoints" ]; then
        local prompt="Atualizar docs/api.md para refletir mudanças no router '$router_name' ($router_file).

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
- Use exemplos reais baseados nos schemas Pydantic do router"

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
        local prompt="Atualizar docs/arquitetura.md para refletir mudanças no service '$service_class' ($service_file).

Verifique e atualize:
1. O service está listado na seção 'Service Layer'?
2. Responsabilidades estão documentadas corretamente?
3. Dependências (repositories, infra clients) estão corretas?
4. Fluxo de dados está atualizado?

Se necessário:
- Atualize diagramas ASCII-art mostrando fluxo
- Adicione service à tabela de services
- Documente novos métodos principais

IMPORTANTE:
- Preserve estrutura e conteúdo existente
- Apenas adicione/atualize seção relacionada a '$service_class'
- Mantenha consistência com outros services documentados"

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
        local prompt="Atualizar docs/database_model.md para refletir mudanças no model ORM ($model_file).

Classes detectadas: $(echo "$classes" | tr '\n' ', ')

Para cada tabela:
1. Atualize schema (colunas, tipos, constraints)
2. Documente relacionamentos (FK, One-to-Many, etc.)
3. Adicione índices se houver
4. Marque campos obrigatórios vs opcionais

IMPORTANTE:
- Use schema REAL do banco (consulte SQLAlchemy metadata se necessário)
- Mantenha formato de tabela markdown existente
- NÃO remova outras tabelas já documentadas
- Se campos foram removidos, remova da doc também"

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
    local route=$(echo "$page_name" | sed 's/Page$//' | tr '[:upper:]' '[:lower:]')

    local prompt="Atualizar docs/arquitetura_front.md para refletir mudanças na página '$page_name' ($page_file).

Página: $page_name
Rota inferida: /$route

Verifique e atualize:
1. Tabela de rotas (path, componente, descrição)
2. Componentes principais usados pela página
3. Hooks utilizados (useQuery, useMutation, custom hooks)
4. Fluxo de dados (API calls, state management)

IMPORTANTE:
- Mantenha formato existente
- NÃO remova outras páginas
- Adicione screenshot ou descrição visual se for nova página"

    PROMPTS+=("$prompt")
    PROMPT_TYPES+=("frontend")
    DOC_FILES+=("docs/arquitetura_front.md")
}

# Função: detecta mudanças em hooks do frontend
detect_hook_changes() {
    local hook_file=$1
    local hook_name=$(basename "$hook_file" .ts)

    local prompt="Atualizar docs/arquitetura_front.md para refletir mudanças no hook '$hook_name' ($hook_file).

Hook: $hook_name

Adicione/atualize na seção 'Custom Hooks':
1. Nome e propósito do hook
2. Parâmetros aceitos (com tipos)
3. Retorno (com tipos)
4. Exemplo de uso

IMPORTANTE:
- Mantenha lista alfabética de hooks
- Use formato consistente com hooks existentes"

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
        detect_router_changes "$router"
    done
fi

# Services
SERVICES=$(echo "$CHANGED_FILES" | grep "src/synth_lab/services/.*\.py" || true)
if [ -n "$SERVICES" ]; then
    echo -e "${YELLOW}⚙️  Services modificados detectados${NC}"
    for service in $SERVICES; do
        detect_service_changes "$service"
    done
fi

# Models ORM
MODELS=$(echo "$CHANGED_FILES" | grep "src/synth_lab/models/orm/.*\.py" | grep -v "__init__.py\|base.py" || true)
if [ -n "$MODELS" ]; then
    echo -e "${YELLOW}🗄️  Models ORM modificados detectados${NC}"
    for model in $MODELS; do
        detect_model_changes "$model"
    done
fi

# Frontend Pages
PAGES=$(echo "$CHANGED_FILES" | grep "frontend/src/pages/.*\\.tsx" || true)
if [ -n "$PAGES" ]; then
    echo -e "${YELLOW}🎨 Páginas frontend modificadas detectadas${NC}"
    for page in $PAGES; do
        detect_page_changes "$page"
    done
fi

# Frontend Hooks
HOOKS=$(echo "$CHANGED_FILES" | grep "frontend/src/hooks/.*\\.ts" || true)
if [ -n "$HOOKS" ]; then
    echo -e "${YELLOW}🪝 Hooks frontend modificados detectados${NC}"
    for hook in $HOOKS; do
        detect_hook_changes "$hook"
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
```

---

### 7. Validação de Docs Atualizadas

**Checklist após atualização:**

```bash
validate_doc_update() {
    local doc_file=$1
    local errors=0

    echo "Validando $doc_file..."

    # 1. Arquivo foi modificado?
    if ! git diff --name-only | grep -q "$doc_file"; then
        echo "❌ $doc_file não foi atualizado"
        return 1
    fi

    # 2. Tamanho razoável (não deletou tudo)?
    local line_count=$(wc -l < "$doc_file")
    if [ "$line_count" -lt 10 ]; then
        echo "❌ $doc_file parece vazio ($line_count linhas)"
        ((errors++))
    fi

    # 3. Sintaxe markdown válida?
    if command -v markdownlint &> /dev/null; then
        if ! markdownlint "$doc_file" --config .markdownlint.json 2>/dev/null; then
            echo "⚠️  Problemas de formatação markdown"
        fi
    fi

    # 4. Links internos quebrados?
    local broken_links=$(grep -o '\[.*\](\.\.*/.*\.md)' "$doc_file" | while IFS= read -r link; do
        local path=$(echo "$link" | sed -E 's/.*\((.*)\).*/\1/')
        local full_path="$(dirname "$doc_file")/$path"

        if [ ! -f "$full_path" ]; then
            echo "$path"
        fi
    done)

    if [ -n "$broken_links" ]; then
        echo "⚠️  Links quebrados encontrados:"
        echo "$broken_links" | sed 's/^/    - /'
    fi

    # 5. Diff razoável (não mudou tudo)?
    local lines_changed=$(git diff --numstat "$doc_file" | awk '{print $1 + $2}')
    local total_lines=$(wc -l < "$doc_file")
    local change_percent=$((lines_changed * 100 / total_lines))

    if [ "$change_percent" -gt 80 ]; then
        echo "⚠️  Mudança muito grande ($change_percent% do arquivo)"
        echo "    Verifique se não houve erro na atualização"
    fi

    if [ $errors -eq 0 ]; then
        echo "✅ $doc_file passou na validação"
        return 0
    else
        echo "❌ $doc_file falhou na validação"
        return 1
    fi
}
```

---

## 📊 Comparação com Sistema de Testes

| Aspecto | Testes (existente) | Docs (proposta) |
|---------|-------------------|-----------------|
| **Script** | `auto-update-tests.sh` | `auto-update-docs.sh` |
| **Git Hook** | `post-commit` | `post-commit` (expandido) |
| **Skill** | `update-tests.md` | `update-docs/SKILL.md` |
| **Workflow** | `tests-*.yml` | `docs-validation.yml` |
| **Validação** | `pytest` | `markdownlint` + diff check |
| **Auto-commit** | ✅ Suportado | ✅ Suportado |
| **Dry-run** | ✅ `--dry-run` | ✅ `--dry-run` |
| **CLI Command** | ❌ Não tem | ✅ `synth-lab update-docs` |

---

## 🚀 Plano de Implementação

### Fase 1: MVP (Mínimo Viável) ✅ COMPLETO
- [x] Criar `scripts/auto-update-docs.sh`
- [x] Adicionar detecção básica:
  - Routers → `docs/api.md`
  - Models → `docs/database_model.md`
  - Services → `docs/arquitetura.md`
  - Pages → `docs/arquitetura_front.md`
  - Hooks → `docs/arquitetura_front.md`
- [x] Integrar no `.githooks/post-commit`
- [x] Adicionar comando `make update-docs` ao Makefile

**Data Implementação:** 2026-01-03
**Status:** ✅ Implementado

### Fase 2: Skill ✅ COMPLETO
- [x] Criar `.claude/skills/update-docs/SKILL.md`
- [x] Adicionar templates de prompts para cada tipo de doc
- [x] Documentar uso em README skill
- [x] Adicionar exemplos de uso

**Data Implementação:** 2026-01-03
**Status:** ✅ Implementado

### Fase 3: CI/CD ✅ COMPLETO
- [x] Criar workflow `.github/workflows/docs-validation.yml`
- [x] Adicionar check de markdown syntax
- [x] Adicionar warning em PRs se docs não atualizadas
- [x] Adicionar check de links quebrados
- [x] Adicionar check de API docs coverage
- [x] Criar `.markdownlint.json` para validação

**Data Implementação:** 2026-01-03
**Status:** ✅ Implementado

### Fase 4: Refinamento ⏭️ PARCIALMENTE IMPLEMENTADO
- [x] ~~Adicionar CLI command `synth-lab update-docs`~~ (Decidido usar `make update-docs`)
- [x] Adicionar suporte para frontend docs
- [x] Adicionar validação de cobertura de docs (API endpoints)
- [ ] Melhorar detecção com diff analysis (mudanças específicas)
- [ ] Adicionar cobertura para services/models

**Status:** 🟡 Parcial (suficiente para uso)

### Fase 5: Features Avançadas (Futuro) 📅 PLANEJADO
- [ ] Metadata tracking (`.docs-metadata.json`)
- [ ] Diff-driven updates (só seções afetadas)
- [ ] Doc coverage metrics completo
- [ ] Schedule weekly reviews (GitHub Actions)

**Status:** 📅 Futuro

---

## 💡 Ideias Avançadas

### 1. Documentação como Código

Guardar metadados em `docs/.metadata.json`:

```json
{
  "api.md": {
    "last_updated": "2026-01-03T10:30:00Z",
    "last_updated_by": "auto-update-docs.sh",
    "source_files": [
      "src/synth_lab/api/routers/research.py",
      "src/synth_lab/api/routers/synthetics.py"
    ],
    "auto_generated_sections": [
      "## Endpoints",
      "### Research Endpoints"
    ],
    "manual_sections": [
      "## Overview",
      "## Authentication"
    ]
  },
  "arquitetura.md": {
    "last_updated": "2026-01-02T15:20:00Z",
    "source_files": [
      "src/synth_lab/services/research_agentic/",
      "src/synth_lab/services/research_prfaq/"
    ],
    "diagrams": ["layer_diagram", "service_flow"]
  }
}
```

**Benefícios:**
- Saber quando cada doc foi atualizada pela última vez
- Rastrear quais arquivos de código afetam cada doc
- Diferenciar seções auto-geradas vs escritas manualmente
- Evitar sobrescrever seções manuais

### 2. Diff-Driven Updates

Ao invés de atualizar doc inteira, atualizar apenas seções específicas:

```bash
# Detecta exatamente o que mudou
git diff HEAD~1 HEAD src/synth_lab/api/routers/research.py

# Se adicionou novo endpoint:
# → Adiciona só esse endpoint em docs/api.md

# Se mudou docstring de endpoint existente:
# → Atualiza só descrição desse endpoint

# Se removeu endpoint:
# → Remove seção correspondente em docs/api.md
```

**Prompt mais preciso:**
```
Foi adicionado novo endpoint GET /research/{id} no router research.py.

Adicione APENAS este endpoint na seção "### Research Endpoints" em docs/api.md.

NÃO modifique outros endpoints.
NÃO modifique outras seções.

Use este formato:
#### GET /research/{id}
...
```

### 3. Doc Coverage Metrics

Similar a test coverage:

```bash
# Calcula % de endpoints documentados
./scripts/check-doc-coverage.sh

# Output:
📊 Documentation Coverage Report

API Endpoints:        15/17 (88%)
Services:             8/10 (80%)
ORM Models:          12/12 (100%)
Frontend Pages:       5/7 (71%)
Frontend Hooks:       4/6 (67%)

Overall:             44/52 (85%)

Missing docs:
  - GET /synthetics/batch
  - POST /synthetics/export
  - Service: EmailService
  - Service: NotificationService
  - Page: SettingsPage
  - Page: ProfilePage
  - Hook: useDebounce
  - Hook: useLocalStorage
```

Dashboard em `docs/coverage.md` (auto-gerado):

```markdown
# Documentation Coverage

Last updated: 2026-01-03 10:45:00

## Summary

| Category | Coverage | Trend |
|----------|----------|-------|
| API Endpoints | 88% (15/17) | 📈 +5% |
| Services | 80% (8/10) | ➡️  0% |
| ORM Models | 100% (12/12) | ✅ 100% |
| Frontend Pages | 71% (5/7) | 📉 -14% |
| Frontend Hooks | 67% (4/6) | ➡️  0% |

**Overall:** 85% (44/52)

## Details

### API Endpoints (88%)

✅ Documented:
- GET /research
- POST /research
- GET /research/{id}
- ...

❌ Missing:
- GET /synthetics/batch
- POST /synthetics/export

...
```

### 4. Schedule Updates

Workflow semanal que verifica se docs precisam refresh:

```yaml
name: Weekly Docs Review

on:
  schedule:
    - cron: '0 10 * * 1'  # Segunda 10am

jobs:
  review-docs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Check docs freshness
        run: |
          # Docs mais antigas que 30 dias
          find docs -name "*.md" -mtime +30

      - name: Generate doc coverage report
        run: |
          ./scripts/check-doc-coverage.sh > docs/coverage.md

      - name: Create issue if coverage < 80%
        run: |
          # Se coverage baixou, cria issue
          ...
```

---

## 🎯 Documentos que SÃO Atualizados

**Backend:**
- ✅ `docs/api.md` - Quando routers mudam
- ✅ `docs/arquitetura.md` - Quando services mudam
- ✅ `docs/database_model.md` - Quando models ORM mudam

**Frontend:**
- ✅ `docs/arquitetura_front.md` - Quando pages/hooks/components mudam

**Projeto:**
- ✅ `README.md` - Quando skills são adicionados/modificados (pode ser futuro)

**NÃO são atualizados automaticamente:**
- ❌ `CLAUDE.md` - Instruções específicas do projeto (manual)
- ❌ `~/.claude/CLAUDE.md` - Instruções globais do usuário (manual)
- ❌ `docs/TESTING.md` - Guia de testes (manual, mas pode ser expandido)
- ❌ `docs/cli.md` - CLI docs (poderia ser auto-gerado futuro)
- ❌ `docs/synth-attributes-reference.md` - Referência (manual)

**Razão:** `CLAUDE.md` são **regras e convenções**, não **estado do código**. São editados manualmente quando convenções mudam.

---

## 📚 Referências

- Script inspirador: `scripts/auto-update-tests.sh`
- Git hooks: `.githooks/post-commit`, `.githooks/pre-commit`
- Skill de referência: `.claude/skills/update-tests.md`
- Workflows: `.github/workflows/test-*.yml`

---

## ✅ Checklist de Implementação

### Fase 1: MVP
- [ ] Criar `scripts/auto-update-docs.sh`
- [ ] Adicionar função `detect_router_changes()`
- [ ] Adicionar função `detect_service_changes()`
- [ ] Adicionar função `detect_model_changes()`
- [ ] Adicionar validação de docs atualizadas
- [ ] Atualizar `.githooks/post-commit`
- [ ] Testar com commit real

### Fase 2: Skill
- [ ] Criar diretório `.claude/skills/update-docs/`
- [ ] Criar `SKILL.md` com templates
- [ ] Adicionar exemplos de uso
- [ ] Linkar em README (se houver)

### Fase 3: CI/CD
- [ ] Criar `.github/workflows/docs-validation.yml`
- [ ] Adicionar job `check-docs-sync`
- [ ] Adicionar job `validate-markdown-syntax`
- [ ] Adicionar job `check-api-docs-coverage`
- [ ] Testar em PR real

### Fase 4: CLI
- [ ] Adicionar command em `src/synth_lab/__main__.py`
- [ ] Testar `synth-lab update-docs`
- [ ] Atualizar `docs/cli.md` (manual)

---

---

## ✅ Status da Implementação

**Implementado em:** 2026-01-03

### Arquivos Criados/Modificados:

**Novos arquivos:**
- ✅ `scripts/auto-update-docs.sh` - Script principal de atualização
- ✅ `.claude/skills/update-docs/SKILL.md` - Skill com templates
- ✅ `.github/workflows/docs-validation.yml` - CI/CD workflow
- ✅ `.markdownlint.json` - Configuração de validação markdown
- ✅ `docs/DOCUMENTATION_MAINTENANCE.md` - Este documento

**Arquivos modificados:**
- ✅ `.githooks/post-commit` - Adicionada seção de docs
- ✅ `Makefile` - Adicionado comando `make update-docs`

### Como Usar:

**1. Via Git Hook (Automático):**
```bash
# Simplesmente commite código que afeta docs
git commit -m "feat: add new endpoint"

# Hook pergunta se quer atualizar docs
# Escolha opção 1 ou 2
```

**2. Via Makefile (Manual):**
```bash
make update-docs
```

**3. Via Script Direto:**
```bash
# Analisa último commit
./scripts/auto-update-docs.sh --last-commit

# Dry-run (só vê prompts)
./scripts/auto-update-docs.sh --last-commit --dry-run

# Auto-commit
./scripts/auto-update-docs.sh --last-commit --auto-commit
```

### Próximos Passos:

1. **Testar sistema:** Fazer commit que muda router/service/model e ver hook em ação
2. **Validar workflow:** Fazer PR e verificar checks do GitHub Actions
3. **Ajustar prompts:** Se prompts gerados não forem bons, editar templates em `.claude/skills/update-docs/SKILL.md`
4. **Implementar Fase 4/5:** Features avançadas conforme necessidade

---

**Sistema pronto para uso! 🎉**
