# 🚀 PostgreSQL Auto-Setup para Testes

O banco PostgreSQL de testes **configura-se automaticamente**! Não é mais necessário rodar scripts manualmente.

## ✨ Como Funciona

Quando você roda `pytest`, o sistema:

1. ✅ Detecta se algum teste precisa de PostgreSQL
2. ✅ Cria o banco `synthlab_test` se não existir
3. ✅ Aplica todas as Alembic migrations automaticamente
4. ✅ Verifica se migrations estão atualizadas
5. ✅ Tudo isso **antes** de rodar os testes

**Você só precisa garantir que:**
- PostgreSQL está rodando
- `DATABASE_TEST_URL` está no `.env`

---

## 📝 Setup Inicial (Apenas Uma Vez)

### 1. Adicione ao `.env`

```bash
DATABASE_TEST_URL=postgresql://synthlab:synthlab@localhost:5432/synthlab_test
```

### 2. Inicie o PostgreSQL

```bash
docker compose up -d postgres
```

### 3. Pronto! Rode os Testes

```bash
pytest tests/
```

**Na primeira execução você verá:**

```
======================================================================
🐘 PostgreSQL Test Database Auto-Setup
======================================================================

🔧 Creating test database 'synthlab_test'...
✅ Database 'synthlab_test' created

🔧 Applying migrations to test database...
   Current: None
   Target:  58b0dafa7483
✅ Migrations applied successfully
======================================================================
```

**Nas próximas execuções:**
- Se migrations estiverem atualizadas: **roda direto**
- Se houver novas migrations: **aplica automaticamente**

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

O workflow continua o mesmo, mas mais simples:

```bash
# 1. Criar migration
DATABASE_URL=$DATABASE_TEST_URL alembic -c src/synth_lab/alembic/alembic.ini \
  revision --autogenerate -m "Add column"

# 2. Aplicar ao banco principal
alembic -c src/synth_lab/alembic/alembic.ini upgrade head

# 3. Rodar testes (auto-setup aplica a migration ao banco de teste)
pytest tests/
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

### Todos os Testes

```bash
pytest tests/
```

### Apenas Testes que Requerem PostgreSQL

```bash
pytest -m requires_postgres
```

### Apenas Testes de Concorrência

```bash
pytest tests/integration/test_concurrent_operations.py
```

### Apenas Testes de Migrations

```bash
pytest tests/schema/test_migrations.py
```

---

## 🔍 O Que Acontece por Trás

```mermaid
graph TD
    A[pytest inicia] --> B{Tem DATABASE_TEST_URL?}
    B -->|Não| C[Testes PostgreSQL são skipped]
    B -->|Sim| D{Algum teste usa PostgreSQL?}
    D -->|Não| E[Continua sem setup]
    D -->|Sim| F[Auto-setup inicia]
    F --> G{Banco existe?}
    G -->|Não| H[Cria banco]
    G -->|Sim| I{Migrations atualizadas?}
    H --> I
    I -->|Não| J[Aplica migrations]
    I -->|Sim| K[Pronto!]
    J --> K
    K --> L[Roda testes]
```

### Detecção Automática

O auto-setup detecta testes PostgreSQL através de:

1. **Fixtures usadas**: `db_session`, `migrated_db_engine`, etc.
2. **Marker**: `@pytest.mark.requires_postgres`

---

## ✅ Vantagens

### Antes (Manual)

```bash
# Toda vez que modificava models:
uv run python scripts/setup_test_db.py --reset
pytest tests/
```

### Agora (Automático)

```bash
# Só isso:
pytest tests/
```

**Benefícios:**
- ✅ Zero setup manual
- ✅ Migrations sempre atualizadas
- ✅ Banco criado automaticamente
- ✅ CI/CD simplificado
- ✅ Onboarding mais fácil

---

## 🚨 Troubleshooting

### "PostgreSQL connection refused"

```bash
# Verificar se PostgreSQL está rodando
docker ps | grep postgres

# Iniciar se necessário
docker compose up -d postgres
```

### "DATABASE_TEST_URL not set"

```bash
echo "DATABASE_TEST_URL=postgresql://synthlab:synthlab@localhost:5432/synthlab_test" >> .env
```

### "Migrations out of date"

Rode pytest novamente - auto-setup aplica as migrations:

```bash
pytest tests/
```

### Forçar Recriação do Banco

Se algo der errado, use o script manual:

```bash
uv run python scripts/setup_test_db.py --reset
```

---

## 📚 Referências

- **Auto-setup**: `tests/conftest.py` → `_auto_setup_postgres_if_needed`
- **Fixtures**: `tests/conftest.py` → Seção "PostgreSQL Test Database Fixtures"
- **Seed Data**: `tests/fixtures/seed_test.py`
- **Setup Manual**: `scripts/setup_test_db.py`
