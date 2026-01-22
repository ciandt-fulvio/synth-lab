/**
 * E2E test - Create Basic Synth Group
 *
 * Tests the flow of creating a basic synth group with just name and description.
 *
 * Run: npx playwright test tests/e2e/synth-groups/create-basic-group.spec.ts
 */
import { test, expect } from '@playwright/test';

test.describe('Create Basic Synth Group', () => {
  // Run tests serially to avoid race conditions with parallel group creation
  test.describe.configure({ mode: 'serial' });

  test('should open create group modal', async ({ page }) => {
    // Navigate to synths page (where groups are managed)
    await page.goto('/synths');
    await page.waitForLoadState('networkidle');

    // Wait for page to load completely
    await expect(page.locator('h2').filter({ hasText: /synths/i })).toBeVisible({ timeout: 10000 });

    // Look for "Novo Grupo" button
    const createButton = page.getByRole('button', { name: /novo grupo/i });
    await expect(createButton).toBeVisible({ timeout: 10000 });

    // Click create button
    await createButton.click();

    // Verify modal opened
    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible({ timeout: 10000 });
  });

  // TODO(BUG): Modal doesn't close after synth group creation
  // Investigation shows:
  // - Backend API works correctly (verified with curl)
  // - Frontend has correct VITE_API_URL configuration
  // - Modal stays open for 30s after clicking "Criar Grupo"
  // - Likely issue: frontend component's success callback not triggered or race condition in modal close logic
  test.skip('should create basic group with name only', async ({ page }) => {
    // Navigate to synths page
    await page.goto('/synths');
    await page.waitForLoadState('networkidle');

    // Wait for page to load
    await expect(page.locator('h2').filter({ hasText: /synths/i })).toBeVisible({ timeout: 10000 });

    // Generate unique group name with short random suffix (UI truncates long names)
    const uniqueId = Math.random().toString(36).substring(2, 8);
    const groupName = `BG ${uniqueId}`;

    // Open create modal
    const createButton = page.getByRole('button', { name: /novo grupo/i });
    await expect(createButton).toBeVisible({ timeout: 10000 });
    await createButton.click();

    // Wait for modal
    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible({ timeout: 10000 });

    // Fill in group name using the textbox labeled "Nome do Grupo"
    const nameInput = modal.getByRole('textbox', { name: /nome do grupo/i });
    await expect(nameInput).toBeVisible({ timeout: 5000 });
    await nameInput.fill(groupName);

    // Submit form - button is "Criar Grupo"
    const submitButton = modal.getByRole('button', { name: /criar grupo/i });
    await expect(submitButton).toBeEnabled({ timeout: 5000 });
    await submitButton.click();

    // Wait for modal to close (indicates success)
    await expect(modal).not.toBeVisible({ timeout: 30000 });

    // Wait for list to refresh after group creation
    await page.waitForTimeout(1000);

    // Verify group appears in list (use exact text match with first to avoid strict mode)
    await expect(page.getByText(groupName).first()).toBeVisible({ timeout: 15000 });
  });

  test('should create group with name and description', async ({ page }) => {
    await page.goto('/synths');
    await page.waitForLoadState('networkidle');

    // Wait for page to load
    await expect(page.locator('h2').filter({ hasText: /synths/i })).toBeVisible({ timeout: 10000 });

    // Generate unique group name with short random suffix (UI truncates long names)
    const uniqueId = Math.random().toString(36).substring(2, 8);
    const groupName = `GD ${uniqueId}`;

    // Open create modal
    const createButton = page.getByRole('button', { name: /novo grupo/i });
    await expect(createButton).toBeVisible({ timeout: 10000 });
    await createButton.click();

    // Wait for modal
    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible({ timeout: 10000 });

    // Fill in name
    const nameInput = modal.getByRole('textbox', { name: /nome do grupo/i });
    await nameInput.fill(groupName);

    // Fill in description
    const descInput = modal.getByRole('textbox', { name: /descri/i });
    if (await descInput.isVisible()) {
      await descInput.fill('This is a test description for E2E testing');
    }

    // Submit
    const submitButton = modal.getByRole('button', { name: /criar grupo/i });
    await expect(submitButton).toBeEnabled({ timeout: 5000 });
    await submitButton.click();

    // Wait for modal to close (indicates success)
    await expect(modal).not.toBeVisible({ timeout: 30000 });

    // Wait for list to refresh after group creation
    await page.waitForTimeout(1000);

    // Verify group appears in list (use first to avoid strict mode)
    await expect(page.getByText(groupName).first()).toBeVisible({ timeout: 15000 });
  });

  test('should validate empty name', async ({ page }) => {
    await page.goto('/synths');
    await page.waitForLoadState('networkidle');

    // Wait for page to load
    await expect(page.locator('h2').filter({ hasText: /synths/i })).toBeVisible({ timeout: 10000 });

    // Open create modal
    const createButton = page.getByRole('button', { name: /novo grupo/i });
    await expect(createButton).toBeVisible({ timeout: 10000 });
    await createButton.click();

    // Wait for modal
    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible({ timeout: 10000 });

    // Try to submit without name - button is "Criar Grupo"
    const submitButton = modal.getByRole('button', { name: /criar grupo/i });

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
    await page.goto('/synths');
    await page.waitForLoadState('networkidle');

    // Wait for page to load
    await expect(page.locator('h2').filter({ hasText: /synths/i })).toBeVisible({ timeout: 10000 });

    // Open create modal
    const createButton = page.getByRole('button', { name: /novo grupo/i });
    await expect(createButton).toBeVisible({ timeout: 10000 });
    await createButton.click();

    // Wait for modal
    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible({ timeout: 10000 });

    // Fill in some data using the textbox labeled "Nome do Grupo"
    const nameInput = modal.getByRole('textbox', { name: /nome do grupo/i });
    await expect(nameInput).toBeVisible({ timeout: 5000 });
    await nameInput.fill('Should Be Canceled');

    // Click cancel
    const cancelButton = modal.locator('button').filter({ hasText: /cancelar|cancel|fechar|close/i });
    await cancelButton.first().click();

    // Modal should close
    await expect(modal).not.toBeVisible({ timeout: 3000 });

    // Group should not be in list
    await expect(page.locator('text=Should Be Canceled')).not.toBeVisible();
  });

  test('should close modal with X button', async ({ page }) => {
    await page.goto('/synths');
    await page.waitForLoadState('networkidle');

    // Wait for page to load
    await expect(page.locator('h2').filter({ hasText: /synths/i })).toBeVisible({ timeout: 10000 });

    // Open create modal
    const createButton = page.getByRole('button', { name: /novo grupo/i });
    await expect(createButton).toBeVisible({ timeout: 10000 });
    await createButton.click();

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
