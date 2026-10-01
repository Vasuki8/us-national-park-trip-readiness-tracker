import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { PUBLIC_PILOT_FRESH_TIME, publicParkSnapshots } from './pilot-clock.ts';
const resources = JSON.parse(readFileSync(new URL('../data/planning-resources.json', import.meta.url), 'utf8')).resources;
const parks = [['yose', 'yosemite'], ['romo', 'rocky-mountain'], ['yell', 'yellowstone'], ['zion', 'zion'], ['grca', 'grand-canyon']];
test.beforeEach(async ({ page }) => { await page.clock.setFixedTime(new Date(PUBLIC_PILOT_FRESH_TIME)); });
test('all five parks expose seven separate source-linked planning checks without claiming conditions coverage', async ({ page }) => {
  for (const [code, slug] of parks) {
    await page.goto(`/parks/${slug}/`);
    const panel = page.locator('[data-planning-resources]');
    await expect(panel).toHaveCount(1);
    await expect(panel.getByText('Official link only', { exact: true })).toHaveCount(7);
    await expect(panel).toContainText('not monitored by this tracker');
    await expect(panel).toContainText('not a conditions check');
    for (const resource of resources.filter((item: any) => item.park_code === code)) {
      const card = panel.locator(`[data-planning-category="${resource.category}"]`);
      await expect(card.getByRole('link')).toHaveAttribute('href', resource.url);
      await expect(card).toContainText(resource.check_prompt);
      await expect(card.locator('time')).toHaveAttribute('datetime', resource.link_reviewed_at);
    }
    const snapshot = JSON.parse((await page.locator('#alert-status').getAttribute('data-snapshot'))!);
    expect(snapshot).toEqual(publicParkSnapshots.find((item) => item.park_code === code));
    expect(snapshot.collection_status).toBe('success');
    await expect(page.getByText('Baseline recorded', { exact: true })).toBeVisible();
    await expect(page.locator('[data-history-status]')).toHaveText('Recent feed check; coverage remains limited');
    await expect(page.locator('#alert-status')).toContainText(snapshot.last_successful_fetch_at);
  }
});
test('checklist jumps to official checks without marking any task reviewed', async ({ page }) => {
  await page.goto('/parks/yosemite/');
  await page.getByRole('link', { name: 'Open the official planning checks' }).click();
  await expect(page).toHaveURL(/#official-checks$/);
  await expect(page.locator('[data-planning-resources]')).toBeVisible();
  for (const checkbox of await page.locator('[data-check]').all()) await expect(checkbox).not.toBeChecked();
  await expect(page.locator('#checklist-progress')).toHaveText('0 of 5 items reviewed by you');
});
test('official planning links and review scope remain usable without JavaScript on every pilot', async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();
  for (const [, slug] of parks) {
    await page.goto(`/parks/${slug}/`);
    const panel = page.locator('[data-planning-resources]');
    await expect(panel.getByRole('link')).toHaveCount(7);
    await expect(panel.getByRole('link').first()).toBeVisible();
    await expect(panel).toContainText('not a conditions check');
  }
  await context.close();
});
test('planning cards fit mobile and retain their links with doubled base text size', async ({ page }) => {
  await page.setViewportSize({ width: 360, height: 800 });
  for (const [, slug] of parks) {
    await page.goto(`/parks/${slug}/`);
    const panel = page.locator('[data-planning-resources]');
    await expect(panel).toHaveCount(1);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.addStyleTag({ content: 'html { font-size: 200% !important; }' });
    // Scoped text-resize check; not a claim of a complete browser-zoom audit.
    expect(await panel.evaluate(el => el.scrollWidth <= el.clientWidth)).toBe(true);
    for (const link of await panel.getByRole('link').all()) await expect(link).toBeVisible();
  }
});
