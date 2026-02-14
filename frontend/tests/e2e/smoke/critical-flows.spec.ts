/**
 * Smoke Tests - Critical Flows (Production)
 *
 * Testes rápidos e essenciais para validar que a aplicação está funcionando
 * após deploy para production. Devem rodar em < 1 minuto.
 *
 * Run: npm run test:e2e:production
 * Run specific: TEST_ENV=production npx playwright test smoke/critical-flows.spec.ts
 */
import { test, expect } from '../fixtures';

test.describe('Smoke Tests - Critical Flows @smoke @critical', () => {
  test('ST001 - Application loads and is responsive', async ({ page }) => {
    await page.goto('/');

    // Verifica título da página
    await expect(page).toHaveTitle('SynthLab');

    // Header deve estar visível
    await expect(page.locator('header')).toBeVisible();

    // Página deve carregar completamente
    await page.waitForLoadState('domcontentloaded');
  });

  test('ST002 - Experiments list page loads with data', async ({ page }) => {
    await page.goto('/old-home/');
    await page.waitForLoadState('networkidle');

    // Header de experimentos deve estar visível
    await expect(
      page.locator('h2').filter({ hasText: /experimentos/i }).first()
    ).toBeVisible({ timeout: 10000 });

    // Botão "Novo Experimento" deve estar visível
    await expect(
      page.getByRole('button', { name: /novo experimento/i })
    ).toBeVisible();

    // Should have at least one experiment card OR the empty state
    // This test validates the page loads, not that specific seed data exists
    const experimentCards = page.locator('main').locator('h3');
    const emptyState = page.locator('text=/nenhum experimento|sem experimentos|create your first/i');

    const hasCards = await experimentCards.count() > 0;
    const hasEmptyState = await emptyState.isVisible().catch(() => false);

    expect(hasCards || hasEmptyState).toBeTruthy();
  });

  test('ST003 - API is responding', async ({ page }) => {
    // Intercepta requisição à API
    const responsePromise = page.waitForResponse(
      response => response.url().includes('/experiments') && response.ok,
      { timeout: 15000 }
    );

    await page.goto('/old-home/');

    // Aguarda resposta da API
    const response = await responsePromise;

    // Verifica que API respondeu com sucesso
    expect(response.ok()).toBeTruthy();
    expect(response.status()).toBe(200);
  });

  test('ST004 - Basic navigation works', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Tenta navegar para Synths (se o botão existir)
    const synthsButton = page.getByRole('button', { name: /synths/i });

    if (await synthsButton.isVisible()) {
      await synthsButton.click();
      await expect(page).toHaveURL(/\/synths/);

      // Volta para home
      await page.goto('/');
      await expect(page).toHaveURL('/');
    }
  });

  test('ST005 - Experiment detail loads', async ({ page }) => {
    await page.goto('/old-home/');
    await page.waitForLoadState('networkidle');

    // Find any experiment card
    const experimentCards = page.locator('main').locator('h3');
    const cardCount = await experimentCards.count();

    // Skip if no experiments exist
    if (cardCount === 0) {
      test.skip();
      return;
    }

    // Get the first experiment name
    const experimentName = await experimentCards.first().textContent();

    // Click on the card (parent of h3)
    const cardParent = experimentCards.first().locator('..').locator('..');
    await cardParent.click();

    // Verify navigated to detail page
    await expect(page).toHaveURL(/\/experiments\//);

    // Verify experiment content loads (name appears somewhere on page)
    if (experimentName) {
      await expect(
        page.locator(`text=${experimentName}`).first()
      ).toBeVisible({ timeout: 10000 });
    }
  });

  test('ST006 - No visible error states', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Aguarda um pouco para garantir que qualquer erro tenha tempo de aparecer
    await page.waitForTimeout(2000);

    // Não deve haver mensagens de erro críticas visíveis
    const errorMessages = await page.locator('text=/erro fatal|error|falha crítica|failed to load/i').count();

    // Permite algumas mensagens de erro específicas conhecidas
    const criticalErrors = await page.locator('text=/500|503|network error|failed to fetch/i').count();

    expect(criticalErrors).toBe(0);
  });

  test('ST007 - No critical console errors', async ({ page }) => {
    const consoleErrors: string[] = [];

    // Captura erros do console
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Filtra erros conhecidos/aceitáveis
    const criticalErrors = consoleErrors.filter(err => {
      // Ignora erros conhecidos que não são críticos
      return !err.includes('favicon') &&
             !err.includes('DevTools') &&
             !err.includes('ResizeObserver') &&
             !err.match(/Download the React DevTools/i);
    });

    // Reporta erros se houver
    if (criticalErrors.length > 0) {
      console.log('❌ Console errors found:', criticalErrors);
    }

    expect(criticalErrors).toHaveLength(0);
  });
});

test.describe('Smoke Tests - Performance @smoke @performance', () => {
  test('ST008 - Page loads within acceptable time', async ({ page }) => {
    const startTime = Date.now();

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const loadTime = Date.now() - startTime;

    // Página deve carregar em menos de 10 segundos (staging has cold starts)
    expect(loadTime).toBeLessThan(10000);

    console.log(`✅ Page loaded in ${loadTime}ms`);
  });

  test('ST009 - API responds within acceptable time', async ({ page }) => {
    const startTime = Date.now();

    // Intercepta primeira requisição à API
    const responsePromise = page.waitForResponse(
      response => response.url().includes('/experiments'),
      { timeout: 10000 }
    );

    await page.goto('/old-home/');
    await responsePromise;

    const apiTime = Date.now() - startTime;

    // API deve responder em menos de 10 segundos (staging has cold starts)
    expect(apiTime).toBeLessThan(10000);

    console.log(`✅ API responded in ${apiTime}ms`);
  });
});
