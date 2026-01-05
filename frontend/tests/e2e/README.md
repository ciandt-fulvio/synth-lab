# Testes E2E - Playwright

## 📁 Estrutura

```
tests/e2e/
├── README.md                    # Este arquivo
├── TEST_SCENARIOS.md            # Catálogo completo de cenários
├── smoke/                       # Smoke tests (Production)
│   └── critical-flows.spec.ts
├── experiments/                 # Testes de experimentos
│   └── crud.spec.ts
└── ... (outros módulos)
```

## 🚀 Rodar Testes

### Local (Desenvolvimento)

```bash
# Todos os testes localmente
npm run test:e2e

# Modo UI (visual, recomendado para debug)
npm run test:e2e:ui

# Arquivo específico
npx playwright test experiments/crud.spec.ts
```

### Staging

```bash
# Todos os testes em staging
npm run test:e2e:staging

# Smoke tests em staging
npm run test:e2e:staging smoke/

# Modo UI
npm run test:e2e:staging:ui
```

### Production (Smoke Tests)

```bash
# Apenas smoke tests críticos
npm run test:e2e:production smoke/

# Com UI
npm run test:e2e:production:ui
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

## 🏷️ Filtrar por Tags

```bash
# Apenas smoke tests
npx playwright test --grep @smoke

# Testes críticos
npx playwright test --grep @critical

# Testes de experimentos
npx playwright test --grep @experiments

# Excluir testes lentos
npx playwright test --grep-invert @slow
```

## 📋 Cenários Disponíveis

Ver [TEST_SCENARIOS.md](./TEST_SCENARIOS.md) para lista completa de cenários organizados por:
- **Smoke Tests (ST001-ST009)**: Production, < 2 min
- **Testes Completos (E001-U003)**: Local/Staging, 5-10 min
- Por módulo: Experiments, Simulations, Interviews, etc.
- Por prioridade: P0 (Crítico), P1 (Alto), P2 (Médio)

## Scripts Disponíveis

```bash
# Local
npm run test:e2e              # Todos os testes
npm run test:e2e:ui           # Modo UI (visual)
npm run test:e2e:debug        # Debug step-by-step
npm run test:e2e:headed       # Ver browser

# Staging
npm run test:e2e:staging      # Todos os testes
npm run test:e2e:staging:ui   # Modo UI
npm run test:e2e:staging:headed

# Production
npm run test:e2e:production   # Smoke tests
npm run test:e2e:production:ui

# Relatório
npm run test:e2e:report       # Ver relatório HTML
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
