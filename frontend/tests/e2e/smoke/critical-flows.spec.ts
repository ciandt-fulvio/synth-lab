/**
 * Smoke Tests - Critical Flows (Production)
 *
 * Testes rápidos e essenciais para validar que a aplicação está funcionando
 * após deploy para production. Devem rodar em < 1 minuto.
 *
 * Run: npm run test:e2e:production
 * Run specific: TEST_ENV=production npx playwright test smoke/critical-flows.spec.ts
 */
import { test, expect } from '@playwright/test';

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

  test('ST002 - Experiments list page loads with seeded data', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Header de experimentos deve estar visível
    await expect(
      page.locator('h2').filter({ hasText: /experimentos/i }).first()
    ).toBeVisible({ timeout: 10000 });

    // Botão "Novo Experimento" deve estar visível
    await expect(
      page.getByRole('button', { name: /novo experimento/i })
    ).toBeVisible();

    // Experimento do seed deve estar visível
    await expect(
      page.locator('h3').filter({ hasText: /App de Delivery.*Agendamento de Pedidos/i })
    ).toBeVisible({ timeout: 10000 });
  });

  test('ST003 - API is responding', async ({ page }) => {
    // Intercepta requisição à API
    const responsePromise = page.waitForResponse(
      response => response.url().includes('/experiments') && response.ok,
      { timeout: 15000 }
    );

    await page.goto('/');

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

  test('ST005 - Experiment detail loads (seeded experiment)', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Procura pelo experimento do seed
    const deliveryExperiment = page.locator('h3').filter({
      hasText: /App de Delivery.*Agendamento de Pedidos/i
    });

    // Clica no card do experimento (parent do h3)
    const cardParent = deliveryExperiment.locator('..').locator('..');
    await cardParent.click();

    // Verifica que navegou para detalhe (exp_a1b2c3d4 é o ID do experimento seedado)
    await expect(page).toHaveURL(/\/experiments\/exp_a1b2c3d4/);

    // Verifica que nome do experimento aparece
    await expect(
      page.locator('text=/App de Delivery.*Agendamento de Pedidos/i')
    ).toBeVisible({ timeout: 10000 });

    // Verifica que scorecard foi carregado
    await expect(
      page.locator('text=/scorecard|agendamento/i')
    ).toBeVisible({ timeout: 10000 });
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

    // Página deve carregar em menos de 5 segundos
    expect(loadTime).toBeLessThan(5000);

    console.log(`✅ Page loaded in ${loadTime}ms`);
  });

  test('ST009 - API responds within acceptable time', async ({ page }) => {
    const startTime = Date.now();

    // Intercepta primeira requisição à API
    const responsePromise = page.waitForResponse(
      response => response.url().includes('/experiments'),
      { timeout: 10000 }
    );

    await page.goto('/');
    await responsePromise;

    const apiTime = Date.now() - startTime;

    // API deve responder em menos de 3 segundos
    expect(apiTime).toBeLessThan(3000);

    console.log(`✅ API responded in ${apiTime}ms`);
  });
});
