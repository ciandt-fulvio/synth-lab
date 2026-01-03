# Update Tests Skill

**Trigger:** `/update-tests` ou quando arquivos críticos mudarem

**Objetivo:** Manter testes sincronizados com mudanças no código.

## O que faz

1. **Detecta mudanças** em routers, models, services
2. **Analisa gaps** de cobertura de testes
3. **Gera/atualiza** testes correspondentes
4. **Valida** que testes passam

## Workflow

### Quando Router Muda

```bash
# Usuário mudou: src/synth_lab/api/routers/experiments.py
# Skill detecta e:

1. Lê o router modificado
2. Identifica novos endpoints ou mudanças em schemas
3. Atualiza tests/contract/test_api_contracts.py
4. Roda pytest -m contract para validar
```

### Quando ORM Model Muda

```bash
# Usuário mudou: src/synth_lab/models/orm/experiment.py
# Skill detecta e:

1. Alerta que schema test vai falhar
2. Sugere: alembic revision --autogenerate
3. Atualiza tests/schema/test_db_schema_validation.py se necessário
```

### Quando Service Muda

```bash
# Usuário mudou: src/synth_lab/services/experiment_service.py
# Skill detecta e:

1. Verifica se já existe integration test
2. Se não existe, cria novo teste em tests/integration/
3. Se existe, analisa se precisa atualizar
```

## Como Usar

### Modo Automático (Recomendado)

Configure Claude Code para rodar após commit:

```bash
# Em .claude/hooks/post-commit (a criar)
claude code --skill update-tests
```

### Modo Manual

```bash
# Atualizar todos os testes
claude code --skill update-tests

# Atualizar apenas contract tests
claude code --skill update-tests --type contract

# Atualizar para arquivos específicos
claude code --skill update-tests --files "src/synth_lab/api/routers/experiments.py"
```

## Exemplos de Prompts

Use esses prompts com Claude Code:

### Contract Tests
```
Analise os routers modificados em src/synth_lab/api/routers/
e atualize tests/contract/test_api_contracts.py para cobrir:
- Novos endpoints
- Mudanças em schemas de resposta
- Campos adicionados/removidos
```

### Schema Tests
```
Analise mudanças nos ORM models em src/synth_lab/models/orm/
e atualize tests/schema/test_db_schema_validation.py para validar:
- Novos campos
- Mudanças de tipo
- Constraints (nullable, FK)
```

### Integration Tests
```
Crie integration test para o service X que valide:
- Fluxo completo de [descrever fluxo]
- Interação com DB
- Tratamento de erros
```

## Checklist de Manutenção

Execute periodicamente (ex: semanalmente):

```bash
# 1. Identifica endpoints sem contract tests
claude code --prompt "Liste endpoints em routers/ sem contract tests correspondentes"

# 2. Identifica services sem integration tests
claude code --prompt "Liste services/ sem integration tests correspondentes"

# 3. Analisa cobertura de E2E
claude code --prompt "Liste fluxos críticos sem E2E tests"

# 4. Atualiza testes desatualizados
claude code --prompt "Analise e atualize testes que podem estar desatualizados baseado em mudanças recentes no código"
```

## Regras

- **SEMPRE** rode os testes após gerar/atualizar
- **NUNCA** delete testes existentes sem confirmar
- **SEMPRE** mantenha o padrão atual de testes
- **SEMPRE** use os markers corretos (@pytest.mark.contract, etc)

## Templates

### Contract Test Template
```python
def test_new_endpoint_returns_valid_schema(self, client: TestClient):
    """GET /api/new-endpoint retorna schema esperado."""
    response = client.get("/api/new-endpoint")

    assert response.status_code == 200
    data = response.json()

    # Validar campos obrigatórios
    required_fields = ["id", "name", "created_at"]
    for field in required_fields:
        assert field in data
```

### Schema Validation Template
```python
def test_new_table_schema(self, db_inspector):
    """Valida schema da tabela 'new_table'."""
    columns = {col["name"]: col for col in db_inspector.get_columns("new_table")}

    # Validar colunas essenciais
    assert "id" in columns
    assert isinstance(columns["id"]["type"], String)
```

### Integration Test Template
```python
def test_new_service_flow(self, db_session):
    """Testa fluxo completo do NewService."""
    service = NewService(db_session)

    # Ação
    result = service.execute_flow(input_data)

    # Validação
    assert result is not None
    assert result.status == "completed"
```
