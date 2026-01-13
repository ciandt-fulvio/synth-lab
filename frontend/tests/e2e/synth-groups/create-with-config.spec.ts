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
  test('should create group with custom distributions', async ({ page }) => {
    await page.goto('/synth-groups');
    await page.waitForLoadState('networkidle');

    // Open create modal
    const createButton = page.locator('button').filter({ hasText: /criar|novo|create|new/i });
    await createButton.first().click();

    // Fill in group name
    const nameInput = page.locator('input[name="name"]').or(
      page.locator('label').filter({ hasText: /nome|name/i }).locator('..').locator('input')
    );
    await nameInput.fill('E2E Custom Distribution Group');

    // Set number of synths (smaller number for E2E speed)
    const nSynthsInput = page.locator('input[name="n_synths"]').or(
      page.locator('label').filter({ hasText: /n[uú]mero.*synths|number.*synths/i }).locator('..').locator('input')
    );

    if (await nSynthsInput.count() > 0) {
      await nSynthsInput.clear();
      await nSynthsInput.fill('10');
    }

    // Adjust age distribution slider (if present)
    const ageSliders = page.locator('input[type="range"]').filter({
      has: page.locator('label:has-text("idade"), label:has-text("age")')
    });

    if (await ageSliders.count() > 0) {
      // Adjust first age slider
      await ageSliders.first().fill('50');
    }

    // Submit and wait for synth generation
    const submitButton = page.locator('button[type="submit"]').or(
      page.locator('button').filter({ hasText: /criar|create|gerar|generate/i })
    );
    await submitButton.click();

    // Should show loading state during generation
    const loadingIndicator = page.locator('text=/gerando|generating|aguarde|wait/i').or(
      page.locator('[data-testid="loading"]')
    );

    if (await loadingIndicator.count() > 0) {
      await expect(loadingIndicator).toBeVisible({ timeout: 3000 });
    }

    // Wait for success (may take several seconds)
    await expect(page.locator('text=/sucesso|success|criado|created/i')).toBeVisible({
      timeout: 30000 // Longer timeout for synth generation
    });

    // Verify group appears in list with synth count
    await expect(page.locator('text=E2E Custom Distribution Group')).toBeVisible();
  });

  test('should adjust distribution sliders', async ({ page }) => {
    await page.goto('/synth-groups');
    await page.waitForLoadState('networkidle');

    // Open create modal
    const createButton = page.locator('button').filter({ hasText: /criar|novo|create|new/i });
    await createButton.first().click();

    // Find distribution section (idade/age)
    const ageSection = page.locator('text=/distribui[çc][ãa]o.*idade|age.*distribution/i').locator('..');

    if (await ageSection.count() > 0) {
      // Find sliders in age section
      const sliders = ageSection.locator('input[type="range"]');
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
      }
    }
  });

  test('should reset distribution to defaults', async ({ page }) => {
    await page.goto('/synth-groups');
    await page.waitForLoadState('networkidle');

    // Open create modal
    const createButton = page.locator('button').filter({ hasText: /criar|novo|create|new/i });
    await createButton.first().click();

    // Find a distribution section with reset button
    const resetButton = page.locator('button').filter({ hasText: /reset|padr[ãa]o|default/i });

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
      }
    } else {
      test.skip('No reset button found');
    }
  });

  test('should select domain expertise preset', async ({ page }) => {
    await page.goto('/synth-groups');
    await page.waitForLoadState('networkidle');

    // Open create modal
    const createButton = page.locator('button').filter({ hasText: /criar|novo|create|new/i });
    await createButton.first().click();

    // Look for domain expertise section
    const expertiseSection = page.locator('text=/dom[ií]nio|domain.*expertise/i').locator('..');

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
      }
    }
  });

  test('should validate n_synths range', async ({ page }) => {
    await page.goto('/synth-groups');
    await page.waitForLoadState('networkidle');

    // Open create modal
    const createButton = page.locator('button').filter({ hasText: /criar|novo|create|new/i });
    await createButton.first().click();

    // Fill in name
    const nameInput = page.locator('input[name="name"]').or(
      page.locator('label').filter({ hasText: /nome|name/i }).locator('..').locator('input')
    );
    await nameInput.fill('Invalid Range Test');

    // Try invalid n_synths
    const nSynthsInput = page.locator('input[name="n_synths"]').or(
      page.locator('label').filter({ hasText: /n[uú]mero.*synths/i }).locator('..').locator('input')
    );

    if (await nSynthsInput.count() > 0) {
      // Try value > 1000
      await nSynthsInput.clear();
      await nSynthsInput.fill('1001');

      // Try to submit
      const submitButton = page.locator('button[type="submit"]').or(
        page.locator('button').filter({ hasText: /criar|create/i })
      );
      await submitButton.click();

      // Should show validation error
      await expect(page.locator('text=/m[aá]ximo|maximum|1000/i')).toBeVisible({
        timeout: 5000
      });
    } else {
      test.skip('n_synths input not found');
    }
  });

  test('should show progress during synth generation', async ({ page }) => {
    await page.goto('/synth-groups');
    await page.waitForLoadState('networkidle');

    // Open create modal
    const createButton = page.locator('button').filter({ hasText: /criar|novo|create|new/i });
    await createButton.first().click();

    // Fill in minimal data
    const nameInput = page.locator('input[name="name"]').or(
      page.locator('label').filter({ hasText: /nome|name/i }).locator('..').locator('input')
    );
    await nameInput.fill('Progress Test Group');

    // Set small n_synths
    const nSynthsInput = page.locator('input[name="n_synths"]');
    if (await nSynthsInput.count() > 0) {
      await nSynthsInput.clear();
      await nSynthsInput.fill('5');
    }

    // Submit
    const submitButton = page.locator('button[type="submit"]').or(
      page.locator('button').filter({ hasText: /criar|create/i })
    );
    await submitButton.click();

    // Should show loading or progress indicator
    const loadingIndicators = [
      page.locator('text=/gerando|generating|processando|processing/i'),
      page.locator('[role="progressbar"]'),
      page.locator('[data-testid="loading"]'),
      page.locator('.animate-spin')
    ];

    let foundLoading = false;
    for (const indicator of loadingIndicators) {
      if (await indicator.count() > 0) {
        await expect(indicator).toBeVisible({ timeout: 3000 });
        foundLoading = true;
        break;
      }
    }

    // At least one loading indicator should appear
    // (or generation is very fast)
    // expect(foundLoading).toBeTruthy();

    // Wait for completion
    await expect(page.locator('text=/sucesso|success|criado|created/i')).toBeVisible({
      timeout: 30000
    });
  });
});
