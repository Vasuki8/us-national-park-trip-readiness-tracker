import { test, expect, type Locator, type Page } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { publicParks } from './pilot-clock.ts';
import type { CatalogActivityInventory, PublicActivityCatalog } from '../scripts/validate-park-activities.ts';

const catalog = JSON.parse(readFileSync(new URL('../data/park-activities.json', import.meta.url), 'utf8')) as PublicActivityCatalog;
const inventories = catalog.inventories;
// Activity evidence has its own age. The older pilot reference excludes these clocks.
const reference = new Date(Math.max(...inventories.map(item => Date.parse(item.last_checked_at))) + 1000);
const origin = 'http://127.0.0.1:4321';

function inventoryFor(code: string) {
  const matches = inventories.filter(item => item.park_code === code);
  expect(matches).toHaveLength(1);
  return matches[0];
}

function minimalClock(snapshot: CatalogActivityInventory) {
  return {
    collection_status: snapshot.collection_status,
    last_checked_at: snapshot.last_checked_at,
    last_successful_fetch_at: snapshot.last_successful_fetch_at,
  };
}

async function monitorRequests(page: Page) {
  const requests: string[] = [], external: string[] = [];
  page.on('request', request => {
    requests.push(request.url());
    if (new URL(request.url()).origin !== origin) external.push(request.url());
  });
  // An unexpected visitor-side source call must fail without reaching a provider.
  await page.route('**/*', route => new URL(route.request().url()).origin === origin ? route.continue() : route.abort());
  return { requests, external };
}

async function expectCounts(section: Locator, snapshot: CatalogActivityInventory) {
  const published = snapshot.records.length;
  const source = snapshot.source_records.length;
  const withheld = snapshot.source_records.filter(record => record.publication_status === 'withheld').length;
  const counts = section.locator('[data-activity-counts]');
  await expect(counts).toHaveCount(1);
  for (const [count, label] of [[published, 'published'], [source, 'source'], [withheld, 'withheld']] as const) {
    await expect(counts).toContainText(new RegExp(`\\b${count} ${label} listings?\\b`));
  }
  expect(published + withheld).toBe(source);
}

async function renderedListings(section: Locator) {
  return section.locator('[data-activity-record]').evaluateAll(elements => elements.map(element => ({
    title: element.querySelector('[data-activity-link]')!.textContent,
    url: element.querySelector('[data-activity-link]')!.getAttribute('href'),
    categories: [...element.querySelectorAll('[data-activity-category]')].map(category => category.textContent),
  })));
}

function expectedListings(snapshot: CatalogActivityInventory) {
  return snapshot.records.map(record => ({
    title: record.title,
    url: record.url,
    categories: record.category_scope === 'published' ? (record.activity_categories ?? []).map(category => category.name) : [],
  }));
}

async function evidence(page: Page) {
  return {
    activityClock: await page.locator('[data-activity-clock]').getAttribute('data-activity-clock'),
    alert: await page.locator('#alert-status').getAttribute('data-snapshot'),
    history: await page.locator('[data-history]').getAttribute('data-history-metadata'),
    clocks: await page.locator('time:not(#print-time)').evaluateAll(elements => elements.map(element => ({
      datetime: element.getAttribute('datetime'), text: element.textContent,
    }))),
    listings: await renderedListings(page.locator('#things-to-do')),
  };
}

async function dispatch(page: Page, event: 'pageshow' | 'visibilitychange' | 'beforeprint') {
  await page.evaluate(event => {
    if (event === 'visibilitychange') document.dispatchEvent(new Event(event));
    else if (event === 'pageshow') window.dispatchEvent(new PageTransitionEvent(event, { persisted: true }));
    else window.dispatchEvent(new Event(event));
  }, event);
}

test('all five parks expose only the approved ordered activity titles, links, categories and original clocks', async ({ page }) => {
  expect(catalog.schema_version).toBe(2);
  await page.clock.setFixedTime(reference);
  const monitored = await monitorRequests(page);
  for (const park of publicParks) {
    const snapshot = inventoryFor(park.code);
    await page.goto(`/parks/${park.slug}/`);
    const section = page.locator('#things-to-do');
    await expect(section).toHaveAttribute('tabindex', '-1');
    await expect(section).toHaveAttribute('aria-labelledby', 'things-to-do-title');
    await expect(section.getByRole('heading', { name: 'Things to Do', exact: true })).toBeVisible();
    await expectCounts(section, snapshot);
    await expect(section).toContainText('Availability is not verified.');
    await expect(section).toContainText('relationship to this park is unconfirmed.');
    await expect(section).toContainText('Responsible agency, difficulty and permit requirements are unknown.');
    await expect(section).toContainText('withholding does not mean source removal');
    const clock = section.locator('[data-activity-clock]');
    expect(JSON.parse((await clock.getAttribute('data-activity-clock'))!)).toEqual(minimalClock(snapshot));
    await expect(section.locator('[data-activity-state]')).toHaveAttribute('data-activity-state', 'fresh');
    await expect(section.locator('[data-activity-state]')).toHaveText('Within the seven-day activity window');
    await expect(section.locator('[data-activity-detail]')).toContainText('does not confirm availability, access or permit requirements.');
    await expect(section.locator('[data-activity-success]')).toHaveAttribute('datetime', snapshot.last_successful_fetch_at);
    await expect(section.locator('[data-activity-success]')).toHaveText(snapshot.last_successful_fetch_at);
    const inventory = section.locator('details[data-activity-inventory]');
    await expect(inventory).not.toHaveAttribute('open');
    await expect(section.locator('[data-activity-record]:visible')).toHaveCount(0);
    await inventory.locator('summary').focus();
    await page.keyboard.press('Enter');
    await expect(inventory).toHaveAttribute('open', '');
    await expect(section.locator('[data-activity-record]:visible')).toHaveCount(snapshot.records.length);
    expect(await renderedListings(section)).toEqual(expectedListings(snapshot));
    for (const link of await section.locator('[data-activity-link]').all()) {
      await expect(link).toHaveAttribute('href', /^https:\/\/www\.nps\.gov\//);
    }
    const sourceDetails = clock.locator('details');
    await sourceDetails.locator('summary').focus();
    await page.keyboard.press('Space');
    await expect(sourceDetails).toHaveAttribute('open', '');
    await expect(sourceDetails).toContainText('Source issue/update time: Not supplied.');
    await expect(sourceDetails.locator('time')).toHaveAttribute('datetime', snapshot.last_checked_at);
    await expect(sourceDetails.locator('time')).toHaveText(snapshot.last_checked_at);
    await expect(sourceDetails.getByRole('link')).toHaveAttribute('href', snapshot.source_url);
  }
  expect(monitored.external).toEqual([]);
});

test('activity microsecond expiry refreshes on every lifecycle event while evidence and visitor choices remain intact', async ({ page }) => {
  const snapshot = inventoryFor('yose');
  const fraction = snapshot.last_successful_fetch_at.match(/\.(\d+)Z$/)![1];
  expect(fraction.length).toBeGreaterThan(3);
  expect(Number(fraction.slice(3))).toBeGreaterThan(0);
  const boundary = Date.parse(snapshot.last_successful_fetch_at) + 168 * 3_600_000;
  // The original .709637 source clock is still fresh at .709 and stale at .710.
  const fresh = new Date(boundary), stale = new Date(boundary + 1);
  await page.clock.install({ time: new Date(boundary - 60_000) });
  await page.clock.pauseAt(fresh);
  const monitored = await monitorRequests(page);
  await page.goto('/parks/yosemite/');
  // Flush the initial page-return reconciliation before recording visitor choices.
  await page.clock.runFor(0);
  const state = page.locator('[data-activity-state]');
  await expect(state).toHaveAttribute('data-activity-state', 'fresh');
  await page.getByLabel('Visit date', { exact: true }).fill('2026-09-30');
  await page.getByLabel('Arrival time').fill('08:00');
  await page.getByLabel('Planned area', { exact: true }).selectOption('general');
  await page.locator('#special-case').check();
  await page.getByRole('button', { name: 'Check entry guidance', exact: true }).click();
  await page.locator('[data-check]').first().check();
  await page.locator('details[data-activity-inventory] summary').click();
  const search = page.getByLabel('Search retained notices', { exact: true });
  const category = page.getByLabel('Notice category', { exact: true });
  await search.fill('nonmatching activity research');
  const categoryValue = await category.locator('option').nth(1).getAttribute('value');
  await category.selectOption(categoryValue!);
  const original = await evidence(page);
  const decision = await page.locator('#entry-decision').innerText();
  const progress = await page.locator('#checklist-progress').innerText();
  const loadedRequests = monitored.requests.length;
  const storage = await page.evaluate(() => ({ local: { ...localStorage }, session: { ...sessionStorage } }));
  await page.clock.fastForward(60_000);
  await expect(state).toHaveAttribute('data-activity-state', 'stale');
  await expect(state).toHaveText('Activity catalog needs a fresh check');
  await expect(page.locator('[data-activity-detail]')).toContainText('Stored activity listings may have changed.');
  for (const event of ['pageshow', 'visibilitychange', 'beforeprint'] as const) {
    await page.clock.setFixedTime(fresh);
    await dispatch(page, event);
    if (event === 'pageshow') await page.clock.runFor(0);
    await expect(state).toHaveAttribute('data-activity-state', 'fresh');
    await page.clock.setFixedTime(stale);
    await dispatch(page, event);
    if (event === 'pageshow') await page.clock.runFor(0);
    await expect(state).toHaveAttribute('data-activity-state', 'stale');
  }
  await page.clock.setFixedTime(fresh);
  await dispatch(page, 'pageshow');
  await page.clock.runFor(0);
  await expect(state).toHaveAttribute('data-activity-state', 'fresh');
  await page.clock.setFixedTime(stale);
  await page.evaluate(() => {
    Object.defineProperty(document, 'visibilityState', { configurable: true, value: 'hidden' });
    Object.defineProperty(document, 'hidden', { configurable: true, value: true });
    document.dispatchEvent(new Event('visibilitychange'));
  });
  await expect(state).toHaveAttribute('data-activity-state', 'fresh');
  await page.evaluate(() => {
    Object.defineProperty(document, 'visibilityState', { configurable: true, value: 'visible' });
    Object.defineProperty(document, 'hidden', { configurable: true, value: false });
    document.dispatchEvent(new Event('visibilitychange'));
  });
  await expect(state).toHaveAttribute('data-activity-state', 'stale');
  expect(await evidence(page)).toEqual(original);
  await expect(page.locator('#trip-date')).toHaveValue('2026-09-30');
  await expect(page.locator('#trip-time')).toHaveValue('08:00');
  await expect(page.locator('#trip-area')).toHaveValue('general');
  await expect(page.locator('#special-case')).toBeChecked();
  await expect(page.locator('[data-check]:checked')).toHaveCount(1);
  await expect(page.locator('#entry-decision')).toHaveText(decision, { useInnerText: true });
  await expect(page.locator('#checklist-progress')).toHaveText(progress);
  await expect(search).toHaveValue('nonmatching activity research');
  await expect(category).toHaveValue(categoryValue!);
  await expect(page.locator('[data-retained-notice]:visible')).toHaveCount(0);
  await expect(page.locator('details[data-activity-inventory]')).toHaveAttribute('open', '');
  expect(await page.evaluate(() => ({ local: { ...localStorage }, session: { ...sessionStorage } }))).toEqual(storage);
  expect(monitored.requests).toHaveLength(loadedRequests);
  expect(monitored.external).toEqual([]);
});

test('unchanged activity labels are not rewritten by minute, page-return, visibility or print refreshes', async ({ page }) => {
  await page.clock.install({ time: reference });
  await page.goto('/parks/yellowstone/');
  const clock = page.locator('[data-activity-clock]');
  await expect(clock.locator('[data-activity-state]')).toHaveAttribute('data-activity-state', 'fresh');
  await clock.evaluate(element => {
    document.documentElement.dataset.activityWrites = '0';
    new MutationObserver(records => {
      document.documentElement.dataset.activityWrites = String(Number(document.documentElement.dataset.activityWrites) + records.length);
    }).observe(element, { childList: true, characterData: true, subtree: true, attributes: true, attributeFilter: ['data-activity-state'] });
  });
  await page.clock.fastForward(60_000);
  for (const event of ['pageshow', 'visibilitychange', 'beforeprint'] as const) await dispatch(page, event);
  await page.evaluate(() => Promise.resolve());
  await expect(page.locator('html')).toHaveAttribute('data-activity-writes', '0');
  const snapshot = inventoryFor('yell');
  await page.clock.setFixedTime(new Date(Date.parse(snapshot.last_successful_fetch_at) + 168 * 3_600_000 + 1));
  await dispatch(page, 'pageshow');
  await expect(clock.locator('[data-activity-state]')).toHaveAttribute('data-activity-state', 'stale');
  expect(Number(await page.locator('html').getAttribute('data-activity-writes'))).toBeGreaterThan(0);
  await page.locator('html').evaluate(element => { (element as HTMLElement).dataset.activityWrites = '0'; });
  await page.clock.fastForward(60_000);
  for (const event of ['pageshow', 'visibilitychange', 'beforeprint'] as const) await dispatch(page, event);
  await page.evaluate(() => Promise.resolve());
  await expect(page.locator('html')).toHaveAttribute('data-activity-writes', '0');
});

test('without JavaScript every activity inventory has native keyboard browsing, original clocks and a freshness disclosure', async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false, baseURL: origin, reducedMotion: 'reduce' });
  try {
    const page = await context.newPage();
    const monitored = await monitorRequests(page);
    for (const park of publicParks) {
      const snapshot = inventoryFor(park.code);
      await page.goto(`/parks/${park.slug}/`);
      const section = page.locator('#things-to-do');
      await expectCounts(section, snapshot);
      const fallback = section.locator('noscript p');
      await expect(fallback).toBeVisible();
      await expect(fallback).toContainText('Freshness labels reflect the build without JavaScript.');
      await expect(section.locator('[data-activity-success]')).toHaveAttribute('datetime', snapshot.last_successful_fetch_at);
      await expect(section.locator('[data-activity-success]')).toHaveText(snapshot.last_successful_fetch_at);
      const inventory = section.locator('details[data-activity-inventory]');
      await expect(inventory).not.toHaveAttribute('open');
      await inventory.locator('summary').focus();
      await page.keyboard.press('Enter');
      await expect(inventory).toHaveAttribute('open', '');
      await page.keyboard.press('Tab');
      await expect(inventory.locator('[data-activity-link]').first()).toBeFocused();
      expect(await renderedListings(section)).toEqual(expectedListings(snapshot));
      await expect(inventory.locator('[data-activity-record]:visible')).toHaveCount(snapshot.records.length);
      await inventory.locator('summary').focus();
      await page.keyboard.press('Space');
      await expect(inventory).not.toHaveAttribute('open');
      await expect(inventory.locator('[data-activity-record]:visible')).toHaveCount(0);
    }
    expect(monitored.external).toEqual([]);
  } finally { await context.close(); }
});

test('opened activity inventories reflow at 320px and at 360px with 200% text without clipping long titles or clocks', async ({ page }) => {
  await page.clock.setFixedTime(reference);
  await page.emulateMedia({ reducedMotion: 'reduce' });
  for (const park of publicParks) {
    await page.goto(`/parks/${park.slug}/`);
    const section = page.locator('#things-to-do');
    await section.locator('details').evaluateAll(elements => elements.forEach(element => { (element as HTMLDetailsElement).open = true; }));
    for (const [width, large] of [[320, false], [360, true]] as const) {
      await page.setViewportSize({ width, height: 900 });
      await page.locator('html').evaluate((element, large) => { element.style.fontSize = large ? '200%' : ''; }, large);
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), `${park.slug}: document reflow at ${width}`).toBe(true);
      const overflow = await section.evaluate(element => {
        const problems: string[] = [], walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT);
        while (walker.nextNode()) {
          const node = walker.currentNode, parent = node.parentElement!;
          if (!node.textContent?.trim() || parent.closest('script,style,noscript,[aria-hidden="true"]')) continue;
          if (getComputedStyle(parent).visibility === 'hidden') continue;
          const range = document.createRange(); range.selectNodeContents(node);
          if ([...range.getClientRects()].some(rect => rect.width > 0 && rect.height > 0 && (rect.left < -1 || rect.right > innerWidth + 1))) problems.push(`${parent.tagName}: painted text outside viewport`);
        }
        for (const child of element.querySelectorAll<HTMLElement>('summary,[data-activity-record],[data-activity-clock]')) {
          if (child.clientWidth && child.scrollWidth > child.clientWidth + 1) problems.push(`${child.tagName}: clipped content`);
        }
        return problems;
      });
      expect(overflow, `${park.slug}: ${width}px, ${large ? '200%' : '100%'} text`).toEqual([]);
      await expect(section.locator('[data-activity-link]:visible')).toHaveCount(inventoryFor(park.code).records.length);
      expect(await renderedListings(section)).toEqual(expectedListings(inventoryFor(park.code)));
    }
  }
});

test('printing preserves closed and open activity inventories and includes original clocks, disclosures and HTTPS destinations', async ({ page }) => {
  await page.clock.setFixedTime(reference);
  for (const park of publicParks) {
    const snapshot = inventoryFor(park.code);
    await page.goto(`/parks/${park.slug}/`);
    const section = page.locator('#things-to-do');
    const inventory = section.locator('details[data-activity-inventory]');
    const original = await evidence(page);
    for (const open of [false, true]) {
      if (open) await inventory.locator('summary').click();
      await dispatch(page, 'beforeprint');
      await page.emulateMedia({ media: 'print' });
      await expect(section).toBeVisible();
      if (open) await expect(inventory).toHaveAttribute('open', '');
      else await expect(inventory).not.toHaveAttribute('open');
      await expect(section.locator('[data-activity-record]:visible')).toHaveCount(open ? snapshot.records.length : 0);
      await expect(section.locator('[data-activity-success]')).toBeVisible();
      await expect(section.locator('[data-activity-success]')).toHaveText(snapshot.last_successful_fetch_at);
      await expect(section.locator('[data-activity-limitations]')).toBeVisible();
      await expect(section).toContainText('Availability is not verified.');
      await expect(section).toContainText('Responsible agency, difficulty and permit requirements are unknown.');
      await expectCounts(section, snapshot);
      if (open) {
        expect(await renderedListings(section)).toEqual(expectedListings(snapshot));
        for (const link of await section.locator('[data-activity-link]').all()) {
          const href = await link.getAttribute('href');
          expect(await link.evaluate(element => getComputedStyle(element, '::after').content)).toContain(href!);
          expect(await link.evaluate(element => getComputedStyle(element, '::after').overflowWrap)).toBe('anywhere');
        }
      }
      expect(await evidence(page)).toEqual(original);
      await page.emulateMedia({ media: 'screen' });
      if (open) await expect(inventory).toHaveAttribute('open', '');
      else await expect(inventory).not.toHaveAttribute('open');
    }
  }
});
