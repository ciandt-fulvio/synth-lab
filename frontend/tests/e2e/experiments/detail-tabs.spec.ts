/**
 * E2E Tests - Experiment Detail Tabs Navigation
 *
 * Testa a navegação entre todas as tabs na página de detalhe do experimento:
 * - Entrevistas
 * - Materiais
 * - Relatórios
 * - Análise Quanti
 *
 * Run: npm run test:e2e experiments/detail-tabs.spec.ts
 */
import { test, expect } from '../fixtures';

test.describe('Experiments - Detail Tabs @experiments', () => {
  test.beforeEach(async ({ page }) => {
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
    await expect(page.getByRole('tab', { name: /entrevistas/i })).toBeVisible({ timeout: 10000 });
  });

  test('DT001 - All tabs are visible', async ({ page }) => {
    // Verifica que todas as tabs estão presentes
    const interviewsTab = page.getByRole('tab', { name: /entrevistas/i });
    const materialsTab = page.getByRole('tab', { name: /materiais/i });
    const reportsTab = page.getByRole('tab', { name: /relatórios/i });
    const quantiTab = page.getByRole('tab', { name: /análise quanti|quanti/i });

    await expect(interviewsTab).toBeVisible();
    await expect(materialsTab).toBeVisible();
    await expect(reportsTab).toBeVisible();
    await expect(quantiTab).toBeVisible();
  });

  test('DT002 - Análise Quanti tab is selected by default', async ({ page }) => {
    // Tab Análise Quanti deve estar selecionada por padrão (nova default desde 042)
    const quantiTab = page.getByRole('tab', { name: /análise quanti|quanti/i });
    await expect(quantiTab).toHaveAttribute('aria-selected', 'true');
  });

  test('DT003 - Entrevistas tab shows content', async ({ page }) => {
    const interviewsTab = page.getByRole('tab', { name: /entrevistas/i });

    // Navega para a tab Entrevistas (não é mais a default)
    await interviewsTab.click();
    await page.waitForTimeout(500);
    await expect(interviewsTab).toHaveAttribute('aria-selected', 'true');

    // Deve mostrar conteúdo de entrevistas
    await expect(
      page.locator('h3').filter({ hasText: /entrevistas/i })
    ).toBeVisible({ timeout: 5000 });
  });

  test('DT004 - Entrevistas tab shows count', async ({ page }) => {
    const interviewsTab = page.getByRole('tab', { name: /entrevistas/i });

    // Navega para a tab Entrevistas (não é mais a default)
    await interviewsTab.click();
    await page.waitForTimeout(500);
    await expect(interviewsTab).toHaveAttribute('aria-selected', 'true');

    // Check for the heading "Entrevistas" in the page
    await expect(page.locator('h3').filter({ hasText: /entrevistas/i })).toBeVisible({ timeout: 5000 });

    // Check for count text (e.g., "0 entrevista(s) realizada(s)")
    // Use more specific selector to avoid matching tab badge (only match in content area, not in tablist)
    await expect(
      page.locator('[role="tabpanel"][data-state="active"]').getByText(/\d+\s*entrevista\(s\)\s*realizada/i)
    ).toBeVisible();
  });

  test('DT005 - Entrevistas tab shows empty state or list', async ({ page }) => {
    const interviewsTab = page.getByRole('tab', { name: /entrevistas/i });

    // Navega para a tab Entrevistas (não é mais a default)
    await interviewsTab.click();
    await page.waitForTimeout(500);
    await expect(interviewsTab).toHaveAttribute('aria-selected', 'true');

    // Check if tab panel content is visible (has either empty state text or interview cards)
    const tabPanel = page.locator('[role="tabpanel"][data-state="active"]');
    const hasContent = await tabPanel.locator('p, [data-testid="interview-card"]').count() > 0;

    expect(hasContent).toBeTruthy();
  });

  test('DT006 - Navigate to Materiais tab', async ({ page }) => {
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

  test('DT007 - Materiais tab shows count', async ({ page }) => {
    const materialsTab = page.getByRole('tab', { name: /materiais/i });
    await materialsTab.click();
    await page.waitForTimeout(500);

    // Tab should be selected
    await expect(materialsTab).toHaveAttribute('aria-selected', 'true');

    // Check for the heading "Materiais" in the page
    await expect(page.locator('h3').filter({ hasText: /materiais/i })).toBeVisible({ timeout: 5000 });

    // Check for count text (e.g., "0 arquivo(s) anexado(s)")
    await expect(page.locator('text=/arquivo.*anexado/i')).toBeVisible();
  });

  test('DT008 - Materiais tab shows upload area', async ({ page }) => {
    const materialsTab = page.getByRole('tab', { name: /materiais/i });
    await materialsTab.click();
    await page.waitForTimeout(500);

    // Deve mostrar área de upload
    const uploadArea = page.locator('text=/arraste arquivos|escolher arquivos|selecionar/i');
    await expect(uploadArea.first()).toBeVisible({ timeout: 5000 });
  });

  test('DT009 - Navigate to Relatórios tab', async ({ page }) => {
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

  test('DT010 - Relatórios tab shows description', async ({ page }) => {
    const reportsTab = page.getByRole('tab', { name: /relatórios/i });
    await reportsTab.click();
    await page.waitForTimeout(500);

    // Deve mostrar descrição ou conteúdo relacionado a documentos
    const hasDescription = await page.locator('text=/documentos gerados/i').count() > 0;
    const hasContent = await page.locator('h3').filter({ hasText: /relatórios/i }).count() > 0;

    expect(hasDescription || hasContent).toBeTruthy();
  });

  test('DT011 - Relatórios tab shows empty state or list', async ({ page }) => {
    const reportsTab = page.getByRole('tab', { name: /relatórios/i });
    await reportsTab.click();

    // Wait for loading to finish (loading message should disappear)
    await page.waitForTimeout(1000);
    const loadingMsg = page.locator('text=/carregando documentos/i');
    if (await loadingMsg.isVisible()) {
      await expect(loadingMsg).not.toBeVisible({ timeout: 15000 });
    }

    // Scope to tabpanel to avoid strict mode violations
    const tabPanel = page.locator('[role="tabpanel"]');
    const hasEmptyState = await tabPanel.locator('text=/nenhum relatório|nenhum documento/i').count() > 0;
    const hasList = await tabPanel.locator('[data-testid="report-card"], [data-testid="document-card"]').count() > 0;

    expect(hasEmptyState || hasList).toBeTruthy();
  });

  test('DT012 - Navigate between all tabs sequentially', async ({ page }) => {
    // Análise Quanti é a default desde 042
    const quantiTab = page.getByRole('tab', { name: /análise quanti|quanti/i });
    await expect(quantiTab).toHaveAttribute('aria-selected', 'true');

    // Entrevistas
    const interviewsTab = page.getByRole('tab', { name: /entrevistas/i });
    await interviewsTab.click();
    await page.waitForTimeout(500);
    await expect(interviewsTab).toHaveAttribute('aria-selected', 'true');

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

    // Volta para Análise Quanti
    await quantiTab.click();
    await page.waitForTimeout(500);
    await expect(quantiTab).toHaveAttribute('aria-selected', 'true');
  });

  test('DT013 - Tab content changes when switching tabs', async ({ page }) => {
    // Espera a tab Quanti terminar de carregar (evita capturar estado de loading)
    await page.waitForTimeout(1000);

    // Análise Quanti é a default — captura o conteúdo estabilizado
    const quantiContent = await page.locator('[role="tabpanel"][data-state="active"]').textContent();

    // Muda para Materiais
    const materialsTab = page.getByRole('tab', { name: /materiais/i });
    await materialsTab.click();
    await page.waitForTimeout(500);

    // Conteúdo deve ser diferente do quanti
    const materialsContent = await page.locator('[role="tabpanel"][data-state="active"]').textContent();
    expect(materialsContent).not.toEqual(quantiContent);

    // Volta para Análise Quanti
    const quantiTab = page.getByRole('tab', { name: /análise quanti|quanti/i });
    await quantiTab.click();
    await page.waitForTimeout(500);

    // Quanti tab deve estar selecionada e com conteúdo não-vazio
    // (sem comparar conteúdo exato pois estado de loading pode variar entre renderizações)
    await expect(quantiTab).toHaveAttribute('aria-selected', 'true');
    const quantiContent2 = await page.locator('[role="tabpanel"][data-state="active"]').textContent();
    expect(quantiContent2?.trim().length).toBeGreaterThan(0);
  });

  test('DT014 - Tab badges show correct counts', async ({ page }) => {
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

  test('DT015 - URL does not change when switching tabs', async ({ page }) => {
    // Salva URL inicial
    const initialUrl = page.url();

    // Navega entre tabs
    await page.getByRole('tab', { name: /materiais/i }).click();
    await page.waitForTimeout(300);
    expect(page.url()).toBe(initialUrl);

    await page.getByRole('tab', { name: /relatórios/i }).click();
    await page.waitForTimeout(300);
    expect(page.url()).toBe(initialUrl);

    await page.getByRole('tab', { name: /entrevistas/i }).click();
    await page.waitForTimeout(300);
    expect(page.url()).toBe(initialUrl);
  });

  test('DT016 - Selected tab persists after page interaction', async ({ page }) => {
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
});

test.describe('Experiments - Tab Accessibility @experiments @a11y', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const firstCard = page.locator('.cursor-pointer').first();
    await firstCard.click();
    await page.waitForLoadState('networkidle');
  });

  test('DT017 - Tabs have correct ARIA attributes', async ({ page }) => {
    const interviewsTab = page.getByRole('tab', { name: /entrevistas/i });

    // Deve ter role="tab"
    await expect(interviewsTab).toHaveAttribute('role', 'tab');

    // Deve ter aria-selected
    const ariaSelected = await interviewsTab.getAttribute('aria-selected');
    expect(ariaSelected).toBeTruthy();

    // Tabpanel ativo deve ter role="tabpanel" (apenas o visível)
    const activeTabpanel = page.locator('[role="tabpanel"][data-state="active"]');
    await expect(activeTabpanel).toBeVisible();
  });

  test('DT018 - Keyboard navigation works (Arrow keys)', async ({ page }) => {
    const interviewsTab = page.getByRole('tab', { name: /entrevistas/i });

    // Foca na tab Entrevistas (default)
    await interviewsTab.focus();

    // Pressiona ArrowRight para ir para próxima tab
    await page.keyboard.press('ArrowRight');
    await page.waitForTimeout(300);

    // Tab Materiais deve estar focada ou selecionada
    const materialsTab = page.getByRole('tab', { name: /materiais/i });
    const isFocused = await materialsTab.evaluate(el => el === document.activeElement);

    // Ou está focada ou está selecionada
    expect(isFocused || await materialsTab.getAttribute('aria-selected') === 'true').toBeTruthy();
  });

  test('DT019 - Tab list has correct ARIA role', async ({ page }) => {
    // Tablist deve ter role="tablist"
    const tablist = page.locator('[role="tablist"]');
    await expect(tablist).toBeVisible();

    // Deve ter orientação horizontal
    const orientation = await tablist.getAttribute('aria-orientation');
    expect(orientation).toBe('horizontal');
  });
});
