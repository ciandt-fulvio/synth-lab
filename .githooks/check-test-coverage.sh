#!/bin/bash
#
# Verifica se mudanças precisam de novos testes
# Roda em pre-commit para alertar desenvolvedor
#

# Arquivos staged
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM)

# Flags para alertas
NEEDS_CONTRACT_TEST=false
NEEDS_SCHEMA_TEST=false
NEEDS_INTEGRATION_TEST=false

# Verifica se mudou routers (precisa contract test)
if echo "$STAGED_FILES" | grep -q "src/synth_lab/api/routers/.*\.py"; then
    NEEDS_CONTRACT_TEST=true
fi

# Verifica se mudou ORM models (precisa schema test)
if echo "$STAGED_FILES" | grep -q "src/synth_lab/models/orm/.*\.py"; then
    NEEDS_SCHEMA_TEST=true
fi

# Verifica se mudou services críticos (precisa integration test)
if echo "$STAGED_FILES" | grep -q "src/synth_lab/services/.*service\.py"; then
    NEEDS_INTEGRATION_TEST=true
fi

# Exibe alertas
if [ "$NEEDS_CONTRACT_TEST" = true ] || [ "$NEEDS_SCHEMA_TEST" = true ] || [ "$NEEDS_INTEGRATION_TEST" = true ]; then
    echo ""
    echo "⚠️  ATENÇÃO: Você pode precisar atualizar testes!"
    echo ""

    if [ "$NEEDS_CONTRACT_TEST" = true ]; then
        echo "  📝 Router mudou → Considere atualizar tests/contract/test_api_contracts.py"
        echo "     Comando: claude code --prompt 'Atualizar contract tests para os routers modificados'"
    fi

    if [ "$NEEDS_SCHEMA_TEST" = true ]; then
        echo "  📝 ORM model mudou → Rode: make test-fast (schema validation)"
        echo "     Se schema test falhar: alembic revision --autogenerate"
    fi

    if [ "$NEEDS_INTEGRATION_TEST" = true ]; then
        echo "  📝 Service mudou → Considere adicionar integration test"
        echo "     Comando: claude code --prompt 'Criar integration test para os services modificados'"
    fi

    echo ""
    echo "  💡 Dica: Use 'claude code' para gerar testes automaticamente"
    echo ""
fi

# Não bloqueia commit, apenas alerta
exit 0
