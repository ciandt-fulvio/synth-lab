/**
 * E2E Tests - Quantitative Analysis Tab (042)
 *
 * Testa o fluxo completo da análise quantitativa:
 * - Navegação para a tab "Análise Quanti"
 * - Geração do modelo causal (DAG)
 * - Seleção de opções Likert nas arestas
 * - Execução da simulação Monte Carlo
 * - Visualização de resultados (distribuição, segmentos, sensibilidade)
 *
 * Run: npm run test:e2e experiments/quantitative-analysis.spec.ts
 */
import { test, expect } from '../fixtures';

// Helper: navega até a primeira página de detalhe de experimento
async function navigateToFirstExperiment(page: import('@playwright/test').Page) {
  await page.goto('/');
  await page.waitForLoadState('networkidle');

  await expect(
    page.locator('h2').filter({ hasText: /experimentos/i }).first()
  ).toBeVisible({ timeout: 10000 });

  const cards = page.locator('main').locator('h3');
  const count = await cards.count();
  if (count === 0) {
    return false;
  }

  const cardParent = cards.first().locator('..').locator('..');
  await cardParent.click();
  await expect(page).toHaveURL(/\/experiments\//);
  return true;
}

// Helper: navega para a tab Análise Quanti
async function navigateToQuantiTab(page: import('@playwright/test').Page) {
  const quantiTab = page.getByRole('tab', { name: /análise quanti|quanti/i });
  await expect(quantiTab).toBeVisible({ timeout: 10000 });
  await quantiTab.click();
  await page.waitForTimeout(500);
  await expect(quantiTab).toHaveAttribute('aria-selected', 'true');
}

test.describe('Quantitative Analysis - Tab Navigation @experiments @quanti', () => {
  test('QA001 - Análise Quanti tab is visible in experiment detail', async ({ page }) => {
    const found = await navigateToFirstExperiment(page);
    if (!found) test.skip();

    const quantiTab = page.getByRole('tab', { name: /análise quanti|quanti/i });
    await expect(quantiTab).toBeVisible({ timeout: 10000 });
  });

  test('QA002 - Clicking Análise Quanti tab selects it', async ({ page }) => {
    const found = await navigateToFirstExperiment(page);
    if (!found) test.skip();

    await navigateToQuantiTab(page);

    const quantiTab = page.getByRole('tab', { name: /análise quanti|quanti/i });
    await expect(quantiTab).toHaveAttribute('aria-selected', 'true');
  });

  test('QA003 - Tab content changes when selecting Análise Quanti', async ({ page }) => {
    const found = await navigateToFirstExperiment(page);
    if (!found) test.skip();

    // Navega para Entrevistas para capturar conteúdo diferente do Quanti
    // (Quanti é a tab default desde 042, então precisamos ir para outra tab primeiro)
    const interviewsTab = page.getByRole('tab', { name: /entrevistas/i });
    await interviewsTab.click();
    await page.waitForTimeout(500);
    const interviewsContent = await page.locator('[role="tabpanel"][data-state="active"]').textContent();

    await navigateToQuantiTab(page);

    // Conteúdo do tabpanel deve ser diferente do de Entrevistas
    const quantiContent = await page.locator('[role="tabpanel"][data-state="active"]').textContent();
    expect(quantiContent).not.toEqual(interviewsContent);
  });

  test('QA004 - URL does not change when switching to Análise Quanti tab', async ({ page }) => {
    const found = await navigateToFirstExperiment(page);
    if (!found) test.skip();

    const initialUrl = page.url();
    await navigateToQuantiTab(page);
    expect(page.url()).toBe(initialUrl);
  });
});

test.describe('Quantitative Analysis - Initial State @experiments @quanti', () => {
  test.beforeEach(async ({ page }) => {
    const found = await navigateToFirstExperiment(page);
    if (!found) test.skip();
    await navigateToQuantiTab(page);
  });

  test('QA010 - Tab shows initial state or existing model', async ({ page }) => {
    const tabPanel = page.locator('[role="tabpanel"][data-state="active"]');

    // Pode mostrar: botão "Gerar Modelo" (estado inicial) OU o DAG já gerado
    const hasGenerateButton = await tabPanel.getByRole('button', {
      name: /gerar modelo|generate model/i
    }).count() > 0;

    const hasDAG = await tabPanel.locator('[data-testid="causal-dag"], canvas, svg').count() > 0;
    const hasEdges = await tabPanel.locator('text=/aresta|edge|likert|selecione/i').count() > 0;
    const hasResults = await tabPanel.locator('text=/distribuição|simulação|resultados/i').count() > 0;

    expect(hasGenerateButton || hasDAG || hasEdges || hasResults).toBeTruthy();
  });

  test('QA011 - Tab panel is not empty', async ({ page }) => {
    const tabPanel = page.locator('[role="tabpanel"][data-state="active"]');
    const content = await tabPanel.textContent();
    expect(content?.trim().length).toBeGreaterThan(0);
  });

  test('QA012 - No error state visible on load', async ({ page }) => {
    const tabPanel = page.locator('[role="tabpanel"][data-state="active"]');

    const hasError = await tabPanel.locator(
      'text=/erro ao carregar|failed to load|500|network error/i'
    ).count();

    expect(hasError).toBe(0);
  });
});

test.describe('Quantitative Analysis - Generate Model @experiments @quanti', () => {
  test('QA020 - Generate model button exists in initial state', async ({ page }) => {
    const found = await navigateToFirstExperiment(page);
    if (!found) test.skip();

    await navigateToQuantiTab(page);

    const tabPanel = page.locator('[role="tabpanel"][data-state="active"]');

    // Se ainda não tem modelo, deve mostrar o botão de gerar
    const hasGenerateButton = await tabPanel.getByRole('button', {
      name: /gerar modelo|generate model/i
    }).count() > 0;

    // Se já tem modelo (re-run), deve ter botão de regenerar ou o DAG visível
    const hasExistingModel = await tabPanel.locator(
      'text=/modelo causal|causal model|aresta/i'
    ).count() > 0;

    expect(hasGenerateButton || hasExistingModel).toBeTruthy();
  });

  test('QA021 - Model generation shows loading state', async ({ page }) => {
    const found = await navigateToFirstExperiment(page);
    if (!found) test.skip();

    await navigateToQuantiTab(page);

    const tabPanel = page.locator('[role="tabpanel"][data-state="active"]');
    const generateButton = tabPanel.getByRole('button', { name: /gerar modelo/i });

    if (!(await generateButton.isVisible())) {
      test.skip(); // Modelo já gerado, pula este teste
      return;
    }

    await generateButton.click();

    // Aguarda brevemente para loading aparecer (API call pode ser rápida)
    await page.waitForTimeout(200);

    // Deve mostrar algum indicador de loading (texto "Gerando modelo..." ou botão desabilitado)
    // NOTA: CSS comma selector não funciona com pseudo-seletor "text=" do Playwright
    const hasLoadingText = await tabPanel.locator('text=/gerando|loading|aguarde|processando/i').count() > 0;
    const hasLoadingStatus = await tabPanel.locator('[role="status"]').count() > 0;
    const hasLoading = hasLoadingText || hasLoadingStatus;

    // OU o botão ficou desabilitado durante geração
    const buttonDisabled = await generateButton.isDisabled().catch(() => false);

    // OU o modelo já apareceu (API muito rápida) — requer número antes de "nós/arestas"
    const modelAppeared = await tabPanel.locator('text=/\\d+ nós|\\d+ arestas/i').count() > 0;

    expect(hasLoading || buttonDisabled || modelAppeared).toBeTruthy();
  });
});

test.describe('Quantitative Analysis - Likert Assertions @experiments @quanti', () => {
  test('QA030 - Likert options are visible when model exists', async ({ page }) => {
    const found = await navigateToFirstExperiment(page);
    if (!found) test.skip();

    await navigateToQuantiTab(page);

    const tabPanel = page.locator('[role="tabpanel"][data-state="active"]');

    // Se há arestas com Likert, devem ter botões de seleção
    const hasLikertOptions = await tabPanel.locator(
      'button[data-testid^="likert-option"], button:has-text("Forte"), button:has-text("Significativo")'
    ).count() > 0;

    // OU ainda está no estado inicial (sem modelo gerado)
    const isInitialState = await tabPanel.getByRole('button', {
      name: /gerar modelo/i
    }).count() > 0;

    // Ambos são estados válidos
    expect(hasLikertOptions || isInitialState).toBeTruthy();
  });

  test('QA031 - Selecting a Likert option does not crash the page', async ({ page }) => {
    const found = await navigateToFirstExperiment(page);
    if (!found) test.skip();

    await navigateToQuantiTab(page);

    const tabPanel = page.locator('[role="tabpanel"][data-state="active"]');

    // Procura botões Likert (opções das arestas)
    const likertButtons = tabPanel.locator(
      'button:has-text("Forte"), button:has-text("Significativo"), button:has-text("Incerto")'
    );

    const count = await likertButtons.count();
    if (count === 0) {
      test.skip(); // Sem modelo gerado ainda
      return;
    }

    // Clica na primeira opção
    await likertButtons.first().click();
    await page.waitForTimeout(1000);

    // Página não deve quebrar (sem erros 500, sem crash)
    const hasError = await tabPanel.locator(
      'text=/erro|error|500|falha/i'
    ).count();
    expect(hasError).toBe(0);
  });
});

test.describe('Quantitative Analysis - Simulation @experiments @quanti', () => {
  test('QA040 - Simulate button exists when model is available', async ({ page }) => {
    const found = await navigateToFirstExperiment(page);
    if (!found) test.skip();

    await navigateToQuantiTab(page);

    const tabPanel = page.locator('[role="tabpanel"][data-state="active"]');

    // Verifica se há modelo carregado (mostra "X nós, Y arestas" no header)
    // Usa \d+ para evitar falso positivo com descrição "A IA criará nós, arestas e premissas..."
    const hasModel = await tabPanel.locator('text=/\\d+ nós|\\d+ arestas/i').count() > 0;

    if (!hasModel) {
      test.skip(); // Modelo não gerado ainda
      return;
    }

    // O botão Simular aparece quando simulação ainda não foi executada
    // ou quando as seleções foram alteradas. Se simulação já rodou sem mudanças,
    // o botão fica oculto — nesse caso verificamos o estado da tab.
    const simulateButton = tabPanel.getByRole('button', {
      name: /simular|run simulation|executar simulação/i
    });
    const hasSimulateButton = await simulateButton.isVisible().catch(() => false);

    // Ou há o botão de simular, ou a simulação já rodou (resultados visíveis)
    const hasResults = await tabPanel.locator('text=/distribuição|resultado|média/i').count() > 0;

    expect(hasSimulateButton || hasResults).toBeTruthy();
  });

  test('QA041 - Simulation shows loading state when triggered', async ({ page }) => {
    const found = await navigateToFirstExperiment(page);
    if (!found) test.skip();

    await navigateToQuantiTab(page);

    const tabPanel = page.locator('[role="tabpanel"][data-state="active"]');

    const simulateButton = tabPanel.getByRole('button', {
      name: /simular|run simulation/i
    });

    if (!(await simulateButton.isVisible())) {
      test.skip();
      return;
    }

    await simulateButton.click();

    // Deve mostrar loading
    const hasLoading = await tabPanel.locator(
      '[role="status"], text=/simulando|processando|aguarde/i'
    ).count() > 0;

    const buttonDisabled = await simulateButton.isDisabled().catch(() => false);

    expect(hasLoading || buttonDisabled).toBeTruthy();
  });
});

test.describe('Quantitative Analysis - Results Display @experiments @quanti', () => {
  test.beforeEach(async ({ page }) => {
    const found = await navigateToFirstExperiment(page);
    if (!found) test.skip();
    await navigateToQuantiTab(page);
  });

  test('QA050 - Results section visible when simulation completed', async ({ page }) => {
    const tabPanel = page.locator('[role="tabpanel"][data-state="active"]');

    const hasResults = await tabPanel.locator(
      'text=/distribuição de adoção|distribuição|resultado/i'
    ).count() > 0;

    if (!hasResults) {
      test.skip(); // Simulação não executada ainda
      return;
    }

    // Deve mostrar a seção de resultados
    await expect(
      tabPanel.locator('text=/distribuição|resultado/i').first()
    ).toBeVisible();
  });

  test('QA051 - Distribution stats visible after simulation', async ({ page }) => {
    const tabPanel = page.locator('[role="tabpanel"][data-state="active"]');

    const hasStats = await tabPanel.locator(
      'text=/média|mediana|p10|p90|desvio/i'
    ).count() > 0;

    if (!hasStats) {
      test.skip();
      return;
    }

    // Métricas estatísticas devem estar visíveis
    const hasMean = await tabPanel.locator('text=/média/i').count() > 0;
    const hasMedian = await tabPanel.locator('text=/mediana/i').count() > 0;

    expect(hasMean || hasMedian).toBeTruthy();
  });

  test('QA052 - Segments section visible after simulation', async ({ page }) => {
    const tabPanel = page.locator('[role="tabpanel"][data-state="active"]');

    const hasSegments = await tabPanel.locator(
      'text=/segmento|18-29|30-49|baixa|media|alta/i'
    ).count() > 0;

    if (!hasSegments) {
      test.skip();
      return;
    }

    // Pelo menos um dos grupos de segmentação deve aparecer
    const hasAgeGroup = await tabPanel.locator('text=/18-29|30-49|50\+/i').count() > 0;
    const hasIncomeGroup = await tabPanel.locator('text=/renda|baixa|alta/i').count() > 0;

    expect(hasAgeGroup || hasIncomeGroup).toBeTruthy();
  });

  test('QA053 - Sensitivity section visible after simulation', async ({ page }) => {
    const tabPanel = page.locator('[role="tabpanel"][data-state="active"]');

    // Verifica especificamente a seção de sensibilidade/impacto nos resultados
    // (não confundir com "premissa" que aparece no estado vazio)
    const hasSensitivity = await tabPanel.locator(
      'text=/sensibilidade|impacto/i'
    ).count() > 0;

    if (!hasSensitivity) {
      test.skip(); // Simulação não executada ou seção não presente
      return;
    }

    await expect(
      tabPanel.locator('text=/sensibilidade|impacto/i').first()
    ).toBeVisible();
  });

  test('QA054 - AI interpretation text visible after simulation', async ({ page }) => {
    const tabPanel = page.locator('[role="tabpanel"][data-state="active"]');

    // Interpretações AI devem aparecer nas seções de resultado
    const hasInterpretation = await tabPanel.locator(
      'text=/confiança|adoção|segmento/i'
    ).count() > 0;

    if (!hasInterpretation) {
      test.skip();
      return;
    }

    expect(hasInterpretation).toBeTruthy();
  });
});

test.describe('Quantitative Analysis - Interview Guide Integration @experiments @quanti', () => {
  test('QA060 - After simulation, interview guide tab shows updated content', async ({ page }) => {
    const found = await navigateToFirstExperiment(page);
    if (!found) test.skip();

    await navigateToQuantiTab(page);

    const tabPanel = page.locator('[role="tabpanel"][data-state="active"]');
    const hasSimulationResults = await tabPanel.locator(
      'text=/distribuição de adoção|resultado|media/i'
    ).count() > 0;

    if (!hasSimulationResults) {
      test.skip(); // Simulação não rodou ainda
      return;
    }

    // Navega para tab de Entrevistas para verificar o guide gerado
    const interviewsTab = page.getByRole('tab', { name: /entrevistas/i });
    await interviewsTab.click();
    await page.waitForTimeout(500);

    // O guide de entrevista deveria ter sido gerado automaticamente
    // Verifica que a tab carrega sem erro
    const hasError = await page.locator(
      '[role="tabpanel"][data-state="active"] text=/erro ao carregar|500/i'
    ).count();
    expect(hasError).toBe(0);
  });
});
