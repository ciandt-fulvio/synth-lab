#!/bin/bash
#
# Helper script to merge a feature branch to main with pre-push validation
#
# Usage: ./scripts/merge-to-main.sh [branch-name]
# Example: ./scripts/merge-to-main.sh 039-narrative-mechanism-config
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if branch name was provided
if [ -z "$1" ]; then
    echo -e "${RED}❌ Erro: Nome da branch não fornecido${NC}"
    echo ""
    echo "Uso: ./scripts/merge-to-main.sh <branch-name>"
    echo ""
    echo "Branches disponíveis:"
    git branch --list | grep -v '^\*' | sed 's/^/  /'
    exit 1
fi

BRANCH_NAME="$1"
CURRENT_BRANCH=$(git branch --show-current)

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}🔀 Merge to Main with Pre-Push Validation${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Verificar se a branch existe
if ! git rev-parse --verify "$BRANCH_NAME" >/dev/null 2>&1; then
    echo -e "${RED}❌ Branch '$BRANCH_NAME' não existe!${NC}"
    echo ""
    echo "Branches disponíveis:"
    git branch --list | sed 's/^/  /'
    exit 1
fi

# Verificar se há mudanças não commitadas
if ! git diff-index --quiet HEAD -- 2>/dev/null; then
    echo -e "${RED}❌ Você tem mudanças não commitadas!${NC}"
    echo ""
    git status --short
    echo ""
    echo "Commit ou stash suas mudanças antes de fazer merge:"
    echo "  git add ."
    echo "  git commit -m 'sua mensagem'"
    echo "  # ou"
    echo "  git stash"
    exit 1
fi

# Fetch latest changes
echo -e "${YELLOW}[1/4] Atualizando referências do remote...${NC}"
git fetch origin --quiet
echo -e "${GREEN}✅ Referências atualizadas${NC}"
echo ""

# Checkout main
echo -e "${YELLOW}[2/4] Mudando para branch main...${NC}"
git checkout main
echo -e "${GREEN}✅ Agora em: main${NC}"
echo ""

# Pull latest main
echo -e "${YELLOW}[3/4] Baixando últimas mudanças da main...${NC}"
git pull origin main --quiet || true
echo -e "${GREEN}✅ Main atualizada${NC}"
echo ""

# Show merge preview
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📊 Preview do Merge${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Branch source: $BRANCH_NAME"
echo "Branch target: main"
echo ""
echo "Commits que serão mergeados:"
git log --oneline main.."$BRANCH_NAME" | cat
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Ask for confirmation
read -p "Deseja continuar com o merge? (y/N) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}❌ Merge cancelado${NC}"
    git checkout "$CURRENT_BRANCH"
    exit 0
fi

echo ""

# Merge
echo -e "${YELLOW}[4/4] Fazendo merge...${NC}"
if ! git merge "$BRANCH_NAME" --no-edit; then
    echo ""
    echo -e "${RED}❌ Conflitos de merge detectados!${NC}"
    echo ""
    echo "Resolva os conflitos manualmente, depois:"
    echo "  git add <arquivos-resolvidos>"
    echo "  git commit"
    echo "  git push origin main  # PRE-PUSH HOOK RODARÁ AQUI!"
    exit 1
fi
echo -e "${GREEN}✅ Merge concluído localmente${NC}"
echo ""

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🚀 Pronto para Push${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${GREEN}✅ Branch '$BRANCH_NAME' foi mergeada na main (localmente)${NC}"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANTE: O merge foi feito LOCALMENTE${NC}"
echo -e "${YELLOW}   Você PRECISA fazer push para enviar ao GitHub:${NC}"
echo ""
echo -e "${BLUE}   git push origin main${NC}"
echo ""
echo -e "${BLUE}Quando você fizer push, o PRE-PUSH HOOK rodará:${NC}"
echo "  [1/5] 🐳 Building Docker images..."
echo "  [2/5] 🧪 Running full test suite (make test)"
echo "  [3/5] 🎭 Running E2E tests (make test-e2e)"
echo "  [4/5] 📦 Pushing images to GHCR"
echo "  [5/5] 📋 Summary"
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}Deseja fazer push agora? (y/N)${NC} "
read -p "" -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "${YELLOW}Fazendo push para main (pre-push hook rodará)...${NC}"
    echo ""
    git push origin main
else
    echo ""
    echo -e "${YELLOW}Push não executado. Quando estiver pronto, execute:${NC}"
    echo "  git push origin main"
    echo ""
fi
