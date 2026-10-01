import { test, expect } from '@playwright/test';
import { guidanceScenarioTime, publicRules, publicParks, publicParkSnapshots } from './pilot-clock.ts';
import { describeHistory } from '../src/lib/history.ts';
const base = '/us-national-park-trip-readiness-tracker/';

test('project-path directory resynchronizes restored filters on page return', async ({ page }) => {
  for (const route of [base, `${base}parks/`]) {
    await page.goto(route);
    // A browser can restore controls without dispatching input/change events.
    await page.evaluate(() => {
      window.dispatchEvent(new PageTransitionEvent('pageshow', { persisted: true }));
      document.querySelector<HTMLInputElement>('#park-search')!.value = 'rocky';
      document.querySelector<HTMLSelectElement>('#state-filter')!.value = 'Colorado';
    });
    await expect(page.locator('[data-park-card]:visible')).toHaveCount(1);
    await expect(page.locator('[data-park-card]:visible h3')).toContainText('Rocky Mountain');
    await expect(page.locator('#search-count')).toHaveText('1 park shown');
    await expect(page.locator('#empty-search')).toBeHidden();
    await page.evaluate(() => {
      window.dispatchEvent(new PageTransitionEvent('pageshow', { persisted: true }));
      document.querySelector<HTMLInputElement>('#park-search')!.value = '';
      document.querySelector<HTMLSelectElement>('#state-filter')!.value = '';
    });
    await expect(page.locator('[data-park-card]:visible')).toHaveCount(5);
    await expect(page.locator('#search-count')).toHaveText('5 parks shown');
  }
});

test('project-path search and navigation load working assets', async ({ page }) => {
  const failures: string[] = [];
  page.on('pageerror', error => failures.push(error.message));
  page.on('response', response => { if (response.status() >= 400) failures.push(response.url()); });
  await page.goto(base);
  await page.getByLabel('Search parks').fill('Yosemite');
  await expect(page.locator('#search-count')).toContainText('1');
  await page.locator('.park-card:visible h3 a').click();
  await expect(page).toHaveURL(new RegExp(`${base}parks/yosemite/$`));
  await expect(page.locator('h1')).toContainText('Yosemite');
  await expect(page.locator('.site-header')).toHaveCSS('display', 'flex');
  await page.getByRole('navigation', { name: 'Breadcrumb' }).getByRole('link', { name: 'Explore parks' }).click();
  await expect(page.locator('.site-header [aria-current="page"]')).toHaveText('Explore parks');
  expect(failures).toEqual([]);
});

test('project-path entry checker and checklist remain interactive', async ({ page }) => {
  await page.clock.setFixedTime(new Date(guidanceScenarioTime(publicRules.filter((rule) => rule.park_code === 'romo' && rule.areas.includes('bear-lake')))));
  await page.goto(`${base}parks/rocky-mountain/`);
  await page.getByLabel('Visit date').fill('2026-09-30');
  await page.getByLabel('Planned area').selectOption('bear-lake');
  await page.getByLabel('Arrival time').fill('08:00');
  await page.getByRole('button', { name: 'Check entry guidance' }).click();
  await expect(page.locator('#decision-title')).toHaveText('Review your timed-entry reservation');
  await page.locator('[data-check]').first().check();
  await expect(page.locator('#checklist-progress')).toContainText('1 of 5');
  await page.getByRole('button', { name: 'Reset checklist' }).click();
  await expect(page.locator('[data-check]:checked')).toHaveCount(0);
});

test('project-path evidence follows restored areas and retains the original review after expiry', async ({ page }) => {
  const rest = publicRules.find((rule) => rule.park_code === 'romo' && rule.areas.includes('rest'))!;
  const bearLake = publicRules.find((rule) => rule.park_code === 'romo' && rule.areas.includes('bear-lake'))!;
  await page.clock.setFixedTime(new Date(guidanceScenarioTime([rest, bearLake])));
  await page.goto(`${base}parks/rocky-mountain/`);
  const evidence = page.locator('#decision-evidence');
  await expect(evidence).toBeHidden();
  await page.getByLabel('Visit date').fill('2026-09-30');
  await page.getByLabel('Planned area').selectOption('bear-lake');
  await page.locator('#special-case').check();
  await page.getByRole('button', { name: 'Check entry guidance' }).click();
  await expect(page.locator('#decision-title')).toHaveText('Check the rules for your circumstances');
  const decisionText = await page.locator('#entry-decision').innerText();
  await expect(evidence).toHaveAttribute('href', `#entry-rule-${encodeURIComponent(bearLake.id)}`);
  // Model restoration after pageshow without claiming a browser-specific cache policy.
  await page.evaluate(() => {
    window.dispatchEvent(new PageTransitionEvent('pageshow', { persisted: true }));
    document.querySelector<HTMLSelectElement>('#trip-area')!.value = 'rest';
  });
  await expect(page.locator('#entry-decision')).toHaveText(decisionText, { useInnerText: true });
  await expect(evidence).toHaveAttribute('href', `#entry-rule-${encodeURIComponent(rest.id)}`);
  await evidence.click();
  await expect(page).toHaveURL(`http://127.0.0.1:4324${base}parks/rocky-mountain/#entry-rule-${encodeURIComponent(rest.id)}`);
  const matched = page.locator(`[id="entry-rule-${rest.id}"]`);
  await expect(matched.getByRole('heading', { name: 'Rest of park', exact: true })).toBeVisible();
  await expect(matched.getByRole('link', { name: 'Read the official source', exact: true })).toHaveAttribute('href', rest.evidence.url);
  await page.clock.setFixedTime(new Date(Date.parse(rest.reviewed_at) + 168 * 3_600_000 + 1));
  await page.evaluate(() => window.dispatchEvent(new PageTransitionEvent('pageshow', { persisted: true })));
  await expect(page.locator('#entry-decision')).toHaveAttribute('data-state', 'stale');
  await expect(evidence).toHaveAttribute('href', `#entry-rule-${encodeURIComponent(rest.id)}`);
  await expect(evidence).toHaveText('View the stored rule needing a fresh review');
  await expect(evidence).toBeVisible();
  await page.setViewportSize({ width: 360, height: 800 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await expect(matched.locator('time').first()).toHaveAttribute('datetime', rest.reviewed_at);
  await expect(matched.locator('time').first()).toHaveText(rest.reviewed_at);
  await expect(matched.locator('[data-reviewed]')).toHaveAttribute('data-reviewed', rest.reviewed_at);
  await expect(matched.locator('[data-reviewed]')).toContainText('Needs a fresh review');
});

test('project-path trip return resynchronizes restored choices and checklist progress', async ({ page }) => {
  await page.clock.setFixedTime(new Date(guidanceScenarioTime(publicRules.filter((rule) => rule.park_code === 'romo'))));
  await page.goto(`${base}parks/rocky-mountain/`);
  await page.getByLabel('Visit date').fill('2026-09-30');
  await page.getByLabel('Planned area').selectOption('bear-lake');
  await page.getByLabel('Arrival time').fill('08:00');
  await page.getByRole('button', { name: 'Check entry guidance' }).click();
  await expect(page.locator('#decision-title')).toHaveText('Review your timed-entry reservation');
  await page.locator('[data-check]').first().check();
  // Model event ordering and silent restoration, not a particular browser's cache policy.
  await page.evaluate(() => {
    window.dispatchEvent(new PageTransitionEvent('pageshow', { persisted: true }));
    document.querySelector<HTMLSelectElement>('#trip-area')!.value = 'rest';
  });
  await expect(page.locator('#entry-decision')).toHaveAttribute('data-state', 'not-required-under-rule');
  await expect(page.locator('#decision-title')).toHaveText('Outside this reviewed timed-entry window');
  await expect(page.locator('[data-check]:checked')).toHaveCount(0);
  await expect(page.locator('#checklist-progress')).toHaveText('0 of 5 items reviewed by you');
  await page.locator('[data-check]').first().check();
  await page.evaluate(() => {
    window.dispatchEvent(new PageTransitionEvent('pageshow', { persisted: true }));
    document.querySelectorAll<HTMLInputElement>('[data-check]')[1].checked = true;
  });
  await expect(page.locator('[data-check]:checked')).toHaveCount(2);
  await expect(page.locator('#checklist-progress')).toHaveText('2 of 5 items reviewed by you');
  await page.evaluate(() => {
    window.dispatchEvent(new PageTransitionEvent('pageshow', { persisted: false }));
    document.querySelectorAll<HTMLInputElement>('[data-check]').forEach((check) => { check.checked = true; });
  });
  await expect(page.locator('[data-check]:checked')).toHaveCount(0);
  await expect(page.locator('#checklist-progress')).toHaveText('0 of 5 items reviewed by you');
});

test('project-path content, footer and fragment links retain destinations', async ({ page }) => {
  await page.goto(`${base}changes/`);
  await expect(page.getByRole('link', { name: 'Explore the pilot parks' })).toHaveAttribute('href', `${base}parks/`);
  await page.getByRole('navigation', { name: 'Jump to park history' }).getByRole('link', { name: 'Zion', exact: true }).click();
  await expect(page).toHaveURL(new RegExp(`${base}changes/#history-zion$`));
  await page.getByRole('navigation', { name: 'Footer navigation' }).getByRole('link', { name: 'About', exact: true }).click();
  await expect(page.locator('.site-footer [aria-current="page"]')).toHaveText('About');
  await page.getByRole('link', { name: 'Park Readiness home' }).click();
  await expect(page).toHaveURL(new RegExp(`${base}$`));
});

test('all project pages and metadata remain available without launch claims', async ({ request }) => {
  for (const route of ['', 'parks/', ...['yosemite', 'rocky-mountain', 'yellowstone', 'zion', 'grand-canyon'].map(slug => `parks/${slug}/`),
    'how-it-works/', 'sources/', 'changes/', 'about/', 'privacy/', 'terms/', 'corrections/']) {
    const response = await request.get(base + route);
    expect(response.status(), route).toBe(200);
    expect(await response.text()).toContain('noindex, nofollow');
  }
  const manifest = await (await request.get(base + 'build.json')).json();
  expect(manifest.base_path).toBe(base);
  expect(manifest.published_at).toBeNull();
  expect(manifest.live_collection_enabled).toBe(false);
  expect(await (await request.get(base + 'robots.txt')).text()).toContain('Disallow: /');
});

test('project-path printing refreshes expired guidance without rewriting source evidence', async ({ page }) => {
  const rule = publicRules.find(rule => rule.park_code === 'romo' && rule.areas.includes('bear-lake'))!;
  await page.clock.setFixedTime(new Date(guidanceScenarioTime([rule])));
  await page.goto(`${base}parks/rocky-mountain/`);
  await page.getByLabel('Visit date').fill('2026-09-30');
  await page.getByLabel('Planned area').selectOption('bear-lake');
  await page.getByLabel('Arrival time').fill('08:00');
  await page.getByRole('button', { name: 'Check entry guidance' }).click();
  await page.locator('[data-check]').first().check();
  const sourceClocks = await page.locator('time:not(#print-time)').evaluateAll(elements => elements.map(element => element.getAttribute('datetime')));
  const snapshotText = await page.locator('#alert-status').getAttribute('data-snapshot');
  const historyText = await page.locator('[data-history]').getAttribute('data-history-metadata');
  const expired = new Date(Date.parse(rule.reviewed_at) + 168 * 3_600_000 + 1);
  await page.clock.setFixedTime(expired);
  await page.evaluate(() => {
    window.print = () => {
      // Model the native event without opening the platform print dialog.
      window.dispatchEvent(new Event('beforeprint'));
      document.documentElement.dataset.printCalls = String(Number(document.documentElement.dataset.printCalls || '0') + 1);
    };
  });
  await page.getByRole('button', { name: 'Print / save this page' }).click();
  await expect(page.locator('html')).toHaveAttribute('data-print-calls', '1');
  await expect(page.locator('#decision-title')).toHaveText('Entry guidance needs a fresh review');
  await expect(page.locator('[data-history-status]')).toHaveText(describeHistory(JSON.parse(historyText!), expired).title);
  await expect(page.locator('#checklist-progress')).toHaveText('1 of 5 items reviewed by you');
  await expect(page.locator('#print-time')).toHaveAttribute('datetime', expired.toISOString());
  await expect(page.locator('#print-time')).toHaveText(expired.toISOString());
  await expect(page.locator('#alert-status')).toHaveAttribute('data-snapshot', snapshotText!);
  await expect(page.locator('[data-history]')).toHaveAttribute('data-history-metadata', historyText!);
  expect(await page.locator('time:not(#print-time)').evaluateAll(elements => elements.map(element => element.getAttribute('datetime')))).toEqual(sourceClocks);
  await page.emulateMedia({ media: 'print' });
  await expect(page.locator('#print-snapshot')).toBeVisible();
  await expect(page.locator('#print-snapshot')).toContainText('not a source check');
  await expect(page.locator('#print-page')).toBeHidden();
  await expect(page.locator('#trip-date')).toHaveValue('2026-09-30');
  await expect(page.locator('[data-check]:checked')).toHaveCount(1);
  for (const link of await page.locator('.planning-link').all()) {
    const href = await link.getAttribute('href');
    expect(await link.evaluate(element => getComputedStyle(element, '::after').content)).toContain(href!);
  }
});

test('project-path corrections retain source identity and return to the exact notice', async ({ page }) => {
  await page.goto(`${base}parks/yosemite/`);
  const article = page.locator('.source-item[id^="alert-yose-"]').first();
  const anchor = await article.getAttribute('id');
  const link = article.locator('[data-correction-link]');
  const destination = await link.getAttribute('href');
  expect(destination).toMatch(new RegExp(`^${base}corrections/\\?source=`));
  await link.click();
  await expect(page).toHaveURL(`http://127.0.0.1:4324${destination}`);
  await expect(page.locator('#correction-source')).toBeVisible();
  await expect(page.locator('#correction-source-label')).toHaveText('Yosemite · Retained NPS notice');
  await expect(page.locator('#correction-return')).toHaveAttribute('href', `${base}parks/yosemite/#${encodeURIComponent(anchor!)}`);
  const draft = new URL((await page.locator('#correction-draft').getAttribute('href'))!);
  expect(draft.searchParams.get('body')).toContain(`https://vasuki8.github.io${base}parks/yosemite/`);
  expect(draft.searchParams.get('body')).not.toContain('127.0.0.1');
  await page.locator('#correction-return').focus();
  await page.keyboard.press('Enter');
  await expect(page).toHaveURL(`http://127.0.0.1:4324${base}parks/yosemite/#${encodeURIComponent(anchor!)}`);
  await expect(page.locator(`[id="${anchor}"] h3`)).toBeInViewport();
});

test('project-path notice filters reveal an exact native fragment without changing correction destinations', async ({ page }) => {
  const snapshot = publicParkSnapshots.find(item => new Set(item.records.map(record => record.category)).size > 1)!;
  const park = publicParks.find(item => item.code === snapshot.park_code)!;
  const selected = snapshot.records[0];
  const target = snapshot.records.find(record => record.category !== selected.category)!;
  const route = `${base}parks/${park.slug}/`;
  await page.goto(route);
  const search = page.getByLabel('Search retained notices', { exact: true });
  const category = page.getByLabel('Notice category', { exact: true });
  await search.fill(selected.title);
  await category.selectOption(selected.category);
  const anchor = `alert-${park.code}-${target.id}`;
  const article = page.locator('[data-retained-notice]').filter({ has: page.getByRole('heading', { name: target.title, exact: true, includeHidden: true }) });
  await expect(article).toHaveCount(1);
  await expect(article).toBeHidden();
  await page.evaluate(fragment => {
    const link = document.createElement('a');
    link.id = 'project-notice-fragment-test';
    link.textContent = 'Open another retained notice';
    link.href = `#${encodeURIComponent(fragment)}`;
    document.querySelector('[data-retained-notices]')!.before(link);
  }, anchor);
  await page.locator('#project-notice-fragment-test').focus();
  await page.keyboard.press('Enter');
  await expect(page).toHaveURL(`http://127.0.0.1:4324${route}#${encodeURIComponent(anchor)}`);
  await expect(search).toHaveValue('');
  await expect(category).toHaveValue('');
  await expect(page.locator('[data-retained-notice]:visible')).toHaveCount(snapshot.records.length);
  await expect(page.locator('[data-notice-count]')).toHaveText(`Showing ${snapshot.records.length} of ${snapshot.records.length} retained notices`);
  await expect(article.getByRole('heading', { name: target.title, exact: true })).toBeInViewport();
  const correction = article.getByRole('link', { name: 'Report a correction about this source', exact: true });
  const destination = `${base}corrections/?source=${encodeURIComponent(`alert:${park.code}:${target.id}`)}`;
  await expect(correction).toHaveAttribute('href', destination);
  await correction.click();
  await expect(page).toHaveURL(`http://127.0.0.1:4324${destination}`);
  await expect(page.locator('#correction-return')).toHaveAttribute('href', `${route}#${encodeURIComponent(anchor)}`);
  await page.locator('#correction-return').focus();
  await page.keyboard.press('Enter');
  await expect(page).toHaveURL(`http://127.0.0.1:4324${route}#${encodeURIComponent(anchor)}`);
  await expect(page.locator('[data-retained-notice]').filter({ has: page.getByRole('heading', { name: target.title, exact: true }) })).toBeVisible();
});
