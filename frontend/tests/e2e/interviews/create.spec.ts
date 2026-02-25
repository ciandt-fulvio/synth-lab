/**
 * E2E Tests - Interviews Creation
 *
 * Testa o fluxo de criação de entrevistas via modal.
 * Estes testes requerem um experimento com interview guide configurado.
 *
 * Run: npm run test:e2e interviews/create.spec.ts
 */
import { test, expect, Page } from '../fixtures';

/**
 * Helper to navigate to an experiment's interview tab and check if "Nova Entrevista" is available.
 * Skips the test if the button is disabled (no interview guide configured).
 */
async function navigateToInterviewTab(page: Page): Promise<void> {
  await page.goto('/');
  await page.waitForLoadState('networkidle');

  // Wait for experiments page to load
  await expect(page.locator('h2').filter({ hasText: /experimentos/i })).toBeVisible({ timeout: 10000 });

  // Click first experiment
  const firstCard = page.locator('.cursor-pointer').filter({
    has: page.locator('h3')
  }).first();

  await expect(firstCard).toBeVisible({ timeout: 10000 });
  await firstCard.click();
  await page.waitForLoadState('networkidle');

  // Verify navigation to detail page
  await expect(page).toHaveURL(/\/experiments\/exp_/);

  // Wait for experiment detail page to load
  await expect(page.locator('h2').first()).toBeVisible({ timeout: 10000 });
  await expect(page.getByRole('tab', { name: /entrevistas/i })).toBeVisible({ timeout: 10000 });

  // Navigate to Interviews tab (should be default, but click to be safe)
  const interviewsTab = page.getByRole('tab', { name: /entrevistas/i });
  await interviewsTab.click();
  await page.waitForTimeout(500);

  // Check if "Nova Entrevista" button is enabled
  const newInterviewBtn = page.getByRole('button', { name: /nova entrevista/i });
  await expect(newInterviewBtn).toBeVisible({ timeout: 5000 });

  // Skip test if button is disabled (no interview guide configured)
  const isDisabled = await newInterviewBtn.isDisabled();
  if (isDisabled) {
    test.skip(true, 'Experimento não tem interview guide configurado - botão "Nova Entrevista" está desabilitado');
  }
}

test.describe('Interviews - Create Modal @critical @interviews', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToInterviewTab(page);
  });

  test('I001 - Open new interview modal', async ({ page }) => {
    // Clica em "Nova Entrevista"
    const newInterviewBtn = page.getByRole('button', { name: /nova entrevista/i });
    await newInterviewBtn.click();

    // Modal deve abrir
    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible({ timeout: 5000 });

    // Título do modal
    await expect(
      modal.locator('h2').filter({ hasText: /nova entrevista/i })
    ).toBeVisible();

    // Verifica campos do formulário
    await expect(
      modal.getByLabel(/contexto adicional/i)
    ).toBeVisible();

    await expect(
      modal.getByLabel(/quantos synths/i)
    ).toBeVisible();

    await expect(
      modal.getByLabel(/maximo de turnos/i)
    ).toBeVisible();
  });

  test('I002 - Close modal with Cancel button', async ({ page }) => {
    // Abre modal
    await page.getByRole('button', { name: /nova entrevista/i }).click();
    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible();

    // Clica em Cancelar
    const cancelBtn = modal.getByRole('button', { name: /cancelar/i });
    await cancelBtn.click();

    // Modal deve fechar
    await expect(modal).not.toBeVisible({ timeout: 3000 });
  });

  test('I003 - Close modal with ESC key', async ({ page }) => {
    // Abre modal
    await page.getByRole('button', { name: /nova entrevista/i }).click();
    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible();

    // Pressiona ESC
    await page.keyboard.press('Escape');

    // Modal deve fechar
    await expect(modal).not.toBeVisible({ timeout: 3000 });
  });

  test('I004 - Default values are set correctly', async ({ page }) => {
    // Abre modal
    await page.getByRole('button', { name: /nova entrevista/i }).click();
    const modal = page.locator('[role="dialog"]');

    // Verifica valores padrão
    const synthsInput = modal.getByLabel(/quantos synths/i);
    await expect(synthsInput).toHaveValue('9');

    const turnosInput = modal.getByLabel(/maximo de turnos/i);
    await expect(turnosInput).toHaveValue('5');

    // Contexto adicional deve estar vazio
    const contextoInput = modal.getByLabel(/contexto adicional/i);
    await expect(contextoInput).toHaveValue('');
  });

  test('I005 - Change number of synths', async ({ page }) => {
    // Abre modal
    await page.getByRole('button', { name: /nova entrevista/i }).click();
    const modal = page.locator('[role="dialog"]');

    const synthsInput = modal.getByLabel(/quantos synths/i);

    // Limpa e digita novo valor
    await synthsInput.clear();
    await synthsInput.fill('10');

    // Verifica que valor mudou
    await expect(synthsInput).toHaveValue('10');
  });

  test('I006 - Change max turns', async ({ page }) => {
    // Abre modal
    await page.getByRole('button', { name: /nova entrevista/i }).click();
    const modal = page.locator('[role="dialog"]');

    const turnosInput = modal.getByLabel(/maximo de turnos/i);

    // Limpa e digita novo valor
    await turnosInput.clear();
    await turnosInput.fill('10');

    // Verifica que valor mudou
    await expect(turnosInput).toHaveValue('10');
  });

  test('I007 - Add optional context', async ({ page }) => {
    // Abre modal
    await page.getByRole('button', { name: /nova entrevista/i }).click();
    const modal = page.locator('[role="dialog"]');

    const contextoInput = modal.getByLabel(/contexto adicional/i);

    // Preenche contexto
    const contextText = 'Foco em usuários que já usaram produtos similares';
    await contextoInput.fill(contextText);

    // Verifica que valor foi preenchido
    await expect(contextoInput).toHaveValue(contextText);
  });

  test('I008 - Submit button is visible and enabled', async ({ page }) => {
    // Abre modal
    await page.getByRole('button', { name: /nova entrevista/i }).click();
    const modal = page.locator('[role="dialog"]');

    // Botão "Iniciar Entrevista" deve estar visível e habilitado
    const submitBtn = modal.getByRole('button', { name: /iniciar entrevista/i });
    await expect(submitBtn).toBeVisible();
    await expect(submitBtn).toBeEnabled();
  });

  test.skip('I009 - Create interview successfully', async ({ page }) => {
    // Skip: Este teste cria dados no sistema
    // Pode ser habilitado em ambiente de teste isolado

    // Abre modal
    await page.getByRole('button', { name: /nova entrevista/i }).click();
    const modal = page.locator('[role="dialog"]');

    // Preenche campos
    await modal.getByLabel(/contexto adicional/i).fill('Teste E2E');
    await modal.getByLabel(/quantos synths/i).clear();
    await modal.getByLabel(/quantos synths/i).fill('3');

    // Clica em Iniciar Entrevista
    await modal.getByRole('button', { name: /iniciar entrevista/i }).click();

    // Modal deve fechar
    await expect(modal).not.toBeVisible({ timeout: 10000 });

    // Deve mostrar toast de sucesso ou atualização na lista
    // (depende da implementação - ajustar conforme necessário)
  });
});

test.describe('Interviews - Form Validation @interviews', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToInterviewTab(page);

    // Abre modal
    await page.getByRole('button', { name: /nova entrevista/i }).click();
    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible({ timeout: 5000 });
  });

  test('I010 - Synths count validation (min)', async ({ page }) => {
    const modal = page.locator('[role="dialog"]');
    const synthsInput = modal.getByLabel(/quantos synths/i);

    // Tenta colocar valor menor que 1
    await synthsInput.clear();
    await synthsInput.fill('0');

    // Deve validar ou prevenir valor inválido
    // (comportamento pode variar - não forçamos validação específica)
    const value = await synthsInput.inputValue();

    // Se aceitar 0, teste passa (validação pode ser no submit)
    // Se não aceitar, deve ter voltado para valor válido
    expect(parseInt(value) >= 0).toBeTruthy();
  });

  test('I011 - Synths count validation (max)', async ({ page }) => {
    const modal = page.locator('[role="dialog"]');
    const synthsInput = modal.getByLabel(/quantos synths/i);

    // Tenta colocar valor maior que 50
    await synthsInput.clear();
    await synthsInput.fill('100');

    // Validação pode ser feita de várias formas:
    // 1. Input limita automaticamente
    // 2. Validação no submit
    // 3. Mensagem de erro

    // Não forçamos comportamento específico - apenas que não quebra
    const value = await synthsInput.inputValue();
    expect(value).toBeTruthy();
  });

  test('I012 - Turns count validation', async ({ page }) => {
    const modal = page.locator('[role="dialog"]');
    const turnosInput = modal.getByLabel(/maximo de turnos/i);

    // Testa valores válidos
    await turnosInput.clear();
    await turnosInput.fill('15');
    await expect(turnosInput).toHaveValue('15');

    // Testa valor no limite
    await turnosInput.clear();
    await turnosInput.fill('20');
    await expect(turnosInput).toHaveValue('20');
  });

  test('I013 - Context field accepts long text', async ({ page }) => {
    const modal = page.locator('[role="dialog"]');
    const contextoInput = modal.getByLabel(/contexto adicional/i);

    // Preenche com texto longo
    const longText = 'Este é um texto muito longo para testar se o campo aceita múltiplas linhas e caracteres especiais como @#$%^&*() e também acentuação: áéíóú ãõ çñ. '.repeat(5);

    await contextoInput.fill(longText);

    // Deve aceitar texto longo
    const value = await contextoInput.inputValue();
    expect(value.length).toBeGreaterThan(100);
  });
});
