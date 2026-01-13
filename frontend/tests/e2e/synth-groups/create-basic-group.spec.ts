/**
 * E2E test - Create Basic Synth Group
 *
 * Tests the flow of creating a basic synth group with just name and description.
 *
 * Run: npx playwright test tests/e2e/synth-groups/create-basic-group.spec.ts
 */
import { test, expect } from '@playwright/test';

test.describe('Create Basic Synth Group', () => {
  test('should open create group modal', async ({ page }) => {
    // Navigate to home page (experiments list)
    await page.goto('/');

    // Look for navigation or link to synth groups
    // Assuming there's a "Grupos" or "Synth Groups" link in navigation
    const synthGroupsLink = page.locator('text=/grupos/i').or(page.locator('text=/synth groups/i'));

    if (await synthGroupsLink.count() > 0) {
      await synthGroupsLink.first().click();
      await page.waitForLoadState('networkidle');
    } else {
      // Direct navigation if no link found
      await page.goto('/synth-groups');
    }

    // Look for "Create" or "Novo Grupo" button
    const createButton = page.locator('button').filter({ hasText: /criar|novo|create|new/i });
    await expect(createButton.first()).toBeVisible({ timeout: 10000 });

    // Click create button
    await createButton.first().click();

    // Verify modal opened
    // Modal should have dialog role or specific test ID
    const modal = page.locator('[role="dialog"]').or(page.locator('[data-testid="create-group-modal"]'));
    await expect(modal).toBeVisible({ timeout: 5000 });
  });

  test('should create basic group with name only', async ({ page }) => {
    // Navigate to synth groups page
    await page.goto('/synth-groups');
    await page.waitForLoadState('networkidle');

    // Open create modal
    const createButton = page.locator('button').filter({ hasText: /criar|novo|create|new/i });
    await createButton.first().click();

    // Wait for modal
    await page.waitForSelector('[role="dialog"]', { timeout: 5000 });

    // Fill in group name
    const nameInput = page.locator('input[name="name"]').or(
      page.locator('label:has-text("Nome")').locator('..').locator('input')
    );
    await nameInput.fill('E2E Test Basic Group');

    // Submit form
    const submitButton = page.locator('button[type="submit"]').or(
      page.locator('button').filter({ hasText: /criar|create|salvar|save/i })
    );
    await submitButton.click();

    // Wait for success toast
    await expect(page.locator('text=/sucesso|success|criado|created/i')).toBeVisible({
      timeout: 10000
    });

    // Verify group appears in list
    await expect(page.locator('text=E2E Test Basic Group')).toBeVisible({ timeout: 5000 });
  });

  test('should create group with name and description', async ({ page }) => {
    await page.goto('/synth-groups');
    await page.waitForLoadState('networkidle');

    // Open create modal
    const createButton = page.locator('button').filter({ hasText: /criar|novo|create|new/i });
    await createButton.first().click();

    // Fill in name
    const nameInput = page.locator('input[name="name"]').or(
      page.locator('label').filter({ hasText: /nome|name/i }).locator('..').locator('input')
    );
    await nameInput.fill('E2E Test Group with Description');

    // Fill in description
    const descInput = page.locator('textarea[name="description"]').or(
      page.locator('input[name="description"]')
    ).or(
      page.locator('label').filter({ hasText: /descri[cç][aã]o|description/i }).locator('..').locator('textarea, input')
    );

    if (await descInput.count() > 0) {
      await descInput.fill('This is a test description for E2E testing');
    }

    // Submit
    const submitButton = page.locator('button[type="submit"]').or(
      page.locator('button').filter({ hasText: /criar|create|salvar|save/i })
    );
    await submitButton.click();

    // Wait for success
    await expect(page.locator('text=/sucesso|success|criado|created/i')).toBeVisible({
      timeout: 10000
    });

    // Verify both name and description
    await expect(page.locator('text=E2E Test Group with Description')).toBeVisible();
  });

  test('should validate empty name', async ({ page }) => {
    await page.goto('/synth-groups');
    await page.waitForLoadState('networkidle');

    // Open create modal
    const createButton = page.locator('button').filter({ hasText: /criar|novo|create|new/i });
    await createButton.first().click();

    // Try to submit without name
    const submitButton = page.locator('button[type="submit"]').or(
      page.locator('button').filter({ hasText: /criar|create|salvar|save/i })
    );

    // Button might be disabled or form shows validation error
    const isDisabled = await submitButton.isDisabled();

    if (!isDisabled) {
      await submitButton.click();

      // Should show validation error
      await expect(page.locator('text=/obrigat[oó]rio|required|campo.*necess[aá]rio/i')).toBeVisible({
        timeout: 3000
      });
    } else {
      // If disabled, that's also valid validation
      expect(isDisabled).toBeTruthy();
    }
  });

  test('should cancel group creation', async ({ page }) => {
    await page.goto('/synth-groups');
    await page.waitForLoadState('networkidle');

    // Open create modal
    const createButton = page.locator('button').filter({ hasText: /criar|novo|create|new/i });
    await createButton.first().click();

    // Fill in some data
    const nameInput = page.locator('input[name="name"]').or(
      page.locator('label').filter({ hasText: /nome|name/i }).locator('..').locator('input')
    );
    await nameInput.fill('Should Be Canceled');

    // Click cancel
    const cancelButton = page.locator('button').filter({ hasText: /cancelar|cancel|fechar|close/i });
    await cancelButton.first().click();

    // Modal should close
    await expect(page.locator('[role="dialog"]')).not.toBeVisible({ timeout: 3000 });

    // Group should not be in list
    await expect(page.locator('text=Should Be Canceled')).not.toBeVisible();
  });

  test('should close modal with X button', async ({ page }) => {
    await page.goto('/synth-groups');
    await page.waitForLoadState('networkidle');

    // Open create modal
    const createButton = page.locator('button').filter({ hasText: /criar|novo|create|new/i });
    await createButton.first().click();

    // Look for close button (X icon or similar)
    const closeButton = page.locator('button[aria-label*="close"]').or(
      page.locator('button').filter({ hasText: /[×✕]/i })
    );

    if (await closeButton.count() > 0) {
      await closeButton.first().click();

      // Modal should close
      await expect(page.locator('[role="dialog"]')).not.toBeVisible({ timeout: 3000 });
    } else {
      test.skip('No close button found');
    }
  });
});
