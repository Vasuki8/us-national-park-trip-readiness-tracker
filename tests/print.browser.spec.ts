import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { guidanceScenarioTime, PUBLIC_PILOT_STALE_TIME, publicParks, publicRules, publicParkSnapshots } from './pilot-clock.ts';

const resources: { park_code: string; category: string; url: string; link_reviewed_at: string }[] =
  JSON.parse(readFileSync(new URL('../data/planning-resources.json', import.meta.url), 'utf8')).resources;

test('printed park pages keep official destinations, link reviews and source clocks on every pilot', async ({ page }) => {
  await page.clock.setFixedTime(new Date(PUBLIC_PILOT_STALE_TIME));
  for (const park of publicParks) {
    await page.goto(`/parks/${park.slug}/`);
    await expect(page.locator('#print-snapshot')).toBeHidden();
    await expect(page.getByRole('button', { name: 'Print / save this page' })).toBeEnabled();
    await page.emulateMedia({ media: 'print' });
    await expect(page.locator('#print-snapshot')).toBeVisible();
    await expect(page.locator('#print-snapshot')).toContainText('Recheck official sources before travel');
    await expect(page.locator('.site-header')).toBeHidden();
    await expect(page.locator('.breadcrumb')).toBeHidden();
    await expect(page.locator('#print-page')).toBeHidden();
    await expect(page.locator('#reset-checklist')).toBeHidden();
    await expect(page.locator('#check-entry')).toBeHidden();
    await expect(page.locator('.checklist-actions')).toBeHidden();
    await expect(page.locator('.planning-grid')).toHaveCSS('grid-template-columns', /^[\d.]+px$/);

    for (const resource of resources.filter(item => item.park_code === park.code)) {
      const card = page.locator(`[data-planning-category="${resource.category}"]`);
      await expect(card).toBeVisible();
      await expect(card.locator('time')).toHaveText(resource.link_reviewed_at);
      await expect(card.locator('time')).toHaveAttribute('datetime', resource.link_reviewed_at);
      const link = card.getByRole('link');
      expect(await link.evaluate(el => getComputedStyle(el, '::after').content)).toContain(resource.url);
      expect(await link.evaluate(el => getComputedStyle(el, '::after').overflowWrap)).toBe('anywhere');
      expect(await card.evaluate(el => el.scrollWidth <= el.clientWidth)).toBe(true);
    }
    for (const link of await page.locator('#main a[href^="https://"]').all()) {
      expect(await link.evaluate(el => getComputedStyle(el, '::after').content)).toContain(await link.getAttribute('href'));
    }
    expect(await page.locator('.checklist-panel a[href="#official-checks"]').evaluate(el => getComputedStyle(el, '::after').content)).toBe('none');
    const snapshot = publicParkSnapshots.find(item => item.park_code === park.code)!;
    await expect(page.locator('#alert-status')).toContainText(snapshot.last_successful_fetch_at ?? 'Never');
    await expect(page.locator('#alert-status')).toContainText(snapshot.source_updated_at ?? 'Not supplied');
    await expect(page.locator('#notice-title')).toContainText('needs a fresh check');
    await expect(page.locator('[data-planning-resources]')).toContainText('not a conditions check');
    for (const checkbox of await page.locator('[data-check]').all()) await expect(checkbox).toBeVisible();
    await page.emulateMedia({ media: 'screen' });
  }
});

test('native printing refreshes an expired decision without replacing source dates or self-reported checks', async ({ page }) => {
  const rule = publicRules.find(item => item.park_code === 'yose')!;
  await page.clock.setFixedTime(new Date(guidanceScenarioTime([rule])));
  await page.goto('/parks/yosemite/');
  await page.getByLabel('Visit date').fill('2026-09-30');
  await page.getByLabel('Planned area').selectOption('general');
  await page.getByLabel('Arrival time').fill('08:00');
  await page.getByRole('button', { name: 'Check entry guidance' }).click();
  await page.locator('[data-check]').first().check();
  const originalReview = await page.locator(`#entry-rule-${rule.id} time`).first().getAttribute('datetime');
  const expiredAt = new Date(Date.parse(rule.reviewed_at) + 168 * 3_600_000 + 1).toISOString();
  await page.clock.setFixedTime(new Date(expiredAt));
  await page.evaluate(() => window.dispatchEvent(new Event('beforeprint')));
  await page.emulateMedia({ media: 'print' });
  await expect(page.locator('#entry-decision')).toHaveAttribute('data-state', 'stale');
  await expect(page.locator(`#entry-rule-${rule.id} .review-status`)).toContainText('Needs a fresh review');
  await expect(page.locator(`#entry-rule-${rule.id} time`).first()).toHaveAttribute('datetime', originalReview!);
  await expect(page.locator('#print-time')).toHaveText(expiredAt);
  await expect(page.locator('#print-time')).toHaveAttribute('datetime', expiredAt);
  await expect(page.locator('#print-snapshot')).toContainText('not a source check');
  await expect(page.locator('[data-check]').first()).toBeChecked();
  await expect(page.locator('#checklist-progress')).toHaveText('1 of 5 items reviewed by you');
  await expect(page.locator('.source-panel details').first()).not.toHaveAttribute('open');
});

test('printing unsubmitted undated guidance preserves uncertainty and does not mark checklist items', async ({ page }) => {
  await page.clock.setFixedTime(new Date(PUBLIC_PILOT_STALE_TIME));
  await page.goto('/parks/yellowstone/');
  await page.getByLabel('Visit date').fill('2026-10-01');
  await page.evaluate(() => window.dispatchEvent(new Event('beforeprint')));
  await page.emulateMedia({ media: 'print' });
  await expect(page.locator('#entry-decision')).toHaveAttribute('data-state', 'needs-input');
  await expect(page.locator('#decision-evidence')).toBeHidden();
  await expect(page.locator('.source-panel')).toContainText('Undated source review');
  await expect(page.locator('[data-undated-guidance]')).toContainText('not a determination for your travel dates');
  await expect(page.locator('#checklist-progress')).toHaveText('0 of 5 items reviewed by you');
  for (const checkbox of await page.locator('[data-check]').all()) await expect(checkbox).not.toBeChecked();
});

test('without JavaScript browser-menu printing preserves static provenance and discloses unrecalculated freshness', async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  try {
    const page = await context.newPage();
    await page.goto('/parks/yosemite/');
    await expect(page.locator('#print-page')).toBeDisabled();
    // Playwright text selectors intentionally skip noscript subtrees.
    const fallback = page.locator('.checklist-panel noscript p');
    await expect(fallback).toBeVisible();
    await expect(fallback).toHaveText('Without JavaScript, use your browser’s print menu.');
    await page.emulateMedia({ media: 'print' });
    await expect(page.locator('#print-snapshot')).toBeVisible();
    await expect(page.locator('#print-snapshot')).toContainText('self-reported checks do not verify bookings or conditions');
    const freshnessNotice = page.locator('#print-snapshot noscript p');
    await expect(freshnessNotice).toBeVisible();
    await expect(freshnessNotice).toContainText('Freshness is not recalculated without JavaScript');
    await expect(page.locator('#print-time')).toHaveText('Print time not recorded');
    await expect(page.locator('#print-time')).not.toHaveAttribute('datetime');
    await expect(page.locator('#entry-decision')).toHaveAttribute('data-state', 'needs-input');
    await expect(page.locator('[data-planning-resources]')).toContainText('not an NPS update');
    for (const resource of resources.filter(item => item.park_code === 'yose')) {
      const card = page.locator(`[data-planning-category="${resource.category}"]`);
      expect(await card.getByRole('link').evaluate(el => getComputedStyle(el, '::after').content)).toContain(resource.url);
      await expect(card.locator('time')).toHaveAttribute('datetime', resource.link_reviewed_at);
    }
    for (const checkbox of await page.locator('[data-check]').all()) {
      await expect(checkbox).toBeVisible();
      await expect(checkbox).toBeDisabled();
      await expect(checkbox).not.toBeChecked();
    }
  } finally {
    await context.close();
  }
});
