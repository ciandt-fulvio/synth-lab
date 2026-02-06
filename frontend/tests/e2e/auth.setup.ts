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
  // - staging: Uses STAGING_BACKEND_URL and STAGING_FRONTEND_URL env vars
  // - docker: frontend=8091, backend=8001
  // - local: frontend=8080, backend=8000
  const testEnv = process.env.TEST_ENV || 'local';

  let backendUrl: string;
  let frontendUrl: string;

  if (testEnv === 'staging') {
    backendUrl = process.env.STAGING_BACKEND_URL || 'https://synth-lab-api-staging.up.railway.app';
    frontendUrl = process.env.STAGING_FRONTEND_URL || 'https://synth-lab-frontend-staging.up.railway.app';
  } else if (testEnv === 'production') {
    backendUrl = process.env.PRODUCTION_BACKEND_URL || 'https://synth-lab-api-production.up.railway.app';
    frontendUrl = process.env.PRODUCTION_FRONTEND_URL || 'https://synth-lab-frontend-production.up.railway.app';
  } else if (testEnv === 'docker') {
    backendUrl = 'http://localhost:8001';
    frontendUrl = 'http://localhost:8091';
  } else {
    backendUrl = 'http://localhost:8000';
    frontendUrl = 'http://localhost:8080';
  }

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
  // For staging, extract domain from URL and use secure cookies
  const isStaging = testEnv === 'staging';
  const cookieDomain = isStaging
    ? new URL(frontendUrl).hostname  // e.g., synth-lab-frontend-staging.up.railway.app
    : 'localhost';

  await page.context().addCookies([
    {
      name: 'auth_token',
      value: authTokenValue,
      domain: cookieDomain,
      path: '/',
      httpOnly: true,
      secure: isStaging,  // HTTPS in staging
      sameSite: isStaging ? 'None' : 'Lax',  // None required for cross-origin in staging
      expires: Math.floor(Date.now() / 1000) + 8 * 60 * 60,
    },
  ]);

  // Step 4: Navigate and verify (or skip for remote environments)
  // Remote environments (staging/production) have cross-origin issues with
  // browser cookie verification. The API token is valid (verified above),
  // so we skip browser-based verification and rely on the route handler
  // in fixtures.ts to inject the cookie for actual tests.
  const isRemoteEnv = testEnv === 'staging' || testEnv === 'production';

  if (isRemoteEnv) {
    console.log(`⏭️  Skipping browser auth verification for ${testEnv} (cross-origin)`);
    console.log(`   Token obtained via API - fixtures.ts route handler will inject cookie`);
  } else {
    await page.goto(frontendUrl, { waitUntil: 'networkidle' });

    // Verify authentication worked
    const isLoginPage = await page.locator('text=Sign in with Google').isVisible({ timeout: 5000 }).catch(() => false);

    if (isLoginPage) {
      throw new Error('Authentication failed - still on login page');
    }

    console.log(`✅ Authentication verified - main app loaded`);
  }

  // Save state (note: the route handler doesn't persist, so tests need it too)
  // We save the auth token in storageState for tests to use
  await page.context().storageState({ path: authFile });

  console.log(`✅ Authentication setup complete - state saved to ${authFile}`);
});
