# Testes E2E - Playwright

## Rodar Testes

```bash
# Automático (Playwright inicia servidores)
npm run test:e2e

# Modo UI (visual, recomendado para debug)
npm run test:e2e:ui

# Manual (mais controle)
# Terminal 1: make serve-test        (backend porta 8009)
# Terminal 2: make serve-front-test  (frontend porta 8089)
# Terminal 3: make test-e2e
```

## Criar Novo Teste

```typescript
// tests/e2e/novo-fluxo.spec.ts
import { test, expect } from '@playwright/test';

test('fluxo de exemplo', async ({ page }) => {
  // 1. Navega
  await page.goto('/');

  // 2. Interage
  await page.click('text=Botão');
  await page.fill('input[name="campo"]', 'valor');

  // 3. Valida
  await expect(page).toHaveURL(/\/sucesso/);
  await expect(page.locator('text=Sucesso')).toBeVisible();
});
```

## Scripts Disponíveis

```bash
npm run test:e2e          # Headless (CI)
npm run test:e2e:ui       # Modo UI (visual)
npm run test:e2e:debug    # Debug step-by-step
npm run test:e2e:headed   # Ver browser
npm run test:e2e:report   # Ver relatório HTML
```

## Portas

- Backend de teste: **8009**
- Frontend de teste: **8089**

(Evita conflito com dev: 8000/8080)

## Troubleshooting

```bash
# Timeout ao iniciar
lsof -ti:8089 | xargs kill -9

# Ver screenshots de erros
ls test-results/

# Debug interativo
npm run test:e2e:debug
```

## Guia Completo

Ver [docs/TESTING.md](../../docs/TESTING.md) para guia detalhado com exemplos e boas práticas.
