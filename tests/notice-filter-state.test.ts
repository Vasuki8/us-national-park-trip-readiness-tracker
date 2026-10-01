import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { runInNewContext } from 'node:vm';
import ts from 'typescript';

class Element extends EventTarget {
  value = '';
  hidden = false;
  id = '';
  dataset: Record<string, string> = {};
  textWrites: string[] = [];
  scrollCalls: { block: string }[] = [];
  private text = '';
  get textContent() { return this.text; }
  set textContent(value: string) { this.text = value; this.textWrites.push(value); }
  set innerHTML(_value: string) { throw new Error('Notice filtering must not interpret visitor text as HTML.'); }
  scrollIntoView(options: { block: string }) { this.scrollCalls.push(options); }
}

function scriptSource() {
  try { return readFileSync(new URL('../src/scripts/notices.ts', import.meta.url), 'utf8'); }
  catch (error) { if ((error as NodeJS.ErrnoException).code !== 'ENOENT') throw error; return ''; }
}

function noticePage({ query = '', category = '', hash = '' } = {}) {
  const search = new Element(); search.value = query;
  const select = new Element(); select.value = category;
  const clear = new Element();
  const controls = new Element(); controls.hidden = true;
  const count = new Element(); count.textContent = '3 retained notices shown'; count.textWrites = [];
  const empty = new Element(); empty.hidden = true;
  const records = [
    { id: 'alert-yose-A', text: 'Glacier Road closure\nTemporary closure for heavy snow.', category: 'Park Closure' },
    { id: 'alert-yose-B encoded /?&é', text: 'River   access\nCaution for bacteria.', category: 'Caution' },
    { id: 'alert-yose-C', text: 'Angels Landing Pilot Permit Program\nInformation about permits; literal [.*] and <img src=x>.', category: 'Information' },
  ];
  const cards = records.map((record) => {
    const card = new Element(); card.id = record.id;
    card.dataset = Object.freeze({ noticeText: record.text, noticeCategory: record.category,
      originalCheck: '2026-09-29T01:02:03.123456Z', originalSourceUpdate: 'Not supplied' });
    return card;
  });
  const selectors = new Map([
    ['[data-notice-search]', search], ['select[data-notice-category]', select], ['[data-notice-clear]', clear],
    ['[data-notice-controls]', controls], ['[data-notice-count]', count], ['[data-notice-empty]', empty],
  ]);
  const root = Object.assign(new Element(), {
    querySelector: (selector: string) => { assert.ok(selectors.has(selector), `Unexpected notice selector ${selector}`); return selectors.get(selector); },
    querySelectorAll: (selector: string) => { assert.equal(selector, '[data-retained-notice]'); return cards; },
  });
  const document = { querySelector: (selector: string) => { assert.equal(selector, '[data-retained-notices]'); return root; } };
  const queuedTasks: (() => void)[] = [];
  const location = { hash };
  const window = Object.assign(new EventTarget(), {
    location,
    setTimeout: (callback: () => void, delay: number) => { assert.equal(delay, 0); queuedTasks.push(callback); },
  });
  const forbidden = () => { throw new Error('Notice filtering cannot fetch, store selections or mutate URLs.'); };
  for (const api of ['localStorage', 'sessionStorage', 'indexedDB']) Object.defineProperty(window, api, { get: forbidden });
  Object.assign(window, { fetch: forbidden, history: { pushState: forbidden, replaceState: forbidden } });
  const before = JSON.stringify(cards.map(({ id, dataset }) => ({ id, dataset })));
  const script = ts.transpileModule(scriptSource(), {
    compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.CommonJS, alwaysStrict: true },
  }).outputText;
  runInNewContext(script, { document, window, fetch: forbidden });
  return {
    search, select, clear, controls, count, empty, cards, location, before,
    input: (value: string) => { search.value = value; search.dispatchEvent(new Event('input')); },
    category: (value: string) => { select.value = value; select.dispatchEvent(new Event('change')); },
    shown: () => records.filter((_, index) => !cards[index].hidden).map(({ id }) => id),
    showPage: () => window.dispatchEvent(new Event('pageshow')),
    flushTasks: () => queuedTasks.splice(0).forEach((callback) => callback()),
    changeHash: (value: string) => { location.hash = value; window.dispatchEvent(new Event('hashchange')); },
    print: () => { window.dispatchEvent(new Event('beforeprint')); window.dispatchEvent(new Event('afterprint')); },
    metadata: () => JSON.stringify(cards.map(({ id, dataset }) => ({ id, dataset }))),
  };
}

test('prefilled search normalizes case and repeated whitespace in the actual notice script', () => {
  const page = noticePage({ query: '  RIVER\t\n access  ' });
  assert.deepEqual(page.shown(), ['alert-yose-B encoded /?&é']);
  assert.equal(page.count.textContent, 'Showing 1 of 3 retained notices');
  assert.equal(page.controls.hidden, false); assert.equal(page.empty.hidden, true);
});

test('category and text filters combine while preserving the complete retained-feed denominator', () => {
  const page = noticePage({ category: 'Park Closure', query: 'closure' });
  assert.deepEqual(page.shown(), ['alert-yose-A']);
  page.category('Caution'); assert.deepEqual(page.shown(), []);
  assert.equal(page.count.textContent, 'Showing 0 of 3 retained notices'); assert.equal(page.empty.hidden, false);
  page.input('bacteria'); assert.deepEqual(page.shown(), ['alert-yose-B encoded /?&é']);
  assert.equal(page.count.textContent, 'Showing 1 of 3 retained notices'); assert.equal(page.empty.hidden, true);
});

test('provider categories remain exact choices and unknown categories do not imply a feed is empty', () => {
  const page = noticePage({ category: 'caution' });
  assert.deepEqual(page.shown(), []); assert.equal(page.empty.hidden, false);
  assert.equal(page.count.textContent, 'Showing 0 of 3 retained notices');
  page.category('Caution'); assert.deepEqual(page.shown(), ['alert-yose-B encoded /?&é']);
});

test('visitor queries remain literal substring text rather than HTML or regular expressions', () => {
  const page = noticePage({ query: '[.*]' }); assert.deepEqual(page.shown(), ['alert-yose-C']);
  page.input('<img src=x>'); assert.deepEqual(page.shown(), ['alert-yose-C']);
  page.input('<script>alert(1)</script>'); assert.deepEqual(page.shown(), []);
  assert.equal(page.count.textContent, 'Showing 0 of 3 retained notices');
});

test('unchanged counts avoid repeated live-region writes across equivalent queries and page returns', () => {
  const page = noticePage({ query: 'river' });
  assert.deepEqual(page.count.textWrites, ['Showing 1 of 3 retained notices']);
  page.input('  RIVER  '); page.category('Caution'); page.showPage(); page.flushTasks();
  assert.deepEqual(page.count.textWrites, ['Showing 1 of 3 retained notices']);
  page.input('not a match');
  assert.deepEqual(page.count.textWrites, ['Showing 1 of 3 retained notices', 'Showing 0 of 3 retained notices']);
});

test('the clear action resets both controls and restores every retained notice', () => {
  const page = noticePage({ query: 'missing', category: 'Park Closure' });
  assert.deepEqual(page.shown(), []);
  page.clear.dispatchEvent(new Event('click'));
  assert.equal(page.search.value, ''); assert.equal(page.select.value, '');
  assert.deepEqual(page.shown(), ['alert-yose-A', 'alert-yose-B encoded /?&é', 'alert-yose-C']);
  assert.equal(page.count.textContent, 'Showing 3 of 3 retained notices'); assert.equal(page.empty.hidden, true);
});

test('page returns queue reconciliation until controls restored after pageshow can be read', () => {
  const page = noticePage(); page.showPage();
  page.search.value = 'river'; page.select.value = 'Caution';
  assert.equal(page.shown().length, 3);
  page.flushTasks(); assert.deepEqual(page.shown(), ['alert-yose-B encoded /?&é']);
  assert.equal(page.count.textContent, 'Showing 1 of 3 retained notices');
});

test('initial exact encoded notice fragments reveal a target that prefilled filters would hide', () => {
  const page = noticePage({ query: 'glacier', category: 'Park Closure', hash: '#alert-yose-B%20encoded%20%2F%3F%26%C3%A9' });
  assert.equal(page.search.value, ''); assert.equal(page.select.value, ''); assert.equal(page.shown().length, 3);
  assert.equal(JSON.stringify(page.cards[1].scrollCalls), '[{"block":"start"}]');
  assert.equal(page.count.textContent, 'Showing 3 of 3 retained notices');
});

test('hash changes reveal only the exact hidden notice and leave ordinary filtering usable afterwards', () => {
  const page = noticePage({ query: 'glacier', category: 'Park Closure' });
  page.changeHash('#alert-yose-C');
  assert.equal(page.search.value, ''); assert.equal(page.select.value, '');
  assert.equal(page.cards[2].hidden, false); assert.equal(JSON.stringify(page.cards[2].scrollCalls), '[{"block":"start"}]');
  page.input('glacier'); assert.deepEqual(page.shown(), ['alert-yose-A']);
  assert.equal(page.search.value, 'glacier'); assert.equal(page.cards[2].scrollCalls.length, 1);
});

test('queued page returns reveal known notice fragments hidden by silently restored controls', () => {
  const page = noticePage({ hash: '#alert-yose-C' });
  assert.equal(page.cards[2].scrollCalls.length, 0);
  page.showPage(); page.search.value = 'glacier'; page.select.value = 'Park Closure';
  page.flushTasks(); assert.equal(page.search.value, ''); assert.equal(page.select.value, '');
  assert.equal(page.shown().length, 3); assert.equal(JSON.stringify(page.cards[2].scrollCalls), '[{"block":"start"}]');
});

test('unknown malformed and non-notice fragments retain current filtering and never scroll another section', () => {
  for (const hash of ['#missing-alert', '#alert-yose-C%ZZ', '#alert-yose-C%E0%A4%A', '#entry-rule-yose-rule', '#guidance-title', '#']) {
    const page = noticePage({ query: 'glacier', category: 'Park Closure', hash });
    assert.deepEqual(page.shown(), ['alert-yose-A'], hash);
    assert.equal(page.search.value, 'glacier'); assert.equal(page.select.value, 'Park Closure');
    page.changeHash(hash); page.showPage(); page.flushTasks();
    assert.deepEqual(page.shown(), ['alert-yose-A'], hash);
    assert.equal(page.cards.reduce((count, card) => count + card.scrollCalls.length, 0), 0, hash);
  }
});

test('already visible fragment targets do not reset useful filters or force scrolling', () => {
  const page = noticePage({ query: 'river', category: 'Caution', hash: '#alert-yose-B%20encoded%20%2F%3F%26%C3%A9' });
  assert.deepEqual(page.shown(), ['alert-yose-B encoded /?&é']); assert.equal(page.search.value, 'river');
  page.changeHash('#alert-yose-B%20encoded%20%2F%3F%26%C3%A9'); page.showPage(); page.flushTasks();
  assert.equal(page.cards[1].scrollCalls.length, 0); assert.equal(page.select.value, 'Caution');
});

test('filtering and print events preserve public source IDs/data/clocks and page-only choices', () => {
  const page = noticePage(); page.input('river'); page.category('Caution');
  assert.deepEqual(page.shown(), ['alert-yose-B encoded /?&é']);
  const hiddenBeforePrint = page.cards.map((card) => card.hidden);
  const countBeforePrint = page.count.textContent; page.print();
  assert.equal(page.search.value, 'river'); assert.equal(page.select.value, 'Caution');
  assert.deepEqual(page.cards.map((card) => card.hidden), hiddenBeforePrint); assert.equal(page.count.textContent, countBeforePrint);
  assert.equal(page.metadata(), page.before); assert.equal(page.location.hash, '');
});

test('pages without the retained-notice component remain untouched', () => {
  const script = ts.transpileModule(scriptSource(), { compilerOptions: { target: ts.ScriptTarget.ES2022 } }).outputText;
  runInNewContext(script, { document: { querySelector: (selector: string) => { assert.equal(selector, '[data-retained-notices]'); return null; } } });
});
