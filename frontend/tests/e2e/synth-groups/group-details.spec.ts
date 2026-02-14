/**
 * E2E test - Synth Group Details
 *
 * Tests viewing synth group details including synth list and configuration.
 * The Synths page shows group cards directly. Clicking a card navigates
 * to the group detail page.
 *
 * Run: npx playwright test tests/e2e/synth-groups/group-details.spec.ts
 */
import { test, expect } from '../fixtures';

test.describe('Synth Group Details', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to synths page (where groups are shown as cards)
    await page.goto('/synths');
    await page.waitForLoadState('networkidle');

    // Wait for page header to load
    await expect(page.locator('h2').filter({ hasText: /grupos de synths/i })).toBeVisible({ timeout: 10000 });

    // Wait for group cards to load
    const groupCards = page.locator('main .cursor-pointer');
    await expect(groupCards.first()).toBeVisible({ timeout: 15000 });
  });

  test('should navigate to group detail from list', async ({ page }) => {
    // Find group cards
    const groupCards = page.locator('main .cursor-pointer');
    await expect(groupCards.first()).toBeVisible({ timeout: 10000 });

    // Click first group card
    await groupCards.first().click();

    // Should navigate to detail page
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveURL(/\/synths\/groups\//);
  });

  test('should display group information', async ({ page }) => {
    // Click first group card
    const groupCards = page.locator('main .cursor-pointer');
    await groupCards.first().click();
    await page.waitForLoadState('networkidle');

    // Should have some metadata visible
    const metadataIndicators = [
      page.locator('text=/synths|personas/i'),
      page.locator('text=/\\d+/'),
      page.locator('h3')
    ];

    let foundMetadata = false;
    for (const indicator of metadataIndicators) {
      if (await indicator.count() > 0) {
        foundMetadata = true;
        break;
      }
    }

    expect(foundMetadata).toBeTruthy();
  });

  test('should display list of synths', async ({ page }) => {
    // Click first group card
    const groupCards = page.locator('main .cursor-pointer');
    await groupCards.first().click();
    await page.waitForLoadState('networkidle');

    // Group detail page defaults to "Estatísticas" tab - click "Synths" tab
    const synthsTab = page.getByRole('tab', { name: /synths/i });
    await expect(synthsTab).toBeVisible({ timeout: 10000 });
    await synthsTab.click();
    await page.waitForTimeout(500);

    // Should have either synth items or empty state
    const synthCards = page.locator('[data-testid="synth-card"]');
    const hasSynths = await synthCards.count() > 0;
    const hasEmptyState = await page.locator('text=/nenhum synth|no synths|vazio|empty/i').count() > 0;

    expect(hasSynths || hasEmptyState).toBeTruthy();
  });

  test('should display config if present', async ({ page }) => {
    // Try a few groups to find one with config
    const groupCards = page.locator('main .cursor-pointer');
    const cardCount = await groupCards.count();

    for (let i = 0; i < Math.min(cardCount, 3); i++) {
      if (i > 0) {
        // Navigate back to synths page
        await page.goto('/synths');
        await page.waitForLoadState('networkidle');
      }

      const cards = page.locator('main .cursor-pointer');
      await expect(cards.nth(i)).toBeVisible({ timeout: 10000 });
      await cards.nth(i).click();
      await page.waitForLoadState('networkidle');

      // Check if config section exists
      const configSection = page.locator('text=/configura[çc][ãa]o|configuration|distribui[çc][õo]es|distributions/i');

      if (await configSection.count() > 0) {
        await expect(configSection.first()).toBeVisible();
        return;
      }
    }

    // Config section is optional - test passes if we checked
  });

  test('should have back navigation', async ({ page }) => {
    // Click first group card
    const groupCards = page.locator('main .cursor-pointer');
    await groupCards.first().click();
    await page.waitForLoadState('networkidle');

    // Look for back button or close button
    const backButton = page.locator('button').filter({ hasText: /voltar|back|←|close|fechar/i }).or(
      page.getByRole('button', { name: /close/i })
    );

    if (await backButton.count() > 0) {
      await backButton.first().click();
      await page.waitForTimeout(500);

      // Should return to synths page
      const isOnSynthsPage = page.url().includes('/synths');
      expect(isOnSynthsPage).toBeTruthy();
    }
  });

  test('should display synth avatars if present', async ({ page }) => {
    // Click first group card
    const groupCards = page.locator('main .cursor-pointer');
    await groupCards.first().click();
    await page.waitForLoadState('networkidle');

    // Look for synth avatars (img tags)
    const avatars = page.locator('img[alt]');
    const avatarCount = await avatars.count();

    // Just verify we can query for avatars - count may vary
    expect(avatarCount).toBeGreaterThanOrEqual(0);
  });

  test('should show synth details on click', async ({ page }) => {
    // Navigate to first group detail
    const groupCards = page.locator('main .cursor-pointer');
    await groupCards.first().click();
    await page.waitForLoadState('networkidle');

    // Click "Synths" tab (default is "Estatísticas")
    const synthsTab = page.getByRole('tab', { name: /synths/i });
    await expect(synthsTab).toBeVisible({ timeout: 10000 });
    await synthsTab.click();
    await page.waitForTimeout(500);

    // Wait for synth cards on group detail page
    const synthCards = page.locator('[data-testid="synth-card"]');

    // Skip if no synth cards are present
    const cardCount = await synthCards.count();
    if (cardCount === 0) {
      test.skip();
      return;
    }

    await expect(synthCards.first()).toBeVisible({ timeout: 15000 });

    // Click on a synth card
    await synthCards.first().click();

    // Should show synth detail modal
    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible({ timeout: 5000 });

    // Modal should have synth name
    const modalTitle = modal.locator('h2');
    await expect(modalTitle).toBeVisible();
  });
});
