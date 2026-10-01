import { test, expect } from '@playwright/test';
import { PUBLIC_PILOT_FRESH_TIME, publicParks, publicRules } from './pilot-clock.ts';
const base = 'http://127.0.0.1:4322/entry-review';
for (const state of ['changed', 'missing', 'failed', 'sticky']) {
  test(`pending ${state} source review blocks a conclusion and retains original evidence dates`, async ({ page }) => {
    await page.goto(`${base}/${state}/`);
    await expect(page.locator('[data-entry-review-notice]')).toBeVisible();
    await expect(page.locator('[data-effective-review-status]')).toHaveText('needs_review');
    await expect(page.locator('[data-review-decision]')).toHaveAttribute('data-state', 'review-required');
    await expect(page.locator('[data-approved-clock]')).toHaveText('2026-09-28T19:55:31Z');
    await expect(page.locator('[data-entry-review-notice]')).toContainText('not an approval date');
    await expect(page.locator('[data-entry-review-notice] a')).toHaveAttribute('href', 'https://www.nps.gov/yose/planyourvisit/reservations.htm');
    expect(await page.content()).not.toContain('SYNTHETIC_REVIEW_CANDIDATE');
    expect(await page.evaluate(() => (window as any).entryReviewInjected)).toBeUndefined();
  });
}
test('matching selected text does not show a new review or imply source monitoring', async ({ page }) => {
  await page.goto(`${base}/matching/`);
  await expect(page.locator('[data-entry-review-notice]')).toHaveCount(0);
  await expect(page.locator('[data-effective-review-status]')).toHaveText('reviewed');
  await expect(page.locator('[data-approved-clock]')).toHaveText('2026-09-28T19:55:31Z');
});
test('review warnings and official links work without JavaScript', async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage(); await page.goto(`${base}/changed/`);
  await expect(page.locator('[data-entry-review-notice]')).toBeVisible();
  await expect(page.locator('[data-entry-review-notice] a')).toBeVisible();
  await expect(page.locator('[data-review-decision]')).toHaveAttribute('data-state', 'review-required');
  await context.close();
});
test('review warning fits 360px and doubled text without hiding source links', async ({ page }) => {
  await page.setViewportSize({ width: 360, height: 800 }); await page.goto(`${base}/changed/`);
  await page.locator('html').evaluate((el) => { el.style.fontSize = '200%'; });
  await expect(page.locator('[data-entry-review-notice] a')).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});
test('production data remains approved and empty register does not expose synthetic review fixtures', async ({ page }) => {
  await page.clock.setFixedTime(new Date(PUBLIC_PILOT_FRESH_TIME));
  for (const park of publicParks) {
    await page.goto(`/parks/${park.slug}/`);
    await expect(page.locator('[data-entry-review-notice]')).toHaveCount(0);
    const rules = JSON.parse(await page.locator('#trip-context').getAttribute('data-rules') || '[]');
    expect(rules).toEqual(publicRules.filter((rule) => rule.park_code === park.code));
    for (const rule of rules) {
      expect(rule.review_status).toBe('reviewed');
      await expect(page.locator(`time[datetime="${rule.reviewed_at}"]`).first()).toBeVisible();
    }
    expect(await page.content()).not.toContain('SYNTHETIC_REVIEW_CANDIDATE');
  }
});
