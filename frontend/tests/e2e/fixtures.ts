/**
 * Playwright fixtures for E2E tests with authentication.
 *
 * Provides a custom `page` fixture that automatically installs
 * a route handler to inject the auth cookie into backend requests.
 * This is needed because browsers don't send cookies with cross-origin
 * requests from localhost:8091 to localhost:8001.
 */
import { test as base, Page, BrowserContext } from '@playwright/test';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Path to the auth state file created by auth.setup.ts
const authFile = path.join(__dirname, '../../playwright/.auth/user.json');

// Get backend URL based on environment
function getBackendUrl(): string {
  const testEnv = process.env.TEST_ENV || 'local';
  return testEnv === 'docker' ? 'http://localhost:8001' : 'http://localhost:8000';
}

// Extract auth token from stored state
function getAuthToken(): string | null {
  try {
    if (!fs.existsSync(authFile)) {
      console.log('[fixtures] Auth file not found, skipping route handler');
      return null;
    }

    const state = JSON.parse(fs.readFileSync(authFile, 'utf-8'));
    const authCookie = state.cookies?.find((c: { name: string }) => c.name === 'auth_token');

    if (!authCookie) {
      console.log('[fixtures] auth_token cookie not found in state');
      return null;
    }

    return authCookie.value;
  } catch (error) {
    console.log('[fixtures] Error reading auth state:', error);
    return null;
  }
}

// Extend the base test to add auth route handler
export const test = base.extend<{ authPage: Page }>({
  // Override the page fixture to add auth route handler
  page: async ({ page }, use) => {
    const authToken = getAuthToken();
    const backendUrl = getBackendUrl();

    if (authToken) {
      // Install route handler to inject auth cookie into all backend requests
      await page.route(`${backendUrl}/**`, async (route, req) => {
        const headers = { ...req.headers(), cookie: `auth_token=${authToken}` };
        await route.continue({ headers });
      });
    }

    await use(page);
  },
});

export { expect } from '@playwright/test';
