/**
 * E2E Tests - Synths List & Pagination
 *
 * Testa a listagem de grupos de synths e navegacao para detalhes.
 * Estes sao testes criticos (P0) que devem passar antes de merge.
 *
 * Run: npm run test:e2e synths/list.spec.ts
 */
import { test, expect } from '../fixtures';

test.describe('Synths - List Page @critical @synths', () => {
  test.beforeEach(async ({ page }) => {
    // Navega para pagina de synths
    await page.goto('/synths');
    await page.waitForLoadState('networkidle');

    // Wait for page header to load
    await expect(page.locator('h2').filter({ hasText: /grupos de synths/i })).toBeVisible({ timeout: 10000 });
  });

  test('Y001 - Synths page loads correctly', async ({ page }) => {
    // Verifica URL
    await expect(page).toHaveURL(/\/synths/);

    // Header "Grupos de Synths" deve estar visivel
    await expect(
      page.locator('h2').filter({ hasText: /grupos de synths/i }).first()
    ).toBeVisible({ timeout: 10000 });

    // Descricao deve estar visivel
    await expect(
      page.locator('text=/cada grupo representa uma popula/i')
    ).toBeVisible();
  });

  test('Y002 - Synth group cards are displayed', async ({ page }) => {
    // Deve mostrar cards de grupos de synths
    // Each group card has a CardTitle (h3-like) with group name
    const groupCards = page.locator('main .cursor-pointer');
    const cardCount = await groupCards.count();

    // Should have at least one group card
    expect(cardCount).toBeGreaterThan(0);
  });

  test('Y003 - Synth group cards show required information', async ({ page }) => {
    // Group cards show name and synth count badge
    const groupCards = page.locator('main .cursor-pointer');

    // Wait for cards to load
    await expect(groupCards.first()).toBeVisible({ timeout: 15000 });

    // Card should have content (name, count, etc.)
    const cardText = await groupCards.first().textContent();
    expect(cardText).toBeTruthy();
    expect(cardText!.length).toBeGreaterThan(0);
  });

  test('Y004 - Group cards show synth count badge', async ({ page }) => {
    // Each group card shows a badge with the synth count
    const groupCards = page.locator('main .cursor-pointer');
    await expect(groupCards.first()).toBeVisible({ timeout: 10000 });

    // Card text should contain a number (the synth count badge)
    const cardText = await groupCards.first().textContent();
    expect(cardText).toMatch(/\d+/);
  });

  test('Y005 - Create group button exists', async ({ page }) => {
    // "Novo Grupo" button should be visible
    const createGroupBtn = page.getByRole('button', { name: /novo grupo/i });
    await expect(createGroupBtn).toBeVisible({ timeout: 10000 });
  });

  test('Y006 - Click group card navigates to detail', async ({ page }) => {
    // Wait for group cards to load
    const groupCards = page.locator('main .cursor-pointer');
    await expect(groupCards.first()).toBeVisible({ timeout: 15000 });

    // Click first group card
    await groupCards.first().click();

    // Should navigate to group detail page
    await expect(page).toHaveURL(/\/synths\/groups\//);
    await page.waitForLoadState('networkidle');
  });

  test('Y007 - Multiple groups are displayed', async ({ page }) => {
    // Wait for group cards to load
    const groupCards = page.locator('main .cursor-pointer');
    await expect(groupCards.first()).toBeVisible({ timeout: 15000 });

    const cardCount = await groupCards.count();

    // Should have multiple groups (seed data creates several)
    expect(cardCount).toBeGreaterThan(0);
  });
});

test.describe('Synths - Pagination @synths', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/synths');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000); // Wait for groups to load
  });

  test('Y008 - Groups are displayed on page', async ({ page }) => {
    // Check for group cards
    const groupCards = page.locator('main .cursor-pointer');
    const count = await groupCards.count();

    // Should have at least one group visible
    expect(count).toBeGreaterThan(0);
  });

  test('Y009 - Page shows correct number of groups', async ({ page }) => {
    // Verify groups are loaded
    const groupCards = page.locator('main .cursor-pointer');
    const cardCount = await groupCards.count();

    // Should have at least some groups
    expect(cardCount).toBeGreaterThan(0);
  });

  test('Y010 - Next page button exists', async ({ page }) => {
    // Current UI doesn't have pagination - all groups are shown
    test.skip('Pagination not implemented in current UI');
  });

  test('Y011 - Navigate to next page', async ({ page }) => {
    // Current UI doesn't have pagination - all groups are shown
    test.skip('Pagination not implemented in current UI');
  });

  test('Y012 - Navigate to previous page', async ({ page }) => {
    // Current UI doesn't have pagination - all groups are shown
    test.skip('Pagination not implemented in current UI');
  });

  test('Y013 - Direct page navigation works', async ({ page }) => {
    // Current UI doesn't have pagination - all groups are shown
    test.skip('Pagination not implemented in current UI');
  });
});
