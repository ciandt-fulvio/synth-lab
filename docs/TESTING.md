# Guia de Testes - Synth Lab

**Objetivo:** Prevenir regressões em produção com feedback rápido.

## Rodando Testes

```bash
# Testes rápidos (~30s) - Rode antes de cada commit
make test-fast

# Todos os testes backend
pytest

# Testes E2E (frontend)
make test-e2e
```

## Tipos de Testes

### 1. Smoke Tests (5s) - Sistema está saudável?

**Quando usar:** Sempre, antes de qualquer outro teste.

**O que valida:**
- Database conecta
- Variáveis de ambiente configuradas (OPENAI_API_KEY)
- Imports críticos funcionam

**Exemplo:**
```python
# tests/smoke/test_critical_health.py
def test_database_connection():
    """Falha se DB não está acessível."""
    engine = create_db_engine()
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar() == 1
```

### 2. Contract Tests (10s) - API mantém promessas?

**Quando usar:** Sempre que criar/modificar endpoint.

**O que valida:**
- Response tem campos esperados pelo frontend
- Tipos de dados corretos (string, number, array)
- Valores válidos (enums, status codes)

**Exemplo:**
```python
# tests/contract/test_api_contracts.py
def test_experiment_list_contract(client):
    """Frontend espera { data: [...], meta: {...} }"""
    response = client.get("/experiments/list")

    assert response.status_code == 200
    body = response.json()

    # Estrutura esperada
    assert "data" in body
    assert "meta" in body

    # Cada experimento tem campos obrigatórios
    for exp in body["data"]:
        assert "id" in exp
        assert "name" in exp
        assert "status" in exp
        assert isinstance(exp["status"], str)  # Não mude para int!
```

**Quando criar:**
- ✅ Novo endpoint público
- ✅ Modificou response de endpoint existente
- ❌ Endpoint interno/privado

### 3. Schema Tests (15s) - DB sincronizado com código?

**Quando usar:** Sempre que modificar models SQLAlchemy.

**O que valida:**
- Tabelas existem para todos os models
- Tipos de colunas batem
- Constraints batem (NOT NULL, FK)
- Migration foi criada

**Exemplo:**
```python
# tests/schema/test_db_schema_validation.py
def test_experiments_table():
    """Falha se mudou model sem criar migration."""
    inspector = inspect(engine)
    columns = {c["name"]: c for c in inspector.get_columns("experiments")}

    # Valida colunas esperadas
    assert "id" in columns
    assert "name" in columns
    assert columns["name"]["nullable"] == False
```

**Quando criar:**
- ✅ Sempre que adicionar novo model
- ✅ Sempre que modificar campos de model existente
- ❌ Não precisa criar manualmente - já existe validação genérica

### 4. Integration Tests (2-5min) - Fluxos completos funcionam?

**Quando usar:** Fluxos críticos de negócio.

**O que valida:**
- API → Service → Repository → DB
- Dados salvos corretamente
- Side effects funcionam (webhooks, emails, etc)

**Exemplo:**
```python
# tests/integration/test_experiment_workflow.py
def test_create_experiment_flow(client, db_session):
    """Cria experimento e valida que salvou no DB."""

    # 1. Cria via API
    response = client.post("/experiments", json={
        "name": "Test Exp",
        "hypothesis": "Users will click more"
    })
    exp_id = response.json()["id"]

    # 2. Valida que salvou no DB
    exp = db_session.query(Experiment).filter_by(id=exp_id).first()
    assert exp is not None
    assert exp.name == "Test Exp"
    assert exp.status == "draft"
```

**Quando criar:**
- ✅ Fluxo crítico de negócio (criar experimento, rodar análise)
- ✅ Operações com side effects
- ❌ Lógica simples (use unit test)

### 5. E2E Tests (10-20min) - UI funciona end-to-end?

**Quando usar:** Fluxos de usuário críticos.

**O que valida:**
- Navegação funciona
- Formulários salvam
- Dados aparecem corretamente
- Integrações funcionam

**Exemplo:**
```typescript
// frontend/tests/e2e/create-experiment.spec.ts
test('create experiment flow', async ({ page }) => {
  // 1. Navega e clica em "Novo"
  await page.goto('/');
  await page.click('text=Novo Experimento');

  // 2. Preenche form
  await page.fill('input[name="name"]', 'E2E Test');
  await page.fill('textarea[name="hypothesis"]', 'Test hypothesis');
  await page.click('button[type="submit"]');

  // 3. Valida redirecionamento
  await expect(page).toHaveURL(/\/experiments\/exp_/);
});
```

**Quando criar:**
- ✅ Fluxo principal (criar experimento, rodar análise)
- ✅ Fluxo que quebra frequentemente
- ❌ Detalhes de UI (use component tests)

## Criando Novos Testes

### Novo Endpoint

```bash
# 1. Crie contract test
vim tests/contract/test_api_contracts.py

# 2. Adicione função
def test_new_endpoint_contract(client):
    response = client.get("/novo-endpoint")
    assert response.status_code == 200
    # Valide schema da response

# 3. Rode
pytest tests/contract/test_api_contracts.py::test_new_endpoint_contract
```

### Novo Model

```bash
# 1. Crie model
vim src/synth_lab/models/orm/new_model.py

# 2. Crie migration (contra dev database)
make db-migrate MSG="Add NewModel"

# 3. Testes de schema validam automaticamente
make test-fast
```

### Novo Fluxo

```bash
# 1. Crie integration test
vim tests/integration/test_new_workflow.py

# 2. Adicione teste
def test_new_workflow(client, db_session):
    # Simule fluxo completo
    pass

# 3. Rode
pytest tests/integration/test_new_workflow.py -v
```

## Checklist Antes de Commitar

```bash
# 1. Rode testes rápidos
make test-fast

# 2. Se mudou model: criou migration?
ls src/synth_lab/alembic/versions/  # Deve ter arquivo novo

# 3. Se mudou API: contract test valida?
pytest -m contract -v

# 4. Push
git push  # Pre-push hook roda testes automaticamente
```

## Servidores de Teste

Alguns testes fazem HTTP requests e **precisam dos servidores rodando**:

- **Contract Tests (OpenAPI)**: `tests/contract/test_openapi_typescript_sync.py`
- **E2E Tests**: `frontend/tests/e2e/`

### Setup (3 Terminais)

**Terminal 1 - Backend de Teste:**
```bash
make serve-test
# API rodando em http://localhost:8000
```

**Terminal 2 - Frontend de Teste (apenas para E2E):**
```bash
make serve-front-test
# Frontend rodando em http://localhost:8080
```

**Terminal 3 - Rodar Testes:**
```bash
# E2E tests (precisa backend + frontend)
make test-e2e

# Contract OpenAPI tests (precisa só backend)
pytest tests/contract/test_openapi_typescript_sync.py -v
```

### Por que Portas Diferentes?

- **Dev:** 8000 (backend), 8080 (frontend)
- **Teste:** 8000 (backend), 8080 (frontend)

**Benefício:** Rodar testes enquanto dev servers estão rodando sem conflito.

### Matar Servidores de Teste

```bash
make kill-test-servers
```

---

## Troubleshooting

### "DB não acessível"
```bash
# Inicie PostgreSQL
make db

# Configure test DB
make db-test
```

### "Migration pending"
```bash
# Aplique migrations ao dev database
DATABASE_URL="postgresql://synthlab:synthlab@localhost:5432/synthlab" \
  alembic -c src/synth_lab/alembic/alembic.ini upgrade head

# Ou rode os testes (container de teste aplica automaticamente)
make test-fast
```

### "Schema diverge"
```bash
# Crie migration
alembic revision --autogenerate -m "Descrição"

# Aplique
alembic upgrade head

# Teste
pytest -m schema
```

### "Contract test falhou"
```bash
# Veja o erro
pytest tests/contract/ -v

# Opções:
# 1. Corrige o endpoint
# 2. Atualiza o test se mudança foi intencional
# 3. Atualiza frontend se quebrou contrato
```

## Automação com Claude Code

### Git Hook Automático

Após commit que modifica routers/models/services:

```bash
git commit -m "Add new endpoint"

# Hook post-commit detecta:
🤖 Arquivos modificados: src/synth_lab/api/routers/experiments.py
   Quer gerar contract tests automaticamente?

   1) Sim, executar agora (interativo)    ← Recomendado
   2) Sim, executar e auto-commit
   3) Não

Escolha (1/2/3): 1

# Claude Code gera teste automaticamente
🤖 Gerando contract test...
✅ Teste criado
✅ Validação passou (make test-fast)

# Você revisa e commita
git diff tests/contract/test_api_contracts.py
git add tests/contract/
git commit -m "test: add contract test"
```

### Uso Manual

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

### Análise Semanal Automática

GitHub Actions roda análise de gaps toda segunda/quarta/sexta às 9am:
- Cria/atualiza issue com gaps de cobertura
- Issue tem comandos Claude Code prontos

### Desabilitar

```bash
# Temporariamente
git commit --no-verify

# Permanentemente
rm .githooks/post-commit
```

## Estrutura de Arquivos

```
tests/
├── smoke/          - Health checks (sempre rode primeiro)
├── contract/       - API schemas (crie para cada endpoint público)
├── schema/         - DB validation (automático, não edite)
├── integration/    - Fluxos completos (crie para fluxos críticos)
└── unit/           - Lógica isolada (crie para funções complexas)

frontend/tests/
└── e2e/            - Testes de navegador (crie para fluxos principais)
```

## Comandos Úteis

```bash
# Backend
make test-fast              # Smoke + Contract + Schema (~30s)
pytest -m unit              # Só unit tests
pytest -m integration       # Só integration tests
pytest -m smoke             # Só smoke tests
pytest -k "experiment"      # Testes com "experiment" no nome
pytest --lf                 # Só testes que falharam antes

# Frontend
make test-e2e               # E2E com Playwright
make test-e2e-ui            # E2E em modo UI (visual)
npm run test:e2e:debug      # E2E em modo debug

# Cobertura
make test-coverage-analysis # Vê gaps de cobertura
```
