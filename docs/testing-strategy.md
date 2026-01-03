# Estratégia de Testes - synth-lab

## Objetivo
Prevenir regressões chegando em produção através de testes em múltiplas camadas.

## Camadas de Testes

### 🟢 Camada 1: Pre-Push (Local - 10-15s)
**Roda:** Antes de `git push` (na sua máquina)
**Ferramentas:** Git hooks ou pre-commit
**Objetivo:** Feedback imediato, bloqueia commits ruins

```bash
# Executado automaticamente antes de push
pytest -m smoke      # 5s  - Health checks básicos
pytest -m contract   # 10s - Schemas de API
```

**Configura:**
```bash
# Opção 1: Git hook manual
cp .git/hooks/pre-push.sample .git/hooks/pre-push
chmod +x .git/hooks/pre-push

# Opção 2: pre-commit framework (recomendado)
pip install pre-commit
pre-commit install --hook-type pre-push
```

---

### 🟡 Camada 2: CI no Push (GitHub - 1-2min)
**Roda:** Quando você faz `git push` (servidores do GitHub)
**Ferramentas:** GitHub Actions
**Objetivo:** Validação completa antes de merge

```yaml
# .github/workflows/ci-push.yml
# Roda automaticamente a cada push
- Smoke tests
- Contract tests
- Schema validation tests
- Unit tests críticos
```

---

### 🟠 Camada 3: CI no PR (GitHub - 2-5min)
**Roda:** Quando você abre Pull Request (servidores do GitHub)
**Ferramentas:** GitHub Actions
**Objetivo:** Validação profunda antes de merge

```yaml
# .github/workflows/ci-pr.yml
# Roda automaticamente em PRs
- Todos os testes da Camada 2
- Integration tests completos
- Migration tests
- Coverage report
```

---

### 🔴 Camada 4: Nightly/Manual (GitHub - 10-20min)
**Roda:** Todo dia às 2am OU manualmente (servidores do GitHub)
**Ferramentas:** GitHub Actions + Playwright
**Objetivo:** Testes pesados de regressão

```yaml
# .github/workflows/nightly.yml
# Roda agendado (cron) ou manual
- Todos os testes anteriores
- E2E tests com Playwright
- Performance tests
- Load tests
```

---

## Detecção de Problemas Específicos

### Problema: "Mudança de schema DB quebra código"

**Solução: Schema Validation Tests**
```python
# tests/schema/test_db_schema_validation.py
# Roda na Camada 2 (CI no push)

def test_experiment_table_schema():
    """Se alguém mudou tipo de coluna sem migration, FALHA aqui."""
    inspector = inspect(engine)
    columns = inspector.get_columns('experiments')

    # Valida que schema DB == esperado pelo código
    assert columns['status']['type'] == String
    # ❌ Se mudou pra Enum sem migration, quebra!
```

**Solução: Migration Tests**
```python
# tests/schema/test_migrations.py
# Roda na Camada 2 (CI no push)

def test_model_matches_migration_head():
    """Se mudou model sem criar migration, FALHA aqui."""
    diff = compare_metadata(context, Base.metadata)
    assert not diff, "Crie migration: alembic revision --autogenerate"
```

---

### Problema: "Mudança de API quebra frontend"

**Solução: Contract Tests**
```python
# tests/contract/test_api_contracts.py
# Roda na Camada 1 (pre-push) e Camada 2 (CI)

def test_list_experiments_contract():
    """Se API mudou schema que frontend espera, FALHA aqui."""
    response = client.get("/api/experiments")
    exp = response.json()[0]

    # Campos que frontend SEMPRE espera
    assert "id" in exp
    assert "status" in exp
    assert exp["status"] in ["draft", "running", "completed"]
    # ❌ Se mudou valores possíveis, quebra!
```

---

### Problema: "Feature quebra fluxo existente"

**Solução: Integration Tests**
```python
# tests/integration/test_experiment_lifecycle.py
# Roda na Camada 3 (CI no PR)

def test_create_experiment_full_flow():
    """Testa fluxo completo: criar → gerar avatares → analisar."""
    # Se alguma mudança quebrou o fluxo, FALHA aqui
```

**Solução: E2E Tests**
```typescript
// tests/e2e/experiment-workflow.spec.ts
// Roda na Camada 4 (nightly)

test('usuário consegue criar e analisar experimento', async ({ page }) => {
  // Simula usuário real fazendo o fluxo completo
  // Se algo quebrou na UI, FALHA aqui
});
```

---

## Fluxo Completo

```
Desenvolvedor faz mudança
         ↓
git add . && git commit -m "..."
         ↓
git push
         ↓
╔════════════════════════════════╗
║ PRE-PUSH HOOK (LOCAL - 15s)   ║  ← Você vê resultado NA HORA
║ ✓ Smoke tests                 ║
║ ✓ Contract tests              ║
╚════════════════════════════════╝
         ↓ (se passar)
    Push vai pro GitHub
         ↓
╔════════════════════════════════╗
║ CI PUSH (GitHub - 2min)       ║  ← Vê no GitHub em 2min
║ ✓ Todos pre-push              ║
║ ✓ Schema validation           ║
║ ✓ Unit tests                  ║
╚════════════════════════════════╝
         ↓ (se passar)
    Abre Pull Request
         ↓
╔════════════════════════════════╗
║ CI PR (GitHub - 5min)         ║  ← Vê no PR antes de merge
║ ✓ Todos anteriores            ║
║ ✓ Integration tests           ║
║ ✓ Coverage report             ║
╚════════════════════════════════╝
         ↓ (se passar)
    Merge para main
         ↓
    Deploy para staging/prod
         ↓
╔════════════════════════════════╗
║ NIGHTLY (GitHub - 20min)      ║  ← Roda toda noite
║ ✓ Todos anteriores            ║
║ ✓ E2E tests                   ║
║ ✓ Performance tests           ║
╚════════════════════════════════╝
```

---

## Configuração Inicial

### 1. Markers do pytest
```ini
# pytest.ini
[pytest]
markers =
    smoke: Testes muito rápidos de health check (5s)
    contract: Testes de contrato de API (10s)
    schema: Validação de schema DB vs models (15s)
    integration: Testes de integração completos (1-5min)
    e2e: Testes end-to-end com browser (5-20min)
    slow: Marca testes lentos
```

### 2. Pre-commit (local)
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: tests-fast
        name: Fast Tests (smoke + contract)
        entry: bash -c 'pytest -m "smoke or contract" --maxfail=5 -q'
        language: system
        pass_filenames: false
        stages: [push]
```

Instalar: `pre-commit install --hook-type pre-push`

### 3. GitHub Actions
Ver arquivos em `.github/workflows/`

---

## Comandos Úteis

```bash
# Rodar localmente os mesmos testes do pre-push
pytest -m "smoke or contract"

# Rodar testes de schema
pytest -m schema

# Rodar todos os testes rápidos (<30s)
pytest -m "smoke or contract or schema"

# Rodar integration tests (como no CI)
pytest -m integration

# Rodar tudo (como nightly)
pytest

# Pular pre-push hook (emergência)
git push --no-verify
```

---

## Métricas de Sucesso

- ✅ 0 regressões chegando em prod sem serem detectadas
- ✅ Feedback em <15s localmente
- ✅ Feedback em <2min no CI
- ✅ 80%+ de cobertura em código crítico
- ✅ Desenvolvedores conseguem iterar rapidamente
