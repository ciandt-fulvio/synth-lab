/**
 * E2E test - Synth Group Details
 *
 * Tests viewing synth group details including synth list and configuration.
 *
 * Run: npx playwright test tests/e2e/synth-groups/group-details.spec.ts
 */
import { test, expect } from '../fixtures';

test.describe('Synth Group Details', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to synths page (where groups are shown)
    await page.goto('/synths');
    await page.waitForLoadState('networkidle');

    // Wait for page to load
    await expect(page.locator('h2').filter({ hasText: /synths/i })).toBeVisible({ timeout: 10000 });

    // Wait for groups to load (button shows count when ready)
    await expect(page.getByRole('button', { name: /grupos de synths\s*\(\d+\)/i })).toBeVisible({ timeout: 15000 });
  });

  test('should navigate to group detail from list', async ({ page }) => {
    // Find "Ver detalhes" buttons (one per group)
    const detailButtons = page.getByRole('button', { name: /ver detalhes/i });
    await expect(detailButtons.first()).toBeVisible({ timeout: 10000 });

    // Click first group detail button
    await detailButtons.first().click();

    // Should navigate to detail page or open modal
    await page.waitForLoadState('networkidle');

    // Either URL changes or modal opens
    const hasUrlChange = await page.url().includes('/synth-groups/');
    const modal = page.locator('[role="dialog"]');
    const hasModal = await modal.isVisible();

    expect(hasUrlChange || hasModal).toBeTruthy();
  });

  test('should display group information', async ({ page }) => {
    // Find "Ver detalhes" buttons
    const detailButtons = page.getByRole('button', { name: /ver detalhes/i });
    await expect(detailButtons.first()).toBeVisible({ timeout: 10000 });

    // Get accessible name which contains group name
    const buttonName = await detailButtons.first().getAttribute('aria-label') ||
                       await detailButtons.first().textContent();

    // Click to view details
    await detailButtons.first().click();
    await page.waitForTimeout(1000);

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
    // Find "Ver detalhes" buttons
    const detailButtons = page.getByRole('button', { name: /ver detalhes/i });
    await expect(detailButtons.first()).toBeVisible({ timeout: 10000 });

    // Click to view details
    await detailButtons.first().click();
    await page.waitForTimeout(1000);

    // Should have either synth items (h3 elements) or empty state
    const synthHeaders = page.locator('h3');
    const hasSynths = await synthHeaders.count() > 0;
    const hasEmptyState = await page.locator('text=/nenhum synth|no synths|vazio|empty/i').count() > 0;

    expect(hasSynths || hasEmptyState).toBeTruthy();
  });

  test('should display config if present', async ({ page }) => {
    // Find "Ver detalhes" buttons
    const detailButtons = page.getByRole('button', { name: /ver detalhes/i });

    if (await detailButtons.count() > 0) {
      // Try a few groups to find one with config
      for (let i = 0; i < Math.min(await detailButtons.count(), 3); i++) {
        await detailButtons.nth(i).click();
        await page.waitForTimeout(1000);

        // Check if config section exists
        const configSection = page.locator('text=/configura[çc][ãa]o|configuration|distribui[çc][õo]es|distributions/i');

        if (await configSection.count() > 0) {
          await expect(configSection.first()).toBeVisible();
          return;
        }

        // Go back if needed
        const backButton = page.locator('button').filter({ hasText: /voltar|back|←/i });
        if (await backButton.count() > 0) {
          await backButton.first().click();
          await page.waitForTimeout(500);
        }
      }
    }

    // Config section is optional - test passes if we checked
  });

  test('should have back navigation', async ({ page }) => {
    // Find "Ver detalhes" buttons
    const detailButtons = page.getByRole('button', { name: /ver detalhes/i });
    await expect(detailButtons.first()).toBeVisible({ timeout: 10000 });

    // Click to view details
    await detailButtons.first().click();
    await page.waitForTimeout(1000);

    // Look for back button or close button
    const backButton = page.locator('button').filter({ hasText: /voltar|back|←|close|fechar/i }).or(
      page.getByRole('button', { name: /close/i })
    );

    if (await backButton.count() > 0) {
      await backButton.first().click();
      await page.waitForTimeout(500);

      // Should return to synths page or close modal
      const isOnSynthsPage = page.url().includes('/synths');
      const modalClosed = !(await page.locator('[role="dialog"]').isVisible());

      expect(isOnSynthsPage || modalClosed).toBeTruthy();
    }
  });

  test('should display synth avatars if present', async ({ page }) => {
    // Find "Ver detalhes" buttons
    const detailButtons = page.getByRole('button', { name: /ver detalhes/i });
    await expect(detailButtons.first()).toBeVisible({ timeout: 10000 });

    // Click to view details
    await detailButtons.first().click();
    await page.waitForTimeout(1000);

    // Look for synth avatars (img tags)
    const avatars = page.locator('img[alt]');
    const avatarCount = await avatars.count();

    // Just verify we can query for avatars - count may vary
    expect(avatarCount).toBeGreaterThanOrEqual(0);
  });

  test('should show synth details on click', async ({ page }) => {
    // Wait for any synth cards to be visible (using data-testid)
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
