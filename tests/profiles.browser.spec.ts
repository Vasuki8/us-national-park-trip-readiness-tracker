import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { publicParks } from './pilot-clock.ts';
import type { PublicProfiles } from '../scripts/validate-park-profiles.ts';

const profiles = (JSON.parse(readFileSync(new URL('../data/park-profiles.json', import.meta.url), 'utf8')) as PublicProfiles).profiles;
const initial = new Date(Math.max(...profiles.map(item => Date.parse(item.last_checked_at))) + 1000);

test('every park exposes source-backed overview and seasonal context without browser API requests', async ({ page }) => {
  await page.clock.setFixedTime(initial);
  const external: string[] = [];
  page.on('request', request => { if (new URL(request.url()).origin !== 'http://127.0.0.1:4321') external.push(request.url()); });
  for (const park of publicParks) {
    const snapshot = profiles.find(item => item.park_code === park.code)!;
    await page.goto(`/parks/${park.slug}/`);
    const overview = page.locator('#overview');
    const seasonal = page.locator('#when-to-visit');
    await expect(overview.getByRole('heading', { name: 'Overview', exact: true })).toBeVisible();
    if (snapshot.profile.description?.trim()) await expect(overview.locator('[data-profile-introduction]')).toHaveText(snapshot.profile.description);
    else await expect(overview).toContainText('The stored official profile has no introduction text.');
    await expect(seasonal.locator('[data-profile-seasonal]')).toHaveText(snapshot.profile.seasonal_weather!.text);
    await expect(seasonal).toContainText('Seasonal context, not a forecast for your travel dates.');
    for (const label of await page.locator('[data-profile-state]').all()) await expect(label).toHaveAttribute('data-profile-state', 'fresh');
    const categories = overview.locator('details[data-profile-categories]');
    await expect(categories).not.toHaveAttribute('open');
    await categories.locator('summary').focus();
    await page.keyboard.press('Enter');
    await expect(categories).toHaveAttribute('open', '');
    await expect(categories.locator('[data-profile-category]')).toHaveText(snapshot.profile.activity_categories!.map(item => item.name));
    await expect(categories).toContainText('Categories do not establish individual activities, seasonal availability or access.');
    for (const section of [overview, seasonal]) {
      await expect(section.locator('[data-profile-source]')).toHaveAttribute('href', snapshot.source_url);
      await expect(section.locator('[data-profile-success]')).toHaveAttribute('datetime', snapshot.last_successful_fetch_at);
    }
  }
  expect(external).toEqual([]);
});

test('profile expiry refreshes on minute, return, visibility and print while original evidence remains unchanged', async ({ page }) => {
  const snapshot = profiles[0];
  const boundary = Date.parse(snapshot.last_successful_fetch_at) + 168 * 3_600_000;
  await page.clock.install({ time: new Date(boundary - 1000) });
  await page.goto('/parks/yosemite/');
  const metadata = await page.locator('[data-profile-clock]').evaluateAll(elements => elements.map(element => element.getAttribute('data-profile-clock')));
  const clocks = await page.locator('[data-profile-success]').evaluateAll(elements => elements.map(element => ({ datetime: element.getAttribute('datetime'), text: element.textContent })));
  await expect(page.locator('[data-profile-state]').first()).toHaveAttribute('data-profile-state', 'fresh');
  await page.clock.fastForward(60_000);
  for (const label of await page.locator('[data-profile-state]').all()) await expect(label).toHaveAttribute('data-profile-state', 'stale');
  for (const event of ['pageshow', 'visibilitychange', 'beforeprint']) {
    await page.clock.setFixedTime(initial);
    await page.evaluate(event => {
      if (event === 'visibilitychange') document.dispatchEvent(new Event(event));
      else window.dispatchEvent(new Event(event));
    }, event);
    for (const label of await page.locator('[data-profile-state]').all()) await expect(label).toHaveAttribute('data-profile-state', 'fresh');
    await page.clock.setFixedTime(new Date(boundary + 1));
    await page.evaluate(event => {
      if (event === 'visibilitychange') document.dispatchEvent(new Event(event));
      else window.dispatchEvent(new Event(event));
    }, event);
    for (const label of await page.locator('[data-profile-state]').all()) await expect(label).toHaveAttribute('data-profile-state', 'stale');
  }
  expect(await page.locator('[data-profile-clock]').evaluateAll(elements => elements.map(element => element.getAttribute('data-profile-clock')))).toEqual(metadata);
  expect(await page.locator('[data-profile-success]').evaluateAll(elements => elements.map(element => ({ datetime: element.getAttribute('datetime'), text: element.textContent })))).toEqual(clocks);
  await page.emulateMedia({ media: 'print' });
  await expect(page.locator('#overview')).toBeVisible();
  await expect(page.locator('#when-to-visit')).toBeVisible();
});

test('without JavaScript the overview and seasonal sources retain original clocks and honest freshness', async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false, baseURL: 'http://127.0.0.1:4321' });
  try {
    const page = await context.newPage();
    for (const park of publicParks) {
      const snapshot = profiles.find(item => item.park_code === park.code)!;
      await page.goto(`/parks/${park.slug}/`);
      for (const id of ['overview', 'when-to-visit']) {
        const section = page.locator(`#${id}`);
        await expect(section).toBeVisible();
        await expect(section.locator('noscript')).toContainText('Freshness labels reflect the build without JavaScript.');
        await expect(section.locator('[data-profile-success]')).toHaveText(snapshot.last_successful_fetch_at);
        await expect(section.locator('[data-profile-source]')).toHaveAttribute('href', snapshot.source_url);
      }
      await page.locator('[data-profile-categories] summary').click();
      await expect(page.locator('[data-profile-category]:visible')).toHaveCount(snapshot.profile.activity_categories!.length);
    }
  } finally { await context.close(); }
});
