import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './tests', testMatch: 'pages.browser.spec.ts', workers: 1, retries: 0,
  reporter: 'list', use: { baseURL: 'http://127.0.0.1:4324', browserName: 'chromium' },
  webServer: { command: 'npm run preview:pages -- --host 127.0.0.1 --ignore-lock',
    url: 'http://127.0.0.1:4324/us-national-park-trip-readiness-tracker/', reuseExistingServer: false },
});
