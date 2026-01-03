# Update Tests Skill

**Trigger:** Mudanças em routers, models ou services

**Objetivo:** Manter testes sincronizados com código.

## Uso

```bash
# Automático (via git hook)
git commit -m "Add endpoint"
# Hook pergunta se quer gerar teste

# Manual
./scripts/auto-update-tests.sh --last-commit
```

## O que faz

**Router mudou** → Atualiza contract tests
**Model mudou** → Alerta para criar migration
**Service mudou** → Cria/atualiza integration test

## Templates

### Contract Test
```python
def test_endpoint_contract(client):
    """Valida schema da resposta."""
    response = client.get("/endpoint")

    assert response.status_code == 200
    body = response.json()

    # Campos obrigatórios
    assert "id" in body
    assert "name" in body
    assert isinstance(body["status"], str)
```

### Integration Test
```python
def test_service_flow(client, db_session):
    """Testa fluxo completo."""
    # 1. Chama API
    response = client.post("/endpoint", json={"data": "value"})
    resource_id = response.json()["id"]

    # 2. Valida no DB
    resource = db_session.query(Model).get(resource_id)
    assert resource is not None
    assert resource.status == "expected"
```

### E2E Test
```typescript
test('user flow', async ({ page }) => {
  // 1. Navega
  await page.goto('/');

  // 2. Interage
  await page.click('text=Button');
  await page.fill('input[name="field"]', 'value');
  await page.click('button[type="submit"]');

  // 3. Valida
  await expect(page).toHaveURL(/\/success/);
});
```

## Regras

- Rode testes após gerar: `make test-fast`
- Use markers: `@pytest.mark.contract`
- Siga padrão existente
- Valide schemas, não implementação

## Guia Completo

Ver [docs/TESTING.md](../../docs/TESTING.md)
