import { test, expect, type Page } from '@playwright/test';
import { summarizeCoverage } from '../src/lib/source-coverage.ts';
import { PUBLIC_PILOT_REFERENCE_TIME, PUBLIC_PILOT_STALE_TIME, publicNotes, publicParkSnapshots, publicParks, publicRules } from './pilot-clock.ts';
const coverageInput = { parks: publicParks, rules: publicRules, notes: publicNotes, snapshots: publicParkSnapshots };
async function assertLabels(page: Page, now: string) {
  const expected = summarizeCoverage(coverageInput, new Date(now));
  for (const row of expected.rows) {
    await expect(page.locator(`[data-entry-label="${row.code}"]`)).toHaveText(row.entryLabel);
    await expect(page.locator(`[data-alert-label="${row.code}"]`)).toHaveText(row.alertLabel);
  }
  return expected;
}
test('source coverage preserves stored guidance counts and each feed freshness', async ({ page }) => {
  await page.clock.install({ time: new Date(PUBLIC_PILOT_REFERENCE_TIME) });
  await page.goto('/');
  const expected = await assertLabels(page, PUBLIC_PILOT_REFERENCE_TIME);
  for (const metric of ['storedReviewParks', 'datedRuleParks', 'recentAlertParks'] as const) {
    await expect(page.locator(`[data-coverage-metric="${metric}"]`).first()).toHaveText(String(expected[metric]).padStart(2, '0'));
  }
  await page.clock.fastForward(8 * 24 * 60 * 60 * 1000);
  await assertLabels(page, PUBLIC_PILOT_STALE_TIME);
  await expect(page.locator('[data-coverage-metric="recentAlertParks"]').first()).toHaveText('00');
});
test('all three undated reviews remain unresolved for a future visit', async ({ page }) => {
  await page.clock.setFixedTime(new Date(PUBLIC_PILOT_REFERENCE_TIME));
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
test('directory labels retain independent review and feed ages while the page stays open', async ({ page }) => {
  await page.clock.install({ time: new Date(PUBLIC_PILOT_REFERENCE_TIME) });
  await page.goto('/parks/');
  await assertLabels(page, PUBLIC_PILOT_REFERENCE_TIME);
  await page.clock.fastForward(8 * 24 * 60 * 60 * 1000);
  await assertLabels(page, PUBLIC_PILOT_STALE_TIME);
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
