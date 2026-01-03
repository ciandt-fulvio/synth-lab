# Auto-Update Tests

## Como Funciona

Após commit que modifica routers/models/services, git hook pergunta se quer gerar testes automaticamente.

```bash
git commit -m "Add new endpoint"

# Hook detecta mudança:
🤖 Arquivos modificados: src/synth_lab/api/routers/experiments.py
   Quer gerar contract tests automaticamente?

   1) Sim, executar agora (interativo)
   2) Sim, executar e auto-commit
   3) Não

Escolha (1/2/3):
```

## Opções

### 1. Interativo (Recomendado)

- Claude Code gera o teste
- Script valida que passa
- **Você revisa e commita manualmente**

```bash
Escolha: 1

🤖 Gerando contract test para 'experiments' router...
✅ Teste criado
✅ Validação passou (make test-fast)

# Você revisa
git diff tests/contract/test_api_contracts.py

# Você commita
git add tests/contract/
git commit -m "test: add contract test for experiments"
```

### 2. Auto-commit

- Tudo automático
- Commita se testes passarem

```bash
Escolha: 2

🤖 Gerando teste...
✅ Criado e commitado automaticamente
```

### 3. Manual

```bash
Escolha: 3

# Gera depois
./scripts/auto-update-tests.sh --last-commit
```

## Uso Manual

```bash
# Analisa gaps de cobertura
make test-coverage-analysis

# Gera teste para último commit
./scripts/auto-update-tests.sh --last-commit

# Gera teste para arquivo específico
./scripts/auto-update-tests.sh --file src/synth_lab/api/routers/experiments.py

# Ver o que seria feito (dry-run)
./scripts/auto-update-tests.sh --last-commit --dry-run
```

## Análise Automática Semanal

GitHub Actions roda análise de gaps toda segunda/quarta/sexta às 9am:

- Cria/atualiza issue com gaps de cobertura
- Issue tem comandos Claude Code prontos para copiar
- Ver: `.github/workflows/test-coverage-analysis.yml`

## Desabilitar

```bash
# Desabilita hook temporariamente
git commit --no-verify

# Desabilita permanentemente
rm .githooks/post-commit
```
