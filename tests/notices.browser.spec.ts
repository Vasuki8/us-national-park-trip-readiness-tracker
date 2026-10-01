import { test, expect, type Page } from '@playwright/test';
import { PUBLIC_PILOT_STALE_TIME, publicParks, publicParkSnapshots } from './pilot-clock.ts';

const normalized = (value: string) => value.trim().replace(/\s+/g, ' ').toLowerCase();
const snapshot = [...publicParkSnapshots]
  .filter(item => new Set(item.records.map(record => record.category)).size > 1)
  .sort((a, b) => b.records.length - a.records.length)[0]!;
const park = publicParks.find(item => item.code === snapshot.park_code)!;
const target = snapshot.records.find(record => snapshot.records.filter(other =>
  normalized(`${other.title} ${other.description}`).includes(normalized(record.title))).length === 1)!;
const other = snapshot.records.find(record => record.category !== target.category)!;
const route = `/parks/${park.slug}/`;
const anchor = (id: string) => `alert-${park.code}-${id}`;
const countText = (shown: number) => `Showing ${shown} of ${snapshot.records.length} retained notices`;
const titleQuery = `  ${target.title.toUpperCase().replace(/\s+/g, '   ')}  `;

async function expectShown(page: Page, ids: string[]) {
  await expect.poll(() => page.locator('[data-retained-notice]:visible').evaluateAll(elements => elements.map(element => element.id)))
    .toEqual(ids.map(anchor));
  await expect(page.locator('[data-notice-count]')).toHaveText(countText(ids.length));
}

test('keyboard notice filters combine title search and category without changing stale evidence', async ({ page }) => {
  await page.clock.setFixedTime(new Date(PUBLIC_PILOT_STALE_TIME));
  const external: string[] = [];
  page.on('request', request => {
    if (new URL(request.url()).origin !== 'http://127.0.0.1:4321') external.push(request.url());
  });
  await page.goto(route);
  const root = page.locator('[data-retained-notices]');
  const search = page.getByLabel('Search retained notices', { exact: true });
  const category = page.getByLabel('Notice category', { exact: true });
  const snapshotText = await page.locator('#alert-status').getAttribute('data-snapshot');
  const historyText = await page.locator('[data-history]').getAttribute('data-history-metadata');
  const sourceTimes = await page.locator('time:not(#print-time)').evaluateAll(elements => elements.map(element => element.getAttribute('datetime')));
  const staleDetail = await page.locator('#notice-detail').textContent();
  await expect(page.locator('#notice-title')).toHaveText('The condition snapshot needs a fresh check');
  await expect(root.locator('[data-notice-controls]')).toBeVisible();
  await expectShown(page, snapshot.records.map(record => record.id));
  const options = await category.locator('option').evaluateAll(elements => elements.map(element => ({ value: element.getAttribute('value'), label: element.textContent })));
  expect(options[0]).toEqual({ value: '', label: 'All categories' });
  expect(options.slice(1).map(option => option.value).sort()).toEqual([...new Set(snapshot.records.map(record => record.category))].sort());
  for (const option of options.slice(1)) expect(option.label).toBe(option.value);

  await search.focus();
  await page.keyboard.type(titleQuery);
  await category.selectOption(target.category);
  await expectShown(page, [target.id]);
  await category.selectOption(other.category);
  await expectShown(page, []);
  await expect(page.locator('[data-notice-empty]')).toBeVisible();
  await expect(page.locator('[data-notice-empty]')).toContainText('No retained notices match');
  await expect(page.locator('[data-notice-empty]')).toContainText('does not establish that conditions are clear');
  await category.selectOption(target.category);
  await expectShown(page, [target.id]);
  await expect(page.locator('[data-notice-empty]')).toBeHidden();

  // Every article contains this action label; it must not become searchable notice evidence.
  await search.fill('Report a correction about this source');
  await expectShown(page, []);
  const description = target.description.trim();
  expect(description.length).toBeGreaterThan(0);
  await search.fill(description.toUpperCase().replace(/\s+/g, '   '));
  const descriptionMatches = snapshot.records.filter(record => record.category === target.category
    && normalized(`${record.title} ${record.description}`).includes(normalized(description)));
  await expectShown(page, descriptionMatches.map(record => record.id));
  await search.fill(titleQuery);

  await page.setViewportSize({ width: 360, height: 800 });
  await page.locator('html').evaluate(element => { element.style.fontSize = '200%'; });
  await expectShown(page, [target.id]);
  await expect(search).toBeVisible();
  await expect(category).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  expect(await root.locator('[data-notice-controls]').evaluate(element => element.scrollWidth <= element.clientWidth)).toBe(true);
  const clear = page.getByRole('button', { name: 'Clear notice filters', exact: true });
  await clear.focus();
  await page.keyboard.press('Enter');
  await expect(search).toHaveValue('');
  await expect(category).toHaveValue('');
  await expectShown(page, snapshot.records.map(record => record.id));
  await expect(page.locator('[data-notice-empty]')).toBeHidden();
  await expect(page.locator('#notice-title')).toHaveText('The condition snapshot needs a fresh check');
  await expect(page.locator('#notice-detail')).toHaveText(staleDetail!);
  await expect(page.locator('#alert-status')).toHaveAttribute('data-snapshot', snapshotText!);
  await expect(page.locator('[data-history]')).toHaveAttribute('data-history-metadata', historyText!);
  expect(await page.locator('time:not(#print-time)').evaluateAll(elements => elements.map(element => element.getAttribute('datetime')))).toEqual(sourceTimes);
  await expect(page).toHaveURL(route);
  expect(external).toEqual([]);
});

test('notice filters reconcile prefilled and restored controls while unchanged counts stay quiet', async ({ page }) => {
  await page.addInitScript(({ query, category }) => {
    const observer = new MutationObserver(() => {
      const search = document.querySelector<HTMLInputElement>('[data-notice-search]');
      const filter = document.querySelector<HTMLSelectElement>('select[data-notice-category]');
      if (!search || !filter || ![...filter.options].some(option => option.value === category)) return;
      search.value = query;
      filter.value = category;
      observer.disconnect();
    });
    observer.observe(document, { childList: true, subtree: true });
  }, { query: titleQuery, category: target.category });
  await page.goto(route);
  await expectShown(page, [target.id]);
  const count = page.locator('[data-notice-count]');
  await count.evaluate(element => {
    element.setAttribute('data-text-changes', '0');
    new MutationObserver(records => {
      element.setAttribute('data-text-changes', String(Number(element.getAttribute('data-text-changes')) + records.length));
    }).observe(element, { childList: true, characterData: true, subtree: true });
  });
  await page.evaluate(async () => {
    window.dispatchEvent(new PageTransitionEvent('pageshow', { persisted: true }));
    await new Promise<void>(resolve => window.setTimeout(resolve, 0));
  });
  await expect(count).toHaveAttribute('data-text-changes', '0');

  // Emulate restoration after pageshow, without claiming a browser's cache policy.
  await page.evaluate(({ query, category }) => {
    window.dispatchEvent(new PageTransitionEvent('pageshow', { persisted: true }));
    document.querySelector<HTMLInputElement>('[data-notice-search]')!.value = query;
    document.querySelector<HTMLSelectElement>('select[data-notice-category]')!.value = category;
  }, { query: target.title, category: other.category });
  await expectShown(page, []);
  await expect(page.locator('[data-notice-empty]')).toBeVisible();
  const writes = await count.getAttribute('data-text-changes');
  await page.evaluate(async () => {
    window.dispatchEvent(new PageTransitionEvent('pageshow', { persisted: true }));
    await new Promise<void>(resolve => window.setTimeout(resolve, 0));
  });
  await expect(count).toHaveAttribute('data-text-changes', writes!);
  await page.evaluate(() => {
    window.dispatchEvent(new PageTransitionEvent('pageshow', { persisted: false }));
    document.querySelector<HTMLInputElement>('[data-notice-search]')!.value = '';
    document.querySelector<HTMLSelectElement>('select[data-notice-category]')!.value = '';
  });
  await expectShown(page, snapshot.records.map(record => record.id));
  await expect(page.locator('[data-notice-empty]')).toBeHidden();
});

test('native notice fragments reveal a filtered target while later typing and unrelated fragments retain filters', async ({ page }) => {
  await page.goto(route);
  const search = page.getByLabel('Search retained notices', { exact: true });
  const category = page.getByLabel('Notice category', { exact: true });
  await search.fill(target.title);
  await category.selectOption(target.category);
  await expectShown(page, [target.id]);
  const destination = anchor(other.id);
  const article = page.locator('[data-retained-notice]').filter({ has: page.getByRole('heading', { name: other.title, exact: true, includeHidden: true }) });
  await expect(article).toHaveCount(1);
  await expect(article).toBeHidden();
  await page.evaluate(fragment => {
    const link = document.createElement('a');
    link.id = 'notice-fragment-test';
    link.textContent = 'Open another retained notice';
    link.href = `#${encodeURIComponent(fragment)}`;
    document.querySelector('[data-retained-notices]')!.before(link);
  }, destination);
  const link = page.locator('#notice-fragment-test');
  await link.focus();
  await page.keyboard.press('Enter');
  await expect(page).toHaveURL(`${route}#${encodeURIComponent(destination)}`);
  await expect(search).toHaveValue('');
  await expect(category).toHaveValue('');
  await expectShown(page, snapshot.records.map(record => record.id));
  await expect(article.getByRole('heading', { name: other.title, exact: true })).toBeInViewport();

  // The existing notice hash must not prevent the visitor making a new search.
  await search.fill(target.title);
  await category.selectOption(target.category);
  await expectShown(page, [target.id]);
  await expect(article).toBeHidden();
  for (const fragment of ['unknown-retained-notice', '%E0%A4%A', 'guidance-title']) {
    await link.evaluate((element, value) => element.setAttribute('href', `#${value}`), fragment);
    await link.click();
    await expect(page).toHaveURL(`${route}#${fragment}`);
    await expect(search).toHaveValue(target.title);
    await expect(category).toHaveValue(target.category);
    await expectShown(page, [target.id]);
  }
});

test('printing includes every retained notice without changing the screen filters or original clocks', async ({ page }) => {
  await page.clock.setFixedTime(new Date(PUBLIC_PILOT_STALE_TIME));
  await page.goto(route);
  const root = page.locator('[data-retained-notices]');
  const search = page.getByLabel('Search retained notices', { exact: true });
  const category = page.getByLabel('Notice category', { exact: true });
  const snapshotText = await page.locator('#alert-status').getAttribute('data-snapshot');
  const historyText = await page.locator('[data-history]').getAttribute('data-history-metadata');
  const sourceTimes = await page.locator('time:not(#print-time)').evaluateAll(elements => elements.map(element => element.getAttribute('datetime')));
  await search.fill(target.title);
  await category.selectOption(other.category);
  await expectShown(page, []);
  await expect(root.locator('[data-notice-empty]')).toBeVisible();
  const screenHidden = await root.locator('[data-retained-notice]').evaluateAll(elements => elements.map(element => (element as HTMLElement).hidden));
  await page.evaluate(() => window.dispatchEvent(new Event('beforeprint')));
  await page.emulateMedia({ media: 'print' });
  await expect(root.locator('[data-retained-notice]:visible')).toHaveCount(snapshot.records.length);
  await expect(root.locator('[data-notice-controls]')).toBeHidden();
  await expect(root.locator('[data-notice-count]')).toBeHidden();
  await expect(root.locator('[data-notice-empty]')).toBeHidden();
  const printNote = root.locator('.print-only');
  await expect(printNote).toBeVisible();
  await expect(printNote).toContainText(`All ${snapshot.records.length} retained notices are included in this page copy.`);
  for (const record of snapshot.records) {
    const article = root.locator('[data-retained-notice]').filter({ has: page.getByRole('heading', { name: record.title, exact: true }) });
    await expect(article).toBeVisible();
    if (record.url) {
      const source = article.getByRole('link', { name: 'More information link supplied by NPS', exact: true });
      await expect(source).toHaveAttribute('href', record.url);
      expect(await source.evaluate(element => getComputedStyle(element, '::after').content)).toContain(record.url);
    }
  }
  await expect(page.locator('#notice-title')).toHaveText('The condition snapshot needs a fresh check');
  await expect(page.locator('#alert-status')).toHaveAttribute('data-snapshot', snapshotText!);
  await expect(page.locator('[data-history]')).toHaveAttribute('data-history-metadata', historyText!);
  expect(await page.locator('time:not(#print-time)').evaluateAll(elements => elements.map(element => element.getAttribute('datetime')))).toEqual(sourceTimes);
  await page.emulateMedia({ media: 'screen' });
  await expect(search).toHaveValue(target.title);
  await expect(category).toHaveValue(other.category);
  await expectShown(page, []);
  await expect(root.locator('[data-notice-empty]')).toBeVisible();
  expect(await root.locator('[data-retained-notice]').evaluateAll(elements => elements.map(element => (element as HTMLElement).hidden))).toEqual(screenHidden);
  await expect(printNote).toBeHidden();
});

test('without JavaScript all retained notices and native source links remain available without active filters', async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  try {
    const page = await context.newPage();
    for (const park of publicParks) {
      const snapshot = publicParkSnapshots.find(item => item.park_code === park.code)!;
      await page.goto(`/parks/${park.slug}/`);
      await expect(page.locator('[data-retained-notice]:visible')).toHaveCount(snapshot.records.length);
      await expect(page.locator('[data-notice-controls]:visible')).toHaveCount(0);
      await expect(page.getByRole('button', { name: 'Clear notice filters', exact: true })).toBeHidden();
      if (!snapshot.records.length) {
        await expect(page.locator('[data-retained-notices]')).toHaveCount(0);
        await expect(page.locator('#alert-status')).toContainText(snapshot.last_successful_fetch_at ?? 'Never');
        continue;
      }
      for (const record of snapshot.records) {
        const article = page.locator('[data-retained-notice]').filter({ has: page.getByRole('heading', { name: record.title, exact: true }) });
        await expect(article).toHaveAttribute('id', `alert-${park.code}-${record.id}`);
        await expect(article).toContainText(record.description);
        const correction = article.getByRole('link', { name: 'Report a correction about this source', exact: true });
        await expect(correction).toHaveAttribute('href', `/corrections/?source=${encodeURIComponent(`alert:${park.code}:${record.id}`)}`);
        if (record.url) {
          const source = article.getByRole('link', { name: 'More information link supplied by NPS', exact: true });
          await expect(source).toHaveAttribute('href', record.url);
          await expect(source).toHaveAttribute('referrerpolicy', 'no-referrer');
        } else await expect(article).toContainText('NPS did not supply a direct link for this alert.');
      }
    }
  } finally {
    await context.close();
  }
});
