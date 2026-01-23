import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for E2E tests.
 *
 * Local tests (default):
 *   npm run test:e2e
 *
 * Docker tests (isolated environment):
 *   TEST_ENV=docker npm run test:e2e
 *   npm run test:e2e:docker
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
  docker: 'http://localhost:8091',
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
  // Add retries for flaky tests (parallel execution can cause race conditions)
  retries: process.env.CI ? 2 : 1,
  // Use 4 workers in CI for faster execution
  // Tests with shared state should use: test.describe.configure({ mode: 'serial' })
  workers: process.env.CI ? 4 : 6,
  reporter: 'html',

  use: {
    baseURL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  projects: [
    // Setup project - runs first to authenticate
    {
      name: 'setup',
      testMatch: /.*\.setup\.ts/,
    },

    // Main test project - depends on setup for authentication
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        // Use authenticated state from setup
        storageState: './playwright/.auth/user.json',
      },
      dependencies: ['setup'],
    },
  ],

  // Only start local dev server when testing locally (not for docker or remote envs)
  ...(isLocal && {
    webServer: {
      command: 'npm run dev:test',
      url: ENVIRONMENTS.local,
      reuseExistingServer: !process.env.CI,
      timeout: 120000,
    },
  }),
});
