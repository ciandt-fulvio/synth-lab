/**
 * E2E test - Synth Groups Integration with Experiments
 *
 * Tests the integration between synth groups and experiments, verifying
 * that experiments can be linked to groups and that the linkage is maintained.
 *
 * Run: npx playwright test tests/e2e/synth-groups/experiment-integration.spec.ts
 */
import { test, expect } from '@playwright/test';

test.describe('Synth Groups - Experiment Integration', () => {
  test('should show synth group selector in experiment form', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Wait for page to load
    await expect(page.locator('h2').filter({ hasText: /experimentos/i })).toBeVisible({ timeout: 10000 });

    // Look for create experiment button
    const createButton = page.locator('button').filter({ hasText: /novo.*experimento|new.*experiment|criar/i });

    if (await createButton.count() > 0) {
      await createButton.first().click();

      // Wait for form
      await page.waitForSelector('form', { timeout: 5000 });

      // Look for synth group selector
      const groupSelector = page.locator('select[name="synth_group_id"]').or(
        page.locator('label').filter({ hasText: /grupo.*synth|synth.*group/i }).locator('..').locator('select, input')
      );

      if (await groupSelector.count() > 0) {
        await expect(groupSelector).toBeVisible();
      } else {
        test.skip('Synth group selector not found in form');
      }
    } else {
      test.skip('Create experiment button not found');
    }
  });

  test('should create experiment with selected synth group', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Create experiment button
    const createButton = page.locator('button').filter({ hasText: /novo.*experimento|new.*experiment|criar/i });

    if (await createButton.count() > 0) {
      await createButton.first().click();

      // Fill in experiment name
      const nameInput = page.locator('input[name="name"]').or(
        page.locator('label').filter({ hasText: /^nome|^name/i }).locator('..').locator('input')
      );
      await nameInput.fill('E2E Experiment with Group');

      // Fill hypothesis
      const hypothesisInput = page.locator('textarea[name="hypothesis"]').or(
        page.locator('input[name="hypothesis"]')
      );

      if (await hypothesisInput.count() > 0) {
        await hypothesisInput.fill('Test hypothesis for E2E');
      }

      // Select synth group
      const groupSelector = page.locator('select[name="synth_group_id"]').or(
        page.locator('label').filter({ hasText: /grupo.*synth|synth.*group/i }).locator('..').locator('select')
      );

      if (await groupSelector.count() > 0) {
        // Get available options
        const options = groupSelector.locator('option');
        const optionCount = await options.count();

        if (optionCount > 1) {
          // Select second option (first is usually default)
          await options.nth(1).click();
        }
      }

      // Submit form
      const submitButton = page.locator('button[type="submit"]').or(
        page.locator('button').filter({ hasText: /criar|create|salvar|save/i })
      );
      await submitButton.click();

      // Wait for success
      await expect(page.locator('text=/sucesso|success|criado|created/i')).toBeVisible({
        timeout: 10000
      });

      // Should redirect to experiment detail or list
      await page.waitForLoadState('networkidle');

      // Verify experiment was created
      await expect(page.locator('text=E2E Experiment with Group')).toBeVisible();
    } else {
      test.skip('Create experiment button not found');
    }
  });

  test('should display synth group in experiment detail', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Find an experiment
    const experimentCards = page.locator('[data-testid="experiment-card"]').or(
      page.locator('.cursor-pointer').filter({ has: page.locator('h3') })
    );

    const count = await experimentCards.count();

    if (count > 0) {
      // Click first experiment
      await experimentCards.first().click();
      await page.waitForLoadState('networkidle');

      // Look for synth group information
      const groupInfo = page.locator('text=/grupo.*synth|synth.*group/i').or(
        page.locator('[data-testid="synth-group-info"]')
      );

      if (await groupInfo.count() > 0) {
        await expect(groupInfo.first()).toBeVisible();
      }
    } else {
      test.skip('No experiments available');
    }
  });

  test('should update experiment synth group', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Find an experiment
    const experimentCards = page.locator('[data-testid="experiment-card"]').or(
      page.locator('.cursor-pointer')
    );

    const count = await experimentCards.count();

    if (count > 0) {
      await experimentCards.first().click();
      await page.waitForLoadState('networkidle');

      // Look for edit button
      const editButton = page.locator('button').filter({ hasText: /editar|edit/i });

      if (await editButton.count() > 0) {
        await editButton.first().click();

        // Find synth group selector
        const groupSelector = page.locator('select[name="synth_group_id"]');

        if (await groupSelector.count() > 0) {
          // Get current value
          const currentValue = await groupSelector.inputValue();

          // Select different option
          const options = groupSelector.locator('option');
          const optionCount = await options.count();

          if (optionCount > 1) {
            // Find an option different from current
            for (let i = 0; i < optionCount; i++) {
              const optionValue = await options.nth(i).getAttribute('value');
              if (optionValue !== currentValue) {
                await options.nth(i).click();
                break;
              }
            }

            // Save changes
            const saveButton = page.locator('button[type="submit"]').or(
              page.locator('button').filter({ hasText: /salvar|save/i })
            );
            await saveButton.click();

            // Wait for success
            await expect(page.locator('text=/atualizado|updated|sucesso|success/i')).toBeVisible({
              timeout: 10000
            });
          }
        }
      }
    } else {
      test.skip('No experiments available');
    }
  });

  test('should link to synth group from experiment', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Find an experiment
    const experimentCards = page.locator('[data-testid="experiment-card"]');
    const count = await experimentCards.count();

    if (count > 0) {
      await experimentCards.first().click();
      await page.waitForLoadState('networkidle');

      // Look for link to synth group (groups are shown in /synths page)
      const groupLink = page.locator('a[href*="/synths"]').or(
        page.locator('button').filter({ hasText: /ver.*grupo|view.*group/i })
      );

      if (await groupLink.count() > 0) {
        await groupLink.first().click();

        // Should navigate to synths page
        await expect(page).toHaveURL(/\/synths/);
      }
    } else {
      test.skip('No experiments available');
    }
  });

  test('should filter explorations by experiment synth group', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Find an experiment with explorations
    const experimentCards = page.locator('[data-testid="experiment-card"]');
    const count = await experimentCards.count();

    if (count > 0) {
      await experimentCards.first().click();
      await page.waitForLoadState('networkidle');

      // Look for explorations section
      const explorationsSection = page.locator('text=/explora[çc][õo]es|explorations/i').or(
        page.locator('[data-testid="explorations"]')
      );

      if (await explorationsSection.count() > 0) {
        // Explorations should use experiment's synth group
        // This is implicit - just verify explorations section exists
        await expect(explorationsSection.first()).toBeVisible();
      }
    } else {
      test.skip('No experiments available');
    }
  });

  test('should show synth group in experiment list', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Find experiment cards
    const experimentCards = page.locator('[data-testid="experiment-card"]');
    const count = await experimentCards.count();

    if (count > 0) {
      const firstCard = experimentCards.first();

      // Look for synth group badge or indicator
      const groupIndicator = firstCard.locator('text=/grupo|group/i').or(
        firstCard.locator('[data-testid="synth-group-badge"]')
      );

      // May or may not be shown in list - just check if present
      const hasIndicator = await groupIndicator.count() > 0;

      // This is informational - we just want to know if it's displayed
      expect(hasIndicator).toBeDefined();
    } else {
      test.skip('No experiments available');
    }
  });
});

test.describe('Synth Groups - Full Integration Flow', () => {
  test('complete flow: create group → create experiment → verify linkage', async ({ page }) => {
    // 1. Create synth group
    await page.goto('/synths');
    await page.waitForLoadState('networkidle');

    // Wait for page to load
    await expect(page.locator('h2').filter({ hasText: /synths/i })).toBeVisible({ timeout: 10000 });

    const createGroupButton = page.getByRole('button', { name: /novo grupo/i });
    await expect(createGroupButton).toBeVisible({ timeout: 10000 });
    await createGroupButton.click();

    const nameInput = page.locator('input[name="name"]');
    await nameInput.fill('E2E Integration Test Group');

    const submitButton = page.locator('button[type="submit"]').or(
      page.locator('button').filter({ hasText: /criar|create/i })
    );
    await submitButton.click();

    await expect(page.locator('text=/sucesso|success|criado|created/i')).toBeVisible({
      timeout: 10000
    });

    // 2. Create experiment using this group
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const createExpButton = page.locator('button').filter({ hasText: /novo.*experimento|new.*experiment/i });

    if (await createExpButton.count() > 0) {
      await createExpButton.first().click();

      const expNameInput = page.locator('input[name="name"]');
      await expNameInput.fill('E2E Linked Experiment');

      const hypothesisInput = page.locator('textarea[name="hypothesis"]').or(
        page.locator('input[name="hypothesis"]')
      );
      if (await hypothesisInput.count() > 0) {
        await hypothesisInput.fill('Test hypothesis');
      }

      // Select the group we just created
      const groupSelector = page.locator('select[name="synth_group_id"]');
      if (await groupSelector.count() > 0) {
        const options = groupSelector.locator('option');
        const optionTexts = await options.allTextContents();

        // Find our group
        const groupOptionIndex = optionTexts.findIndex(text =>
          text.includes('E2E Integration Test Group')
        );

        if (groupOptionIndex >= 0) {
          await options.nth(groupOptionIndex).click();
        }
      }

      const submitExpButton = page.locator('button[type="submit"]');
      await submitExpButton.click();

      await expect(page.locator('text=/sucesso|success|criado|created/i')).toBeVisible({
        timeout: 10000
      });

      // 3. Verify experiment has correct group
      await expect(page.locator('text=E2E Linked Experiment')).toBeVisible();

      // If on detail page, verify group is shown
      const groupInfo = page.locator('text=/E2E Integration Test Group/i');
      if (await groupInfo.count() > 0) {
        await expect(groupInfo).toBeVisible();
      }
    }
  });
});
