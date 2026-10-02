import { test, expect, type Page } from '@playwright/test';

const routes = ['/', '/parks/', ...['yosemite', 'rocky-mountain', 'yellowstone', 'zion', 'grand-canyon'].map((slug) => `/parks/${slug}/`),
  ...['how-it-works', 'sources', 'changes', 'about', 'privacy', 'terms', 'corrections'].map((slug) => `/${slug}/`)];
const parkRoutes = routes.filter((route) => route.startsWith('/parks/') && route !== '/parks/');

async function overflow(page: Page) {
  return page.evaluate(() => {
    const issues: string[] = [];
    if (document.documentElement.scrollWidth > innerWidth + 1) issues.push(`document:${document.documentElement.scrollWidth}>${innerWidth}`);
    // Check painted text too: hiding an overflowing heading must not make the test pass.
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    while (walker.nextNode()) {
      const text = walker.currentNode, element = text.parentElement!;
      if (!text.textContent?.trim() || element.closest('script,style,noscript,option,[aria-hidden="true"],.skip-link')) continue;
      if (getComputedStyle(element).visibility === 'hidden') continue;
      const range = document.createRange(); range.selectNodeContents(text);
      if ([...range.getClientRects()].some((r) => r.width > 0 && r.height > 0 && (r.left < -1 || r.right > innerWidth + 1))) {
        issues.push(`${element.tagName}.${element.className}:text outside viewport`);
      }
    }
    // Measure content children, not the deliberately clipped decorative ::after.
    for (const element of document.querySelectorAll<HTMLElement>('main input,main select,main button,main summary,.hero-note > *,.park-card h3 a,.notice-panel,.decision')) {
      if (element.getClientRects().length && element.clientWidth && element.scrollWidth > element.clientWidth + 1) issues.push(`${element.tagName}.${element.className}:clipped contents`);
    }
    return issues.slice(0, 15);
  });
}

for (const route of routes) {
  test(`reflow and 200% text retain content: ${route}`, async ({ page }, info) => {
    await page.emulateMedia({ reducedMotion: 'reduce' });
    await page.goto(route);
    await page.locator('details').evaluateAll((elements) => elements.forEach((element) => { (element as HTMLDetailsElement).open = true; }));
    const headings = await page.locator('main h1,main h2,main h3').allTextContents();
    const linkCount = await page.locator('main a:visible').count();
    for (const [width, enlarged] of [[320, false], [640, false], [1280, true], [360, true]] as const) {
      await page.setViewportSize({ width, height: 900 });
      await page.locator('html').evaluate((element, large) => { element.style.fontSize = large ? '200%' : ''; }, enlarged);
      await page.evaluate(() => window.scrollTo(0, 0));
      expect.soft(await overflow(page), `${route}, width=${width}, text=${enlarged ? '200%' : '100%'}`).toEqual([]);
      expect(await page.locator('main a:visible').count()).toBe(linkCount);
      for (const heading of await page.locator('main h1,main h2,main h3').all()) await expect(heading).toBeVisible();
    }
    expect(await page.locator('main h1,main h2,main h3').allTextContents()).toEqual(headings);
    if (['/', '/parks/yellowstone/', '/about/'].includes(route)) await page.screenshot({ path: info.outputPath('text-200-mobile.png'), fullPage: true });
  });

  test(`native skip link and evidence work without JavaScript: ${route}`, async ({ browser }) => {
    const context = await browser.newContext({ javaScriptEnabled: false, reducedMotion: 'reduce', viewport: { width: 640, height: 700 } });
    try {
      const page = await context.newPage(); await page.goto(`http://127.0.0.1:4321${route}`);
      await page.keyboard.press('Tab');
      const skip = page.getByRole('link', { name: 'Skip to content', exact: true });
      await expect(skip).toBeFocused(); await expect(skip).toBeInViewport();
      await page.keyboard.press('Enter');
      await expect(page.locator('main')).toBeFocused();
      const mainStops = page.locator('main a[href]:visible,main input:not(:disabled):visible,main select:not(:disabled):visible,main button:not(:disabled):visible,main summary:visible');
      const next = await mainStops.count() ? mainStops.first() : page.locator('.site-footer a').first();
      await page.keyboard.press('Tab');
      await expect(next).toBeFocused();
      const summaries = page.locator('main summary');
      if (await summaries.count()) {
        await summaries.first().focus(); await page.keyboard.press('Enter');
        await expect(page.locator('main details').first()).toHaveAttribute('open', '');
        await page.keyboard.press('Enter');
        await expect(page.locator('main details').first()).not.toHaveAttribute('open', '');
      }
      await expect(page.locator('main h1')).toBeVisible();
    } finally { await context.close(); }
  });
}

test('page landmarks, labels, IDs and current-page navigation are coherent across the site', async ({ page }) => {
  for (const route of routes) {
    await page.goto(route);
    await expect(page.locator('html')).toHaveAttribute('lang', 'en');
    await expect(page.locator('main')).toHaveCount(1); await expect(page.locator('h1')).toHaveCount(1);
    expect(await page.title()).not.toBe('');
    const errors = await page.evaluate(() => {
      const problems: string[] = [], ids = new Set<string>();
      document.querySelectorAll('[id]').forEach((element) => { if (ids.has(element.id)) problems.push('duplicate_id'); ids.add(element.id); });
      document.querySelectorAll<HTMLInputElement | HTMLSelectElement>('input,select').forEach((element) => {
        if (!element.labels?.length || ![...element.labels].some((label) => label.textContent?.trim())) problems.push(`missing_label:${element.id}`);
      });
      document.querySelectorAll('nav a[href]').forEach((element) => {
        const current = element.getAttribute('aria-current');
        const destination = new URL(element.getAttribute('href')!, location.href);
        // Fragment jumps identify sections, not the current page in site navigation.
        if (destination.hash) return;
        const isHere = destination.pathname === location.pathname;
        if (current === 'page' && !isHere) problems.push('wrong_current_page');
        if (isHere && current !== 'page') problems.push('missing_current_page');
      });
      if (document.querySelector('[tabindex]:not([tabindex="0"]):not([tabindex="-1"])')) problems.push('positive_tabindex');
      return problems;
    });
    expect.soft(errors, route).toEqual([]);
  }
});

test('visible enabled text meets the fixed light-theme contrast thresholds', async ({ page }) => {
  for (const route of routes) {
    await page.goto(route);
    await page.locator('details').evaluateAll((elements) => elements.forEach((element) => { (element as HTMLDetailsElement).open = true; }));
    const issues = await page.evaluate(() => {
      const rgb = (color: string) => color.match(/[\d.]+/g)!.slice(0, 3).map(Number);
      const luminance = (color: string) => rgb(color).map((v) => { v /= 255; return v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4; }).reduce((sum, v, i) => sum + v * [.2126, .7152, .0722][i], 0);
      const issues: string[] = [], walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
      while (walker.nextNode()) {
        const node = walker.currentNode, element = node.parentElement!;
        if (!node.textContent?.trim() || element.closest('script,style,noscript,option,[aria-hidden="true"],.skip-link,:disabled')) continue;
        const range = document.createRange(); range.selectNodeContents(node);
        if (![...range.getClientRects()].some((r) => r.width && r.height)) continue;
        const style = getComputedStyle(element); if (style.visibility === 'hidden') continue;
        let ancestor: Element | null = element;
        while (ancestor && getComputedStyle(ancestor).backgroundColor === 'rgba(0, 0, 0, 0)') ancestor = ancestor.parentElement;
        const background = ancestor ? getComputedStyle(ancestor).backgroundColor : 'rgb(255, 255, 255)';
        const foreground = luminance(style.color), backdrop = luminance(background);
        const ratio = (Math.max(foreground, backdrop) + .05) / (Math.min(foreground, backdrop) + .05);
        const minimum = parseFloat(style.fontSize) >= 24 || (parseFloat(style.fontWeight) >= 700 && parseFloat(style.fontSize) >= 18.667) ? 3 : 4.5;
        if (ratio < minimum) issues.push(`${element.tagName}.${element.className}: ${ratio.toFixed(2)} < ${minimum}`);
      }
      return [...new Set(issues)];
    });
    expect.soft(issues, route).toEqual([]);
  }
});

for (const route of parkRoutes) {
  test(`keyboard operates form, checklist and evidence with visible focus: ${route}`, async ({ page }) => {
    await page.emulateMedia({ reducedMotion: 'reduce' }); await page.goto(route);
    await page.locator('#trip-date').fill('2027-01-02');
    await page.locator('#trip-area').focus();
    await page.keyboard.press('Home'); await page.keyboard.press('ArrowDown');
    await page.keyboard.press('Tab'); await expect(page.locator('#special-case')).toBeFocused();
    await page.keyboard.press('Space'); await expect(page.locator('#special-case')).toBeChecked();
    await page.keyboard.press('Tab'); await expect(page.locator('#check-entry')).toBeFocused();
    const focusStyle = await page.locator('#check-entry').evaluate((element) => {
      const style = getComputedStyle(element), r = element.getBoundingClientRect();
      return { visible: element.matches(':focus-visible'), outline: parseFloat(style.outlineWidth), style: style.outlineStyle, within: r.top >= 0 && r.bottom <= innerHeight };
    });
    expect(focusStyle.visible).toBe(true); expect(focusStyle.outline).toBeGreaterThanOrEqual(2); expect(focusStyle.style).not.toBe('none'); expect(focusStyle.within).toBe(true);
    await page.keyboard.press('Enter'); await expect(page.locator('#entry-decision')).toHaveAttribute('role', 'status');
    const checkbox = page.locator('[data-check]').first(); await checkbox.focus(); await page.keyboard.press('Space'); await expect(checkbox).toBeChecked();
    await page.locator('#reset-checklist').focus(); await page.keyboard.press('Enter'); await expect(checkbox).not.toBeChecked();
    const summary = page.locator('main summary').first(); await summary.focus(); await page.keyboard.press('Enter');
    await expect(page.locator('main details').first()).toHaveAttribute('open', '');
  });
}

for (const route of ['/', '/parks/']) {
  test(`keyboard search and state filtering retain an announced empty state: ${route}`, async ({ page }) => {
    await page.goto(route); await page.locator('#park-search').focus(); await page.keyboard.type('unmatched-park');
    await expect(page.locator('#empty-search')).toBeVisible(); await expect(page.locator('#search-count')).toHaveAttribute('role', 'status');
    await page.keyboard.press('ControlOrMeta+A'); await page.keyboard.press('Backspace'); await page.keyboard.press('Tab');
    await expect(page.locator('#state-filter')).toBeFocused(); await page.keyboard.press('Home'); await page.keyboard.press('ArrowDown');
    await expect(page.locator('[data-park-card]:visible')).toHaveCount(1);
  });
}

test('reduced-motion preference disables animated scrolling', async ({ page }) => {
  await page.emulateMedia({ reducedMotion: 'reduce' }); await page.goto('/parks/yosemite/');
  expect(await page.locator('html').evaluate((element) => getComputedStyle(element).scrollBehavior)).toBe('auto');
});
