# Cenários de Teste E2E - SynthLab

Documento de referência com todos os cenários de teste organizados por ambiente e prioridade.

## 📋 Índice

- [Smoke Tests (Production)](#smoke-tests-production)
- [Testes Completos (Local/Staging)](#testes-completos-localstaging)
- [Priorização](#priorização)
- [Implementação](#implementação)

---

## 🔥 Smoke Tests (Production)

**Objetivo**: Garantir que funcionalidades críticas estão funcionando após deploy.
**Duração alvo**: < 2 minutos
**Frequência**: Após cada deploy para production

### ST001: Health Check Básico
**Prioridade**: P0 (Crítico)
**Descrição**: Verifica se a aplicação carrega e está responsiva

```typescript
test('ST001 - Application loads and is responsive', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveTitle('SynthLab');
  await expect(page.locator('header')).toBeVisible();
});
```

### ST002: Lista de Experimentos Carrega
**Prioridade**: P0 (Crítico)
**Descrição**: Página principal carrega corretamente

```typescript
test('ST002 - Experiments list page loads', async ({ page }) => {
  await page.goto('/');
  await page.waitForLoadState('networkidle');

  // Deve ter header de experimentos
  await expect(
    page.locator('h2').filter({ hasText: /experimentos/i }).first()
  ).toBeVisible({ timeout: 10000 });

  // Deve ter botão de criar experimento
  await expect(
    page.getByRole('button', { name: /criar experimento/i })
  ).toBeVisible();
});
```

### ST003: API está Respondendo
**Prioridade**: P0 (Crítico)
**Descrição**: Backend API está acessível e respondendo

```typescript
test('ST003 - API is responding', async ({ page }) => {
  // Intercepta requisição à API
  const responsePromise = page.waitForResponse(
    response => response.url().includes('/api/experiments') && response.status() === 200
  );

  await page.goto('/');
  await responsePromise;

  // API respondeu com sucesso
});
```

### ST004: Navegação Básica Funciona
**Prioridade**: P0 (Crítico)
**Descrição**: Links principais navegam corretamente

```typescript
test('ST004 - Basic navigation works', async ({ page }) => {
  await page.goto('/');

  // Navega para página de Synths
  await page.getByRole('button', { name: /synths/i }).click();
  await expect(page).toHaveURL(/\/synths/);

  // Volta para home
  await page.getByRole('button', { name: /experimentos/i }).click();
  await expect(page).toHaveURL('/');
});
```

### ST005: Detalhe de Experimento Carrega
**Prioridade**: P1 (Alto)
**Descrição**: Página de detalhe de experimento carrega (se houver experimentos)

```typescript
test('ST005 - Experiment detail loads', async ({ page }) => {
  await page.goto('/');
  await page.waitForLoadState('networkidle');

  // Clica no primeiro experimento (se existir)
  const experimentCards = page.locator('.cursor-pointer').filter({
    has: page.locator('h3')
  });

  const count = await experimentCards.count();
  if (count > 0) {
    await experimentCards.first().click();
    await expect(page).toHaveURL(/\/experiments\/exp_/);
    await expect(page.locator('h2').first()).toBeVisible();
  } else {
    test.skip('Nenhum experimento disponível');
  }
});
```

### ST006: Estado de Erro Não Aparece
**Prioridade**: P1 (Alto)
**Descrição**: Não há erros visíveis na UI

```typescript
test('ST006 - No error states visible', async ({ page }) => {
  await page.goto('/');
  await page.waitForLoadState('networkidle');

  // Não deve haver mensagens de erro visíveis
  const errorMessages = page.locator('text=/erro|error|falha|failed/i').filter({
    hasNot: page.locator('[role="status"]') // Ignora loading states
  });

  await expect(errorMessages).toHaveCount(0);
});
```

### ST007: Console Errors Check
**Prioridade**: P1 (Alto)
**Descrição**: Não há erros críticos no console do browser

```typescript
test('ST007 - No critical console errors', async ({ page }) => {
  const errors: string[] = [];

  page.on('console', msg => {
    if (msg.type() === 'error') {
      errors.push(msg.text());
    }
  });

  await page.goto('/');
  await page.waitForLoadState('networkidle');

  // Filtra erros conhecidos/aceitáveis
  const criticalErrors = errors.filter(
    err => !err.includes('favicon') && !err.includes('DevTools')
  );

  expect(criticalErrors).toHaveLength(0);
});
```

---

## 🧪 Testes Completos (Local/Staging)

**Objetivo**: Testar todas as funcionalidades antes de deploy para production.
**Duração alvo**: 5-10 minutos
**Frequência**: Antes de cada deploy, em PRs importantes

### 📊 Módulo: Experiments

#### E001: Criar Novo Experimento
**Prioridade**: P0 (Crítico)
**User Story**: Como usuário, quero criar um experimento para iniciar minha pesquisa

```typescript
test('E001 - Create new experiment', async ({ page }) => {
  await page.goto('/');

  // Clica em criar experimento
  await page.getByRole('button', { name: /criar experimento/i }).click();

  // Preenche formulário
  await page.getByLabel(/nome/i).fill('Teste E2E Experimento');
  await page.getByLabel(/descrição/i).fill('Experimento criado via teste E2E');
  await page.getByLabel(/objetivo/i).fill('Validar criação de experimento');

  // Submete
  await page.getByRole('button', { name: /criar/i }).click();

  // Aguarda toast de sucesso
  await expect(
    page.locator('text=/criado com sucesso/i')
  ).toBeVisible({ timeout: 5000 });

  // Verifica que experimento aparece na lista
  await expect(
    page.locator('text=Teste E2E Experimento')
  ).toBeVisible();
});
```

#### E002: Listar Experimentos
**Prioridade**: P0 (Crítico)
**User Story**: Como usuário, quero ver todos os meus experimentos

```typescript
test('E002 - List experiments', async ({ page }) => {
  await page.goto('/');
  await page.waitForLoadState('networkidle');

  // Deve mostrar header
  await expect(
    page.locator('h2').filter({ hasText: /experimentos/i }).first()
  ).toBeVisible();

  // Cards ou empty state devem estar visíveis
  const hasCards = await page.locator('.cursor-pointer h3').count() > 0;
  const hasEmptyState = await page.locator('text=/nenhum experimento/i').count() > 0;

  expect(hasCards || hasEmptyState).toBeTruthy();
});
```

#### E003: Ver Detalhes do Experimento
**Prioridade**: P0 (Crítico)
**User Story**: Como usuário, quero ver detalhes de um experimento específico

```typescript
test('E003 - View experiment details', async ({ page }) => {
  await page.goto('/');
  await page.waitForLoadState('networkidle');

  // Clica no primeiro experimento
  const firstCard = page.locator('.cursor-pointer').filter({
    has: page.locator('h3')
  }).first();

  const experimentName = await firstCard.locator('h3').textContent();
  await firstCard.click();

  // Verifica que navegou corretamente
  await expect(page).toHaveURL(/\/experiments\/exp_/);

  // Verifica que nome do experimento aparece
  await expect(page.locator(`text=${experimentName}`)).toBeVisible();

  // Verifica seções principais
  await expect(page.locator('text=/simulações|simulations/i')).toBeVisible();
  await expect(page.locator('text=/exploration/i')).toBeVisible();
});
```

#### E004: Validação de Formulário
**Prioridade**: P1 (Alto)
**User Story**: Como usuário, quero ver mensagens claras quando preencher o formulário incorretamente

```typescript
test('E004 - Experiment form validation', async ({ page }) => {
  await page.goto('/');

  // Abre modal de criação
  await page.getByRole('button', { name: /criar experimento/i }).click();

  // Tenta submeter vazio
  await page.getByRole('button', { name: /criar/i }).click();

  // Deve mostrar erros de validação
  await expect(page.locator('text=/obrigatório|required/i')).toBeVisible();

  // Preenche nome muito curto
  await page.getByLabel(/nome/i).fill('ab');

  // Deve mostrar erro de tamanho mínimo
  await expect(page.locator('text=/mínimo|minimum/i')).toBeVisible();
});
```

#### E005: Navegação Entre Experimentos
**Prioridade**: P2 (Médio)
**User Story**: Como usuário, quero navegar facilmente entre experimentos

```typescript
test('E005 - Navigate between experiments', async ({ page }) => {
  await page.goto('/');
  await page.waitForLoadState('networkidle');

  const cards = page.locator('.cursor-pointer').filter({
    has: page.locator('h3')
  });

  const count = await cards.count();
  if (count >= 2) {
    // Clica no primeiro
    await cards.first().click();
    await expect(page).toHaveURL(/\/experiments\/exp_/);

    // Volta
    await page.goBack();
    await expect(page).toHaveURL('/');

    // Clica no segundo
    await cards.nth(1).click();
    await expect(page).toHaveURL(/\/experiments\/exp_/);
  } else {
    test.skip('Não há experimentos suficientes');
  }
});
```

### 🎯 Módulo: Simulations

#### S001: Criar Nova Simulação
**Prioridade**: P0 (Crítico)
**User Story**: Como usuário, quero criar uma simulação para meu experimento

```typescript
test('S001 - Create new simulation', async ({ page }) => {
  // Pré-requisito: ter um experimento
  await page.goto('/');
  await page.waitForLoadState('networkidle');

  const firstCard = page.locator('.cursor-pointer').first();
  await firstCard.click();

  // Clica em criar simulação
  await page.getByRole('button', { name: /nova simulação|new simulation/i }).click();

  // Preenche formulário
  await page.getByLabel(/nome|name/i).fill('Simulação E2E');
  await page.getByLabel(/número de synths|number of synths/i).fill('10');

  // Submete
  await page.getByRole('button', { name: /criar|create/i }).click();

  // Aguarda confirmação
  await expect(
    page.locator('text=/simulação criada|simulation created/i')
  ).toBeVisible({ timeout: 10000 });
});
```

#### S002: Listar Simulações do Experimento
**Prioridade**: P0 (Crítico)
**User Story**: Como usuário, quero ver todas as simulações de um experimento

```typescript
test('S002 - List experiment simulations', async ({ page }) => {
  await page.goto('/');
  const firstCard = page.locator('.cursor-pointer').first();
  await firstCard.click();

  // Seção de simulações deve estar visível
  const simulationsSection = page.locator('text=/simulações|simulations/i').first();
  await expect(simulationsSection).toBeVisible();

  // Deve ter lista ou empty state
  const hasSimulations = await page.locator('text=/simulação/i').count() > 0;
  const hasEmptyState = await page.locator('text=/nenhuma simulação/i').count() > 0;

  expect(hasSimulations || hasEmptyState).toBeTruthy();
});
```

#### S003: Ver Detalhes da Simulação
**Prioridade**: P1 (Alto)
**User Story**: Como usuário, quero ver os resultados de uma simulação

```typescript
test('S003 - View simulation details', async ({ page }) => {
  await page.goto('/');
  const firstCard = page.locator('.cursor-pointer').first();
  await firstCard.click();

  // Clica na primeira simulação (se existir)
  const simCard = page.locator('text=/simulação/i').first();
  if (await simCard.isVisible()) {
    await simCard.click();

    // Verifica que navegou
    await expect(page).toHaveURL(/\/simulations\/sim_/);

    // Verifica conteúdo
    await expect(page.locator('h2').first()).toBeVisible();
  } else {
    test.skip('Nenhuma simulação disponível');
  }
});
```

### 🎙️ Módulo: Interviews

#### I001: Criar Nova Entrevista
**Prioridade**: P0 (Crítico)
**User Story**: Como usuário, quero criar entrevistas para coletar insights

```typescript
test('I001 - Create new interview', async ({ page }) => {
  await page.goto('/');
  const firstCard = page.locator('.cursor-pointer').first();
  await firstCard.click();

  // Clica em criar entrevista
  await page.getByRole('button', { name: /nova entrevista|new interview/i }).click();

  // Preenche formulário
  await page.getByLabel(/prompt|pergunta/i).fill('Qual sua opinião sobre o produto?');
  await page.getByLabel(/número de entrevistas/i).fill('5');

  // Submete
  await page.getByRole('button', { name: /criar|create|iniciar|start/i }).click();

  // Aguarda confirmação
  await expect(
    page.locator('text=/entrevista|interview/i')
  ).toBeVisible({ timeout: 10000 });
});
```

#### I002: Visualizar Status de Entrevista
**Prioridade**: P1 (Alto)
**User Story**: Como usuário, quero ver o progresso das minhas entrevistas

```typescript
test('I002 - View interview status', async ({ page }) => {
  await page.goto('/');
  const firstCard = page.locator('.cursor-pointer').first();
  await firstCard.click();

  // Procura por cards de entrevista
  const interviewCards = page.locator('[data-testid="interview-card"]');

  if (await interviewCards.count() > 0) {
    const firstInterview = interviewCards.first();

    // Deve mostrar status (pending, running, completed, failed)
    await expect(
      firstInterview.locator('text=/pending|running|completed|failed/i')
    ).toBeVisible();

    // Deve mostrar progresso ou resultado
    await expect(firstInterview).toBeVisible();
  } else {
    test.skip('Nenhuma entrevista disponível');
  }
});
```

#### I003: Ver Transcrição de Entrevista
**Prioridade**: P1 (Alto)
**User Story**: Como usuário, quero ler a transcrição completa de uma entrevista

```typescript
test('I003 - View interview transcript', async ({ page }) => {
  await page.goto('/');
  const firstCard = page.locator('.cursor-pointer').first();
  await firstCard.click();

  // Procura botão de ver transcrição
  const transcriptButton = page.getByRole('button', {
    name: /transcrição|transcript|ver mais/i
  }).first();

  if (await transcriptButton.isVisible()) {
    await transcriptButton.click();

    // Modal/dialog deve abrir
    await expect(page.locator('[role="dialog"]')).toBeVisible();

    // Deve ter conteúdo da transcrição
    await expect(
      page.locator('[role="dialog"]').locator('text=/entrevista|interview|pergunta|resposta/i')
    ).toBeVisible();
  } else {
    test.skip('Nenhuma transcrição disponível');
  }
});
```

### 🌳 Módulo: Exploration

#### X001: Visualizar Árvore de Exploração
**Prioridade**: P1 (Alto)
**User Story**: Como usuário, quero ver a árvore de decisões/cenários

```typescript
test('X001 - View exploration tree', async ({ page }) => {
  await page.goto('/');
  const firstCard = page.locator('.cursor-pointer').first();
  await firstCard.click();

  // Procura seção de exploration
  const explorationSection = page.locator('text=/exploration|exploração/i').first();

  if (await explorationSection.isVisible()) {
    // Deve ter visualização de árvore ou nós
    await expect(
      page.locator('[data-testid="exploration-tree"]')
        .or(page.locator('text=/nó|node|cenário|scenario/i'))
    ).toBeVisible();
  } else {
    test.skip('Nenhuma exploração disponível');
  }
});
```

#### X002: Navegar Entre Nós da Exploração
**Prioridade**: P2 (Médio)
**User Story**: Como usuário, quero explorar diferentes nós/cenários

```typescript
test('X002 - Navigate exploration nodes', async ({ page }) => {
  await page.goto('/');
  const firstCard = page.locator('.cursor-pointer').first();
  await firstCard.click();

  // Clica em um nó da exploração
  const explorationNode = page.locator('[data-testid="exploration-node"]').first();

  if (await explorationNode.isVisible()) {
    await explorationNode.click();

    // Deve mostrar detalhes do nó
    await expect(
      page.locator('text=/cenário|scenario|descrição|description/i')
    ).toBeVisible();
  } else {
    test.skip('Nenhum nó de exploração disponível');
  }
});
```

### 👤 Módulo: Synths

#### Y001: Listar Synths
**Prioridade**: P0 (Crítico)
**User Story**: Como usuário, quero ver todos os synths disponíveis

```typescript
test('Y001 - List synths', async ({ page }) => {
  await page.goto('/synths');
  await page.waitForLoadState('networkidle');

  // Verifica header
  await expect(
    page.locator('h2').filter({ hasText: /synths/i }).first()
  ).toBeVisible();

  // Cards ou empty state
  const hasSynthCards = await page.locator('[data-testid="synth-card"]').count() > 0;
  const hasEmptyState = await page.locator('text=/nenhum synth/i').count() > 0;

  expect(hasSynthCards || hasEmptyState).toBeTruthy();
});
```

#### Y002: Ver Detalhes do Synth
**Prioridade**: P1 (Alto)
**User Story**: Como usuário, quero ver detalhes e personalidade de um synth

```typescript
test('Y002 - View synth details', async ({ page }) => {
  await page.goto('/synths');
  await page.waitForLoadState('networkidle');

  // Clica no primeiro synth
  const synthCard = page.locator('[data-testid="synth-card"]').first();

  if (await synthCard.isVisible()) {
    await synthCard.click();

    // Dialog/modal deve abrir
    await expect(page.locator('[role="dialog"]')).toBeVisible();

    // Deve mostrar características do synth
    await expect(
      page.locator('[role="dialog"]').locator('text=/personalidade|personality|traço|trait/i')
    ).toBeVisible();
  } else {
    test.skip('Nenhum synth disponível');
  }
});
```

#### Y003: Chat com Synth
**Prioridade**: P2 (Médio)
**User Story**: Como usuário, quero conversar com um synth

```typescript
test('Y003 - Chat with synth', async ({ page }) => {
  await page.goto('/synths');
  await page.waitForLoadState('networkidle');

  // Clica em chat
  const chatButton = page.getByRole('button', { name: /chat|conversar/i }).first();

  if (await chatButton.isVisible()) {
    await chatButton.click();

    // Dialog de chat deve abrir
    await expect(page.locator('[role="dialog"]')).toBeVisible();

    // Input de mensagem deve estar visível
    await expect(
      page.locator('[role="dialog"]').getByPlaceholder(/mensagem|message/i)
    ).toBeVisible();
  } else {
    test.skip('Chat não disponível');
  }
});
```

### 📈 Módulo: Results & Analysis

#### R001: Visualizar Gráficos de Resultado
**Prioridade**: P1 (Alto)
**User Story**: Como usuário, quero ver análises visuais dos resultados

```typescript
test('R001 - View result charts', async ({ page }) => {
  await page.goto('/');
  const firstCard = page.locator('.cursor-pointer').first();
  await firstCard.click();

  // Procura por seção de análises
  const analysisTab = page.getByRole('tab', { name: /análise|analysis|resultados|results/i });

  if (await analysisTab.isVisible()) {
    await analysisTab.click();

    // Deve ter gráficos (canvas ou svg)
    await expect(
      page.locator('canvas').or(page.locator('svg'))
    ).toBeVisible({ timeout: 10000 });
  } else {
    test.skip('Análises não disponíveis');
  }
});
```

#### R002: Navegação Entre Fases de Análise
**Prioridade**: P2 (Médio)
**User Story**: Como usuário, quero navegar entre diferentes fases de análise

```typescript
test('R002 - Navigate analysis phases', async ({ page }) => {
  await page.goto('/');
  const firstCard = page.locator('.cursor-pointer').first();
  await firstCard.click();

  // Clica em tab de análises
  const analysisTab = page.getByRole('tab', { name: /análise|analysis/i });
  if (await analysisTab.isVisible()) {
    await analysisTab.click();

    // Deve ter múltiplas fases/tabs
    const phaseTabs = page.locator('[role="tab"]').filter({
      hasText: /fase|phase|overview|insights/i
    });

    const count = await phaseTabs.count();
    if (count >= 2) {
      // Clica na segunda fase
      await phaseTabs.nth(1).click();

      // Conteúdo deve mudar
      await page.waitForTimeout(500);
      await expect(page.locator('canvas, svg')).toBeVisible();
    }
  } else {
    test.skip('Análises não disponíveis');
  }
});
```

### 🔄 Módulo: Responsividade & UX

#### U001: Responsividade Mobile
**Prioridade**: P2 (Médio)
**User Story**: Como usuário mobile, quero usar a aplicação no meu celular

```typescript
test('U001 - Mobile responsiveness', async ({ page }) => {
  // Define viewport mobile
  await page.setViewportSize({ width: 375, height: 667 });

  await page.goto('/');

  // Verifica que página carrega
  await expect(page).toHaveTitle('SynthLab');

  // Header deve estar visível
  await expect(page.locator('header')).toBeVisible();

  // Botões devem estar acessíveis (não cortados)
  const createButton = page.getByRole('button', { name: /criar/i }).first();
  await expect(createButton).toBeVisible();
});
```

#### U002: Loading States
**Prioridade**: P2 (Médio)
**User Story**: Como usuário, quero ver indicadores de carregamento

```typescript
test('U002 - Loading states visible', async ({ page }) => {
  // Slow down network to see loading states
  await page.route('**/*', route => {
    setTimeout(() => route.continue(), 1000);
  });

  const loadingPromise = page.locator('[role="status"]').or(
    page.locator('text=/carregando|loading/i')
  ).waitFor({ state: 'visible', timeout: 3000 });

  await page.goto('/');

  // Loading indicator deve aparecer
  await loadingPromise;
});
```

#### U003: Error States
**Prioridade**: P2 (Médio)
**User Story**: Como usuário, quero ver mensagens claras quando algo dá errado

```typescript
test('U003 - Error states display correctly', async ({ page }) => {
  // Simula erro de API
  await page.route('**/api/**', route => {
    route.fulfill({
      status: 500,
      body: JSON.stringify({ detail: 'Erro interno do servidor' })
    });
  });

  await page.goto('/');
  await page.waitForLoadState('networkidle');

  // Deve mostrar mensagem de erro
  await expect(
    page.locator('text=/erro|error|falha|problema/i')
  ).toBeVisible({ timeout: 10000 });
});
```

---

## 📊 Priorização

### P0 - Crítico (Smoke Tests + Core Features)
**Deve rodar em**: Production, Staging, Local
**Bloqueante para deploy**: Sim

- ST001-ST007 (Todos os smoke tests)
- E001-E003 (CRUD básico de experimentos)
- S001-S002 (Criar e listar simulações)
- I001 (Criar entrevista)
- Y001 (Listar synths)

### P1 - Alto (Features Importantes)
**Deve rodar em**: Staging, Local
**Bloqueante para deploy**: Recomendado

- E004-E005 (Validações e navegação)
- S003 (Detalhes de simulação)
- I002-I003 (Status e transcrição de entrevistas)
- X001 (Visualizar exploração)
- Y002 (Detalhes de synth)
- R001 (Gráficos de resultado)

### P2 - Médio (Nice to Have)
**Deve rodar em**: Local, ocasionalmente Staging
**Bloqueante para deploy**: Não

- X002 (Navegação entre nós)
- Y003 (Chat com synth)
- R002 (Navegação entre fases)
- U001-U003 (UX e responsividade)

---

## 🛠️ Implementação

### Estrutura de Arquivos Recomendada

```
frontend/tests/e2e/
├── TEST_SCENARIOS.md           # Este arquivo
├── smoke/                      # Smoke tests (production)
│   ├── health-check.spec.ts
│   ├── api-connectivity.spec.ts
│   └── critical-flows.spec.ts
├── experiments/                # Testes de experimentos
│   ├── crud.spec.ts
│   ├── navigation.spec.ts
│   └── validation.spec.ts
├── simulations/                # Testes de simulações
│   ├── create.spec.ts
│   └── details.spec.ts
├── interviews/                 # Testes de entrevistas
│   ├── create.spec.ts
│   ├── status.spec.ts
│   └── transcript.spec.ts
├── exploration/                # Testes de exploration
│   └── tree-navigation.spec.ts
├── synths/                     # Testes de synths
│   ├── list.spec.ts
│   ├── details.spec.ts
│   └── chat.spec.ts
├── results/                    # Testes de análises
│   └── charts.spec.ts
└── ux/                         # Testes de UX
    ├── responsive.spec.ts
    ├── loading-states.spec.ts
    └── error-states.spec.ts
```

### Tags para Organização

```typescript
// Usar tags do Playwright para filtrar testes
test.describe('Experiments @critical @smoke', () => {
  // Testes críticos
});

test.describe('Advanced Features @p2', () => {
  // Testes de prioridade baixa
});
```

### Comandos de Execução

```bash
# Smoke tests apenas (production)
npx playwright test --grep @smoke

# Testes críticos (staging)
npx playwright test --grep "@critical"

# Testes de um módulo específico
npx playwright test experiments/

# Pular testes lentos
npx playwright test --grep-invert "@slow"
```

### Configuração de Timeouts

```typescript
// playwright.config.ts
export default defineConfig({
  timeout: 30000,        // 30s por teste (padrão)
  expect: {
    timeout: 10000,      // 10s para expects
  },

  // Smoke tests mais rápidos
  projects: [
    {
      name: 'smoke',
      testMatch: '**/smoke/**/*.spec.ts',
      timeout: 10000,    // 10s para smoke tests
    },
  ],
});
```

---

## 📝 Próximos Passos

1. ✅ Criar estrutura de pastas
2. ⬜ Implementar smoke tests (ST001-ST007)
3. ⬜ Implementar testes P0 de experimentos (E001-E003)
4. ⬜ Adicionar testes de simulações (S001-S002)
5. ⬜ Configurar CI/CD para rodar smoke tests após deploy
6. ⬜ Implementar testes P1 gradualmente
7. ⬜ Adicionar testes P2 conforme necessidade

---

## 🔗 Referências

- [Playwright Best Practices](https://playwright.dev/docs/best-practices)
- [E2E Testing Guide](../E2E_TESTING.md)
- [Railway Environments](../../docs/railway-environments.md)
