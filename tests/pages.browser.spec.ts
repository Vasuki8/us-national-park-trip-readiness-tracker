import { test, expect } from '@playwright/test';
import { guidanceScenarioTime, publicRules } from './pilot-clock.ts';
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
