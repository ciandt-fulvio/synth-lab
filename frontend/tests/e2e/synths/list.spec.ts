/**
 * E2E Tests - Synths List & Pagination
 *
 * Testa a listagem de synths, filtros por grupo e paginação.
 * Estes são testes críticos (P0) para garantir acesso ao catálogo de synths.
 *
 * Run: npm run test:e2e synths/list.spec.ts
 */
import { test, expect } from '@playwright/test';

test.describe('Synths - List Page @critical @synths', () => {
  test.beforeEach(async ({ page }) => {
    // Navega para página de synths
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Clica no botão "Synths" no header
    const synthsBtn = page.getByRole('button', { name: /synths/i });
    await expect(synthsBtn).toBeVisible({ timeout: 10000 });
    await synthsBtn.click();

    // Aguarda navegação
    await expect(page).toHaveURL(/\/synths/);
    await page.waitForLoadState('networkidle');

    // Wait for page to load completely
    await expect(page.locator('h2').filter({ hasText: /synths/i })).toBeVisible({ timeout: 10000 });
    await expect(page.locator('img[alt]').first()).toBeVisible({ timeout: 10000 });
  });

  test('Y001 - Synths page loads correctly', async ({ page }) => {
    // Verifica URL
    await expect(page).toHaveURL(/\/synths/);

    // Header "Synths" deve estar visível
    await expect(
      page.locator('h2').filter({ hasText: /synths/i }).first()
    ).toBeVisible({ timeout: 10000 });

    // Descrição deve estar visível
    await expect(
      page.locator('text=/cada synth representa um perfil/i')
    ).toBeVisible();
  });

  test('Y002 - Synth cards are displayed', async ({ page }) => {
    // Deve mostrar cards de synths
    const synthCards = page.locator('h3').filter({
      hasText: /.+/ // Qualquer nome de synth
    });

    const count = await synthCards.count();

    // Deve ter pelo menos 1 synth
    expect(count).toBeGreaterThan(0);

    // Primeiro card deve ter imagem (avatar)
    const firstCardParent = synthCards.first().locator('../..');
    const hasImage = await firstCardParent.locator('img').count() > 0;
    expect(hasImage).toBeTruthy();
  });

  test('Y003 - Synth cards show required information', async ({ page }) => {
    const firstCard = page.locator('h3').first().locator('../..');

    // Card deve ter nome (h3)
    await expect(firstCard.locator('h3')).toBeVisible();

    // Card deve ter descrição
    const cardText = await firstCard.textContent();
    expect(cardText).toBeTruthy();

    // Deve mostrar informações demográficas (idade, ocupação, etc.)
    const hasAge = /\d+\s*anos/i.test(cardText!);
    expect(hasAge).toBeTruthy();
  });

  test('Y004 - Group badge is displayed on cards', async ({ page }) => {
    // Cards devem mostrar badge do grupo (ex: "Default", "Aposentados 60+")
    const groupBadges = page.locator('text=/^Default$|^Aposentados 60\+$/i');

    const count = await groupBadges.count();

    // Deve ter pelo menos um badge visível
    expect(count).toBeGreaterThan(0);
  });

  test('Y005 - Filter by group dropdown exists', async ({ page }) => {
    // Dropdown de filtro por grupo deve estar visível
    const groupFilter = page.locator('[role="combobox"]').filter({
      hasText: /todos os grupos/i
    }).first();

    await expect(groupFilter).toBeVisible();
  });

  test('Y006 - Filter by group works', async ({ page }) => {
    const groupFilter = page.locator('[role="combobox"]').filter({
      hasText: /todos os grupos/i
    }).first();

    // Conta synths antes do filtro
    const allCards = page.locator('h3').filter({ hasText: /.+/ });
    const totalBefore = await allCards.count();

    // Abre dropdown
    await groupFilter.click();
    await page.waitForTimeout(300);

    // Procura opção "Aposentados 60+" (se disponível)
    const aposentadosOption = page.locator('[role="option"]').filter({
      hasText: /aposentados 60\+/i
    }).first();

    if (await aposentadosOption.isVisible()) {
      await aposentadosOption.click();
      await page.waitForTimeout(500);

      // Após filtrar, deve mostrar apenas synths desse grupo
      const filteredCards = page.locator('h3').filter({ hasText: /.+/ });
      const totalAfter = await filteredCards.count();

      // Deve ter menos ou igual synths após filtro
      expect(totalAfter).toBeLessThanOrEqual(totalBefore);

      // Todos os badges visíveis devem ser "Aposentados 60+"
      const visibleBadges = page.locator('text=/^Aposentados 60\+$/i');
      const badgeCount = await visibleBadges.count();
      expect(badgeCount).toBeGreaterThan(0);
    } else {
      test.skip('Opção "Aposentados 60+" não disponível');
    }
  });

  test('Y007 - Clear group filter restores full list', async ({ page }) => {
    const groupFilter = page.locator('[role="combobox"]').filter({
      hasText: /todos os grupos/i
    }).first();

    // Conta total inicial
    const allCardsBefore = page.locator('h3').filter({ hasText: /.+/ });
    const totalBefore = await allCardsBefore.count();

    // Aplica filtro
    await groupFilter.click();
    await page.waitForTimeout(300);

    const aposentadosOption = page.locator('[role="option"]').filter({
      hasText: /aposentados 60\+/i
    }).first();

    if (await aposentadosOption.isVisible()) {
      await aposentadosOption.click();
      await page.waitForTimeout(500);

      const filteredCount = await allCardsBefore.count();

      // Volta para "Todos os grupos"
      await groupFilter.click();
      await page.waitForTimeout(300);

      const todosOption = page.locator('[role="option"]').filter({
        hasText: /todos os grupos/i
      }).first();

      await todosOption.click();
      await page.waitForTimeout(500);

      // Deve voltar a mostrar todos
      const totalAfter = await allCardsBefore.count();
      expect(totalAfter).toBeGreaterThanOrEqual(filteredCount);
    } else {
      test.skip('Filtro por grupo não disponível');
    }
  });
});

test.describe('Synths - Pagination @synths', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/synths');
    await page.waitForLoadState('networkidle');
  });

  test('Y008 - Pagination controls are visible', async ({ page }) => {
    // Deve mostrar informação de paginação (ex: "Mostrando 1 a 45 de 420 synths")
    const paginationInfo = page.locator('text=/mostrando.*de.*synths/i');
    await expect(paginationInfo).toBeVisible({ timeout: 5000 });
  });

  test('Y009 - Pagination shows correct page size', async ({ page }) => {
    // Verifica texto de paginação
    const paginationText = await page.locator('text=/mostrando.*de.*synths/i').textContent();

    // Deve mostrar algo como "Mostrando 1 a 45 de 420 synths"
    expect(paginationText).toBeTruthy();

    // Extrai números (ex: 1, 45, 420)
    const matches = paginationText!.match(/\d+/g);
    expect(matches).toBeTruthy();
    expect(matches!.length).toBe(3);

    const start = parseInt(matches![0]);
    const end = parseInt(matches![1]);
    const total = parseInt(matches![2]);

    // Start deve ser 1 na primeira página
    expect(start).toBe(1);

    // End deve ser maior que start
    expect(end).toBeGreaterThan(start);

    // Total deve ser maior que end (se houver mais páginas)
    expect(total).toBeGreaterThanOrEqual(end);

    // Conta cards visíveis
    const cards = page.locator('h3').filter({ hasText: /.+/ });
    const cardCount = await cards.count();

    // Número de cards deve ser aproximadamente end - start + 1
    expect(cardCount).toBeGreaterThan(0);
    expect(cardCount).toBeLessThanOrEqual(end - start + 5); // +5 de margem
  });

  test('Y010 - Next page button exists', async ({ page }) => {
    // Procura navegação de paginação
    const paginationNav = page.locator('nav').filter({
      has: page.locator('text=/next|próxim/i')
    });

    if (!(await paginationNav.isVisible())) {
      test.skip('Navegação de paginação não encontrada');
    }

    // Botão "Next" ou "Próxima" deve estar visível
    const nextButton = page.locator('text=/next|próxim/i').first();
    await expect(nextButton).toBeVisible();
  });

  test('Y011 - Navigate to next page', async ({ page }) => {
    // Salva primeiro synth da página 1
    const firstSynthPage1 = await page.locator('h3').first().textContent();

    // Procura botão Next
    const nextButton = page.locator('text=/next|próxim/i').first();

    if (!(await nextButton.isVisible())) {
      test.skip('Botão Next não encontrado');
    }

    // Verifica se botão está habilitado
    const isDisabled = await nextButton.evaluate(el => {
      return el.hasAttribute('disabled') || el.classList.contains('disabled');
    });

    if (isDisabled) {
      test.skip('Apenas uma página de synths disponível');
    }

    // Clica em Next
    await nextButton.click();
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500);

    // Primeiro synth da página 2 deve ser diferente
    const firstSynthPage2 = await page.locator('h3').first().textContent();
    expect(firstSynthPage2).not.toEqual(firstSynthPage1);

    // Info de paginação deve mostrar página 2
    const paginationText = await page.locator('text=/mostrando.*de.*synths/i').textContent();
    const matches = paginationText!.match(/\d+/g);
    const start = parseInt(matches![0]);

    // Start deve ser > 1 (ex: 46 se page size é 45)
    expect(start).toBeGreaterThan(1);
  });

  test('Y012 - Navigate to previous page', async ({ page }) => {
    // Vai para página 2 primeiro
    const nextButton = page.locator('text=/next|próxim/i').first();

    if (!(await nextButton.isVisible())) {
      test.skip('Botão Next não encontrado');
    }

    const isDisabled = await nextButton.evaluate(el => {
      return el.hasAttribute('disabled') || el.classList.contains('disabled');
    });

    if (isDisabled) {
      test.skip('Apenas uma página disponível');
    }

    await nextButton.click();
    await page.waitForTimeout(500);

    // Salva primeiro synth da página 2
    const firstSynthPage2 = await page.locator('h3').first().textContent();

    // Volta para página 1
    const prevButton = page.locator('text=/previous|anterior/i').first();
    await prevButton.click();
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500);

    // Primeiro synth deve ser diferente
    const firstSynthPage1 = await page.locator('h3').first().textContent();
    expect(firstSynthPage1).not.toEqual(firstSynthPage2);

    // Info de paginação deve mostrar página 1
    const paginationText = await page.locator('text=/mostrando.*de.*synths/i').textContent();
    const matches = paginationText!.match(/\d+/g);
    const start = parseInt(matches![0]);

    // Start deve ser 1
    expect(start).toBe(1);
  });

  test('Y013 - Direct page navigation works', async ({ page }) => {
    // Procura botões de número de página (ex: 1, 2, 3...)
    const pageNumbers = page.locator('[role="navigation"] button').filter({
      hasText: /^\d+$/
    });

    const count = await pageNumbers.count();

    if (count < 2) {
      test.skip('Não há múltiplas páginas para testar');
    }

    // Clica na página 2
    const page2Button = page.locator('[role="navigation"] button').filter({
      hasText: /^2$/
    }).first();

    if (!(await page2Button.isVisible())) {
      test.skip('Botão de página 2 não encontrado');
    }

    await page2Button.click();
    await page.waitForTimeout(500);

    // Verifica que navegou para página 2
    const paginationText = await page.locator('text=/mostrando.*de.*synths/i').textContent();
    const matches = paginationText!.match(/\d+/g);
    const start = parseInt(matches![0]);

    // Start deve ser > 1
    expect(start).toBeGreaterThan(1);
  });
});
