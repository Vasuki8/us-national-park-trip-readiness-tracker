import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './tests', testMatch: ['browser.spec.ts', 'coverage.browser.spec.ts', 'history.browser.spec.ts'], workers: 1, retries: 0,
  reporter: 'list', use: { baseURL: 'http://127.0.0.1:4321', browserName: 'chromium' },
  webServer: [
    { command: 'npm run preview -- --host 127.0.0.1', url: 'http://127.0.0.1:4321', reuseExistingServer: !process.env.CI },
    { command: 'npx --no-install astro build --root tests/history-site && npx --no-install astro preview --root tests/history-site --host 127.0.0.1 --port 4322', url: 'http://127.0.0.1:4322/mixed/', reuseExistingServer: false, timeout: 120_000 },
  ],
});
