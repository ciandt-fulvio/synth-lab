# E2E Testing com Playwright

Guia completo para rodar testes end-to-end contra diferentes ambientes.

## Ambientes Disponíveis

| Ambiente | URL | Quando Usar |
|----------|-----|-------------|
| **Local** | `http://localhost:8089` | Desenvolvimento local (padrão) |
| **Staging** | `https://synth-lab-frontend-staging.up.railway.app` | Testes antes de deploy production |
| **Production** | `https://synth-lab-frontend-production.up.railway.app` | Smoke tests após deploy |

## Comandos Rápidos

### Local (Padrão)

```bash
# Rodar todos os testes localmente
npm run test:e2e

# Modo UI interativo
npm run test:e2e:ui

# Modo debug
npm run test:e2e:debug

# Ver no browser (headed mode)
npm run test:e2e:headed

# Ver relatório do último teste
npm run test:e2e:report
```

### Staging

```bash
# Rodar todos os testes contra staging
npm run test:e2e:staging

# Modo UI contra staging
npm run test:e2e:staging:ui

# Ver no browser contra staging
npm run test:e2e:staging:headed
```

### Production

```bash
# Rodar smoke tests contra production
npm run test:e2e:production

# Modo UI contra production
npm run test:e2e:production:ui
```

## Uso Avançado

### Testar Contra URL Customizada

```bash
# Qualquer URL customizada
BASE_URL=https://meu-ambiente.com npm run test:e2e

# Com modo UI
BASE_URL=https://meu-ambiente.com npm run test:e2e:ui
```

### Rodar Teste Específico

```bash
# Local
npx playwright test experiment-list.spec.ts

# Staging
TEST_ENV=staging npx playwright test experiment-list.spec.ts

# Production
TEST_ENV=production npx playwright test experiment-list.spec.ts
```

### Rodar com Diferentes Browsers

```bash
# Staging com Firefox (se configurado)
TEST_ENV=staging npx playwright test --project=firefox

# Staging com todos os browsers
TEST_ENV=staging npx playwright test --project=chromium --project=firefox --project=webkit
```

## Configuração de CI/CD

### GitHub Actions

```yaml
name: E2E Tests Staging

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test-staging:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18

      - name: Install dependencies
        run: cd frontend && npm ci

      - name: Install Playwright Browsers
        run: cd frontend && npx playwright install --with-deps chromium

      - name: Run E2E tests against staging
        run: cd frontend && npm run test:e2e:staging

      - name: Upload test report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: frontend/playwright-report/
```

### Railway Deploy Hook

Adicione no seu processo de deploy:

```bash
# Após deploy para staging
railway run --environment staging "cd frontend && npm run test:e2e:staging"
```

## Estrutura dos Testes

```
frontend/
├── tests/
│   └── e2e/
│       ├── experiment-list.spec.ts    # Testes da lista de experimentos
│       └── ...                        # Adicione mais testes aqui
├── playwright.config.ts               # Configuração principal
└── E2E_TESTING.md                     # Este arquivo
```

## Escrevendo Testes

Os testes usam o `baseURL` configurado automaticamente:

```typescript
import { test, expect } from '@playwright/test';

test.describe('Meu Teste', () => {
  test('deve carregar a página', async ({ page }) => {
    // URL relativa - automaticamente usa baseURL configurado
    await page.goto('/');

    // Funciona em local, staging e production!
    await expect(page).toHaveTitle('SynthLab');
  });
});
```

## Variáveis de Ambiente

O `playwright.config.ts` reconhece as seguintes variáveis:

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `TEST_ENV` | Ambiente alvo (local, staging, production) | `TEST_ENV=staging` |
| `BASE_URL` | URL customizada (sobrescreve TEST_ENV) | `BASE_URL=https://...` |
| `VITE_PORT` | Porta local customizada | `VITE_PORT=3000` |
| `CI` | Modo CI (mais retries, 1 worker) | `CI=true` |

## Debugging

### Ver Trace do Teste

```bash
# Rodar com trace
TEST_ENV=staging npx playwright test --trace on

# Ver trace no UI
npx playwright show-trace trace.zip
```

### Screenshots de Falhas

Screenshots são automaticamente salvos em `test-results/` quando um teste falha.

```bash
# Ver screenshots
ls -la frontend/test-results/
```

### Debug Interativo

```bash
# Local
npm run test:e2e:debug

# Staging com debug
TEST_ENV=staging npx playwright test --debug
```

## Best Practices

### 1. Teste em Staging Antes de Production

```bash
# Workflow recomendado
npm run test:e2e                    # 1. Teste localmente
npm run test:e2e:staging           # 2. Teste em staging
# Deploy para production
npm run test:e2e:production        # 3. Smoke test em production
```

### 2. Use Seletores Semânticos

```typescript
// ✅ Bom - independente de classe CSS
await page.getByRole('button', { name: /criar experimento/i });
await page.getByText('SynthLab');

// ❌ Ruim - frágil
await page.locator('.btn-primary-123');
```

### 3. Espere por Estado de Rede

```typescript
// Aguarde requisições completarem
await page.goto('/');
await page.waitForLoadState('networkidle');

// Ou espere por elemento específico
await expect(page.locator('h2')).toBeVisible({ timeout: 10000 });
```

### 4. Isole Testes

```typescript
// Cada teste deve ser independente
test('teste 1', async ({ page }) => {
  // Setup próprio
  await page.goto('/');
  // ...
});

test('teste 2', async ({ page }) => {
  // Não depende do teste 1
  await page.goto('/');
  // ...
});
```

## Troubleshooting

### Teste Falha em Staging mas Passa Localmente

**Problema**: Diferenças de dados entre ambientes

**Solução**:
- Use verificações condicionais para listas vazias
- Verifique se os dados de teste existem em staging
- Use `test.skip()` se dados necessários não existem

```typescript
const hasData = await page.locator('.data-item').count() > 0;
if (!hasData) {
  test.skip('Dados de teste não disponíveis em staging');
}
```

### Timeout em Staging

**Problema**: Requisições levam mais tempo em staging

**Solução**: Aumente timeouts

```typescript
await expect(page.locator('h2')).toBeVisible({
  timeout: 30000  // 30 segundos para staging
});
```

### Autenticação Necessária

**Problema**: Staging/Production requer login

**Solução**: Configure state de autenticação

```typescript
// setup-auth.ts
import { test as setup } from '@playwright/test';

setup('authenticate', async ({ page }) => {
  await page.goto('/login');
  // ... realizar login
  await page.context().storageState({
    path: 'playwright/.auth/user.json'
  });
});
```

```typescript
// playwright.config.ts
export default defineConfig({
  projects: [
    { name: 'setup', testMatch: /.*\.setup\.ts/ },
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        storageState: 'playwright/.auth/user.json',
      },
      dependencies: ['setup'],
    },
  ],
});
```

## Referências

- [Playwright Documentation](https://playwright.dev/)
- [Best Practices](https://playwright.dev/docs/best-practices)
- [Railway Environments](../docs/railway-environments.md)

## Próximos Passos

1. ✅ Configurar testes contra staging
2. 🔄 Adicionar mais cenários de teste
3. 📋 Configurar CI/CD para rodar testes automaticamente
4. 🔐 Adicionar testes de autenticação (quando implementado)
5. 📊 Adicionar testes de performance
