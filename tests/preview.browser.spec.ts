import { test, expect } from '@playwright/test';
import { PUBLIC_PILOT_FRESH_TIME, publicParkSnapshots, publicParks } from './pilot-clock.ts';
const url='http://127.0.0.1:4323/';
test('real candidate bundle builds five separately labeled park previews',async({page})=>{
  await page.clock.install({time:new Date('2026-09-28T13:00:00Z')});await page.goto(url);
  await expect(page.getByRole('heading',{name:'Private candidate preview',exact:true})).toBeVisible();
  await expect(page.locator('[data-preview-banner]')).toContainText('Not published');
  await expect(page.locator('[data-preview-park]')).toHaveCount(5);
  await expect(page.locator('[data-preview-park="yose"] [data-current-record]')).toHaveCount(1);
  const unlinked=page.locator('[data-preview-park="yose"] [data-current-record]');
  await expect(unlinked).toContainText('NPS did not supply a direct link for this alert.');
  await expect(unlinked.locator('a')).toHaveCount(0);
  const supplied=page.locator('[data-preview-park="romo"] [data-current-record]').getByRole('link',{name:'More information link supplied by NPS'});
  await expect(supplied).toHaveAttribute('href','https://www.nps.gov/romo/test.htm');
  await expect(supplied).toHaveAttribute('rel','noopener noreferrer');
  await expect(supplied).toHaveAttribute('referrerpolicy','no-referrer');
  await expect(page.locator('[data-preview-park="yose"] [data-history-observation]')).toHaveCount(2);
  await expect(page.locator('[data-preview-park="grca"] [data-history-status]')).toHaveText('History not collected');
  await expect(page.locator('meta[name="robots"]')).toHaveAttribute('content','noindex, nofollow');
});
test('failed and quarantined candidates retain original successful-check times',async({page})=>{
  await page.clock.install({time:new Date('2026-09-28T13:00:00Z')});await page.goto(url);
  for(const code of ['romo','yell']){
    const park=page.locator(`[data-preview-park="${code}"]`);
    await expect(park.locator('[data-history-status]')).toHaveText('The latest check was not successful');
    await expect(park.locator('[data-current-record]')).toHaveCount(1);
    await expect(park).toContainText('2026-09-28T10:00:00Z');
  }
  await expect(page.locator('[data-preview-park="yell"]')).toContainText('Check requires review');
});
test('preview metadata matches page bundle identity and excludes private state',async({page,request})=>{
  await page.goto(url);const response=await request.get(url+'preview.json');expect(response.ok()).toBe(true);
  const data=await response.json();expect(data.publication_performed).toBe(false);expect(data.parks).toHaveLength(5);
  await expect(page.locator('[data-preview-id]')).toHaveText(data.bundle_id);
  const text=await page.content();for(const forbidden of ['PREVIEW_PENDING_SENTINEL','record_refs','private_path'])expect(text).not.toContain(forbidden);
  await expect(page.locator('[data-preview-park="yose"]')).toContainText('not a confirmed reopening');
});
test('candidate source markup stays text and evidence remains usable without JavaScript',async({browser,page})=>{
  await page.goto(url);expect(await page.evaluate(()=>(window as any).previewInjected)).toBeUndefined();
  const context=await browser.newContext({javaScriptEnabled:false});const plain=await context.newPage();await plain.goto(url);
  const detail=plain.locator('[data-preview-park="yose"] details').first();await detail.locator('summary').click();
  await expect(detail.getByRole('link',{name:'More information link supplied by NPS'}).first()).toBeVisible();
  await expect(plain.locator('[data-preview-park="yose"] noscript p')).toBeVisible();await context.close();
});
test('candidate preview fits a 360px screen with expanded evidence',async({page})=>{
  await page.setViewportSize({width:360,height:800});await page.goto(url);
  for(const summary of await page.locator('details summary').all())await summary.click();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
});
test('production build retains public baselines and does not expose candidate routes or notices',async({page,request})=>{
  await page.clock.setFixedTime(new Date(PUBLIC_PILOT_FRESH_TIME));
  await page.goto('/changes/');await expect(page.locator('[data-history-observation]')).toHaveCount(5);
  await expect(page.getByText('Baseline recorded',{exact:true})).toHaveCount(5);
  expect(await page.content()).not.toContain('Preview-only synthetic notice');
  for(const park of publicParks){
    await page.goto(`/parks/${park.slug}/`);
    expect(JSON.parse((await page.locator('#alert-status').getAttribute('data-snapshot'))!)).toEqual(publicParkSnapshots.find((snapshot)=>snapshot.park_code===park.code));
    await expect(page.locator('[data-preview-banner],[data-preview-park]')).toHaveCount(0);
    const html=await page.content();
    for(const forbidden of ['Preview-only synthetic notice','previewInjected','PREVIEW_PENDING_SENTINEL'])expect(html).not.toContain(forbidden);
  }
  expect((await request.get('http://127.0.0.1:4321/preview.json')).status()).toBe(404);
});
