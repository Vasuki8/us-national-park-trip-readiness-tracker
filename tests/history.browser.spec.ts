import { test, expect } from '@playwright/test';
const fixtureBase = 'http://127.0.0.1:4322';
test('production changes page and all parks disclose missing history without fixture text', async ({ page }) => {
  await page.goto('/changes/');
  await expect(page.locator('[data-history]')).toHaveCount(5);
  await expect(page.getByText('History not collected', { exact: true })).toHaveCount(5);
  await expect(page.locator('[data-history-observation]')).toHaveCount(0);
  for (const slug of ['yosemite', 'rocky-mountain', 'yellowstone', 'zion', 'grand-canyon']) {
    await page.goto(`/parks/${slug}/`);
    await expect(page.locator('[data-history]')).toHaveCount(1);
    await expect(page.getByText('History not collected', { exact: true })).toBeVisible();
    expect(await page.content()).not.toContain('historyInjected');
  }
});
test('synthetic timeline renders baseline and source-linked before-after changes without executing markup', async ({ page }) => {
  await page.clock.install({ time: new Date('2026-09-28T13:00:00Z') });
  await page.goto(`${fixtureBase}/mixed/`);
  await expect(page.locator('[data-history-observation]')).toHaveCount(2);
  await expect(page.getByText('Baseline recorded', { exact: true })).toBeVisible();
  await expect(page.getByText('Notice added to the checked feed', { exact: true })).toBeVisible();
  await expect(page.getByText('Notice changed in the checked feed', { exact: true })).toBeVisible();
  await expect(page.getByText('Notice no longer present in the checked feed', { exact: true })).toBeVisible();
  const detail = page.locator('[data-history] details').first(); await detail.locator('summary').click();
  await expect(detail).toContainText('Café — synthetic text. <script>window.historyInjected=1</script>');
  expect(await page.evaluate(() => (window as any).historyInjected)).toBeUndefined();
  await expect(detail.getByRole('link', { name: 'More information link supplied by NPS' }).first()).toHaveAttribute('href', 'https://www.nps.gov/yose/test.htm');
  await expect(page.locator('[data-history]')).toContainText('not a confirmed reopening');
});
test('failed check retains earlier changes and does not become a fresh successful check', async ({ page }) => {
  await page.clock.install({ time: new Date('2026-09-28T14:01:00Z') });
  await page.goto(`${fixtureBase}/failed/`);
  await expect(page.locator('[data-history-status]')).toHaveText('The latest check was not successful');
  await expect(page.locator('[data-history-observation]').first()).toContainText('Check failed');
  await expect(page.getByText('Notice changed in the checked feed', { exact: true })).toBeVisible();
  await expect(page.locator('[data-history]')).toContainText('2026-09-28T12:00:00Z');
});
test('history freshness ages on an open page without rewriting evidence clocks', async ({ page }) => {
  await page.clock.install({ time: new Date('2026-09-28T13:00:00Z') });
  await page.goto(`${fixtureBase}/mixed/`);
  await expect(page.locator('[data-history-status]')).toContainText('Recent feed check');
  const times = await page.locator('[data-history] time').evaluateAll((items) => items.map((el) => el.getAttribute('datetime')));
  await page.clock.fastForward(3 * 3_600_000 + 60_000);
  await expect(page.locator('[data-history-status]')).toHaveText('History needs a fresh check');
  expect(await page.locator('[data-history] time').evaluateAll((items) => items.map((el) => el.getAttribute('datetime')))).toEqual(times);
});
test('omitted history is disclosed rather than presented as zero changes', async ({ page }) => {
  await page.goto(`${fixtureBase}/truncated/`);
  await expect(page.locator('[data-history]')).toContainText('2 older recorded checks not shown');
  await expect(page.locator('[data-history]')).toContainText('3 recorded notice changes not shown');
  await expect(page.locator('[data-history-observation]')).toHaveCount(1);
});
test('synthetic history evidence works without JavaScript', async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage(); await page.goto(`${fixtureBase}/mixed/`);
  await expect(page.locator('[data-history-observation]')).toHaveCount(2);
  const detail = page.locator('[data-history] details').first(); await detail.locator('summary').click();
  await expect(detail.getByRole('link', { name: 'More information link supplied by NPS' }).first()).toBeVisible();
  // Playwright deliberately skips NOSCRIPT when aggregating ancestor text.
  // Check the actual fallback paragraph so both rendered visibility and copy are proved.
  const fallback = page.locator('[data-history] noscript p');
  await expect(fallback).toBeVisible();
  await expect(fallback).toContainText('Without JavaScript');
  await context.close();
});
test('populated histories and evidence hashes fit a 360px viewport', async ({ page }) => {
  await page.setViewportSize({ width: 360, height: 800 });
  for (const scenario of ['mixed', 'failed', 'truncated', 'empty']) {
    await page.goto(`${fixtureBase}/${scenario}/`);
    await expect(page.locator('[data-history]')).toHaveCount(1);
    for (const detail of await page.locator('[data-history] summary').all()) await detail.click();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  }
});

test('production assets contain no synthetic history fixtures or private archive fields', async () => {
  const { readdirSync, readFileSync, statSync } = await import('node:fs');
  const { join } = await import('node:path');
  const walk = (folder: string): string[] => readdirSync(folder).flatMap((name) => {
    const path = join(folder, name); return statSync(path).isDirectory() ? walk(path) : [path];
  });
  const files = walk('dist').filter((path) => /\.(html|js|json)$/.test(path));
  expect(files.length).toBeGreaterThan(14);
  for (const path of files) {
    const text = readFileSync(path, 'utf8');
    for (const forbidden of ['historyInjected', 'SYNTHETIC TEST DATA', 'pending_receipt', 'private_path', 'record_refs']) {
      expect(text, `${path} contains test/private content`).not.toContain(forbidden);
    }
  }
});
