import { test, expect } from '@playwright/test';
import { PUBLIC_PILOT_FRESH_TIME, PUBLIC_PILOT_STALE_TIME, publicParkSnapshots, publicParks } from './pilot-clock.ts';
test.beforeEach(async ({ page }) => { await page.clock.setFixedTime(new Date(PUBLIC_PILOT_FRESH_TIME)); });
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
  await page.goto('/parks/rocky-mountain/');
  await page.getByLabel('Visit date').fill('2026-09-30');
  await page.getByRole('button', { name: 'Check entry guidance' }).click();
  await expect(page.locator('#decision-title')).toHaveText('Choose the area you plan to enter');
  await page.getByLabel('Planned area').selectOption('rest');
  await page.getByLabel('Arrival time').fill('08:00');
  await page.getByRole('button', { name: 'Check entry guidance' }).click();
  await expect(page.locator('#decision-title')).toHaveText('Outside this reviewed timed-entry window');
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
  expect(JSON.parse((await page.locator('#alert-status').getAttribute('data-snapshot'))!)).toEqual(snapshot);
  await expect(page.getByRole('heading', { name: 'Notices retained from the checked feed' })).toBeVisible();
  await expect(page.getByRole('heading', { name: snapshot.records[0].title, exact: true })).toBeVisible();
  await expect(page.locator('#alert-status')).toContainText(snapshot.last_successful_fetch_at!);
  await expect(page.locator('[data-history-observation]')).toHaveCount(1);
  await expect(page.getByText('Baseline recorded', { exact: true })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Read the official source', exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Check entry guidance' })).toBeDisabled();
  await expect(page.locator('[data-check]').first()).toBeDisabled();
  await expect(page.getByRole('button', { name: 'Reset checklist' })).toBeDisabled();
  await context.close();
});

test('successful checked feeds retain notices and never give a park-wide all-clear', async ({ page }) => {
  for (const park of publicParks) {
    const snapshot = publicParkSnapshots.find((item) => item.park_code === park.code)!;
    await page.goto(`/parks/${park.slug}/`);
    expect(JSON.parse((await page.locator('#alert-status').getAttribute('data-snapshot'))!)).toEqual(snapshot);
    await expect(page.locator('#alert-status')).toContainText('Coverage incomplete');
    await expect(page.locator('#alert-status')).toContainText(snapshot.last_successful_fetch_at!);
    await expect(page.locator('#alert-status a')).toHaveAttribute('href', park.conditions_url);
    const retained = page.locator('section.panel').filter({ has: page.getByRole('heading', { name: 'Notices retained from the checked feed', exact: true }) });
    if (snapshot.records.length) {
      await expect(page.locator('#notice-title')).toHaveText('Official notices need your review');
      await expect(page.locator('#notice-detail')).toContainText('not a park-wide status');
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
      await expect(page.locator('#notice-title')).toHaveText('No alerts returned by the checked feed');
      await expect(page.locator('#notice-detail')).toContainText('This is not an all-clear.');
    }
    await page.clock.setFixedTime(new Date(PUBLIC_PILOT_STALE_TIME));
    await page.evaluate(() => document.dispatchEvent(new Event('visibilitychange')));
    await expect(page.locator('#notice-title')).toHaveText('The condition snapshot needs a fresh check');
    expect(JSON.parse((await page.locator('#alert-status').getAttribute('data-snapshot'))!)).toEqual(snapshot);
    await page.clock.setFixedTime(new Date(PUBLIC_PILOT_FRESH_TIME));
  }
});
