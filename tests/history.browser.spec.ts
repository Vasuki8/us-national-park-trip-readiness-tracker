import { test, expect, type Page } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { historyDigest } from '../scripts/validate-history.ts';
import { changeLabels, describeHistory } from '../src/lib/history.ts';
import { PUBLIC_PILOT_REFERENCE_TIME, publicHistories, publicParkSnapshots, publicParks } from './pilot-clock.ts';
const fixtureBase = 'http://127.0.0.1:4322';
const publicObservations = publicHistories.flatMap((history) => history.observations);
const expectedClocks = (snapshot: (typeof publicParkSnapshots)[number], history: (typeof publicHistories)[number]) => [
  ...(snapshot.last_successful_fetch_at ? [snapshot.last_successful_fetch_at] : []),
  ...history.observations.map((observation) => observation.checked_at),
];
const retainedFixtures: Record<'mixed' | 'failed', {
  snapshot: (typeof publicParkSnapshots)[number]; history: (typeof publicHistories)[number];
}> = JSON.parse(readFileSync(new URL('./fixtures/history-preview.json', import.meta.url), 'utf8')).cases;
const retainedAnchor = (parkCode: string, id: string) => `alert-${parkCode}-${id}`;
const historyClocks = (page: Page) => page.locator('[data-history] time').evaluateAll(elements => elements.map(element => ({
  datetime: element.getAttribute('datetime'), text: element.textContent,
})));
test('production changes page and all parks retain paired public history without fixture text', async ({ page }) => {
  await page.clock.setFixedTime(new Date(PUBLIC_PILOT_REFERENCE_TIME));
  await page.goto('/changes/');
  await expect(page.locator('[data-history]')).toHaveCount(5);
  await expect(page.getByText('Baseline recorded', { exact: true })).toHaveCount(publicObservations.filter((item) => item.comparison === 'baseline').length);
  await expect(page.locator('[data-history-observation]')).toHaveCount(publicObservations.length);
  for (const park of publicParks) {
    const snapshot = publicParkSnapshots.find((item) => item.park_code === park.code)!;
    const history = publicHistories.find((item) => item.park_code === park.code)!;
    expect(history.snapshot_hash).toBe(historyDigest(snapshot));
    const expectedMetadata = {
      collection_status: snapshot.collection_status, last_checked_at: snapshot.last_checked_at,
      last_successful_fetch_at: snapshot.last_successful_fetch_at,
    };
    const overview = page.locator(`#history-${park.code}`);
    expect(JSON.parse((await overview.getAttribute('data-history-metadata'))!)).toEqual(expectedMetadata);
    expect(await overview.locator('time').evaluateAll((items) => items.map((el) => el.getAttribute('datetime')))).toEqual(expectedClocks(snapshot, history));
    await expect(overview.locator('[data-history-status]')).toHaveText(describeHistory(snapshot, new Date(PUBLIC_PILOT_REFERENCE_TIME)).title);
  }
  for (const park of publicParks) {
    const snapshot = publicParkSnapshots.find((item) => item.park_code === park.code)!;
    const history = publicHistories.find((item) => item.park_code === park.code)!;
    await page.goto(`/parks/${park.slug}/`);
    await expect(page.locator('[data-history]')).toHaveCount(1);
    const baselines = history.observations.filter((item) => item.comparison === 'baseline').length;
    await expect(page.getByText('Baseline recorded', { exact: true })).toHaveCount(baselines);
    await expect(page.locator('[data-history-observation]')).toHaveCount(history.observations.length);
    expect(await page.locator('[data-history] time').evaluateAll((items) => items.map((el) => el.getAttribute('datetime')))).toEqual(expectedClocks(snapshot, history));
    if (baselines) await expect(page.locator('[data-history]')).toContainText('not evidence that its restrictions began at this time');
    else await expect(page.locator('[data-history]')).not.toContainText('not evidence that its restrictions began at this time');
    await expect(page.locator('[data-history-status]')).toHaveText(describeHistory(snapshot, new Date(PUBLIC_PILOT_REFERENCE_TIME)).title);
    expect(await page.content()).not.toContain('historyInjected');
  }
});

test('separate uncollected fixture discloses missing history without an all-clear', async ({ page }) => {
  await page.goto(`${fixtureBase}/empty/`);
  await expect(page.locator('[data-history-status]')).toHaveText('History not collected');
  await expect(page.locator('[data-history-observation]')).toHaveCount(0);
  await expect(page.locator('[data-history-detail]')).toContainText('An empty timeline does not mean that nothing has changed');
  const metadata = JSON.parse((await page.locator('[data-history]').getAttribute('data-history-metadata'))!);
  expect(metadata).toEqual({ collection_status: 'never_checked', last_checked_at: null, last_successful_fetch_at: null });
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
test('history expires on page return without advancing timers or rewriting evidence', async ({ page }) => {
  await page.clock.setFixedTime(new Date('2026-09-28T13:00:00Z'));
  await page.goto(`${fixtureBase}/mixed/`);
  await expect(page.locator('[data-history-status]')).toContainText('Recent feed check');
  const metadata = await page.locator('[data-history]').getAttribute('data-history-metadata');
  const times = await page.locator('[data-history] time').evaluateAll((items) => items.map((element) => element.getAttribute('datetime')));
  await page.clock.setFixedTime(new Date('2026-09-28T16:00:00Z'));
  await page.evaluate(() => window.dispatchEvent(new PageTransitionEvent('pageshow', { persisted: true })));
  await expect(page.locator('[data-history-status]')).toContainText('Recent feed check');
  await page.clock.setFixedTime(new Date('2026-09-28T16:00:00.001Z'));
  await page.evaluate(() => window.dispatchEvent(new PageTransitionEvent('pageshow', { persisted: true })));
  await expect(page.locator('[data-history-status]')).toHaveText('History needs a fresh check');
  expect(await page.locator('[data-history]').getAttribute('data-history-metadata')).toBe(metadata);
  expect(await page.locator('[data-history] time').evaluateAll((items) => items.map((element) => element.getAttribute('datetime')))).toEqual(times);
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

test('synthetic history links identify current retained IDs while archived wording and removed-notice uncertainty persist', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.goto(`${fixtureBase}/mixed/`);
  await expect(page.locator('[data-history-notice-link],[data-history-park-link]')).toHaveCount(0);
  await expect(page.locator('[data-history]')).not.toContainText('A unique retained notice could not be identified for this comparison.');
  for (const state of ['mixed', 'failed'] as const) {
    const view = retainedFixtures[state];
    await page.clock.setFixedTime(new Date(Date.parse(view.snapshot.last_checked_at!) + 1_000));
    await page.goto(`${fixtureBase}/retained/${state}/`);
    await expect(page.locator('h1')).toHaveText('Synthetic test data — not park conditions');
    const snapshotText = await page.locator('[data-fixture-snapshot]').getAttribute('data-fixture-snapshot');
    expect(JSON.parse(snapshotText!)).toEqual(view.snapshot);
    const metadata = await page.locator('[data-history]').getAttribute('data-history-metadata');
    const clocks = await historyClocks(page);
    const changes = view.history.observations.flatMap(observation => observation.changes);
    await expect(page.locator('.history-change')).toHaveCount(changes.length);
    for (const [index, change] of changes.entries()) {
      const article = page.locator('.history-change').nth(index);
      await expect(article.locator('h4')).toHaveText(changeLabels[change.kind]);
      await expect(article.locator('.change-title')).toHaveText((change.after ?? change.before)!.title);
      const matches = view.snapshot.records.filter(record => record.id === change.record_id);
      const link = article.locator('[data-history-notice-link]');
      if (matches.length === 1) {
        await expect(link).toHaveText('View retained notice with this ID');
        await expect(link).toHaveAttribute('href', `#${encodeURIComponent(retainedAnchor(view.snapshot.park_code, change.record_id))}`);
        await expect(article).toContainText('Retained wording may differ from this comparison. This is stored evidence, not live conditions.');
        await expect(page.locator(`[id="${retainedAnchor(view.snapshot.park_code, change.record_id)}"]`)).toContainText(matches[0].description);
      } else {
        await expect(link).toHaveCount(0);
        await expect(article).toContainText('A unique retained notice could not be identified for this comparison. This does not establish reopening.');
        await expect(article).toContainText('A notice disappearing is not a confirmed reopening.');
      }
      const details = article.locator('details');
      await details.locator('summary').focus();
      await page.keyboard.press('Enter');
      await expect(details).toHaveAttribute('open', '');
      const sides = [change.before, change.after].filter(side => side !== null);
      await expect(details.locator('blockquote')).toHaveText(sides.map(side => side.description || 'The checked feed supplied no description.'));
      await expect(details.locator('code')).toHaveText(sides.map(side => side.content_hash));
    }
    if (state === 'failed') {
      await expect(page.locator('[data-history-status]')).toHaveText('The latest check was not successful');
      await expect(page.locator('[data-history]')).toContainText(view.snapshot.last_successful_fetch_at!);
      await expect(page.locator('[data-history-observation]').first()).toContainText('No notice comparison was made.');
    }
    await page.setViewportSize({ width: 360, height: 800 });
    await page.locator('html').evaluate(element => { element.style.fontSize = '200%'; });
    const overflow = await page.locator('[data-retained-notice] > p').evaluateAll(elements => elements
      .filter(element => element.scrollWidth > element.clientWidth + 1)
      .map(element => ({ id: element.parentElement?.id, text: element.textContent, width: element.clientWidth, scroll: element.scrollWidth })));
    expect(overflow, 'retained source text wraps at doubled size without changing its wording').toEqual([]);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
    for (const link of await page.locator('[data-history-notice-link]').all()) {
      await expect(link).toBeVisible();
      expect(await link.evaluate(element => element.scrollWidth <= element.clientWidth + 1)).toBe(true);
    }
    await expect(page.locator('[data-fixture-snapshot]')).toHaveAttribute('data-fixture-snapshot', snapshotText!);
    await expect(page.locator('[data-history]')).toHaveAttribute('data-history-metadata', metadata!);
    expect(await historyClocks(page)).toEqual(clocks);
    expect(await page.evaluate(() => (window as any).historyInjected)).toBeUndefined();
  }
});

test('history keyboard links reveal an excluded notice on a new and repeated fragment without changing archived evidence', async ({ page }) => {
  const view = retainedFixtures.mixed;
  const changes = view.history.observations.flatMap(observation => observation.changes);
  const index = changes.findIndex(change => change.kind === 'edited');
  const change = changes[index];
  const record = view.snapshot.records.find(record => record.id === change.record_id)!;
  const other = view.snapshot.records.find(candidate => candidate.id !== record.id)!;
  const fragment = retainedAnchor(view.snapshot.park_code, record.id);
  const route = `${fixtureBase}/retained/mixed/`;
  await page.clock.setFixedTime(new Date(Date.parse(view.snapshot.last_checked_at!) + 1_000));
  await page.emulateMedia({ reducedMotion: 'reduce' });
  const external: string[] = [];
  page.on('request', request => { if (new URL(request.url()).origin !== fixtureBase) external.push(request.url()); });
  await page.goto(route);
  const history = page.locator('[data-history]');
  const metadata = await history.getAttribute('data-history-metadata');
  const clocks = await historyClocks(page);
  const archived = await history.locator('.history-evidence').allTextContents();
  const link = page.locator('.history-change').nth(index).locator('[data-history-notice-link]');
  const article = page.locator(`[id="${fragment}"]`);
  await expect(article).toHaveCount(1);
  await expect(article).toHaveAttribute('tabindex', '-1');
  const search = page.getByLabel('Search retained notices', { exact: true });
  const category = page.getByLabel('Notice category', { exact: true });
  for (const activation of ['new fragment', 'same fragment']) {
    await search.fill(other.title);
    await category.selectOption(other.category);
    await expect(article, activation).toBeHidden();
    await link.focus();
    await page.keyboard.press('Enter');
    await expect(page).toHaveURL(`${route}#${encodeURIComponent(fragment)}`);
    await expect(search).toHaveValue('');
    await expect(category).toHaveValue('');
    await expect(page.locator('[data-retained-notice]:visible')).toHaveCount(view.snapshot.records.length);
    await expect(article, activation).toBeVisible();
    await expect(article, activation).toBeFocused();
    await expect(article, activation).toBeInViewport();
    await page.keyboard.press('Tab');
    await expect(article.locator('a[href]').first()).toBeFocused();
    await expect(article.locator('a:not([data-correction-link])')).toHaveAttribute('href', record.url!);
    await expect(history).toHaveAttribute('data-history-metadata', metadata!);
    expect(await historyClocks(page)).toEqual(clocks);
    expect(await history.locator('.history-evidence').allTextContents()).toEqual(archived);
  }
  expect(external).toEqual([]);
});

test('without JavaScript synthetic added and edited history links focus retained source articles even after a failed check', async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false, reducedMotion: 'reduce' });
  try {
    const page = await context.newPage();
    for (const state of ['mixed', 'failed'] as const) {
      const view = retainedFixtures[state];
      const route = `${fixtureBase}/retained/${state}/`;
      await page.goto(route);
      await expect(page.locator('[data-retained-notice]:visible')).toHaveCount(view.snapshot.records.length);
      await expect(page.locator('[data-notice-controls]:visible')).toHaveCount(0);
      const clocks = await historyClocks(page);
      const changes = view.history.observations.flatMap(observation => observation.changes);
      for (const [index, change] of changes.entries()) {
        const record = view.snapshot.records.find(record => record.id === change.record_id);
        const comparison = page.locator('.history-change').nth(index);
        if (!record) {
          await expect(comparison.locator('[data-history-notice-link]')).toHaveCount(0);
          await expect(comparison).toContainText('This does not establish reopening.');
          continue;
        }
        const fragment = retainedAnchor(view.snapshot.park_code, record.id);
        const link = comparison.locator('[data-history-notice-link]');
        await expect(link).toHaveAttribute('href', `#${encodeURIComponent(fragment)}`);
        await link.focus();
        await page.keyboard.press('Enter');
        await expect(page).toHaveURL(`${route}#${encodeURIComponent(fragment)}`);
        const article = page.locator(`[id="${fragment}"]`);
        await expect(article).toBeFocused();
        await expect(article).toBeInViewport();
        await expect(article).toContainText(record.description);
        await page.keyboard.press('Tab');
        await expect(article.locator('a[href]').first()).toBeFocused();
        await expect(article.locator('a:not([data-correction-link])')).toHaveAttribute('href', record.url!);
      }
      if (state === 'failed') await expect(page.locator('[data-history-status]')).toHaveText('The latest check was not successful');
      expect(await historyClocks(page)).toEqual(clocks);
    }
  } finally {
    await context.close();
  }
});
