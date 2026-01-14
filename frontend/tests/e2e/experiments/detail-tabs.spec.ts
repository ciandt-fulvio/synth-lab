/**
 * E2E Tests - Experiment Detail Tabs Navigation
 *
 * Testa a navegação entre todas as tabs na página de detalhe do experimento:
 * - Análise (scorecard)
 * - Entrevistas
 * - Explorações
 * - Materiais
 * - Relatórios
 *
 * Run: npm run test:e2e experiments/detail-tabs.spec.ts
 */
import { test, expect } from '@playwright/test';

test.describe('Experiments - Detail Tabs @experiments', () => {
  test.beforeEach(async ({ page }) => {
    // Navega para home e clica no primeiro experimento
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Wait for experiments page to load
    await expect(page.locator('h2').filter({ hasText: /experimentos/i })).toBeVisible({ timeout: 10000 });

    const firstCard = page.locator('.cursor-pointer').filter({
      has: page.locator('h3')
    }).first();

    await expect(firstCard).toBeVisible({ timeout: 10000 });
    await firstCard.click();
    await page.waitForLoadState('networkidle');

    // Verifica que navegou para página de detalhe
    await expect(page).toHaveURL(/\/experiments\/exp_/);

    // Wait for experiment detail page to load
    await expect(page.locator('h2').first()).toBeVisible({ timeout: 10000 });
    await expect(page.getByRole('tab', { name: /análise/i })).toBeVisible({ timeout: 10000 });
  });

  test('DT001 - All tabs are visible', async ({ page }) => {
    // Verifica que todas as tabs estão presentes
    const analysisTab = page.getByRole('tab', { name: /análise/i });
    const interviewsTab = page.getByRole('tab', { name: /entrevistas/i });
    const explorationsTab = page.getByRole('tab', { name: /explorações/i });
    const materialsTab = page.getByRole('tab', { name: /materiais/i });
    const reportsTab = page.getByRole('tab', { name: /relatórios/i });

    await expect(analysisTab).toBeVisible();
    await expect(interviewsTab).toBeVisible();
    await expect(explorationsTab).toBeVisible();
    await expect(materialsTab).toBeVisible();
    await expect(reportsTab).toBeVisible();
  });

  test('DT002 - Análise tab is selected by default', async ({ page }) => {
    // Tab Análise deve estar selecionada por padrão
    const analysisTab = page.getByRole('tab', { name: /análise/i });
    await expect(analysisTab).toHaveAttribute('aria-selected', 'true');
  });

  test('DT003 - Análise tab shows scorecard or message', async ({ page }) => {
    const analysisTab = page.getByRole('tab', { name: /análise/i });

    // Garante que está na tab Análise
    if (await analysisTab.getAttribute('aria-selected') !== 'true') {
      await analysisTab.click();
      await page.waitForTimeout(500);
    }

    // Deve mostrar scorecard OU mensagem de scorecard não configurado
    const hasScorecardConfig = await page.locator('h3').filter({
      hasText: /scorecard não configurado/i
    }).count() > 0;

    const hasScorecardContent = await page.locator('text=/scorecard|atributos|dimensões/i').count() > 0;

    // Uma das duas opções deve ser verdadeira
    expect(hasScorecardConfig || hasScorecardContent).toBeTruthy();
  });

  test('DT004 - Navigate to Entrevistas tab', async ({ page }) => {
    const interviewsTab = page.getByRole('tab', { name: /entrevistas/i });
    await interviewsTab.click();
    await page.waitForTimeout(500);

    // Tab deve estar selecionada
    await expect(interviewsTab).toHaveAttribute('aria-selected', 'true');

    // Deve mostrar conteúdo de entrevistas
    await expect(
      page.locator('h3').filter({ hasText: /entrevistas/i })
    ).toBeVisible({ timeout: 5000 });
  });

  test('DT005 - Entrevistas tab shows count', async ({ page }) => {
    const interviewsTab = page.getByRole('tab', { name: /entrevistas/i });
    await interviewsTab.click();
    await page.waitForTimeout(500);

    // Deve mostrar contagem (ex: "0 entrevista(s) realizada(s)")
    const countText = page.locator('text=/\d+\s*entrevista\(s\)/i');
    await expect(countText).toBeVisible({ timeout: 5000 });
  });

  test('DT006 - Entrevistas tab shows empty state or list', async ({ page }) => {
    const interviewsTab = page.getByRole('tab', { name: /entrevistas/i });
    await interviewsTab.click();
    await page.waitForTimeout(500);

    // Deve mostrar botão "Nova Entrevista"
    const newInterviewBtn = page.getByRole('button', { name: /nova entrevista/i });
    await expect(newInterviewBtn).toBeVisible();

    // Deve ter empty state OU lista de entrevistas
    const hasEmptyState = await page.locator('text=/nenhuma entrevista/i').count() > 0;
    const hasList = await page.locator('[data-testid="interview-card"]').count() > 0;

    expect(hasEmptyState || hasList).toBeTruthy();
  });

  test('DT007 - Navigate to Explorações tab', async ({ page }) => {
    const explorationsTab = page.getByRole('tab', { name: /explorações/i });

    // Verifica se tab está habilitada
    const isDisabled = await explorationsTab.getAttribute('aria-disabled');

    if (isDisabled === 'true') {
      test.skip('Tab Explorações está desabilitada para este experimento');
    }

    await explorationsTab.click();
    await page.waitForTimeout(500);

    // Tab deve estar selecionada
    await expect(explorationsTab).toHaveAttribute('aria-selected', 'true');
  });

  test('DT008 - Explorações tab shows content when enabled', async ({ page }) => {
    const explorationsTab = page.getByRole('tab', { name: /explorações/i });

    const isDisabled = await explorationsTab.getAttribute('aria-disabled');

    if (isDisabled === 'true') {
      test.skip('Tab Explorações está desabilitada');
    }

    await explorationsTab.click();
    await page.waitForTimeout(500);

    // Deve mostrar algum conteúdo relacionado a explorações
    // (árvore, nós, cenários, ou empty state)
    const hasContent = await page.locator('text=/exploração|exploration|cenário|scenario|nó|node/i').count() > 0;
    expect(hasContent).toBeTruthy();
  });

  test('DT009 - Navigate to Materiais tab', async ({ page }) => {
    const materialsTab = page.getByRole('tab', { name: /materiais/i });
    await materialsTab.click();
    await page.waitForTimeout(500);

    // Tab deve estar selecionada
    await expect(materialsTab).toHaveAttribute('aria-selected', 'true');

    // Deve mostrar heading "Materiais"
    await expect(
      page.locator('h3').filter({ hasText: /materiais/i })
    ).toBeVisible({ timeout: 5000 });
  });

  test('DT010 - Materiais tab shows count', async ({ page }) => {
    const materialsTab = page.getByRole('tab', { name: /materiais/i });
    await materialsTab.click();
    await page.waitForTimeout(500);

    // Deve mostrar contagem (ex: "0 arquivo(s) anexado(s)")
    const countText = page.locator('text=/\d+\s*arquivo\(s\)/i');
    await expect(countText).toBeVisible({ timeout: 5000 });
  });

  test('DT011 - Materiais tab shows upload area', async ({ page }) => {
    const materialsTab = page.getByRole('tab', { name: /materiais/i });
    await materialsTab.click();
    await page.waitForTimeout(500);

    // Deve mostrar área de upload
    const uploadArea = page.locator('text=/arraste arquivos|escolher arquivos|selecionar/i');
    await expect(uploadArea.first()).toBeVisible({ timeout: 5000 });
  });

  test('DT012 - Navigate to Relatórios tab', async ({ page }) => {
    const reportsTab = page.getByRole('tab', { name: /relatórios/i });
    await reportsTab.click();
    await page.waitForTimeout(500);

    // Tab deve estar selecionada
    await expect(reportsTab).toHaveAttribute('aria-selected', 'true');

    // Deve mostrar heading "Relatórios"
    await expect(
      page.locator('h3').filter({ hasText: /relatórios/i })
    ).toBeVisible({ timeout: 5000 });
  });

  test('DT013 - Relatórios tab shows description', async ({ page }) => {
    const reportsTab = page.getByRole('tab', { name: /relatórios/i });
    await reportsTab.click();
    await page.waitForTimeout(500);

    // Deve mostrar descrição
    const description = page.locator('text=/documentos gerados.*análises.*explorações/i');
    await expect(description).toBeVisible({ timeout: 5000 });
  });

  test('DT014 - Relatórios tab shows empty state or list', async ({ page }) => {
    const reportsTab = page.getByRole('tab', { name: /relatórios/i });
    await reportsTab.click();
    await page.waitForTimeout(500);

    // Deve ter empty state OU lista de relatórios
    const hasEmptyState = await page.locator('text=/nenhum relatório/i').count() > 0;
    const hasList = await page.locator('[data-testid="report-card"]').count() > 0;

    expect(hasEmptyState || hasList).toBeTruthy();
  });

  test('DT015 - Navigate between all tabs sequentially', async ({ page }) => {
    // Análise (já está selecionada)
    const analysisTab = page.getByRole('tab', { name: /análise/i });
    await expect(analysisTab).toHaveAttribute('aria-selected', 'true');

    // Entrevistas
    const interviewsTab = page.getByRole('tab', { name: /entrevistas/i });
    await interviewsTab.click();
    await page.waitForTimeout(500);
    await expect(interviewsTab).toHaveAttribute('aria-selected', 'true');

    // Explorações (se habilitada)
    const explorationsTab = page.getByRole('tab', { name: /explorações/i });
    const isDisabled = await explorationsTab.getAttribute('aria-disabled');
    if (isDisabled !== 'true') {
      await explorationsTab.click();
      await page.waitForTimeout(500);
      await expect(explorationsTab).toHaveAttribute('aria-selected', 'true');
    }

    // Materiais
    const materialsTab = page.getByRole('tab', { name: /materiais/i });
    await materialsTab.click();
    await page.waitForTimeout(500);
    await expect(materialsTab).toHaveAttribute('aria-selected', 'true');

    // Relatórios
    const reportsTab = page.getByRole('tab', { name: /relatórios/i });
    await reportsTab.click();
    await page.waitForTimeout(500);
    await expect(reportsTab).toHaveAttribute('aria-selected', 'true');

    // Volta para Análise
    await analysisTab.click();
    await page.waitForTimeout(500);
    await expect(analysisTab).toHaveAttribute('aria-selected', 'true');
  });

  test('DT016 - Tab content changes when switching tabs', async ({ page }) => {
    // Pega conteúdo da tab Análise
    const analysisContent = await page.locator('main').textContent();

    // Muda para Entrevistas
    const interviewsTab = page.getByRole('tab', { name: /entrevistas/i });
    await interviewsTab.click();
    await page.waitForTimeout(500);

    // Conteúdo deve ser diferente
    const interviewsContent = await page.locator('main').textContent();
    expect(interviewsContent).not.toEqual(analysisContent);

    // Muda para Materiais
    const materialsTab = page.getByRole('tab', { name: /materiais/i });
    await materialsTab.click();
    await page.waitForTimeout(500);

    // Conteúdo deve ser diferente novamente
    const materialsContent = await page.locator('main').textContent();
    expect(materialsContent).not.toEqual(interviewsContent);
    expect(materialsContent).not.toEqual(analysisContent);
  });

  test('DT017 - Tab badges show correct counts', async ({ page }) => {
    // Verifica que badges nas tabs mostram contagens corretas

    // Tab Entrevistas deve mostrar número
    const interviewsTab = page.getByRole('tab', { name: /entrevistas/i });
    const interviewsText = await interviewsTab.textContent();
    const hasInterviewCount = /\d+/.test(interviewsText || '');
    expect(hasInterviewCount).toBeTruthy();

    // Tab Materiais deve mostrar número
    const materialsTab = page.getByRole('tab', { name: /materiais/i });
    const materialsText = await materialsTab.textContent();
    const hasMaterialCount = /\d+/.test(materialsText || '');
    expect(hasMaterialCount).toBeTruthy();

    // Tab Relatórios deve mostrar número
    const reportsTab = page.getByRole('tab', { name: /relatórios/i });
    const reportsText = await reportsTab.textContent();
    const hasReportCount = /\d+/.test(reportsText || '');
    expect(hasReportCount).toBeTruthy();
  });

  test('DT018 - URL does not change when switching tabs', async ({ page }) => {
    // Salva URL inicial
    const initialUrl = page.url();

    // Navega entre tabs
    await page.getByRole('tab', { name: /entrevistas/i }).click();
    await page.waitForTimeout(300);
    expect(page.url()).toBe(initialUrl);

    await page.getByRole('tab', { name: /materiais/i }).click();
    await page.waitForTimeout(300);
    expect(page.url()).toBe(initialUrl);

    await page.getByRole('tab', { name: /relatórios/i }).click();
    await page.waitForTimeout(300);
    expect(page.url()).toBe(initialUrl);

    // URL deve permanecer a mesma (não deve adicionar hash ou query params)
  });

  test('DT019 - Selected tab persists after page interaction', async ({ page }) => {
    // Vai para tab Materiais
    const materialsTab = page.getByRole('tab', { name: /materiais/i });
    await materialsTab.click();
    await page.waitForTimeout(500);

    // Interage com a página (scroll, por exemplo)
    await page.evaluate(() => window.scrollTo(0, 100));
    await page.waitForTimeout(300);

    // Tab ainda deve estar selecionada
    await expect(materialsTab).toHaveAttribute('aria-selected', 'true');
  });

  test('DT020 - Disabled tab cannot be selected', async ({ page }) => {
    const explorationsTab = page.getByRole('tab', { name: /explorações/i });

    const isDisabled = await explorationsTab.getAttribute('aria-disabled');

    if (isDisabled !== 'true') {
      test.skip('Tab Explorações está habilitada para este experimento');
    }

    // Tenta clicar na tab desabilitada
    await explorationsTab.click({ force: true });
    await page.waitForTimeout(500);

    // Tab NÃO deve estar selecionada
    const isSelected = await explorationsTab.getAttribute('aria-selected');
    expect(isSelected).not.toBe('true');
  });
});

test.describe('Experiments - Tab Accessibility @experiments @a11y', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const firstCard = page.locator('.cursor-pointer').first();
    await firstCard.click();
    await page.waitForLoadState('networkidle');
  });

  test('DT021 - Tabs have correct ARIA attributes', async ({ page }) => {
    const analysisTab = page.getByRole('tab', { name: /análise/i });

    // Deve ter role="tab"
    await expect(analysisTab).toHaveAttribute('role', 'tab');

    // Deve ter aria-selected
    const ariaSelected = await analysisTab.getAttribute('aria-selected');
    expect(ariaSelected).toBeTruthy();

    // Tabpanel deve ter role="tabpanel"
    const tabpanel = page.locator('[role="tabpanel"]');
    await expect(tabpanel).toBeVisible();
  });

  test('DT022 - Keyboard navigation works (Arrow keys)', async ({ page }) => {
    const analysisTab = page.getByRole('tab', { name: /análise/i });

    // Foca na tab Análise
    await analysisTab.focus();

    // Pressiona ArrowRight para ir para próxima tab
    await page.keyboard.press('ArrowRight');
    await page.waitForTimeout(300);

    // Tab Entrevistas deve estar focada ou selecionada
    const interviewsTab = page.getByRole('tab', { name: /entrevistas/i });
    const isFocused = await interviewsTab.evaluate(el => el === document.activeElement);

    // Ou está focada ou está selecionada
    expect(isFocused || await interviewsTab.getAttribute('aria-selected') === 'true').toBeTruthy();
  });

  test('DT023 - Tab list has correct ARIA role', async ({ page }) => {
    // Tablist deve ter role="tablist"
    const tablist = page.locator('[role="tablist"]');
    await expect(tablist).toBeVisible();

    // Deve ter orientação horizontal
    const orientation = await tablist.getAttribute('aria-orientation');
    expect(orientation).toBe('horizontal');
  });
});
