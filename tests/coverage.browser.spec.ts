import { test, expect } from '@playwright/test';
import { PUBLIC_PILOT_FRESH_TIME } from './pilot-clock.ts';
test('source coverage distinguishes five reviewed parks from two dated-rule parks', async ({ page }) => {
  await page.clock.install({ time: new Date(PUBLIC_PILOT_FRESH_TIME) });
  await page.goto('/');
  await expect(page.locator('[data-coverage-metric="storedReviewParks"]').first()).toHaveText('05');
  await expect(page.locator('[data-coverage-metric="datedRuleParks"]').first()).toHaveText('02');
  await expect(page.locator('[data-coverage-metric="recentAlertParks"]').first()).toHaveText('05');
  await expect(page.locator('[data-alert-label]').filter({ hasText: 'Alert feed checked' })).toHaveCount(5);
  await expect(page.locator('[data-entry-label]').filter({ hasText: 'Undated source review' })).toHaveCount(3);
  await page.clock.fastForward(8 * 24 * 60 * 60 * 1000);
  await expect(page.locator('[data-coverage-metric="recentAlertParks"]').first()).toHaveText('00');
  await expect(page.locator('[data-alert-label]').filter({ hasText: 'Alert check needs refreshing' })).toHaveCount(5);
});
test('all three undated reviews remain unresolved for a future visit', async ({ page }) => {
  await page.clock.setFixedTime(new Date(PUBLIC_PILOT_FRESH_TIME));
  for (const slug of ['yellowstone', 'zion', 'grand-canyon']) {
    await page.goto(`/parks/${slug}/`);
    await expect(page.locator('[data-undated-guidance]')).toBeVisible();
    await expect(page.locator('[data-undated-guidance]')).toContainText('Dates not published');
    await expect(page.locator('[data-undated-guidance] a')).toHaveAttribute('href', /^https:\/\/www\.nps\.gov\//);
    await page.getByLabel('Visit date').fill('2027-06-01');
    await page.getByRole('button', { name: 'Check entry guidance' }).click();
    await expect(page.locator('#entry-decision')).toHaveAttribute('data-state', 'not-verified');
  }
});
test('directory review labels expire while the existing page stays open', async ({ page }) => {
  await page.clock.install({ time: new Date(PUBLIC_PILOT_FRESH_TIME) });
  await page.goto('/parks/');
  await expect(page.locator('[data-entry-label]').filter({ hasText: 'needs refreshing' })).toHaveCount(0);
  await expect(page.locator('[data-alert-label]').filter({ hasText: 'Alert feed checked' })).toHaveCount(5);
  await page.clock.fastForward(8 * 24 * 60 * 60 * 1000);
  await expect(page.locator('[data-entry-label]').filter({ hasText: 'needs refreshing' })).toHaveCount(5);
  await expect(page.locator('[data-alert-label]').filter({ hasText: 'Alert check needs refreshing' })).toHaveCount(5);
});
test('undated supporting evidence and limitations work without JavaScript', async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();
  await page.goto('http://127.0.0.1:4321/parks/grand-canyon/');
  await expect(page.locator('[data-undated-guidance]')).toContainText('not a determination for your travel dates');
  await expect(page.locator('[data-undated-guidance] a')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Check entry guidance' })).toBeDisabled();
  await context.close();
});
