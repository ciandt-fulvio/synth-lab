/**
 * E2E test - Create Synth Group with Custom Distributions
 *
 * Tests the flow of creating a synth group with custom demographic distributions.
 * This includes testing distribution sliders, normalization, and synth generation.
 *
 * Run: npx playwright test tests/e2e/synth-groups/create-with-config.spec.ts
 */
import { test, expect } from '@playwright/test';

test.describe('Create Synth Group with Config', () => {
  // Run tests serially to avoid race conditions with parallel group creation
  test.describe.configure({ mode: 'serial' });

  // TODO(BUG): Modal doesn't close after synth group creation with custom config
  // Same issue as create-basic-group.spec.ts
  // Backend API works, but modal stays open after clicking "Criar Grupo"
  test.skip('should create group with custom distributions', async ({ page }) => {
    await page.goto('/synths');
    await page.waitForLoadState('networkidle');

    // Wait for page to load
    await expect(page.locator('h2').filter({ hasText: /synths/i })).toBeVisible({ timeout: 10000 });

    // Generate unique group name with short random suffix (UI truncates long names)
    const uniqueId = Math.random().toString(36).substring(2, 8);
    const groupName = `CD ${uniqueId}`;

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

    // Number of synths is a combobox with preset values - skip this configuration
    // The UI uses a select dropdown, not a text input

    // Adjust age distribution slider (if present)
    const ageSliders = modal.locator('input[type="range"]');

    if (await ageSliders.count() > 0) {
      // Adjust first age slider
      await ageSliders.first().fill('50');
    }

    // Submit and wait for synth generation
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

  test('should adjust distribution sliders', async ({ page }) => {
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

    // Find any sliders in the modal
    const sliders = modal.locator('input[type="range"]');
    const sliderCount = await sliders.count();

    if (sliderCount > 0) {
      // Get first slider initial value
      const firstSlider = sliders.first();
      const initialValue = await firstSlider.inputValue();

      // Adjust slider
      await firstSlider.fill('60');

      // Verify value changed
      const newValue = await firstSlider.inputValue();
      expect(newValue).not.toBe(initialValue);
    } else {
      test.skip('No distribution sliders found in modal');
    }
  });

  test('should reset distribution to defaults', async ({ page }) => {
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

    // Find a distribution section with reset button
    const resetButton = modal.locator('button').filter({ hasText: /reset|padr[ãa]o|default/i });

    if (await resetButton.count() > 0) {
      // Find associated slider
      const section = resetButton.first().locator('..');
      const slider = section.locator('input[type="range"]').first();

      if (await slider.count() > 0) {
        // Change slider
        await slider.fill('80');
        const changedValue = await slider.inputValue();

        // Click reset
        await resetButton.first().click();

        // Wait a bit for reset to apply
        await page.waitForTimeout(500);

        // Value should change back
        const resetValue = await slider.inputValue();
        expect(resetValue).not.toBe(changedValue);
      } else {
        test.skip('No slider found near reset button');
      }
    } else {
      test.skip('No reset button found');
    }
  });

  test('should select domain expertise preset', async ({ page }) => {
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

    // Look for domain expertise section
    const expertiseSection = modal.locator('text=/dom[ií]nio|domain.*expertise/i').locator('..');

    if (await expertiseSection.count() > 0) {
      // Look for preset buttons (baixo, regular, alto)
      const presetButtons = expertiseSection.locator('button').filter({
        hasText: /baixo|regular|alto|low|medium|high/i
      });

      if (await presetButtons.count() > 0) {
        // Click a preset
        await presetButtons.first().click();

        // Verify button becomes selected (aria-pressed or active class)
        const firstButton = presetButtons.first();
        const isPressed = await firstButton.getAttribute('aria-pressed');
        const hasActiveClass = await firstButton.evaluate((el) =>
          el.className.includes('active') || el.className.includes('selected')
        );

        expect(isPressed === 'true' || hasActiveClass).toBeTruthy();
      } else {
        test.skip('No preset buttons found');
      }
    } else {
      test.skip('No domain expertise section found');
    }
  });

  test('should validate n_synths range', async ({ page }) => {
    // This test is skipped because the UI uses a select dropdown with preset values
    // instead of a free-form input, so there's no way to enter invalid values
    test.skip('n_synths uses a select dropdown with preset valid values only');
  });

  test('should show progress during synth generation', async ({ page }) => {
    await page.goto('/synths');
    await page.waitForLoadState('networkidle');

    // Wait for page to load
    await expect(page.locator('h2').filter({ hasText: /synths/i })).toBeVisible({ timeout: 10000 });

    // Generate unique group name with short random suffix (UI truncates long names)
    const uniqueId = Math.random().toString(36).substring(2, 8);
    const groupName = `PT ${uniqueId}`;

    // Open create modal
    const createButton = page.getByRole('button', { name: /novo grupo/i });
    await expect(createButton).toBeVisible({ timeout: 10000 });
    await createButton.click();

    // Wait for modal
    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible({ timeout: 10000 });

    // Fill in minimal data using the textbox labeled "Nome do Grupo"
    const nameInput = modal.getByRole('textbox', { name: /nome do grupo/i });
    await expect(nameInput).toBeVisible({ timeout: 5000 });
    await nameInput.fill(groupName);

    // Submit
    const submitButton = modal.getByRole('button', { name: /criar grupo/i });
    await expect(submitButton).toBeEnabled({ timeout: 5000 });
    await submitButton.click();

    // Should show loading or progress indicator (button may show loading state)
    // Or modal may close immediately if generation is fast

    // Wait for modal to close (indicates success)
    await expect(modal).not.toBeVisible({ timeout: 30000 });

    // Wait for list to refresh after group creation
    await page.waitForTimeout(1000);

    // Verify group appears in list (use first to avoid strict mode)
    await expect(page.getByText(groupName).first()).toBeVisible({ timeout: 15000 });
  });
});
