import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for E2E tests.
 *
 * Local tests (default):
 *   npm run test:e2e
 *
 * Staging tests:
 *   npm run test:e2e:staging
 *   TEST_ENV=staging npm run test:e2e
 *
 * Production tests:
 *   TEST_ENV=production npm run test:e2e
 *
 * Custom URL:
 *   BASE_URL=https://my-custom-url.com npm run test:e2e
 */

// Environment URLs
const ENVIRONMENTS = {
  local: process.env.VITE_PORT ? `http://localhost:${process.env.VITE_PORT}` : 'http://localhost:8080',
  staging: 'https://synth-lab-frontend-staging.up.railway.app',
  production: 'https://synth-lab-frontend-production.up.railway.app',
} as const;

// Determine which environment to use
const testEnv = (process.env.TEST_ENV || 'local') as keyof typeof ENVIRONMENTS;
const baseURL = process.env.BASE_URL || ENVIRONMENTS[testEnv] || ENVIRONMENTS.local;
const isLocal = testEnv === 'local' && !process.env.BASE_URL;

console.log(`🎭 Playwright running against: ${baseURL} (environment: ${testEnv})`);

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',

  use: {
    baseURL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  // Only start local dev server when testing locally
  ...(isLocal && {
    webServer: {
      command: 'npm run dev:test',
      url: ENVIRONMENTS.local,
      reuseExistingServer: !process.env.CI,
      timeout: 120000,
    },
  }),
});
