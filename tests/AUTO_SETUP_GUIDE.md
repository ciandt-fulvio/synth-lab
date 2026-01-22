# 🚀 PostgreSQL Auto-Setup para Testes

O banco PostgreSQL de testes **configura-se automaticamente** via container Docker isolado.

## ✨ Como Funciona

Quando você roda `make test` ou `make test-fast`:

1. ✅ Sobe o container `postgres-test` (porta 5433, efêmero)
2. ✅ Aguarda o banco ficar healthy
3. ✅ Aplica todas as Alembic migrations automaticamente
4. ✅ Roda os testes com `DATABASE_URL` apontando para o container
5. ✅ Para o container ao final (dados são descartados)

**Você só precisa garantir que:**
- Docker/Podman está rodando
- Ambiente de dev está up: `make dev-up`

---

## 📝 Setup Inicial (Apenas Uma Vez)

### 1. Suba o ambiente de desenvolvimento

```bash
make dev-up
```

### 2. Pronto! Rode os Testes

```bash
make test-fast  # Testes rápidos (~5s)
make test       # Suite completa (~4min)
```

**Na execução você verá:**

```
🐘 Starting test database container...
⏳ Waiting for postgres-test to be healthy...
✅ Test database ready at localhost:5433
🚀 Running fast anti-regression tests...

======================================================================
🐘 PostgreSQL Test Database Auto-Setup
======================================================================
   🗑️  Dropping all tables...
   ✅ All tables dropped
   🔧 Running Alembic migrations...
   ✅ Migrations applied (HEAD: abc123)
   🌱 Seeding test data...
   ✅ Test data seeded
======================================================================
✅ Test database ready!
======================================================================

84 passed, 4 skipped in 4.30s
```

---

## 🎯 Como Usar em Novos Testes

### Opção 1: Usar Fixtures PostgreSQL

Use qualquer uma destas fixtures - auto-setup acontece automaticamente:

```python
def test_with_clean_db(db_session):
    """db_session → banco limpo com migrations."""
    db_session.add(Experiment(...))
    db_session.commit()


def test_with_seed_data(seeded_db_session):
    """seeded_db_session → banco com dados de teste."""
    experiments = seeded_db_session.query(Experiment).all()
    assert len(experiments) == 3  # Seed data
```

### Opção 2: Marcar Classe de Teste

```python
@pytest.mark.requires_postgres
class TestMyFeature:
    def test_something(self, migrated_db_engine):
        # Auto-setup detecta o marker
        pass
```

---

## 🔄 Quando Modificar Models

```bash
# 1. Criar migration (contra dev database)
make db-migrate MSG="Add column"

# 2. Rodar testes (container de teste aplica migrations automaticamente)
make test-fast
```

**Não precisa mais** rodar `setup_test_db.py` manualmente!

---

## 🛠️ Fixtures Disponíveis

| Fixture | Scope | Descrição |
|---------|-------|-----------|
| `postgres_test_url` | session | URL do banco de teste |
| `migrated_db_engine` | session | Engine com migrations aplicadas |
| `db_session` | function | Sessão limpa com rollback automático |
| `seeded_db_session` | function | Sessão com dados de teste pré-carregados |

### Escolhendo a Fixture Certa

```python
# Preciso de banco vazio para cada teste
def test_create(db_session):
    pass

# Preciso de dados já populados
def test_list(seeded_db_session):
    pass

# Só preciso do engine
def test_raw_sql(migrated_db_engine):
    pass
```

---

## 🧪 Executando Testes

### Testes Rápidos (Recomendado para Desenvolvimento)

```bash
make test-fast  # smoke + contract + schema (~5s)
```

### Suite Completa

```bash
make test  # Todos os testes (~4min)
```

### Apenas Testes que Requerem PostgreSQL

```bash
DATABASE_URL="postgresql://synthlab:synthlab@localhost:5433/synthlab" \
  uv run pytest -m requires_postgres
```

### Apenas Testes de Migrations

```bash
DATABASE_URL="postgresql://synthlab:synthlab@localhost:5433/synthlab" \
  uv run pytest tests/schema/test_migrations.py
```

---

## 🔍 O Que Acontece por Trás

```mermaid
graph TD
    A[make test] --> B[Sobe postgres-test container]
    B --> C[Aguarda healthy]
    C --> D[Seta DATABASE_URL para container]
    D --> E[pytest inicia]
    E --> F[conftest.py detecta DATABASE_URL]
    F --> G[Drop all tables]
    G --> H[Aplica migrations]
    H --> I[Seed test data]
    I --> J[Roda testes]
    J --> K[Para container]
```

---

## ✅ Vantagens

### Antes (Manual)

```bash
# Toda vez que modificava models:
uv run python scripts/setup_test_db.py --reset
DATABASE_URL=... pytest tests/
```

### Agora (Automático)

```bash
# Só isso:
make test
```

**Benefícios:**
- ✅ Zero setup manual
- ✅ Container isolado (porta 5433)
- ✅ Dados efêmeros (sem persistência)
- ✅ Migrations sempre atualizadas
- ✅ CI/CD simplificado
- ✅ Onboarding mais fácil

---

## 🚨 Troubleshooting

### "Container not starting"

```bash
# Verificar se Docker/Podman está rodando
docker ps

# Verificar logs do container
docker logs synthlab-postgres-test
```

### "DATABASE_URL must point to test database"

Você está tentando rodar pytest diretamente sem `make test`:

```bash
# Use o Makefile que configura DATABASE_URL corretamente
make test-fast
```

### "Migrations out of date"

O container de teste sempre aplica migrations do zero. Se houver erro:

```bash
# Verifique se migrations estão corretas no dev
make db-migrate MSG="Fix migration"
```

### Forçar Limpeza

```bash
# Para e remove o container de teste
make test-db-down

# Remove volumes órfãos
docker volume prune
```

---

## 📚 Referências

- **Auto-setup**: `tests/conftest.py` → `_ensure_test_database_setup`
- **Fixtures**: `tests/conftest.py` → Seção "PostgreSQL Test Database Fixtures"
- **Seed Data**: `tests/fixtures/seed_test.py`
- **Docker Config**: `docker/docker-compose.yml` → `postgres-test` service
