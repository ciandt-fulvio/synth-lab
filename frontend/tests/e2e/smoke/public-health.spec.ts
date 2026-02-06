/**
 * Public Smoke Tests - No Authentication Required
 *
 * These tests validate that services are up and responsive without
 * requiring login. Used for production smoke tests where we don't
 * want a test-login backdoor.
 *
 * Run: make test-smoke-production
 */
import { test, expect } from '@playwright/test';

const testEnv = process.env.TEST_ENV || 'local';
const backendUrl = testEnv === 'production'
  ? (process.env.PRODUCTION_BACKEND_URL || 'https://synth-lab-api-production.up.railway.app')
  : testEnv === 'staging'
    ? (process.env.STAGING_BACKEND_URL || 'https://synth-lab-api-staging.up.railway.app')
    : testEnv === 'docker' ? 'http://localhost:8001' : 'http://localhost:8000';

test.describe('Public Smoke Tests - No Auth Required @smoke', () => {
  test('PUB001 - Backend health check returns healthy', async ({ request }) => {
    const response = await request.get(`${backendUrl}/health`);
    expect(response.ok()).toBeTruthy();

    const body = await response.json();
    expect(body.status).toBe('healthy');
    expect(body.service).toBe('synth-lab-api');

    console.log(`✅ Backend healthy - version: ${body.version}, env: ${body.environment}`);
  });

  test('PUB002 - Frontend loads and returns HTML', async ({ page }) => {
    const response = await page.goto('/');
    expect(response?.ok()).toBeTruthy();

    // Page should have a title
    const title = await page.title();
    expect(title).toBeTruthy();
    console.log(`✅ Frontend loaded - title: "${title}"`);
  });

  test('PUB003 - Frontend shows login page (not a crash)', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');

    // In production without auth, we expect either:
    // 1. Login page (Sign in with Google)
    // 2. Main app (if somehow authenticated)
    // Both are valid - we just confirm it's not a crash/error page
    const hasLoginButton = await page.locator('text=/sign in|google|login/i').first().isVisible({ timeout: 5000 }).catch(() => false);
    const hasAppContent = await page.locator('header').isVisible({ timeout: 2000 }).catch(() => false);

    expect(hasLoginButton || hasAppContent).toBeTruthy();
    console.log(`✅ Frontend renders correctly (login: ${hasLoginButton}, app: ${hasAppContent})`);
  });

  test('PUB004 - No server errors (5xx)', async ({ request }) => {
    // Check backend root
    const rootResponse = await request.get(`${backendUrl}/`);
    expect(rootResponse.status()).toBeLessThan(500);

    // Check docs endpoint
    const docsResponse = await request.get(`${backendUrl}/docs`);
    expect(docsResponse.status()).toBeLessThan(500);

    console.log(`✅ No 5xx errors on public endpoints`);
  });

  test('PUB005 - Backend responds within acceptable time', async ({ request }) => {
    const start = Date.now();
    await request.get(`${backendUrl}/health`);
    const elapsed = Date.now() - start;

    expect(elapsed).toBeLessThan(3000);
    console.log(`✅ Backend responded in ${elapsed}ms`);
  });

  test('PUB006 - Frontend loads within acceptable time', async ({ page }) => {
    const start = Date.now();
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');
    const elapsed = Date.now() - start;

    expect(elapsed).toBeLessThan(5000);
    console.log(`✅ Frontend loaded in ${elapsed}ms`);
  });
});
