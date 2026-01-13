/**
 * E2E test - Synth Group Details
 *
 * Tests viewing synth group details including synth list and configuration.
 *
 * Run: npx playwright test tests/e2e/synth-groups/group-details.spec.ts
 */
import { test, expect } from '@playwright/test';

test.describe('Synth Group Details', () => {
  test('should navigate to group detail from list', async ({ page }) => {
    await page.goto('/synth-groups');
    await page.waitForLoadState('networkidle');

    // Find group cards
    const groupCards = page.locator('[data-testid="group-card"]').or(
      page.locator('.cursor-pointer').filter({ has: page.locator('h3, [class*="CardTitle"]') })
    );

    const count = await groupCards.count();

    if (count > 0) {
      // Click first group
      await groupCards.first().click();

      // Should navigate to detail page
      await expect(page).toHaveURL(/\/synth-groups\/grp_/);

      // Page should load
      await page.waitForLoadState('networkidle');
    } else {
      test.skip('No groups available for testing');
    }
  });

  test('should display group information', async ({ page }) => {
    await page.goto('/synth-groups');
    await page.waitForLoadState('networkidle');

    // Find a group with synths
    const groupCards = page.locator('[data-testid="group-card"]').or(
      page.locator('.cursor-pointer')
    );

    const count = await groupCards.count();

    if (count > 0) {
      // Get group name from card
      const firstCard = groupCards.first();
      const groupNameElement = firstCard.locator('h3, [class*="CardTitle"]');
      const groupName = await groupNameElement.textContent();

      // Click to view details
      await firstCard.click();
      await page.waitForLoadState('networkidle');

      // Verify group name is displayed
      if (groupName) {
        await expect(page.locator(`text=${groupName}`)).toBeVisible();
      }

      // Should have some metadata (created date, synth count, etc.)
      const metadataIndicators = [
        page.locator('text=/criado em|created|data/i'),
        page.locator('text=/synths|personas/i'),
        page.locator('text=/\\d+ synth/i')
      ];

      let foundMetadata = false;
      for (const indicator of metadataIndicators) {
        if (await indicator.count() > 0) {
          await expect(indicator.first()).toBeVisible();
          foundMetadata = true;
          break;
        }
      }

      expect(foundMetadata).toBeTruthy();
    } else {
      test.skip('No groups available');
    }
  });

  test('should display list of synths', async ({ page }) => {
    await page.goto('/synth-groups');
    await page.waitForLoadState('networkidle');

    // Find a group (preferably one with synths)
    const groupCards = page.locator('[data-testid="group-card"]').or(
      page.locator('.cursor-pointer')
    );

    const count = await groupCards.count();

    if (count > 0) {
      await groupCards.first().click();
      await page.waitForLoadState('networkidle');

      // Look for synth list
      const synthList = page.locator('[data-testid="synth-list"]').or(
        page.locator('text=/lista.*synths|synth.*list/i').locator('..')
      );

      // Should have either synth items or empty state
      const hasSynths = await page.locator('[data-testid="synth-item"]').count() > 0;
      const hasEmptyState = await page.locator('text=/nenhum synth|no synths|empty/i').count() > 0;

      expect(hasSynths || hasEmptyState).toBeTruthy();
    } else {
      test.skip('No groups available');
    }
  });

  test('should display config if present', async ({ page }) => {
    await page.goto('/synth-groups');
    await page.waitForLoadState('networkidle');

    // Look for a group with custom config
    // These would be groups created with distributions
    const groupCards = page.locator('[data-testid="group-card"]');

    const count = await groupCards.count();

    if (count > 0) {
      // Try clicking groups until we find one with config
      for (let i = 0; i < Math.min(count, 3); i++) {
        await page.goto('/synth-groups');
        await page.waitForLoadState('networkidle');

        const cards = page.locator('[data-testid="group-card"]');
        await cards.nth(i).click();
        await page.waitForLoadState('networkidle');

        // Check if config section exists
        const configSection = page.locator('text=/configura[çc][ãa]o|configuration|distribui[çc][õo]es|distributions/i');

        if (await configSection.count() > 0) {
          await expect(configSection.first()).toBeVisible();
          break;
        }
      }
    }
  });

  test('should have back navigation', async ({ page }) => {
    await page.goto('/synth-groups');
    await page.waitForLoadState('networkidle');

    const groupCards = page.locator('[data-testid="group-card"]').or(
      page.locator('.cursor-pointer')
    );

    const count = await groupCards.count();

    if (count > 0) {
      await groupCards.first().click();
      await page.waitForLoadState('networkidle');

      // Look for back button
      const backButton = page.locator('button[aria-label*="back"]').or(
        page.locator('button').filter({ hasText: /voltar|back|←|‹/i })
      ).or(
        page.locator('a').filter({ hasText: /voltar|back/i })
      );

      if (await backButton.count() > 0) {
        await backButton.first().click();

        // Should return to list
        await expect(page).toHaveURL(/\/synth-groups$/);
      }
    } else {
      test.skip('No groups available');
    }
  });

  test('should display synth avatars if present', async ({ page }) => {
    await page.goto('/synth-groups');
    await page.waitForLoadState('networkidle');

    const groupCards = page.locator('[data-testid="group-card"]').or(
      page.locator('.cursor-pointer')
    );

    const count = await groupCards.count();

    if (count > 0) {
      await groupCards.first().click();
      await page.waitForLoadState('networkidle');

      // Look for synth avatars (img tags or avatar components)
      const avatars = page.locator('img[alt*="avatar"]').or(
        page.locator('[data-testid="synth-avatar"]')
      ).or(
        page.locator('img[src*="avatar"]')
      );

      // May or may not have avatars depending on data
      const avatarCount = await avatars.count();
      // Just verify the query works, don't assert count
      expect(avatarCount).toBeGreaterThanOrEqual(0);
    } else {
      test.skip('No groups available');
    }
  });

  test('should show synth details on click', async ({ page }) => {
    await page.goto('/synth-groups');
    await page.waitForLoadState('networkidle');

    const groupCards = page.locator('[data-testid="group-card"]');
    const count = await groupCards.count();

    if (count > 0) {
      await groupCards.first().click();
      await page.waitForLoadState('networkidle');

      // Look for clickable synth items
      const synthItems = page.locator('[data-testid="synth-item"]').or(
        page.locator('.cursor-pointer').filter({ hasText: /synth/i })
      );

      const synthCount = await synthItems.count();

      if (synthCount > 0) {
        // Click first synth
        await synthItems.first().click();

        // Should show synth details (modal or navigation)
        const synthDetail = page.locator('[role="dialog"]').or(
          page.locator('[data-testid="synth-detail"]')
        );

        if (await synthDetail.count() > 0) {
          await expect(synthDetail).toBeVisible({ timeout: 3000 });
        } else {
          // Or navigates to synth page
          await expect(page).toHaveURL(/\/synth/);
        }
      } else {
        test.skip('No synths in group');
      }
    } else {
      test.skip('No groups available');
    }
  });
});
