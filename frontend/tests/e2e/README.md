# E2E Tests - Playwright

## Portas Configuradas

Para evitar conflitos com servidores de desenvolvimento:

- **Backend de teste**: `http://localhost:8009`
- **Frontend de teste**: `http://localhost:8089`

## Como Executar

### Opção 1: Usando Makefile (Recomendado)

```bash
# Terminal 1 - Backend de teste
make serve-test

# Terminal 2 - Frontend de teste
make serve-front-test

# Terminal 3 - Rodar testes E2E
make test-e2e

# OU em modo UI (interativo)
make test-e2e-ui
```

### Opção 2: Manualmente

```bash
# Terminal 1 - Backend (porta 8009)
DATABASE_URL="postgresql://synthlab:synthlab@localhost:5432/synthlab_test" \
  uv run uvicorn synth_lab.api.main:app --host 127.0.0.1 --port 8009

# Terminal 2 - Frontend (porta 8089)
cd frontend
VITE_PORT=8089 VITE_API_PORT=8009 npm run dev:test

# Terminal 3 - Testes
cd frontend
npm run test:e2e
```

### Opção 3: Deixar Playwright iniciar os servidores (automático)

```bash
cd frontend
npm run test:e2e
```

O Playwright vai automaticamente:
1. Iniciar o frontend na porta 8089 (via `npm run dev:test`)
2. Aguardar o servidor estar pronto
3. Executar os testes
4. Parar o servidor ao final

## Scripts Disponíveis

```bash
npm run test:e2e          # Rodar testes headless
npm run test:e2e:ui       # Modo UI (visualizar testes)
npm run test:e2e:debug    # Debug mode (step-by-step)
npm run test:e2e:headed   # Ver browser durante execução
npm run test:e2e:report   # Ver relatório HTML dos testes
```

## Estrutura

```
tests/e2e/
├── experiment-list.spec.ts    # Exemplo: lista de experimentos
└── README.md                  # Este arquivo
```

## Adicionando Novos Testes

1. Crie arquivo `*.spec.ts` em `tests/e2e/`
2. Use os exemplos em `experiment-list.spec.ts` como referência
3. Use `data-testid` nos componentes para seletores estáveis

Exemplo:

```typescript
import { test, expect } from '@playwright/test';

test.describe('Feature Name', () => {
  test('should do something', async ({ page }) => {
    await page.goto('/path');
    await expect(page.locator('[data-testid="element"]')).toBeVisible();
  });
});
```

## Troubleshooting

### Porta já em uso

```bash
# Matar servidores de teste
make kill-test-servers

# OU manualmente
lsof -ti:8009 | xargs kill -9
lsof -ti:8089 | xargs kill -9
```

### Timeout ao iniciar servidor

- Verifique se o backend está rodando (`make serve-test`)
- Verifique se a porta 8089 está livre
- Aumente timeout em `playwright.config.ts` se necessário

### Testes falhando

```bash
# Ver screenshots dos erros
ls playwright-report/

# Rodar em modo debug
npm run test:e2e:debug

# Rodar em modo headed (ver o browser)
npm run test:e2e:headed
```
