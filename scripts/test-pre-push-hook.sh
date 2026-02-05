#!/bin/bash
#
# Script de Teste do Pre-Push Hook
# Verifica se o hook está configurado e funcionando corretamente
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}🔍 Diagnóstico do Pre-Push Hook${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# ========================================================================
# Check 1: Git Hooks Path
# ========================================================================
echo -e "${YELLOW}[1/5] Verificando configuração do Git...${NC}"
HOOKS_PATH=$(git config core.hooksPath)
if [ "$HOOKS_PATH" == ".githooks" ]; then
    echo -e "${GREEN}  ✅ Git hooks path configurado corretamente: $HOOKS_PATH${NC}"
else
    echo -e "${RED}  ❌ Git hooks path não configurado!${NC}"
    echo -e "${YELLOW}     Configurando agora...${NC}"
    git config core.hooksPath .githooks
    echo -e "${GREEN}  ✅ Configurado: .githooks${NC}"
fi
echo ""

# ========================================================================
# Check 2: Hook File Exists
# ========================================================================
echo -e "${YELLOW}[2/5] Verificando existência do hook...${NC}"
if [ -f .githooks/pre-push ]; then
    echo -e "${GREEN}  ✅ Hook existe: .githooks/pre-push${NC}"
else
    echo -e "${RED}  ❌ Hook não encontrado!${NC}"
    exit 1
fi
echo ""

# ========================================================================
# Check 3: Hook is Executable
# ========================================================================
echo -e "${YELLOW}[3/5] Verificando permissões do hook...${NC}"
if [ -x .githooks/pre-push ]; then
    echo -e "${GREEN}  ✅ Hook tem permissão de execução${NC}"
else
    echo -e "${RED}  ❌ Hook não tem permissão de execução!${NC}"
    echo -e "${YELLOW}     Adicionando permissão...${NC}"
    chmod +x .githooks/pre-push
    echo -e "${GREEN}  ✅ Permissão adicionada${NC}"
fi
echo ""

# ========================================================================
# Check 4: Current Branch
# ========================================================================
echo -e "${YELLOW}[4/5] Verificando branch atual...${NC}"
CURRENT_BRANCH=$(git branch --show-current)
echo -e "${BLUE}  Branch atual: $CURRENT_BRANCH${NC}"

if [ "$CURRENT_BRANCH" == "main" ]; then
    echo -e "${YELLOW}  ⚠️  Você está na branch main${NC}"
    echo -e "${BLUE}     Hook rodará quando você fizer: git push origin main${NC}"
else
    echo -e "${BLUE}  ℹ️  Você está em uma feature branch${NC}"
    echo -e "${BLUE}     Hook rodará quando você fizer: git push origin main${NC}"
    echo -e "${BLUE}     Ou quando fizer: git push origin $CURRENT_BRANCH:main${NC}"
fi
echo ""

# ========================================================================
# Check 5: Test Hook (Dry Run)
# ========================================================================
echo -e "${YELLOW}[5/5] Testando hook com dry-run...${NC}"
echo -e "${BLUE}  Executando: git push origin HEAD:refs/heads/main --dry-run${NC}"
echo ""

# Create temporary hook wrapper to detect if it runs
HOOK_WRAPPER_FILE="/tmp/pre-push-hook-test-marker-$$"
cat > "$HOOK_WRAPPER_FILE" << 'WRAPPER_EOF'
#!/bin/bash
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "✅ PRE-PUSH HOOK FOI DISPARADO!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "O hook completo rodaria as seguintes etapas:"
echo "  [1/5] 🐳 Building Docker images..."
echo "  [2/5] 🧪 Running full test suite (make test)"
echo "  [3/5] 🎭 Running E2E tests (make test-e2e)"
echo "  [4/5] 📦 Pushing images to GHCR"
echo "  [5/5] 📋 Summary"
echo ""
echo "Pulando execução completa para este teste de diagnóstico..."
echo "═══════════════════════════════════════════════════════════════"
echo ""
exit 0
WRAPPER_EOF
chmod +x "$HOOK_WRAPPER_FILE"

# Backup original hook
cp .githooks/pre-push .githooks/pre-push.backup

# Use wrapper
cp "$HOOK_WRAPPER_FILE" .githooks/pre-push

# Test push to main (dry-run)
if git push origin HEAD:refs/heads/main --dry-run 2>&1 | grep -q "PRE-PUSH HOOK FOI DISPARADO"; then
    echo -e "${GREEN}✅ Hook foi disparado corretamente!${NC}"
    HOOK_WORKING=true
else
    echo -e "${RED}❌ Hook NÃO foi disparado!${NC}"
    HOOK_WORKING=false
fi

# Restore original hook
mv .githooks/pre-push.backup .githooks/pre-push

# Clean up
rm -f "$HOOK_WRAPPER_FILE"

echo ""

# ========================================================================
# Summary
# ========================================================================
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}📋 Resumo${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""

if [ "$HOOK_WORKING" = true ]; then
    echo -e "${GREEN}✅ Pre-push hook está funcionando corretamente!${NC}"
    echo ""
    echo -e "${BLUE}Quando você fizer push para main:${NC}"
    echo -e "  1. Docker images serão buildadas"
    echo -e "  2. Testes unitários rodarão (make test)"
    echo -e "  3. Testes E2E rodarão (make test-e2e)"
    echo -e "  4. Images serão enviadas para GHCR"
    echo -e "  5. Push para main será permitido"
    echo ""
    echo -e "${BLUE}Para testar de verdade:${NC}"
    echo -e "  git push origin main"
    echo ""
else
    echo -e "${RED}❌ Problema detectado!${NC}"
    echo ""
    echo -e "${YELLOW}Tente estas soluções:${NC}"
    echo -e "  1. Verifique se você tem permissão para fazer push para main"
    echo -e "  2. Verifique se o remote 'origin' está configurado:"
    echo -e "     git remote -v"
    echo -e "  3. Tente configurar novamente:"
    echo -e "     git config core.hooksPath .githooks"
    echo -e "     chmod +x .githooks/pre-push"
    echo ""
fi

echo -e "${BLUE}Para mais detalhes, consulte:${NC}"
echo -e "  docs/testing-pre-push-hook.md"
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
