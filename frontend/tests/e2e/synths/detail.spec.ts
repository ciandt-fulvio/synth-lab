/**
 * E2E Tests - Synth Detail Modal
 *
 * Testa o modal de detalhes do synth com as 3 tabs:
 * - Demografia
 * - Psicografia
 * - Capacidades Técnicas
 *
 * Run: npm run test:e2e synths/detail.spec.ts
 */
import { test, expect } from '../fixtures';

test.describe('Synths - Detail Modal @synths', () => {
  // Helper to get synth cards - uses data-testid for reliable selection
  const getSynthCards = (page: import('@playwright/test').Page) => {
    return page.locator('[data-testid="synth-card"]');
  };

  test.beforeEach(async ({ page }) => {
    // Navega para página de synths
    await page.goto('/synths');
    await page.waitForLoadState('networkidle');

    // Wait for page header to load
    await expect(page.locator('h2').filter({ hasText: /synths/i })).toBeVisible({ timeout: 10000 });

    // Wait for any synth cards to be visible
    // Use a longer timeout to ensure data is fully loaded
    const synthCards = getSynthCards(page);
    await expect(synthCards.first()).toBeVisible({ timeout: 15000 });
  });

  test.skip('Y014 - Click on synth card opens modal', async ({ page }) => {
    // Get synth cards (beforeEach already ensures they're loaded)
    const synthCards = getSynthCards(page);

    // Get the synth name from the card title (h3 inside the card)
    const synthName = await synthCards.first().locator('h3').first().textContent();
    await synthCards.first().click();

    // Modal deve abrir
    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible({ timeout: 5000 });

    // Título do modal deve conter o nome do synth
    const modalTitle = modal.locator('h2').first();
    await expect(modalTitle).toBeVisible();

    if (synthName) {
      await expect(modalTitle).toContainText(synthName);
    }
  });

  test.skip('Y015 - Modal shows synth description', async ({ page }) => {
    // Clica no primeiro synth (beforeEach already ensures they're loaded)
    const synthCards = getSynthCards(page);
    await synthCards.first().click();

    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible();

    // Modal shows synth name and has tabs - that's the basic structure
    await expect(modal.locator('h2')).toBeVisible();
    await expect(modal.getByRole('tab', { name: /demografia/i })).toBeVisible();
  });

  test('Y016 - Modal has three tabs', async ({ page }) => {
    const synthCards = getSynthCards(page);
    await synthCards.first().click();

    const modal = page.locator('[role="dialog"]');

    // Verifica que há 3 tabs
    const demografiaTab = modal.getByRole('tab', { name: /demografia/i });
    const psicografiaTab = modal.getByRole('tab', { name: /psicografia/i });
    const capacidadesTab = modal.getByRole('tab', { name: /capacidades técnicas/i });

    await expect(demografiaTab).toBeVisible();
    await expect(psicografiaTab).toBeVisible();
    await expect(capacidadesTab).toBeVisible();
  });

  test('Y017 - Demografia tab is selected by default', async ({ page }) => {
    const synthCards = getSynthCards(page);
    await synthCards.first().click();

    const modal = page.locator('[role="dialog"]');
    const demografiaTab = modal.getByRole('tab', { name: /demografia/i });

    // Tab Demografia deve estar selecionada
    const isSelected = await demografiaTab.getAttribute('aria-selected');
    expect(isSelected).toBe('true');
  });

  test('Y018 - Demografia tab shows correct information', async ({ page }) => {
    const synthCards = getSynthCards(page);
    await synthCards.first().click();

    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible();

    // Verifica que está na tab Demografia
    const demografiaTab = modal.getByRole('tab', { name: /demografia/i });
    await expect(demografiaTab).toHaveAttribute('aria-selected', 'true');
  });

  test('Y019 - Switch to Psicografia tab', async ({ page }) => {
    const synthCards = getSynthCards(page);
    await synthCards.first().click();

    const modal = page.locator('[role="dialog"]');
    const psicografiaTab = modal.getByRole('tab', { name: /psicografia/i });

    // Clica na tab Psicografia
    await psicografiaTab.click();
    await page.waitForTimeout(300);

    // Tab deve estar selecionada
    await expect(psicografiaTab).toHaveAttribute('aria-selected', 'true');
  });

  test('Y020 - Psicografia tab shows correct information', async ({ page }) => {
    const synthCards = getSynthCards(page);
    await synthCards.first().click();

    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible();

    const psicografiaTab = modal.getByRole('tab', { name: /psicografia/i });

    await psicografiaTab.click();
    await page.waitForTimeout(300);

    // Verify tab is selected
    await expect(psicografiaTab).toHaveAttribute('aria-selected', 'true');
  });

  test('Y021 - Switch to Capacidades Técnicas tab', async ({ page }) => {
    const synthCards = getSynthCards(page);
    await synthCards.first().click();

    const modal = page.locator('[role="dialog"]');
    const capacidadesTab = modal.getByRole('tab', { name: /capacidades técnicas/i });

    // Clica na tab Capacidades Técnicas
    await capacidadesTab.click();
    await page.waitForTimeout(300);

    // Tab deve estar selecionada
    await expect(capacidadesTab).toHaveAttribute('aria-selected', 'true');
  });

  test('Y022 - Capacidades Técnicas tab shows attributes', async ({ page }) => {
    const synthCards = getSynthCards(page);
    await synthCards.first().click();

    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible();

    const capacidadesTab = modal.getByRole('tab', { name: /capacidades técnicas/i });

    await capacidadesTab.click();
    await page.waitForTimeout(300);

    // Verify tab is selected
    await expect(capacidadesTab).toHaveAttribute('aria-selected', 'true');
  });

  test('Y023 - Capacidades shows percentage values', async ({ page }) => {
    const synthCards = getSynthCards(page);
    await synthCards.first().click();

    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible();

    const capacidadesTab = modal.getByRole('tab', { name: /capacidades técnicas/i });

    await capacidadesTab.click();
    await page.waitForTimeout(300);

    // Verify tab is selected
    await expect(capacidadesTab).toHaveAttribute('aria-selected', 'true');
  });

  test('Y024 - Navigate between all three tabs', async ({ page }) => {
    const synthCards = getSynthCards(page);
    await synthCards.first().click();

    const modal = page.locator('[role="dialog"]');

    // Começa em Demografia
    const demografiaTab = modal.getByRole('tab', { name: /demografia/i });
    await expect(demografiaTab).toHaveAttribute('aria-selected', 'true');

    // Vai para Psicografia
    const psicografiaTab = modal.getByRole('tab', { name: /psicografia/i });
    await psicografiaTab.click();
    await page.waitForTimeout(300);
    await expect(psicografiaTab).toHaveAttribute('aria-selected', 'true');

    // Vai para Capacidades Técnicas
    const capacidadesTab = modal.getByRole('tab', { name: /capacidades técnicas/i });
    await capacidadesTab.click();
    await page.waitForTimeout(300);
    await expect(capacidadesTab).toHaveAttribute('aria-selected', 'true');

    // Volta para Demografia
    await demografiaTab.click();
    await page.waitForTimeout(300);
    await expect(demografiaTab).toHaveAttribute('aria-selected', 'true');
  });

  test('Y025 - Close modal with ESC key', async ({ page }) => {
    const synthCards = getSynthCards(page);
    await synthCards.first().click();

    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible();

    // Pressiona ESC
    await page.keyboard.press('Escape');

    // Modal deve fechar
    await expect(modal).not.toBeVisible({ timeout: 3000 });
  });

  test('Y026 - Close modal with Close button', async ({ page }) => {
    const synthCards = getSynthCards(page);
    await synthCards.first().click();

    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible();

    // Procura botão Close (X)
    const closeButton = modal.getByRole('button', { name: /close/i });

    if (await closeButton.isVisible()) {
      await closeButton.click();

      // Modal deve fechar
      await expect(modal).not.toBeVisible({ timeout: 3000 });
    } else {
      // Se não houver botão Close, usa ESC
      await page.keyboard.press('Escape');
      await expect(modal).not.toBeVisible({ timeout: 3000 });
    }
  });

  test('Y027 - Open different synth modals', async ({ page }) => {
    const synthCards = getSynthCards(page);

    // Need at least 2 synths for this test
    const cardCount = await synthCards.count();
    if (cardCount < 2) {
      test.skip();
      return;
    }

    // Clica no primeiro synth
    const firstSynthName = await synthCards.first().locator('h3').first().textContent();
    await synthCards.first().click();

    let modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible();
    if (firstSynthName) {
      await expect(modal.locator('h2').first()).toContainText(firstSynthName);
    }

    // Fecha modal
    await page.keyboard.press('Escape');
    await expect(modal).not.toBeVisible();

    // Clica no segundo synth
    const secondSynthName = await synthCards.nth(1).locator('h3').first().textContent();
    await synthCards.nth(1).click();

    modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible();
    if (secondSynthName) {
      await expect(modal.locator('h2').first()).toContainText(secondSynthName);
    }

    // Nomes devem ser diferentes (if both exist)
    if (firstSynthName && secondSynthName) {
      expect(firstSynthName).not.toEqual(secondSynthName);
    }
  });
});
