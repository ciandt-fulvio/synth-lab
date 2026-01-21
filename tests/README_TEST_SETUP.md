# PostgreSQL Test Database Setup

Este documento explica como configurar e usar o banco PostgreSQL de testes para synth-lab.

## 📋 Visão Geral

O banco de testes usa um **container Docker isolado** (porta 5433) para garantir que:
- ✅ Schema de testes = schema de produção (via Alembic migrations)
- ✅ Dados efêmeros (sem persistência entre execuções)
- ✅ Isolamento total do banco de desenvolvimento
- ✅ Testes de concorrência rodam com PostgreSQL real

---

## 🚀 Setup Inicial

### 1. Suba o ambiente de desenvolvimento

```bash
make dev-up
```

### 2. Rode os testes

```bash
make test-fast  # Testes rápidos (~5s)
make test       # Suite completa (~4min)
```

**É só isso!** O Makefile:
1. Sobe o container `postgres-test` (porta 5433)
2. Configura `DATABASE_URL` para o container de teste
3. Aplica migrations automaticamente
4. Roda os testes
5. Para o container ao final

---

## 🧪 Rodando Testes

### Testes Rápidos (Recomendado para Desenvolvimento)

```bash
make test-fast  # smoke + contract + schema (~5s)
```

### Suite Completa

```bash
make test  # Todos os testes (~4min)
```

### Testes Específicos (Manual)

Se precisar rodar testes específicos manualmente:

```bash
# Primeiro, suba o container de teste
make test-db-up

# Rode os testes desejados
DATABASE_URL="postgresql://synthlab_test:synthlab_test@localhost:5433/synthlab_test" \
  uv run pytest tests/integration/test_concurrent_operations.py -v

# Depois, pare o container
make test-db-down
```

---

## 📦 Fixtures Disponíveis

### `migrated_db_engine` (session scope)

Engine do PostgreSQL com migrations aplicadas.

```python
def test_something(migrated_db_engine):
    # Engine já tem schema do Alembic
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
   make db-migrate MSG="Add new column"
   ```
3. **Rodar testes** (migrations são aplicadas automaticamente no container):
   ```bash
   make test-fast
   ```

### Quando Testes de Migration Falharem

O container de teste sempre começa do zero, aplicando todas as migrations. Se houver erro:

```bash
# Verifique se migrations estão corretas
make db-migrate MSG="Fix model changes"

# Rode os testes novamente
make test-fast
```

---

## 🛡️ Segurança

### Checks Automáticos

- ✅ `conftest.py` verifica que `DATABASE_URL` contém "test"
- ✅ Container de teste é efêmero (sem volume persistente)
- ✅ Porta diferente (5433) do dev (5432)

### Nunca Use

❌ Rodar pytest sem `make test` (DATABASE_URL errado)
❌ Container de dev para testes
❌ `Base.metadata.create_all()` em testes de integration

---

## 🐛 Troubleshooting

### Erro: "DATABASE_URL must point to test database"

Você está tentando rodar pytest diretamente. Use o Makefile:

```bash
make test-fast
```

### Erro: "Container not starting"

```bash
# Verificar se Docker/Podman está rodando
docker ps

# Verificar logs
docker logs synthlab-postgres-test

# Forçar limpeza e tentar novamente
make test-db-down
make test-fast
```

### Erro: "relation already exists" ou "Models divergem"

```bash
# Crie a migration faltante
make db-migrate MSG="Fix model changes"

# Rode os testes
make test-fast
```

### PostgreSQL de Dev não está rodando

```bash
# Verificar containers
docker ps

# Iniciar ambiente completo
make dev-up
```

---

## 📚 Referências

- **Auto-setup**: `tests/conftest.py` → `_ensure_test_database_setup`
- **Fixtures**: `tests/conftest.py` → Seção "PostgreSQL Test Database Fixtures"
- **Seed Data**: `tests/fixtures/seed_test.py`
- **Docker Config**: `docker/docker-compose.yml` → `postgres-test` service
- **Alembic**: https://alembic.sqlalchemy.org/
- **SQLAlchemy Testing**: https://docs.sqlalchemy.org/en/20/orm/session_transaction.html
