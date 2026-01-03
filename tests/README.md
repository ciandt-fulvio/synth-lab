# Testes Backend

## Rodar Testes

```bash
# Testes rápidos (~30s) - Rode antes de commit
make test-fast

# Todos os testes
pytest

# Por tipo
pytest -m smoke          # Health checks
pytest -m contract       # API schemas
pytest -m schema         # DB validation
pytest -m integration    # Fluxos completos
pytest -m unit           # Lógica isolada
```

## Estrutura

```
tests/
├── smoke/          - Health checks (DB, configs, imports)
├── contract/       - API response schemas
├── schema/         - DB vs Models validation
├── integration/    - Fluxos API → Service → DB
└── unit/           - Funções isoladas
```

## Criar Novo Teste

```python
# tests/contract/test_api_contracts.py
def test_new_endpoint(client):
    response = client.get("/novo-endpoint")
    assert response.status_code == 200
    body = response.json()

    # Valide estrutura esperada pelo frontend
    assert "data" in body
    assert isinstance(body["data"], list)
```

## Troubleshooting

```bash
# DB não conecta
make db && make db-test

# Migration pendente
alembic upgrade head

# Schema diverge (mudou model)
alembic revision --autogenerate -m "Descrição"
alembic upgrade head
pytest -m schema
```

## Guia Completo

Ver [docs/TESTING.md](../docs/TESTING.md) para guia detalhado com exemplos e boas práticas.
