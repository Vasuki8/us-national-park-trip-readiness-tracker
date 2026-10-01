import { test, expect, type Page } from '@playwright/test';
import { summarizeCoverage } from '../src/lib/source-coverage.ts';
import { PUBLIC_PILOT_REFERENCE_TIME, PUBLIC_PILOT_STALE_TIME, guidanceScenarioTime, publicNotes, publicParkSnapshots, publicParks, publicRules } from './pilot-clock.ts';
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
test('source coverage expires on page return without advancing timers or rewriting evidence', async ({ page }) => {
  const reviews = [...publicRules, ...publicNotes];
  const latest = reviews.filter((review) => review.review_status === 'reviewed')
    .sort((left, right) => Date.parse(right.reviewed_at) - Date.parse(left.reviewed_at))[0];
  const initialTime = guidanceScenarioTime(reviews.filter((review) => review.park_code === latest.park_code));
  const expiredTime = new Date(Date.parse(latest.reviewed_at) + 168 * 3_600_000 + 1).toISOString();
  await page.clock.setFixedTime(new Date(initialTime));
  await page.goto('/');
  const initial = await assertLabels(page, initialTime);
  expect(initial.rows.find((row) => row.code === latest.park_code)!.reviewWithinWindow).toBe(true);
  const payloads = await page.locator('[data-coverage]').evaluateAll((items) => items.map((element) => element.getAttribute('data-coverage')));
  const clocks = await page.locator('time').evaluateAll((items) => items.map((element) => element.getAttribute('datetime')));
  const stored = await page.locator('[data-coverage-metric="storedReviewParks"], [data-coverage-metric="datedRuleParks"]').allTextContents();
  await page.clock.setFixedTime(new Date(expiredTime));
  await page.evaluate(() => window.dispatchEvent(new PageTransitionEvent('pageshow', { persisted: true })));
  const returned = await assertLabels(page, expiredTime);
  await expect(page.locator(`[data-entry-label="${latest.park_code}"]`)).toHaveText('Source review needs refreshing');
  await expect(page.locator('[data-coverage-metric="recentAlertParks"]').first()).toHaveText(String(returned.recentAlertParks).padStart(2, '0'));
  expect(await page.locator('[data-coverage-metric="storedReviewParks"], [data-coverage-metric="datedRuleParks"]').allTextContents()).toEqual(stored);
  expect(await page.locator('[data-coverage]').evaluateAll((items) => items.map((element) => element.getAttribute('data-coverage')))).toEqual(payloads);
  expect(await page.locator('time').evaluateAll((items) => items.map((element) => element.getAttribute('datetime')))).toEqual(clocks);
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
