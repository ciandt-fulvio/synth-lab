/**
 * E2E test - Experiment list page
 *
 * Testa o fluxo básico de listar experimentos.
 * Este é um teste exemplo - adicione mais testes para outros fluxos críticos.
 *
 * Run: npx playwright test experiment-list.spec.ts
 */
import { test, expect } from '@playwright/test';

test.describe('Experiment List Page', () => {
  test('should load experiments page', async ({ page }) => {
    // Navega para a página inicial
    await page.goto('/');

    // Verifica que a página carregou
    await expect(page).toHaveTitle(/Synth Lab/i);

    // Verifica que há algum conteúdo de experimentos
    // (pode ser lista vazia ou com experimentos)
    await expect(
      page.locator('h1, h2').filter({ hasText: /experimento/i }).first()
    ).toBeVisible({ timeout: 10000 });
  });

  test('should display experiment cards or empty state', async ({ page }) => {
    await page.goto('/');

    // Aguarda carregamento
    await page.waitForLoadState('networkidle');

    // Deve ter ou cards de experimento OU mensagem de lista vazia
    const hasExperiments = await page.locator('[data-testid="experiment-card"]').count();
    const hasEmptyState = await page.locator('text=/nenhum experimento/i').count();

    expect(hasExperiments > 0 || hasEmptyState > 0).toBeTruthy();
  });

  test('should navigate to experiment detail when clicked', async ({ page }) => {
    await page.goto('/');

    // Aguarda lista carregar
    await page.waitForLoadState('networkidle');

    // Se houver experimentos, testa navegação
    const experimentCards = page.locator('[data-testid="experiment-card"]');
    const count = await experimentCards.count();

    if (count > 0) {
      // Clica no primeiro experimento
      await experimentCards.first().click();

      // Verifica que navegou para página de detalhe
      await expect(page).toHaveURL(/\/experiments\/exp_/);

      // Verifica que página de detalhe carregou
      await expect(page.locator('h1, h2')).toBeVisible();
    } else {
      test.skip('Nenhum experimento disponível para testar navegação');
    }
  });
});
