import { test, expect } from '@playwright/test';
import { describeAlerts } from '../src/lib/readiness.ts';
import { PUBLIC_PILOT_REFERENCE_TIME, PUBLIC_PILOT_STALE_TIME, guidanceScenarioTime, publicHistories, publicParkSnapshots, publicParks, publicRules } from './pilot-clock.ts';
test.beforeEach(async ({ page }) => { await page.clock.setFixedTime(new Date(PUBLIC_PILOT_REFERENCE_TIME)); });
test('keyboard search, state filtering and empty results', async ({ page }) => {
  const external: string[] = [];
  page.on('request', (request) => { if (!request.url().startsWith('http://127.0.0.1:4321/')) external.push(request.url()); });
  await page.goto('/parks/');
  await expect(page.locator('[data-park-card]:visible')).toHaveCount(5);
  await page.getByLabel('Search parks').fill('yellow');
  await expect(page.locator('[data-park-card]:visible')).toHaveCount(1);
  await page.getByLabel('Search parks').fill('nothing-matches');
  await expect(page.getByText('No parks match your search.')).toBeVisible();
  await page.getByLabel('Search parks').fill('');
  await page.getByLabel('Filter by state').selectOption('Colorado');
  await expect(page.locator('[data-park-card]:visible')).toHaveCount(1);
  await page.getByLabel('Filter by state').selectOption('');
  await page.screenshot({ path: 'test-results/pilot-directory-desktop.png', fullPage: true });
  expect(external).toEqual([]);
});
test('Yosemite date checks never reuse a year or stale review', async ({ page }) => {
  await page.clock.setFixedTime(new Date(guidanceScenarioTime(publicRules.filter((rule) => rule.park_code === 'yose'))));
  await page.goto('/parks/yosemite/');
  await page.getByLabel('Visit date').fill('2026-09-30');
  await page.getByRole('button', { name: 'Check entry guidance' }).click();
  await expect(page.locator('#decision-title')).toHaveText('No timed entry under this reviewed rule');
  await page.getByLabel('Visit date').fill('2027-06-01');
  await page.getByRole('button', { name: 'Check entry guidance' }).click();
  await expect(page.locator('#decision-title')).toHaveText('Entry requirements not verified for this date');
  await page.clock.setFixedTime(new Date(PUBLIC_PILOT_STALE_TIME));
  await page.getByLabel('Visit date').fill('2026-10-11');
  await page.getByRole('button', { name: 'Check entry guidance' }).click();
  await expect(page.locator('#decision-title')).toHaveText('Entry guidance needs a fresh review');
});
test('Rocky Mountain separates areas and exact time boundaries', async ({ page }) => {
  await page.clock.setFixedTime(new Date(guidanceScenarioTime(publicRules.filter((rule) => rule.park_code === 'romo' && rule.areas.includes('rest')))));
  await page.goto('/parks/rocky-mountain/');
  await page.getByLabel('Visit date').fill('2026-09-30');
  await page.getByRole('button', { name: 'Check entry guidance' }).click();
  await expect(page.locator('#decision-title')).toHaveText('Choose the area you plan to enter');
  await page.getByLabel('Planned area').selectOption('rest');
  await page.getByLabel('Arrival time').fill('08:00');
  await page.getByRole('button', { name: 'Check entry guidance' }).click();
  await expect(page.locator('#decision-title')).toHaveText('Outside this reviewed timed-entry window');
  await page.clock.setFixedTime(new Date(guidanceScenarioTime(publicRules.filter((rule) => rule.park_code === 'romo' && rule.areas.includes('bear-lake')))));
  await page.getByLabel('Planned area').selectOption('bear-lake');
  await page.getByRole('button', { name: 'Check entry guidance' }).click();
  await expect(page.locator('#decision-title')).toHaveText('Review your timed-entry reservation');
  await page.getByLabel('Arrival time').fill('18:00');
  await page.getByRole('button', { name: 'Check entry guidance' }).click();
  await expect(page.locator('#decision-title')).toHaveText('Verify the exact time boundary');
});
test('checklist is self-reported and resets when trip details change', async ({ page }) => {
  await page.goto('/parks/yosemite/');
  await page.locator('[data-check]').first().check();
  await expect(page.locator('#checklist-progress')).toContainText('1 of 5');
  await page.getByLabel('Visit date').fill('2026-09-30');
  await expect(page.locator('#checklist-progress')).toContainText('0 of 5');
  for (const box of await page.locator('[data-check]').all()) await box.check();
  await expect(page.locator('#checklist-progress')).toContainText('Your checklist is complete');
  await page.getByRole('button', { name: 'Reset checklist' }).click();
  await expect(page.locator('[data-check]:checked')).toHaveCount(0);
  expect(await page.evaluate(() => localStorage.length)).toBe(0);
});
test('all pilot pages fit a 360px viewport without horizontal scrolling', async ({ page }) => {
  await page.setViewportSize({ width: 360, height: 800 });
  for (const path of ['/', '/parks/', '/parks/yosemite/', '/parks/rocky-mountain/', '/parks/yellowstone/', '/parks/zion/', '/parks/grand-canyon/', '/sources/']) {
    await page.goto(path);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  }
  await page.goto('/parks/yosemite/');
  await page.screenshot({ path: 'test-results/pilot-yosemite-mobile.png', fullPage: true });
});
test('official links and evidence remain usable with JavaScript disabled', async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();
  await page.goto('http://127.0.0.1:4321/parks/yosemite/');
  const snapshot = publicParkSnapshots.find((item) => item.park_code === 'yose')!;
  const history = publicHistories.find((item) => item.park_code === 'yose')!;
  expect(JSON.parse((await page.locator('#alert-status').getAttribute('data-snapshot'))!)).toEqual(snapshot);
  const retained = page.locator('section.panel').filter({ has: page.getByRole('heading', { name: 'Notices retained from the checked feed', exact: true }) });
  await expect(retained).toHaveCount(snapshot.records.length ? 1 : 0);
  if (snapshot.records.length) {
    await expect(retained.getByRole('heading', { name: snapshot.records[0].title, exact: true })).toBeVisible();
    await expect(retained.locator('article')).toHaveCount(snapshot.records.length);
  }
  await expect(page.locator('#alert-status')).toContainText(snapshot.last_successful_fetch_at ?? 'Never');
  await expect(page.locator('[data-history-observation]')).toHaveCount(history.observations.length);
  await expect(page.getByText('Baseline recorded', { exact: true })).toHaveCount(history.observations.filter((observation) => observation.comparison === 'baseline').length);
  await expect(page.getByRole('link', { name: 'Read the official source', exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Check entry guidance' })).toBeDisabled();
  await expect(page.locator('[data-check]').first()).toBeDisabled();
  await expect(page.getByRole('button', { name: 'Reset checklist' })).toBeDisabled();
  await context.close();
});

test('paired feed evidence retains notices and its independently aged limitations', async ({ page }) => {
  for (const park of publicParks) {
    const snapshot = publicParkSnapshots.find((item) => item.park_code === park.code)!;
    await page.goto(`/parks/${park.slug}/`);
    expect(JSON.parse((await page.locator('#alert-status').getAttribute('data-snapshot'))!)).toEqual(snapshot);
    await expect(page.locator('#alert-status')).toContainText('Coverage incomplete');
    await expect(page.locator('#alert-status')).toContainText(snapshot.last_successful_fetch_at ?? 'Never');
    await expect(page.locator('#alert-status a')).toHaveAttribute('href', park.conditions_url);
    const expected = describeAlerts(snapshot, new Date(PUBLIC_PILOT_REFERENCE_TIME));
    await expect(page.locator('#notice-title')).toHaveText(expected.title);
    await expect(page.locator('#notice-detail')).toHaveText(expected.detail);
    const retained = page.locator('section.panel').filter({ has: page.getByRole('heading', { name: 'Notices retained from the checked feed', exact: true }) });
    if (snapshot.records.length) {
      await expect(retained.locator('article')).toHaveCount(snapshot.records.length);
      for (const record of snapshot.records) {
        const notice = retained.locator('article').filter({ has: page.getByRole('heading', { name: record.title, exact: true }) });
        await expect(notice).toContainText(record.description);
        if (record.url) await expect(notice.getByRole('link')).toHaveAttribute('href', record.url);
        else {
          await expect(notice).toContainText('NPS did not supply a direct link for this alert.');
          await expect(notice.locator('a')).toHaveCount(0);
        }
      }
    } else {
      await expect(retained).toHaveCount(0);
    }
    await page.clock.setFixedTime(new Date(PUBLIC_PILOT_STALE_TIME));
    await page.evaluate(() => document.dispatchEvent(new Event('visibilitychange')));
    const aged = describeAlerts(snapshot, new Date(PUBLIC_PILOT_STALE_TIME));
    await expect(page.locator('#notice-title')).toHaveText(aged.title);
    await expect(page.locator('#notice-detail')).toHaveText(aged.detail);
    expect(JSON.parse((await page.locator('#alert-status').getAttribute('data-snapshot'))!)).toEqual(snapshot);
    await page.clock.setFixedTime(new Date(PUBLIC_PILOT_REFERENCE_TIME));
  }
});

test('entry live-region text changes only when the displayed decision changes', async ({ page }) => {
  const rule = publicRules.find((item) => item.park_code === 'yose')!;
  await page.clock.install({ time: new Date(guidanceScenarioTime([rule])) });
  await page.goto('/parks/yosemite/');
  await page.getByLabel('Visit date').fill(rule.effective_from);
  await page.getByRole('button', { name: 'Check entry guidance' }).click();
  const decision = page.locator('#entry-decision');
  await expect(decision).toHaveAttribute('role', 'status');
  await expect(decision).toHaveAttribute('aria-live', 'polite');
  await expect(decision).toHaveAttribute('data-state', 'not-required-under-rule');
  await decision.evaluate((element) => {
    element.setAttribute('data-text-changes', '0');
    new MutationObserver((records) => {
      element.setAttribute('data-text-changes', String(Number(element.getAttribute('data-text-changes')) + records.length));
    }).observe(element, { childList: true, characterData: true, subtree: true });
  });
  await page.clock.fastForward(60_000);
  await page.evaluate(() => document.dispatchEvent(new Event('visibilitychange')));
  await expect(decision).toHaveAttribute('data-text-changes', '0');
  const expiry = Date.parse(rule.reviewed_at) + 168 * 3_600_000;
  await page.clock.setFixedTime(new Date(expiry));
  await page.evaluate(() => document.dispatchEvent(new Event('visibilitychange')));
  await expect(decision).toHaveAttribute('data-state', 'not-required-under-rule');
  await expect(decision).toHaveAttribute('data-text-changes', '0');
  await page.clock.setFixedTime(new Date(expiry + 1));
  await page.evaluate(() => document.dispatchEvent(new Event('visibilitychange')));
  await expect(decision).toHaveAttribute('data-state', 'stale');
  await expect(page.locator('#decision-title')).toHaveText('Entry guidance needs a fresh review');
  await expect.poll(async () => Number(await decision.getAttribute('data-text-changes'))).toBeGreaterThan(0);
  const changed = await decision.getAttribute('data-text-changes');
  await page.clock.fastForward(60_000);
  await page.evaluate(() => document.dispatchEvent(new Event('visibilitychange')));
  await expect(decision).toHaveAttribute('data-text-changes', changed!);
});
