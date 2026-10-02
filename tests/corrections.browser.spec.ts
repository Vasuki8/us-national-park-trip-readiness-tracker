import { test, expect } from '@playwright/test';
import { PUBLIC_PILOT_STALE_TIME, publicRules, publicNotes, publicParks, publicParkSnapshots } from './pilot-clock.ts';

const storedGuidance = [
  ...publicRules.map(record => ({ kind: 'rule' as const, record })),
  ...publicNotes.map(record => ({ kind: 'note' as const, record })),
];

test('keyboard correction returns focus every stored guidance article without refreshing its evidence', async ({ page }) => {
  await page.clock.setFixedTime(new Date(PUBLIC_PILOT_STALE_TIME));
  await page.emulateMedia({ reducedMotion: 'reduce' });
  const external: string[] = [];
  page.on('request', request => { if (!request.url().startsWith('http://127.0.0.1:4321/')) external.push(request.url()); });
  for (const { kind, record } of storedGuidance) {
    const park = publicParks.find(park => park.code === record.park_code)!;
    const anchor = `entry-${kind}-${record.id}`;
    await page.goto(`/parks/${park.slug}/`);
    const article = page.locator(`[id="${anchor}"]`);
    await expect(article).toHaveCount(1);
    await expect(article.locator('time').first()).toHaveAttribute('datetime', record.reviewed_at);
    await expect(article.locator('.review-status')).toContainText('Needs a fresh review');
    await article.locator('[data-correction-link]').focus();
    await page.keyboard.press('Enter');
    await expect(page).toHaveURL(`/corrections/?source=${encodeURIComponent(`${kind}:${park.code}:${record.id}`)}`);
    await expect(page.locator('#correction-source')).toBeVisible();
    await expect(page.locator('#correction-wording')).toContainText(record.summary);
    await expect(page.locator('#correction-facts')).toContainText(record.reviewed_at);
    if ('limitation' in record) {
      await expect(page.locator('#correction-wording')).toContainText(record.limitation);
      await expect(page.locator('#correction-facts')).not.toContainText('Effective from');
    }
    const returnLink = page.locator('#correction-return');
    await expect(returnLink).toHaveAttribute('href', `/parks/${park.slug}/#${encodeURIComponent(anchor)}`);
    await returnLink.focus();
    await page.keyboard.press('Enter');
    await expect(page).toHaveURL(`/parks/${park.slug}/#${encodeURIComponent(anchor)}`);
    await expect(article).toHaveCount(1);
    await expect(article).toBeFocused();
    await expect(article).toBeInViewport();
    await expect(article.locator('details')).not.toHaveAttribute('open', '');
    await page.keyboard.press('Tab');
    await expect(article.locator('summary')).toBeFocused();
    await page.keyboard.press('Enter');
    await expect(article.locator('blockquote')).toBeVisible();
    await expect(article.locator('blockquote')).toHaveText(record.evidence.excerpt);
    await expect(article.locator('code')).toHaveText(record.evidence.content_hash);
    await expect(article.getByRole('link', { name: 'Read the official source', exact: true })).toHaveAttribute('href', record.evidence.url);
    await expect(article.locator('time').first()).toHaveAttribute('datetime', record.reviewed_at);
    await expect(article.locator('time').first()).toHaveText(record.reviewed_at);
    await expect(article.locator('.review-status')).toContainText('Needs a fresh review');
    if ('limitation' in record) await expect(article).toContainText(record.limitation);
    await expect(page.locator('#decision-evidence')).toBeHidden();
    await expect(page.locator('#decision-title')).toHaveText('Start with your visit date');
    await expect(page.locator('[data-check]:checked')).toHaveCount(0);
    expect(await page.evaluate(() => ({ local: localStorage.length, session: sessionStorage.length }))).toEqual({ local: 0, session: 0 });
  }
  expect(external).toEqual([]);
});

test('without JavaScript exact dated and undated fragments focus their native supporting evidence', async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false, reducedMotion: 'reduce', baseURL: 'http://127.0.0.1:4321' });
  try {
    const page = await context.newPage();
    const external: string[] = [];
    page.on('request', request => { if (!request.url().startsWith('http://127.0.0.1:4321/')) external.push(request.url()); });
    for (const { kind, record } of storedGuidance) {
      const park = publicParks.find(park => park.code === record.park_code)!;
      const anchor = `entry-${kind}-${record.id}`;
      await page.goto(`/parks/${park.slug}/#${encodeURIComponent(anchor)}`);
      await expect(page).toHaveURL(`/parks/${park.slug}/#${encodeURIComponent(anchor)}`);
      const article = page.locator(`[id="${anchor}"]`);
      await expect(article).toHaveCount(1);
      await expect(article).toBeFocused();
      await expect(article).toBeInViewport();
      await page.keyboard.press('Tab');
      await expect(article.locator('summary')).toBeFocused();
      await page.keyboard.press('Enter');
      await expect(article.locator('blockquote')).toBeVisible();
      await expect(article.locator('blockquote')).toHaveText(record.evidence.excerpt);
      await expect(article.locator('code')).toHaveText(record.evidence.content_hash);
      await expect(article.getByRole('link', { name: 'Read the official source', exact: true })).toHaveAttribute('href', record.evidence.url);
      await expect(article.locator('time').first()).toHaveAttribute('datetime', record.reviewed_at);
      await expect(article.locator('time').first()).toHaveText(record.reviewed_at);
      if ('limitation' in record) await expect(article).toContainText(record.limitation);
      await expect(page.locator('#trip-context noscript')).toContainText('Interactive date checking requires JavaScript');
      await expect(page.getByRole('button', { name: 'Check entry guidance', exact: true })).toBeDisabled();
      await expect(page.locator('#decision-title')).toHaveText('Start with your visit date');
      await expect(page.locator('#decision-evidence')).toBeHidden();
      await expect(page.locator('[data-check]:checked')).toHaveCount(0);
    }
    expect(external).toEqual([]);
  } finally { await context.close(); }
});

test('source-specific correction navigation keeps exact public guidance and original clocks', async ({ page }) => {
  const rule = publicRules.find(rule => rule.park_code === 'romo' && rule.areas.includes('bear-lake'))!;
  const external: string[] = [];
  page.on('request', request => { if (!request.url().startsWith('http://127.0.0.1:4321/')) external.push(request.url()); });
  await page.goto('/parks/rocky-mountain/');
  await page.getByLabel('Visit date').fill('2027-06-01');
  await page.getByLabel('Arrival time').fill('08:37');
  await page.getByLabel('Planned area').selectOption('bear-lake');
  await page.locator('[data-check]').first().check();
  const link = page.locator(`[id="entry-rule-${rule.id}"] [data-correction-link]`);
  await link.focus();
  await page.keyboard.press('Enter');
  await expect(page).toHaveURL(`/corrections/?source=${encodeURIComponent(`rule:romo:${rule.id}`)}`);
  await expect(page.locator('#correction-source')).toBeVisible();
  await expect(page.locator('#correction-source-label')).toHaveText('Rocky Mountain · Dated entry guidance');
  await expect(page.locator('#correction-wording')).toHaveText(`${rule.summary}\n\n${rule.exception_note}`);
  await expect(page.locator('#correction-facts')).toContainText(rule.reviewed_at);
  await expect(page.locator('#correction-official-source')).toHaveAttribute('href', rule.evidence.url);
  const draft = new URL((await page.locator('#correction-draft').getAttribute('href'))!);
  expect(draft.origin).toBe('https://github.com');
  expect([...draft.searchParams.keys()]).toEqual(['title', 'body']);
  const body = draft.searchParams.get('body')!;
  expect(body).toContain(rule.reviewed_at);
  expect(body).toContain(`rule:romo:${rule.id}`);
  expect(body).toContain('https://vasuki8.github.io/us-national-park-trip-readiness-tracker/parks/rocky-mountain/');
  expect(body).not.toMatch(/2027-06-01|08:37|127\.0\.0\.1|data-check/);
  await page.locator('#correction-return').click();
  await expect(page).toHaveURL(`/parks/rocky-mountain/#${encodeURIComponent(`entry-rule-${rule.id}`)}`);
  await expect(page.locator(`[id="entry-rule-${rule.id}"] h3`)).toBeInViewport();
  expect(external).toEqual([]);
});

test('undated and retained notice corrections preserve their different source meaning', async ({ page }) => {
  const note = publicNotes.find(note => note.park_code === 'yell')!;
  await page.goto('/parks/yellowstone/');
  await page.locator(`[id="entry-note-${note.id}"] [data-correction-link]`).click();
  await expect(page.locator('#correction-source-label')).toHaveText('Yellowstone · Undated entry observation');
  await expect(page.locator('#correction-wording')).toContainText(note.limitation);
  await expect(page.locator('#correction-facts')).toContainText(note.reviewed_at);
  await expect(page.locator('#correction-facts')).not.toContainText('Effective from');
  const snapshot = publicParkSnapshots.find(snapshot => snapshot.park_code === 'yose')!;
  const notice = snapshot.records[0];
  await page.goto('/parks/yosemite/');
  await page.locator(`[id="alert-yose-${notice.id}"] [data-correction-link]`).click();
  await expect(page.locator('#correction-source-label')).toHaveText('Yosemite · Retained NPS notice');
  await expect(page.locator('#correction-wording')).toHaveText(`${notice.title}\n\n${notice.description}`);
  await expect(page.locator('#correction-facts')).toContainText(snapshot.last_successful_fetch_at!);
  if (notice.url) {
    await expect(page.locator('#correction-official-source')).toHaveText('Source link supplied by NPS');
    await expect(page.locator('#correction-official-source')).toHaveAttribute('href', notice.url);
  } else await expect(page.locator('#correction-missing-link')).toBeVisible();
  await page.setViewportSize({ width: 360, height: 800 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.locator('html').evaluate(element => { element.style.fontSize = '200%'; });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});

test('correction destinations suppress referrers and never forward unrelated query values', async ({ page }) => {
  const rule = publicRules.find(rule => rule.park_code === 'yose')!;
  const selected = `/corrections/?source=${encodeURIComponent(`rule:yose:${rule.id}`)}&date=PRIVATE_QUERY_MARKER`;
  const requests: { url: string; referer: string | undefined }[] = [];
  const capture = async (route: import('@playwright/test').Route) => {
    requests.push({ url: route.request().url(), referer: route.request().headers().referer });
    await route.fulfill({ status: 200, contentType: 'text/plain', body: 'Synthetic destination; no report submitted.' });
  };
  await page.route(rule.evidence.url, capture);
  await page.route('https://github.com/**', capture);
  await page.goto(selected);
  await page.locator('#correction-official-source').click();
  await expect(page).toHaveURL(rule.evidence.url);
  await page.goto(selected);
  await page.locator('#correction-draft').click();
  await expect(page).toHaveURL(/^https:\/\/github\.com\//);
  await page.goto('/corrections/?source=unknown&date=PRIVATE_QUERY_MARKER');
  await page.getByRole('link', { name: 'Open a correction on GitHub' }).click();
  await expect(page).toHaveURL('https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/issues/new');
  expect(requests).toHaveLength(3);
  for (const request of requests) {
    expect(request.referer).toBeUndefined();
    expect(request.url).not.toContain('PRIVATE_QUERY_MARKER');
  }
});

test('unknown, malformed and ambiguous references keep general reporting without reflecting query text', async ({ page }) => {
  const known = `rule:${publicRules[0].park_code}:${publicRules[0].id}`;
  for (const query of ['source=%3Cimg%20src=x%20onerror=alert(1)%3E&date=PRIVATE_TRIP_MARKER',
    `source=${encodeURIComponent(known)}&source=${encodeURIComponent(known)}`, 'source=%E0%A4%A', 'source=removed-record']) {
    await page.goto(`/corrections/?${query}`);
    await expect(page.locator('#correction-unavailable')).toBeVisible();
    await expect(page.locator('#correction-source')).toBeHidden();
    await expect(page.locator('main')).not.toContainText('PRIVATE_TRIP_MARKER');
    await expect(page.locator('main img')).toHaveCount(0);
    await expect(page.getByRole('link', { name: 'Open a correction on GitHub' })).toHaveAttribute('href', 'https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/issues/new');
  }
  await page.goto('/corrections/');
  await expect(page.locator('#correction-unavailable')).toBeHidden();
  await expect(page.locator('#correction-source')).toBeHidden();
});

test('source correction links and general reporting remain usable without JavaScript', async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  try {
    const page = await context.newPage();
    const rule = publicRules.find(rule => rule.park_code === 'yose')!;
    await page.goto('/parks/yosemite/');
    await page.locator(`[id="entry-rule-${rule.id}"] [data-correction-link]`).click();
    await expect(page.locator('#correction-source')).toBeHidden();
    await expect(page.locator('#correction-context noscript p')).toBeVisible();
    await expect(page.locator('#correction-context noscript p')).toContainText('Include the park page');
    await expect(page.getByRole('link', { name: 'Open a correction on GitHub' })).toBeVisible();
  } finally { await context.close(); }
});
