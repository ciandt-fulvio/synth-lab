# PostgreSQL Test Database Setup

Este documento explica como configurar e usar o banco PostgreSQL de testes para synth-lab.

## 📋 Visão Geral

O banco de testes usa **Alembic migrations** (não `create_all()`) para garantir que:
- ✅ Schema de testes = schema de produção
- ✅ Testes de migration detectam mudanças não migradas
- ✅ Testes de concorrência rodam com PostgreSQL real
- ✅ Dados de teste realistas via seed

---

## 🚀 Setup Inicial

### 1. Configurar Variável de Ambiente

Adicione ao seu `.env`:

```bash
DATABASE_TEST_URL=postgresql://synthlab:synthlab@localhost:5432/synthlab_test
```

> **IMPORTANTE**: O banco DEVE ter `test` no nome para segurança!

### 2. Criar e Migrar o Banco de Teste

Execute o script de setup:

```bash
# Criar banco limpo com migrations
uv run python scripts/setup_test_db.py --reset

# Com dados de seed (opcional)
uv run python scripts/setup_test_db.py --reset --seed
```

**O que este script faz:**
1. ❌ Dropa o banco `synthlab_test` (se existir)
2. ✅ Cria um banco novo vazio
3. ✅ Aplica todas as Alembic migrations
4. ✅ Opcionalmente popula com dados de teste (--seed)

---

## 🧪 Rodando Testes

### Todos os Testes

```bash
pytest tests/
```

### Apenas Testes que Usam PostgreSQL

```bash
# Testes de concorrência
pytest tests/integration/test_concurrent_operations.py -v

# Testes de migrations
pytest tests/schema/test_migrations.py -v
```

### Apenas Testes de Contract/Smoke

```bash
pytest tests/smoke/ tests/contract/ -v
```

---

## 📦 Fixtures Disponíveis

### `migrated_db_engine` (session scope)

Engine do PostgreSQL com migrations aplicadas.

```python
def test_something(migrated_db_engine):
    # Engine já tem schema do Alembic
    # Não usa create_all()
    pass
```

### `db_session` (function scope)

Sessão limpa para cada teste com rollback automático.

```python
def test_with_db(db_session):
    # Sessão isolada via SAVEPOINT
    # Mudanças são revertidas após o teste
    db_session.add(Experiment(...))
    db_session.commit()
```

### `seeded_db_session` (function scope)

Sessão com dados de teste pré-carregados.

```python
def test_with_data(seeded_db_session):
    # Dados de seed já estão no banco
    # 3 experiments, 2 synth groups, etc.
    experiments = seeded_db_session.query(Experiment).all()
    assert len(experiments) == 3
```

---

## 🌱 Dados de Seed

O arquivo `tests/fixtures/seed_test.py` cria:

| Entidade | Quantidade | IDs |
|----------|-----------|-----|
| Experiments | 3 | `exp_test_001`, `exp_test_002`, `exp_test_003` |
| Synth Groups | 2 | `grp_test_001`, `grp_test_002` |
| Synths | 3 | `syn_test_001`, `syn_test_002`, `syn_test_003` |
| Research Executions | 2 | `batch_exp_...` |
| Explorations | 1 | `expl_test_001` |
| Documents | 2 | `doc_test_001`, `doc_test_002` |

**Usar seed em testes:**

```python
def test_list_experiments(seeded_db_session):
    # Usa fixture seeded_db_session
    service = ExperimentService(session=seeded_db_session)
    result = service.list_experiments()
    assert result.pagination.total == 3  # Seed criou 3 experiments
```

---

## 🔄 Workflow de Desenvolvimento

### Quando Modificar Models

1. **Alterar o model** (ex: adicionar coluna)
2. **Criar migration**:
   ```bash
   source .env
   DATABASE_URL=$DATABASE_TEST_URL alembic -c src/synth_lab/alembic/alembic.ini \
     revision --autogenerate -m "Add new column"
   ```
3. **Aplicar ao banco de teste**:
   ```bash
   uv run python scripts/setup_test_db.py --reset
   ```
4. **Aplicar ao banco principal**:
   ```bash
   alembic -c src/synth_lab/alembic/alembic.ini upgrade head
   ```
5. **Rodar testes**:
   ```bash
   pytest tests/
   ```

### Quando Testes de Migration Falharem

```
❌ Database migrations out of date!
Run: uv run python scripts/setup_test_db.py --reset
```

**Solução:**
```bash
uv run python scripts/setup_test_db.py --reset
pytest tests/schema/test_migrations.py -v
```

---

## 🛡️ Segurança

### Checks Automáticos

- ✅ Fixture `postgres_test_url` só aceita URLs com `test` no nome
- ✅ Script `setup_test_db.py` verifica `DATABASE_TEST_URL`
- ✅ Banco de teste é SEMPRE separado do desenvolvimento

### Nunca Use

❌ `DATABASE_URL` para testes
❌ Banco `synthlab` (sem _test)
❌ `Base.metadata.create_all()` em testes de integration

---

## 🐛 Troubleshooting

### Erro: "DATABASE_TEST_URL not set"

```bash
echo "DATABASE_TEST_URL=postgresql://synthlab:synthlab@localhost:5432/synthlab_test" >> .env
```

### Erro: "relation already exists"

O banco tem schema antigo. Reset:

```bash
uv run python scripts/setup_test_db.py --reset
```

### Erro: "Models divergem do DB"

Você mudou um model sem criar migration:

```bash
source .env
DATABASE_URL=$DATABASE_TEST_URL alembic -c src/synth_lab/alembic/alembic.ini \
  revision --autogenerate -m "Fix model changes"
uv run python scripts/setup_test_db.py --reset
```

### PostgreSQL não está rodando

```bash
# Verificar se está rodando
docker ps | grep postgres

# Iniciar se necessário
docker compose up -d postgres
```

---

## 📚 Referências

- **Alembic**: https://alembic.sqlalchemy.org/
- **SQLAlchemy Testing**: https://docs.sqlalchemy.org/en/20/orm/session_transaction.html
- **Pytest Fixtures**: https://docs.pytest.org/en/stable/fixture.html
