/**
 * Authentication setup for Playwright E2E tests.
 *
 * This setup script runs before all tests to establish authentication state.
 * It calls the /auth/test-login endpoint to get a test user session and
 * saves the authenticated state (including cookies) for reuse across tests.
 *
 * This eliminates the need for each test to handle authentication individually.
 */
import { test as setup, expect } from '@playwright/test';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const authFile = path.join(__dirname, '../../playwright/.auth/user.json');

setup('authenticate', async ({ page, request }) => {
  // Determine URLs based on environment
  // In Docker E2E: frontend=8091, backend=8001
  // In local dev: frontend=8080, backend=8000
  const testEnv = process.env.TEST_ENV || 'local';
  const backendUrl = testEnv === 'docker'
    ? 'http://localhost:8001'
    : 'http://localhost:8000';
  const frontendUrl = testEnv === 'docker'
    ? 'http://localhost:8091'
    : 'http://localhost:8080';

  console.log(`🔐 Auth setup: environment=${testEnv}, backend=${backendUrl}, frontend=${frontendUrl}`);

  // Step 1: Get auth token from backend using API request
  const loginResponse = await request.post(`${backendUrl}/auth/test-login`);
  if (!loginResponse.ok()) {
    throw new Error(`Login failed: ${loginResponse.status()}`);
  }

  const user = await loginResponse.json();
  console.log(`✅ Test login successful: ${user.email}`);

  // Extract auth_token from Set-Cookie header
  const setCookieHeader = loginResponse.headers()['set-cookie'];
  if (!setCookieHeader) {
    throw new Error('No Set-Cookie header in response');
  }

  const cookieMatch = setCookieHeader.match(/auth_token=([^;]+)/);
  if (!cookieMatch) {
    throw new Error('auth_token not found in Set-Cookie header');
  }

  const authTokenValue = cookieMatch[1];
  console.log(`🍪 Got auth token (length: ${authTokenValue.length})`);

  // Step 2: Route handler to inject cookie into all backend requests
  // This ensures the cookie is always sent, regardless of browser cookie policy
  await page.route(`${backendUrl}/**`, async (route, req) => {
    const headers = { ...req.headers(), cookie: `auth_token=${authTokenValue}` };
    await route.continue({ headers });
  });

  console.log(`🔧 Route handler installed for ${backendUrl}/**`);

  // Step 3: Also add cookie to browser context (for completeness)
  await page.context().addCookies([
    {
      name: 'auth_token',
      value: authTokenValue,
      domain: 'localhost',
      path: '/',
      httpOnly: true,
      secure: false,
      sameSite: 'Lax',
      expires: Math.floor(Date.now() / 1000) + 8 * 60 * 60,
    },
  ]);

  // Step 4: Navigate to frontend
  await page.goto(frontendUrl, { waitUntil: 'networkidle' });

  // Step 5: Verify authentication worked
  const isLoginPage = await page.locator('text=Sign in with Google').isVisible({ timeout: 5000 }).catch(() => false);

  if (isLoginPage) {
    throw new Error('Authentication failed - still on login page');
  }

  console.log(`✅ Authentication verified - main app loaded`);

  // Step 6: Save state (note: the route handler doesn't persist, so tests need it too)
  // We save the auth token in storageState for tests to use
  await page.context().storageState({ path: authFile });

  console.log(`✅ Authentication setup complete - state saved to ${authFile}`);
});
