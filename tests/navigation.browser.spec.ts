import { test, expect, type Page } from '@playwright/test';
import { PUBLIC_PILOT_STALE_TIME, publicParks, publicParkSnapshots, publicRules, publicNotes } from './pilot-clock.ts';

type PilotPark = (typeof publicParks)[number];
const origin = 'http://127.0.0.1:4321';
const normalized = (value: string) => value.trim().replace(/\s+/g, ' ').toLowerCase();
const selectedSnapshot = publicParkSnapshots.find(snapshot => snapshot.records.length > 0
  && publicRules.some(rule => rule.park_code === snapshot.park_code))!;
const selectedPark = publicParks.find(park => park.code === selectedSnapshot.park_code)!;
const selectedRule = publicRules.find(rule => rule.park_code === selectedPark.code)!;
const selectedNotice = selectedSnapshot.records[0];

function sections(park: PilotPark) {
  const snapshot = publicParkSnapshots.find(item => item.park_code === park.code)!;
  return [
    { name: 'Conditions snapshot', id: 'alert-status' },
    ...(snapshot.records.length ? [{ name: 'Retained notices', id: 'retained-notices' }] : []),
    { name: 'Entry guidance check', id: 'trip-context' },
    { name: 'Before-you-go checklist', id: 'checklist-title' },
    { name: 'Stored entry guidance', id: 'guidance-title' },
    { name: 'Notice history', id: `history-${park.code}` },
    { name: 'Official planning checks', id: 'official-checks' },
  ];
}

async function expectSectionInventory(page: Page, park: PilotPark) {
  const nav = page.getByRole('navigation', { name: 'On this page', exact: true });
  const expected = sections(park);
  await expect(nav).toHaveAttribute('data-park-page-nav', '');
  await expect(nav.getByRole('link')).toHaveText(expected.map(section => section.name));
  for (const section of expected) {
    await expect(nav.getByRole('link', { name: section.name, exact: true })).toHaveAttribute('href', `#${section.id}`);
    await expect(page.locator(`[id="${section.id}"]`)).toHaveCount(1);
    await expect(page.locator(`[id="${section.id}"]`)).toHaveAttribute('tabindex', '-1');
  }
  const snapshot = publicParkSnapshots.find(item => item.park_code === park.code)!;
  if (snapshot.records.length) {
    await expect(page.locator('#retained-notices')).toHaveAttribute('aria-labelledby', 'retained-notices-title');
    await expect(page.locator('#retained-notices-title')).toHaveText('Notices retained from the checked feed');
  } else {
    await expect(nav.getByRole('link', { name: 'Retained notices', exact: true })).toHaveCount(0);
    await expect(page.locator('#retained-notices')).toHaveCount(0);
  }
}

async function followSections(page: Page, park: PilotPark) {
  const nav = page.getByRole('navigation', { name: 'On this page', exact: true });
  for (const section of sections(park)) {
    const link = nav.getByRole('link', { name: section.name, exact: true });
    await link.focus();
    await page.keyboard.press('Enter');
    await expect(page).toHaveURL(`${origin}/parks/${park.slug}/#${section.id}`);
    const target = page.locator(`[id="${section.id}"]`);
    await expect(target).toBeFocused();
    await expect(target).toBeInViewport();
    if (section.id === 'trip-context') {
      await page.keyboard.press('Tab');
      await expect(page.getByLabel('Visit date', { exact: true })).toBeFocused();
    }
  }
}

async function evidence(page: Page) {
  return {
    snapshot: await page.locator('#alert-status').getAttribute('data-snapshot'),
    history: await page.locator('[data-history]').getAttribute('data-history-metadata'),
    clocks: await page.locator('time:not(#print-time)').evaluateAll(elements => elements.map(element => ({
      datetime: element.getAttribute('datetime'), text: element.textContent,
    }))),
  };
}

async function expectEvidence(page: Page, original: Awaited<ReturnType<typeof evidence>>) {
  await expect(page.locator('#alert-status')).toHaveAttribute('data-snapshot', original.snapshot!);
  await expect(page.locator('[data-history]')).toHaveAttribute('data-history-metadata', original.history!);
  await expect.poll(() => page.locator('time:not(#print-time)').evaluateAll(elements => elements.map(element => ({
    datetime: element.getAttribute('datetime'), text: element.textContent,
  })))).toEqual(original.clocks);
}

test('native keyboard section jumps on every pilot preserve submitted choices, filters and stale evidence', async ({ page }) => {
  await page.clock.setFixedTime(new Date(PUBLIC_PILOT_STALE_TIME));
  await page.emulateMedia({ reducedMotion: 'reduce' });
  const external: string[] = [];
  page.on('request', request => {
    if (new URL(request.url()).origin !== origin) external.push(request.url());
  });
  for (const park of publicParks) {
    await page.goto(`/parks/${park.slug}/`);
    await expectSectionInventory(page, park);
    const original = await evidence(page);
    expect(JSON.parse(original.snapshot!)).toEqual(publicParkSnapshots.find(snapshot => snapshot.park_code === park.code));
    const noticeTitle = await page.locator('#notice-title').innerText();
    const noticeDetail = await page.locator('#notice-detail').innerText();
    const historyStatus = await page.locator('[data-history-status]').innerText();
    let decisionText = '';
    let progress = '';
    let shownNotices: string[] = [];
    let selectedArea = '';
    const isSelected = park.code === selectedPark.code;
    if (isSelected) {
      await page.getByLabel('Visit date', { exact: true }).fill(selectedRule.effective_from);
      await page.getByLabel('Arrival time').fill('08:00');
      selectedArea = await page.locator('#trip-area option').evaluateAll((elements, areas) =>
        elements.map(element => element.getAttribute('value') ?? '')
          .find(value => value !== '' && (areas.includes('*') || areas.includes(value))) ?? '', selectedRule.areas);
      expect(selectedArea, 'The stored rule must cover a selectable park area').not.toBe('');
      await page.getByLabel('Planned area', { exact: true }).selectOption(selectedArea);
      await page.locator('#special-case').check();
      await page.getByRole('button', { name: 'Check entry guidance', exact: true }).click();
      await expect(page.locator('#entry-decision')).toHaveAttribute('data-state', 'stale');
      await page.locator('[data-check]').first().check();
      await page.getByLabel('Search retained notices', { exact: true }).fill(selectedNotice.title);
      await page.getByLabel('Notice category', { exact: true }).selectOption(selectedNotice.category);
      const matching = selectedSnapshot.records.filter(record => record.category === selectedNotice.category
        && normalized(`${record.title} ${record.description}`).includes(normalized(selectedNotice.title)));
      await expect(page.locator('[data-retained-notice]:visible')).toHaveCount(matching.length);
      shownNotices = matching.map(record => `alert-${park.code}-${record.id}`);
      decisionText = await page.locator('#entry-decision').innerText();
      progress = await page.locator('#checklist-progress').innerText();
    }
    await followSections(page, park);
    await expectEvidence(page, original);
    await expect(page.locator('#notice-title')).toHaveText(noticeTitle);
    await expect(page.locator('#notice-detail')).toHaveText(noticeDetail);
    await expect(page.locator('[data-history-status]')).toHaveText(historyStatus);
    if (isSelected) {
      await expect(page.getByLabel('Visit date', { exact: true })).toHaveValue(selectedRule.effective_from);
      await expect(page.getByLabel('Arrival time')).toHaveValue('08:00');
      await expect(page.getByLabel('Planned area', { exact: true })).toHaveValue(selectedArea);
      await expect(page.locator('#special-case')).toBeChecked();
      await expect(page.locator('[data-check]:checked')).toHaveCount(1);
      await expect(page.locator('#checklist-progress')).toHaveText(progress);
      await expect(page.locator('#entry-decision')).toHaveText(decisionText, { useInnerText: true });
      await expect(page.locator('#entry-decision')).toHaveAttribute('data-state', 'stale');
      await expect(page.getByLabel('Search retained notices', { exact: true })).toHaveValue(selectedNotice.title);
      await expect(page.getByLabel('Notice category', { exact: true })).toHaveValue(selectedNotice.category);
      await expect.poll(() => page.locator('[data-retained-notice]:visible').evaluateAll(elements => elements.map(element => element.id)))
        .toEqual(shownNotices);
    }
  }
  expect(external).toEqual([]);
});

test('without JavaScript every pilot retains native keyboard sections, source links and checklist uncertainty', async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false, reducedMotion: 'reduce', baseURL: origin });
  try {
    const page = await context.newPage();
    for (const park of publicParks) {
      await page.goto(`/parks/${park.slug}/`);
      await expectSectionInventory(page, park);
      const original = await evidence(page);
      await followSections(page, park);
      await expectEvidence(page, original);
      const snapshot = publicParkSnapshots.find(item => item.park_code === park.code)!;
      await expect(page.locator('[data-retained-notice]:visible')).toHaveCount(snapshot.records.length);
      await expect(page.locator('[data-notice-controls]:visible')).toHaveCount(0);
      await expect(page.locator('#alert-status a')).toHaveAttribute('href', park.conditions_url);
      await expect(page.locator('[data-planning-resources] a')).toHaveCount(7);
      await expect(page.locator('[data-planning-resources]')).toContainText('not a conditions check');
      const records = [...publicRules, ...publicNotes].filter(record => record.park_code === park.code);
      const sources = page.locator('.source-panel a[href^="https://"]');
      await expect(sources).toHaveCount(records.length);
      expect(await sources.evaluateAll(elements => elements.map(element => element.getAttribute('href'))))
        .toEqual(records.map(record => record.evidence.url));
      await expect(page.locator('#entry-decision')).toHaveAttribute('data-state', 'needs-input');
      await expect(page.locator('#decision-evidence')).toBeHidden();
      await expect(page.locator('#trip-context noscript p')).toContainText('Stored guidance and official source links remain available');
      await expect(page.locator('.checklist-panel')).toContainText('We do not verify bookings, permits or conditions');
      for (const checkbox of await page.locator('[data-check]').all()) {
        await expect(checkbox).toBeDisabled();
        await expect(checkbox).not.toBeChecked();
      }
    }
  } finally {
    await context.close();
  }
});

test('section navigation wraps at 360px and 200% text, shows keyboard focus and hides for a complete printed copy', async ({ page }) => {
  await page.clock.setFixedTime(new Date(PUBLIC_PILOT_STALE_TIME));
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.setViewportSize({ width: 360, height: 800 });
  for (const park of publicParks) {
    await page.goto(`/parks/${park.slug}/`);
    await page.locator('html').evaluate(element => { element.style.fontSize = '200%'; });
    const nav = page.getByRole('navigation', { name: 'On this page', exact: true });
    await expectSectionInventory(page, park);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
    expect(await nav.evaluate(element => element.scrollWidth <= element.clientWidth + 1)).toBe(true);
    expect(await nav.getByRole('link').evaluateAll(elements => {
      const tops = elements.flatMap(element => [...element.getClientRects()].map(rect => Math.round(rect.top)));
      return new Set(tops).size;
    })).toBeGreaterThan(1);
    for (const link of await nav.getByRole('link').all()) {
      await expect(link).toBeVisible();
      expect(await link.evaluate(element => [...element.getClientRects()].every(rect => rect.left >= -1 && rect.right <= innerWidth + 1))).toBe(true);
    }
    expect(await nav.evaluate(element => getComputedStyle(element).position)).not.toMatch(/^(fixed|sticky)$/);
    await nav.getByRole('link').first().focus();
    await page.keyboard.press('Tab');
    const focused = nav.getByRole('link').nth(1);
    await expect(focused).toBeFocused();
    await expect(focused).toBeInViewport();
    expect(await focused.evaluate(element => element.matches(':focus-visible'))).toBe(true);
    await expect(focused).toHaveCSS('outline-style', 'solid');
    expect(await focused.evaluate(element => parseFloat(getComputedStyle(element).outlineWidth))).toBeGreaterThanOrEqual(2);

    const original = await evidence(page);
    const snapshot = publicParkSnapshots.find(item => item.park_code === park.code)!;
    if (snapshot.records.length) {
      await page.getByLabel('Search retained notices', { exact: true }).fill('Report a correction about this source');
      await expect(page.locator('[data-retained-notice]:visible')).toHaveCount(0);
      const hiddenArticle = page.locator('[data-retained-notice]').filter({
        has: page.getByRole('heading', { name: snapshot.records[0].title, exact: true, includeHidden: true }),
      });
      await expect(hiddenArticle).toHaveCount(1);
      await expect(hiddenArticle).toBeHidden();
    }
    await page.evaluate(() => window.dispatchEvent(new Event('beforeprint')));
    await page.emulateMedia({ media: 'print' });
    await expect(page.locator('nav[data-park-page-nav]')).toHaveCount(1);
    await expect(page.locator('nav[data-park-page-nav]')).toBeHidden();
    await expect(page.locator('#print-snapshot')).toBeVisible();
    await expect(page.locator('[data-retained-notice]:visible')).toHaveCount(snapshot.records.length);
    for (const record of snapshot.records) {
      const article = page.locator(`[id="alert-${park.code}-${record.id}"]`);
      await expect(article).toBeVisible();
      await expect(article).toContainText(record.title);
      await expect(article).toContainText(record.description);
      if (record.url) await expect(article.locator('a:not([data-correction-link])')).toHaveAttribute('href', record.url);
    }
    await expectEvidence(page, original);
    await expect(page.locator('#alert-status')).toContainText(snapshot.last_successful_fetch_at ?? 'Never');
    await expect(page.locator('#alert-status')).toContainText(snapshot.source_updated_at ?? 'Not supplied');
    for (const link of await page.locator('.source-panel a[href^="https://"],.planning-link').all()) {
      expect(await link.evaluate(element => getComputedStyle(element, '::after').content)).toContain(await link.getAttribute('href'));
    }
    await page.emulateMedia({ media: 'screen' });
    await expect(nav).toBeVisible();
    if (snapshot.records.length) {
      await expect(page.getByLabel('Search retained notices', { exact: true })).toHaveValue('Report a correction about this source');
      await expect(page.locator('[data-retained-notice]:visible')).toHaveCount(0);
    }
  }
});
