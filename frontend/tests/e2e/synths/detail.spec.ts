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
  test.beforeEach(async ({ page }) => {
    // Navega para página de synths
    await page.goto('/synths');
    await page.waitForLoadState('networkidle');

    // Wait for synth cards to load
    await expect(page.locator('h2').filter({ hasText: /synths/i })).toBeVisible({ timeout: 10000 });
    await expect(page.locator('img[alt]').first()).toBeVisible({ timeout: 10000 });
  });

  test('Y014 - Click on synth card opens modal', async ({ page }) => {
    // Clica no primeiro card de synth (imagem ou nome)
    const firstCard = page.locator('img[alt]').first();
    const synthName = await firstCard.getAttribute('alt');

    await firstCard.click();

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
    // Clica no primeiro synth
    await page.locator('img[alt]').first().click();

    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible();

    // Deve mostrar descrição completa (idade, ocupação, localização, interesses)
    const description = modal.locator('text=/anos.*mora em/i').first();
    await expect(description).toBeVisible();
  });

  test('Y016 - Modal has three tabs', async ({ page }) => {
    await page.locator('img[alt]').first().click();

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
    await page.locator('img[alt]').first().click();

    const modal = page.locator('[role="dialog"]');
    const demografiaTab = modal.getByRole('tab', { name: /demografia/i });

    // Tab Demografia deve estar selecionada
    const isSelected = await demografiaTab.getAttribute('aria-selected');
    expect(isSelected).toBe('true');
  });

  test('Y018 - Demografia tab shows correct information', async ({ page }) => {
    await page.locator('img[alt]').first().click();

    const modal = page.locator('[role="dialog"]');

    // Verifica que está na tab Demografia
    const demografiaTab = modal.getByRole('tab', { name: /demografia/i });
    await expect(demografiaTab).toHaveAttribute('aria-selected', 'true');

    // Deve mostrar campos demográficos
    await expect(modal.locator('text=/idade:/i')).toBeVisible();
    await expect(modal.locator('text=/gênero/i')).toBeVisible();
    await expect(modal.locator('text=/raça.*etnia/i')).toBeVisible();
    await expect(modal.locator('text=/escolaridade/i')).toBeVisible();
    await expect(modal.locator('text=/ocupação/i')).toBeVisible();
    await expect(modal.locator('text=/renda/i')).toBeVisible();
    await expect(modal.locator('text=/estado civil/i')).toBeVisible();
    await expect(modal.locator('text=/localização/i')).toBeVisible();
  });

  test('Y019 - Switch to Psicografia tab', async ({ page }) => {
    await page.locator('img[alt]').first().click();

    const modal = page.locator('[role="dialog"]');
    const psicografiaTab = modal.getByRole('tab', { name: /psicografia/i });

    // Clica na tab Psicografia
    await psicografiaTab.click();
    await page.waitForTimeout(300);

    // Tab deve estar selecionada
    await expect(psicografiaTab).toHaveAttribute('aria-selected', 'true');
  });

  test('Y020 - Psicografia tab shows correct information', async ({ page }) => {
    await page.locator('img[alt]').first().click();

    const modal = page.locator('[role="dialog"]');
    const psicografiaTab = modal.getByRole('tab', { name: /psicografia/i });

    await psicografiaTab.click();
    await page.waitForTimeout(300);

    // Deve mostrar Interesses
    await expect(modal.locator('h3').filter({ hasText: /interesses/i })).toBeVisible();

    // Deve mostrar Contrato Cognitivo
    await expect(modal.locator('h3').filter({ hasText: /contrato cognitivo/i })).toBeVisible();

    // Deve mostrar tipo, perfil e efeito esperado
    await expect(modal.locator('text=/tipo:/i')).toBeVisible();
    await expect(modal.locator('text=/perfil:/i')).toBeVisible();
    await expect(modal.locator('text=/efeito esperado:/i')).toBeVisible();
  });

  test('Y021 - Switch to Capacidades Técnicas tab', async ({ page }) => {
    await page.locator('img[alt]').first().click();

    const modal = page.locator('[role="dialog"]');
    const capacidadesTab = modal.getByRole('tab', { name: /capacidades técnicas/i });

    // Clica na tab Capacidades Técnicas
    await capacidadesTab.click();
    await page.waitForTimeout(300);

    // Tab deve estar selecionada
    await expect(capacidadesTab).toHaveAttribute('aria-selected', 'true');
  });

  test('Y022 - Capacidades Técnicas tab shows attributes', async ({ page }) => {
    await page.locator('img[alt]').first().click();

    const modal = page.locator('[role="dialog"]');
    const capacidadesTab = modal.getByRole('tab', { name: /capacidades técnicas/i });

    await capacidadesTab.click();
    await page.waitForTimeout(300);

    // Deve mostrar título de Atributos Observáveis
    await expect(
      modal.locator('h3').filter({ hasText: /atributos observáveis/i })
    ).toBeVisible();

    // Deve mostrar descrição
    await expect(
      modal.locator('text=/características que podem ser identificadas/i')
    ).toBeVisible();

    // Deve mostrar atributos (pelo menos um)
    // Exemplos: Familiaridade com tecnologia, Experiência com ferramentas similares, etc.
    const attributes = modal.locator('text=/familiaridade.*tecnologia|experiência.*ferramentas|habilidade física|disponibilidade.*tempo|conhecimento.*assunto/i');
    const count = await attributes.count();
    expect(count).toBeGreaterThan(0);
  });

  test('Y023 - Capacidades shows percentage values', async ({ page }) => {
    await page.locator('img[alt]').first().click();

    const modal = page.locator('[role="dialog"]');
    const capacidadesTab = modal.getByRole('tab', { name: /capacidades técnicas/i });

    await capacidadesTab.click();
    await page.waitForTimeout(300);

    // Deve mostrar valores percentuais (ex: 52%, 63%)
    const percentages = modal.locator('text=/\d+%/');
    const count = await percentages.count();
    expect(count).toBeGreaterThan(0);
  });

  test('Y024 - Navigate between all three tabs', async ({ page }) => {
    await page.locator('img[alt]').first().click();

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
    await page.locator('img[alt]').first().click();

    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible();

    // Pressiona ESC
    await page.keyboard.press('Escape');

    // Modal deve fechar
    await expect(modal).not.toBeVisible({ timeout: 3000 });
  });

  test('Y026 - Close modal with Close button', async ({ page }) => {
    await page.locator('img[alt]').first().click();

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
    // Clica no primeiro synth
    const firstSynthName = await page.locator('h3').first().textContent();
    await page.locator('img[alt]').first().click();

    let modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible();
    await expect(modal.locator('h2').first()).toHaveText(new RegExp(firstSynthName!, 'i'));

    // Fecha modal
    await page.keyboard.press('Escape');
    await expect(modal).not.toBeVisible();

    // Clica no segundo synth
    const secondSynthName = await page.locator('h3').nth(1).textContent();
    await page.locator('img[alt]').nth(1).click();

    modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible();
    await expect(modal.locator('h2').first()).toHaveText(new RegExp(secondSynthName!, 'i'));

    // Nomes devem ser diferentes
    expect(firstSynthName).not.toEqual(secondSynthName);
  });
});
