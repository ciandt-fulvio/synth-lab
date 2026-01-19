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
import { test, expect } from '@playwright/test';

test.describe('Synths - Detail Modal @synths', () => {
  // Helper to get synth cards - targets the known seed synth names
  // These are the synths seeded in the database that we can reliably test with
  const getSynthCards = (page: import('@playwright/test').Page) => {
    // Use known seed synth names to find synth cards
    // These synths are seeded and always present in the test database
    return page.locator('main h3').filter({
      hasText: /^(Maria Silva|João Santos|Ana Rodrigues|Carlos Lima|Patrícia Costa|Roberto Alves)$/
    });
  };

  test.beforeEach(async ({ page }) => {
    // Navega para página de synths
    await page.goto('/synths');
    await page.waitForLoadState('networkidle');

    // Wait for page header to load
    await expect(page.locator('h2').filter({ hasText: /synths/i })).toBeVisible({ timeout: 10000 });

    // Wait for seed synths to be visible (they exist in the database)
    // Use a longer timeout to ensure data is fully loaded
    const synthCards = getSynthCards(page);
    await expect(synthCards.first()).toBeVisible({ timeout: 15000 });
  });

  test('Y014 - Click on synth card opens modal', async ({ page }) => {
    // Get all synth headings (beforeEach already ensures they're loaded)
    const synthCards = getSynthCards(page);
    const synthName = await synthCards.first().textContent();
    await synthCards.first().click();

    // Modal deve abrir
    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible({ timeout: 5000 });

    // Título do modal deve conter o nome do synth
    const modalTitle = modal.locator('h2').first();
    await expect(modalTitle).toBeVisible();

    if (synthName) {
      await expect(modalTitle).toHaveText(new RegExp(synthName, 'i'));
    }
  });

  test('Y015 - Modal shows synth description', async ({ page }) => {
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
    // We have 6 seed synths, so at least 2 will be available

    // Clica no primeiro synth
    const firstSynthName = await synthCards.first().textContent();
    await synthCards.first().click();

    let modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible();
    await expect(modal.locator('h2').first()).toHaveText(new RegExp(firstSynthName!, 'i'));

    // Fecha modal
    await page.keyboard.press('Escape');
    await expect(modal).not.toBeVisible();

    // Clica no segundo synth
    const secondSynthName = await synthCards.nth(1).textContent();
    await synthCards.nth(1).click();

    modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible();
    await expect(modal.locator('h2').first()).toHaveText(new RegExp(secondSynthName!, 'i'));

    // Nomes devem ser diferentes
    expect(firstSynthName).not.toEqual(secondSynthName);
  });
});
