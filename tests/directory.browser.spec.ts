import { test, expect } from '@playwright/test';

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
