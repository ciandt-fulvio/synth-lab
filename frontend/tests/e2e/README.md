# Testes E2E - Playwright

## 📁 Estrutura

```
tests/e2e/
├── README.md                    # Este arquivo
├── E2E_TEST_PLAN.md             # Plano de testes e roadmap
├── smoke/                       # Smoke tests (Production)
│   └── critical-flows.spec.ts   # ST001-ST009
├── experiments/                 # Testes de experimentos
│   ├── crud.spec.ts             # E001-E011 (criar, listar, visualizar)
│   └── list.spec.ts             # EL001-EL008 (filtros, busca, ordenação)
├── interviews/                  # Testes de entrevistas
│   └── create.spec.ts           # I001-I013 (modal, validação)
└── synths/                      # Testes de synths
    ├── list.spec.ts             # Y001-Y013 (listagem, filtros, paginação)
    └── detail.spec.ts           # Y014-Y027 (modal com tabs)
```

## 🚀 Rodar Testes

### ⭐ Testes Críticos (Gate de PR)

```bash
# Rodar apenas testes P0 (críticos) - DEVE PASSAR antes de PR
npx playwright test --grep "@critical"

# Duração esperada: < 3 minutos
# Cobertura: Smoke tests + CRUD + Filtros + Entrevistas + Synths
```

### Local (Desenvolvimento)

```bash
# Todos os testes localmente
npm run test:e2e

# Modo UI (visual, recomendado para debug)
npm run test:e2e:ui

# Arquivo específico
npx playwright test experiments/crud.spec.ts

# Por módulo
npx playwright test experiments/
npx playwright test synths/
npx playwright test interviews/
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

## 📋 Cobertura de Testes

### Implementados (✅)

| Módulo | Arquivo | Testes | Prioridade |
|--------|---------|--------|------------|
| **Smoke** | `smoke/critical-flows.spec.ts` | ST001-ST009 | P0 |
| **Experiments** | `experiments/crud.spec.ts` | E001-E011 | P0 |
| **Experiments** | `experiments/list.spec.ts` | EL001-EL008 | P0 |
| **Interviews** | `interviews/create.spec.ts` | I001-I013 | P0 |
| **Synths** | `synths/list.spec.ts` | Y001-Y013 | P0/P1 |
| **Synths** | `synths/detail.spec.ts` | Y014-Y027 | P1 |

**Total**: ~60 cenários de teste cobrindo os fluxos críticos da aplicação.

### Roadmap (Ver E2E_TEST_PLAN.md)

- [ ] `experiments/detail-tabs.spec.ts` - Navegação entre todas as tabs (P1)
- [ ] `experiments/materials.spec.ts` - Upload de materiais (P1)
- [ ] `shared/navigation.spec.ts` - Navegação geral (P2)

Ver [E2E_TEST_PLAN.md](./E2E_TEST_PLAN.md) para plano detalhado e roadmap.

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

- Backend de teste: **8000**
- Frontend de teste: **8080**

(Evita conflito com dev: 8000/8080)

## Troubleshooting

```bash
# Timeout ao iniciar
lsof -ti:8080 | xargs kill -9

# Ver screenshots de erros
ls test-results/

# Debug interativo
npm run test:e2e:debug
```

## Guia Completo

Ver [docs/TESTING.md](../../docs/TESTING.md) para guia detalhado com exemplos e boas práticas.
