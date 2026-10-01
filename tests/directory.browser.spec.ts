import { test, expect, type Page } from '@playwright/test';
import { PUBLIC_PILOT_REFERENCE_TIME, publicParks } from './pilot-clock.ts';

type DirectoryPark = (typeof publicParks)[number] & { name: string; states: string[] };
const directoryParks = publicParks as DirectoryPark[];
const target = directoryParks.find(park => park.code === 'romo')!;
const matchingState = target.states[0];
const differentState = directoryParks.flatMap(park => park.states).find(state => !target.states.includes(state))!;
const prefilled = `  ${target.name.toUpperCase().replace(/\s+/g, '   ')}  `;
const equivalent = `\t${target.name.toLowerCase().replace(/\s+/g, ' \t  ')}\t`;

async function expectDirectoryResults(page: Page, codes: string[]) {
  await expect.poll(() => page.locator('[data-park-card]:visible').evaluateAll(elements =>
    elements.map(element => element.querySelector('[data-entry-label]')!.getAttribute('data-entry-label')))).toEqual(codes);
  await expect(page.locator('#search-count')).toHaveText(`${codes.length} ${codes.length === 1 ? 'park' : 'parks'} shown`);
  if (codes.length) await expect(page.locator('#empty-search')).toBeHidden();
  else await expect(page.locator('#empty-search')).toBeVisible();
}

const directoryMetadata = (page: Page) => page.locator('[data-park-card]').evaluateAll(elements => elements.map(element => ({
  search: element.getAttribute('data-search'), states: element.getAttribute('data-states'), text: element.textContent,
  code: element.querySelector('[data-entry-label]')!.getAttribute('data-entry-label'),
  href: element.querySelector('h3 a')!.getAttribute('href'),
})));

for (const route of ['/', '/parks/']) {
  test(`directory reconciles restored controls and keeps unchanged counts quiet: ${route}`, async ({ page }) => {
    // Emulate controls restored before the deferred directory script initializes.
    await page.addInitScript(() => {
      const observer = new MutationObserver(() => {
        const search = document.querySelector<HTMLInputElement>('#park-search');
        const filter = document.querySelector<HTMLSelectElement>('#state-filter');
        if (!search || !filter?.querySelector('option[value="Wyoming"]')) return;
        search.value = 'yellow';
        filter.value = 'Wyoming';
        observer.disconnect();
      });
      observer.observe(document, { childList: true, subtree: true });
    });
    await page.goto(route);
    const count = page.locator('#search-count');
    const cards = page.locator('[data-park-card]:visible');
    await expect(page.locator('#park-search')).toHaveValue('yellow');
    await expect(page.locator('#state-filter')).toHaveValue('Wyoming');
    await expect(cards).toHaveCount(1);
    await expect(cards.getByRole('link', { name: 'Yellowstone' })).toBeVisible();
    await expect(count).toHaveText('1 park shown');
    await count.evaluate((element) => {
      element.setAttribute('data-text-changes', '0');
      new MutationObserver((records) => {
        element.setAttribute('data-text-changes', String(Number(element.getAttribute('data-text-changes')) + records.length));
      }).observe(element, { childList: true, characterData: true, subtree: true });
    });
    await page.evaluate(async () => {
      window.dispatchEvent(new PageTransitionEvent('pageshow', { persisted: true }));
      await new Promise<void>((resolve) => window.setTimeout(resolve, 0));
    });
    await expect(count).toHaveAttribute('data-text-changes', '0');

    // Restore a different filter on page return without dispatching input/change.
    await page.evaluate(() => {
      document.querySelector<HTMLSelectElement>('#state-filter')!.value = 'Utah';
      window.dispatchEvent(new PageTransitionEvent('pageshow', { persisted: true }));
    });
    await expect(cards).toHaveCount(0);
    await expect(count).toHaveText('0 parks shown');
    await expect(page.locator('#empty-search')).toBeVisible();
    const textChanges = await count.getAttribute('data-text-changes');
    await page.evaluate(async () => {
      window.dispatchEvent(new PageTransitionEvent('pageshow', { persisted: true }));
      await new Promise<void>((resolve) => window.setTimeout(resolve, 0));
    });
    await expect(count).toHaveAttribute('data-text-changes', textChanges!);

    // History traversal may restore controls after pageshow in the same task.
    await page.evaluate(() => {
      window.dispatchEvent(new PageTransitionEvent('pageshow', { persisted: true }));
      document.querySelector<HTMLInputElement>('#park-search')!.value = '';
      document.querySelector<HTMLSelectElement>('#state-filter')!.value = '';
    });
    await expect(cards).toHaveCount(5);
    await expect(count).toHaveText('5 parks shown');
    await expect(page.locator('#empty-search')).toBeHidden();
  });
}

for (const route of ['/', '/parks/']) {
  test(`directory normalizes multiword whitespace while preserving raw choices and source metadata: ${route}`, async ({ page }) => {
    await page.clock.setFixedTime(new Date(PUBLIC_PILOT_REFERENCE_TIME));
    await page.addInitScript(({ query, state }) => {
      const observer = new MutationObserver(() => {
        const search = document.querySelector<HTMLInputElement>('#park-search');
        const filter = document.querySelector<HTMLSelectElement>('#state-filter');
        if (!search || !filter || ![...filter.options].some(option => option.value === state)) return;
        search.value = query;
        filter.value = state;
        observer.disconnect();
      });
      observer.observe(document, { childList: true, subtree: true });
    }, { query: prefilled, state: matchingState });
    const requests: string[] = [];
    page.on('request', request => requests.push(request.url()));
    await page.goto(route);
    const loadedRequests = requests.length;
    const search = page.getByLabel('Search parks', { exact: true });
    const state = page.getByLabel('Filter by state', { exact: true });
    const count = page.locator('#search-count');
    await expect(search).toHaveValue(prefilled);
    await expect(state).toHaveValue(matchingState);
    await expectDirectoryResults(page, [target.code]);
    await expect(page.locator('[data-park-card]:visible').getByRole('link', { name: target.name, exact: true })).toBeVisible();
    const metadata = await directoryMetadata(page);
    const coverage = await page.locator('.directory[data-coverage]').getAttribute('data-coverage');
    const warning = 'Neither confirms access or safe conditions.';
    await expect(page.locator('.directory')).toContainText(warning);
    await count.evaluate(element => {
      element.setAttribute('data-normalized-query-writes', '0');
      new MutationObserver(records => element.setAttribute('data-normalized-query-writes',
        String(Number(element.getAttribute('data-normalized-query-writes')) + records.length)))
        .observe(element, { childList: true, characterData: true, subtree: true });
    });
    await search.fill(equivalent);
    await expect(search).toHaveValue(equivalent);
    await expectDirectoryResults(page, [target.code]);
    await page.evaluate(() => new Promise<void>(resolve => window.setTimeout(resolve, 0)));
    await expect(count).toHaveAttribute('data-normalized-query-writes', '0');

    await state.selectOption(differentState);
    await expectDirectoryResults(page, []);
    await expect(search).toHaveValue(equivalent);
    // Restoration follows pageshow in the same task, without input/change events.
    await page.evaluate(({ query, state }) => {
      window.dispatchEvent(new PageTransitionEvent('pageshow', { persisted: true }));
      document.querySelector<HTMLInputElement>('#park-search')!.value = query;
      document.querySelector<HTMLSelectElement>('#state-filter')!.value = state;
    }, { query: prefilled, state: matchingState });
    await expectDirectoryResults(page, [target.code]);
    await expect(search).toHaveValue(prefilled);
    await expect(state).toHaveValue(matchingState);
    const writes = await count.getAttribute('data-normalized-query-writes');
    await page.evaluate(async ({ query, state }) => {
      window.dispatchEvent(new PageTransitionEvent('pageshow', { persisted: true }));
      document.querySelector<HTMLInputElement>('#park-search')!.value = query;
      document.querySelector<HTMLSelectElement>('#state-filter')!.value = state;
      await new Promise<void>(resolve => window.setTimeout(resolve, 0));
    }, { query: equivalent, state: matchingState });
    await expectDirectoryResults(page, [target.code]);
    await expect(search).toHaveValue(equivalent);
    await expect(count).toHaveAttribute('data-normalized-query-writes', writes!);

    await state.selectOption('');
    const literal = 'rocky.*mountain|.*';
    await search.fill(literal);
    await expect(search).toHaveValue(literal);
    await expectDirectoryResults(page, []);
    await expect(page.locator('#empty-search')).toContainText('No parks match your search.');
    await search.fill(' \t  ');
    await expect(search).toHaveValue(' \t  ');
    await expectDirectoryResults(page, directoryParks.map(park => park.code));
    await search.fill('');
    await expectDirectoryResults(page, directoryParks.map(park => park.code));
    expect(await directoryMetadata(page)).toEqual(metadata);
    await expect(page.locator('.directory[data-coverage]')).toHaveAttribute('data-coverage', coverage!);
    await expect(page.locator('.directory')).toContainText(warning);
    expect(await page.evaluate(() => ({ local: localStorage.length, session: sessionStorage.length }))).toEqual({ local: 0, session: 0 });
    await expect(page).toHaveURL(`http://127.0.0.1:4321${route}`);
    expect(requests).toHaveLength(loadedRequests);
    expect(requests.every(url => new URL(url).origin === 'http://127.0.0.1:4321')).toBe(true);
    const parkLink = page.locator('[data-park-card]').filter({ has: page.locator(`[data-entry-label="${target.code}"]`) })
      .getByRole('link', { name: target.name, exact: true });
    await expect(parkLink).toHaveAttribute('href', `/parks/${target.slug}/`);
    await parkLink.focus();
    await page.keyboard.press('Enter');
    await expect(page).toHaveURL(`http://127.0.0.1:4321/parks/${target.slug}/`);
    await expect(page.locator('h1')).toContainText(target.name);
    expect(requests.every(url => new URL(url).origin === 'http://127.0.0.1:4321')).toBe(true);
  });
}
