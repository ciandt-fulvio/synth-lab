# Suíte de Testes - Synth Lab

## 🎯 Objetivo

Prevenir regressões chegando em produção através de testes em múltiplas camadas executados em diferentes momentos do desenvolvimento.

## 📁 Estrutura de Testes

```
tests/
├── smoke/                      # ⚡ 5s - Health checks críticos
│   └── test_critical_health.py
├── contract/                   # ⚡ 10s - Schemas de API
│   └── test_api_contracts.py
├── schema/                     # ⚡ 15s - Validação DB vs Models
│   ├── test_db_schema_validation.py
│   └── test_migrations.py
├── integration/                # 🟡 2-5min - Fluxos completos
│   ├── api/
│   └── repositories/
└── unit/                       # ⚡ <1min - Lógica isolada
    ├── gen_synth/
    ├── simulation/
    └── services/

frontend/tests/
├── e2e/                        # 🔴 10-20min - Testes de navegador
│   └── experiment-list.spec.ts
└── unit/                       # ⚡ <30s - Componentes/hooks
    └── ...
```

## 🚀 Rodando Testes

### Testes Rápidos (Localmente antes de commit)

```bash
# Smoke tests - Verifica que sistema está saudável
pytest -m smoke

# Contract tests - Valida schemas da API
pytest -m contract

# Schema validation - Detecta mudanças de DB sem migration
pytest -m schema

# Todos os testes rápidos (<30s)
pytest -m "smoke or contract or schema"
```

### Testes Completos

```bash
# Todos os testes backend
pytest

# Com coverage
pytest --cov=src/synth_lab --cov-report=html

# E2E tests (frontend)
cd frontend && npx playwright test
```

### Por Categoria

```bash
pytest -m unit          # Unit tests
pytest -m integration   # Integration tests
pytest -m e2e          # E2E tests (Playwright)
pytest -m slow         # Testes lentos
```

## 🔄 Fluxo de CI/CD

### Local (Pre-push Hook)

Quando você faz `git push`, automaticamente executa:

```
✓ Smoke tests (5s)
✓ Contract tests (10s)
✓ Schema validation (15s)
──────────────────────
Total: ~30s
```

**Já está configurado!** O projeto usa `.githooks/pre-push`

**Testar manualmente:**

```bash
make test-fast
```

**Pular (emergência):**

```bash
git push --no-verify
```

### GitHub Actions - Fast Tests (Todo push)

Executa em ~2min:

```
✓ Smoke tests
✓ Contract tests
✓ Schema validation
✓ Setup PostgreSQL
✓ Rodas migrations
```

**Arquivo:** `.github/workflows/tests-fast.yml`

### GitHub Actions - PR Tests (Pull Requests)

Executa em ~5min:

```
✓ Todos os fast tests
✓ Integration tests
✓ Coverage report
```

**Arquivo:** `.github/workflows/tests-pr.yml`

### GitHub Actions - Nightly (Diário às 2am)

Executa em ~20min:

```
✓ Todos os testes anteriores
✓ E2E tests com Playwright
✓ Performance tests (futuro)
```

**Arquivo:** `.github/workflows/tests-nightly.yml`

## 📋 Tipos de Testes

### 1. Smoke Tests (🟢 Crítico)

**O que testa:** Sistema está saudável para rodar.

```python
# tests/smoke/test_critical_health.py
- DB está acessível
- OPENAI_API_KEY configurada
- Imports críticos funcionam
- Diretórios de dados existem
```

**Quando falha:**

- Alguém quebrou configuração básica
- DB não está rodando
- Variáveis de ambiente faltando

### 2. Contract Tests (🟢 Crítico)

**O que testa:** API mantém schemas esperados pelo frontend.

```python
# tests/contract/test_api_contracts.py
- GET /api/experiments retorna { experiments: [...], meta: {...} }
- Campos obrigatórios presentes (id, name, status, created_at)
- Tipos corretos (status é string, não enum)
- Valores válidos (status in ["draft", "running", ...])
```

**Quando falha:**

- Alguém mudou resposta da API sem avisar frontend
- Removeu campo que frontend espera
- Mudou tipo de campo (string → number)

**Exemplo de breaking change detectado:**

```python
# Antes
{"status": "completed"}  ✓ Frontend funciona

# Alguém muda para enum
{"status": 1}  ✗ Contract test FALHA
                  Frontend quebra!
```

### 3. Schema Validation Tests (🟢 Crítico)

**O que testa:** DB schema sincronizado com SQLAlchemy models.

```python
# tests/schema/test_db_schema_validation.py
- Tabelas existem para todos os models
- Tipos de colunas batem (String, Integer, JSONB)
- Constraints batem (NOT NULL, FK)
- Nenhuma tabela órfã
```

**Quando falha:**

```python
# Cenário 1: Mudou model sem migration
class Experiment(Base):
    status = Column(Enum(...))  # Mudou de String → Enum

# ❌ FALHA: "experiments.status deve ser String, falta migration!"
# SOLUÇÃO: alembic revision --autogenerate
```

```python
# Cenário 2: DB desatualizado
# ❌ FALHA: "Tabela 'explorations' não existe"
# SOLUÇÃO: alembic upgrade head
```

### 4. Migration Tests (🟢 Crítico)

**O que testa:** Migrations do Alembic estão corretas.

```python
# tests/schema/test_migrations.py
- Models sincronizados com migration head
- DB está na versão correta (alembic_version)
- Nenhuma mudança pendente
```

**Quando falha:**

```
❌ FALHA: Models divergem do DB! 3 mudança(s) detectada(s)
  - Added column 'experiments.new_field'
  - Modified type of 'synths.age' (Integer → String)
  - Removed column 'analysis.old_field'

AÇÃO: alembic revision --autogenerate -m "Descrição"
```

### 5. Integration Tests (🟡 Importante)

**O que testa:** Fluxos completos através da API.

```python
# tests/integration/test_experiment_flows.py
- Criar experimento → Gerar avatares → Verificar DB
- Rodar simulação → Calcular análise → Gerar insights
- Upload documento → Processar → Salvar metadados
```

### 6. E2E Tests (🔴 Regressão)

**O que testa:** Fluxos de usuário no navegador.

```typescript
// frontend/tests/e2e/experiment-workflow.spec.ts
- Navegar para / → Ver lista de experimentos
- Clicar em experimento → Ver detalhes
- Criar novo experimento → Preencher form → Salvar
- Ver análise → Gerar insights → Ver resultados
```

## 🐛 Problemas Detectados

### Problema 1: "Funcionou local mas quebrou em prod"

**Causa:** Schema de DB diferente entre local e prod.

**Detectado por:**

- ✅ Schema Validation Tests
- ✅ Migration Tests

**Exemplo:**

```
Local: ALTER TABLE experiments ADD COLUMN new_field (migration aplicada)
Prod:  Tabela sem new_field (migration não aplicada)

❌ Schema test FALHA: "experiments.new_field não existe"
🛠️ SOLUÇÃO: alembic upgrade head em prod
```

### Problema 2: "API mudou e frontend quebrou"

**Causa:** Mudança de schema da API sem atualizar frontend.

**Detectado por:**

- ✅ Contract Tests

**Exemplo:**

```javascript
// Frontend espera
exp.status === "completed"  // String

// Backend mudou para
exp.status === 1  // Enum number

❌ Contract test FALHA: "status deve ser string"
🛠️ SOLUÇÃO: Manter string OU atualizar frontend
```

### Problema 3: "Feature quebrou fluxo existente"

**Causa:** Nova feature introduziu bug em fluxo antigo.

**Detectado por:**

- ✅ Integration Tests
- ✅ E2E Tests

## 📊 Cobertura Esperada

| Camada                      | Alvo   | Status Atual |
| --------------------------- | ------ | ------------ |
| Smoke tests                 | 100%   | ✅ 100%      |
| Contract tests (endpoints)  | 80%    | 🟡 30%       |
| Schema validation           | 100%   | ✅ 100%      |
| Integration tests (backend) | 70%    | 🟡 40%       |
| Unit tests (backend)        | 60%    | ✅ 65%       |
| E2E tests (frontend)        | 50%    | ⚠️ 5%        |
| Frontend unit tests         | 60%    | ⚠️ 10%       |

## ✅ Checklist de Novo Código

Antes de fazer PR, verifique:

- [ ] Testes locais passam: `pytest -m "smoke or contract or schema"`
- [ ] Se mudou model: Criou migration (`alembic revision --autogenerate`)
- [ ] Se mudou API: Contract tests validam novos campos
- [ ] Se novo endpoint crítico: Criou contract test
- [ ] Se novo fluxo crítico: Criou integration test
- [ ] CI passou (green check no GitHub)

## 🔧 Troubleshooting

### Pre-commit hook não roda

```bash
pre-commit install --hook-type pre-push
```

### Testes falham com "DB não acessível"

```bash
# Verifique se PostgreSQL está rodando
psql $DATABASE_URL -c "SELECT 1"

# Configure DATABASE_URL
export DATABASE_URL="postgresql://user:pass@localhost:5432/synthlab_test"
```

### Testes falham com "Migration pending"

```bash
cd src/synth_lab/alembic
alembic upgrade head
```

### Schema tests falham após mudar model

```bash
# Crie a migration
alembic revision --autogenerate -m "Add new_field to experiments"

# Aplique
alembic upgrade head

# Rode tests novamente
pytest -m schema
```

## 📖 Documentação Adicional

- [Estratégia de Testes](../docs/testing-strategy.md) - Visão geral completa
- [pytest markers](../pytest.ini) - Markers disponíveis
- [Pre-commit config](../.pre-commit-config.yaml) - Configuração de hooks
- [GitHub Actions](../.github/workflows/) - CI/CD workflows

## 🎓 Boas Práticas

1. **Rode testes rápidos frequentemente** - `pytest -m smoke` antes de cada commit
2. **Não pule pre-commit hooks** - Eles existem para te proteger
3. **CI falhou? Não ignore** - Investigue e corrija antes de merge
4. **Criou migration? Teste localmente** - `alembic upgrade head && pytest -m schema`
5. **Mudou API? Valide contrato** - `pytest -m contract`
