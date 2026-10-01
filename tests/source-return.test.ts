import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { runInNewContext } from 'node:vm';
import ts from 'typescript';
import * as coverage from '../src/lib/source-coverage.ts';
import * as history from '../src/lib/history.ts';

const checked = '2026-09-28T12:00:00Z';
const later = '2026-09-28T13:00:00Z';
const snapshot = (code: string, overrides = {}) => ({
  park_code: code, collection_status: 'success', coverage_status: 'checked_feed_only',
  last_checked_at: checked, last_successful_fetch_at: checked, ...overrides,
});
const review = (code: string, reviewed_at = checked) => ({ park_code: code, review_status: 'reviewed', reviewed_at });

class Element {
  dataset: Record<string, string> = {};
  children = new Map<string, Element[]>();
  writes = 0;
  private text = '';
  get textContent() { return this.text; }
  set textContent(value: string) { this.text = value; this.writes++; }
  querySelectorAll(selector: string) { return this.children.get(selector) ?? []; }
  querySelector(selector: string) { return this.querySelectorAll(selector)[0] ?? null; }
}

function coverageRoot(input: coverage.CoverageInput) {
  const root = new Element(); root.dataset.coverage = JSON.stringify(input);
  const metrics = new Map(['storedReviewParks', 'datedRuleParks', 'reviewWithinWindowParks', 'recentAlertParks'].map((key) => {
    const element = new Element(); element.dataset.coverageMetric = key; return [key, element];
  }));
  const entries = new Map(input.parks.map(({ code }) => {
    const element = new Element(); element.dataset.entryLabel = code; return [code, element];
  }));
  const alerts = new Map(input.parks.map(({ code }) => {
    const element = new Element(); element.dataset.alertLabel = code; return [code, element];
  }));
  root.children.set('[data-coverage-metric]', [...metrics.values()]);
  root.children.set('[data-entry-label]', [...entries.values()]);
  root.children.set('[data-alert-label]', [...alerts.values()]);
  root.children.set('[data-entry-label], [data-alert-label]', [...entries.values(), ...alerts.values()]);
  return { root, metrics, entries, alerts };
}

// Execute both actual scripts and real clock-injected copy functions. Timers are held;
// pageshow is the only refresh signal, independent of browser restoration policy.
function sourcePage(inputs: coverage.CoverageInput[] = [], metadata: (history.HistoryMetadata | string)[] = []) {
  let now = Date.parse(later);
  const roots = inputs.map(coverageRoot);
  const timelines = metadata.map((value) => {
    const root = new Element(); root.dataset.historyMetadata = typeof value === 'string' ? value : JSON.stringify(value);
    const title = new Element(), detail = new Element();
    root.children.set('[data-history-status]', [title]); root.children.set('[data-history-detail]', [detail]);
    return { root, title, detail };
  });
  const document = Object.assign(new EventTarget(), {
    hidden: false,
    querySelectorAll: (selector: string) => {
      if (selector === '[data-coverage]') return roots.map(({ root }) => root);
      assert.equal(selector, '[data-history]'); return timelines.map(({ root }) => root);
    },
  });
  const window = Object.assign(new EventTarget(), {
    setInterval: (_callback: () => void, delay: number) => { assert.equal(delay, 60_000); },
  });
  for (const [name, dependency] of [['coverage', coverage], ['history', history]] as const) {
    const source = ts.transpileModule(readFileSync(new URL(`../src/scripts/${name}.ts`, import.meta.url), 'utf8'), {
      compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.CommonJS },
    }).outputText;
    runInNewContext(source, {
      document, window, exports: {}, Date: class extends Date { constructor() { super(now); } },
      require: (specifier: string) => { assert.equal(specifier, `../lib/${name === 'coverage' ? 'source-coverage' : 'history'}`); return dependency; },
    });
  }
  return {
    roots, timelines,
    setTime: (time: string) => { now = Date.parse(time); },
    showPage: (persisted = true) => window.dispatchEvent(Object.assign(new Event('pageshow'), { persisted })),
  };
}

const input = (overrides = {}): coverage.CoverageInput => ({ parks: [{ code: 'early' }, { code: 'later' }], rules: [], notes: [], snapshots: [], ...overrides });

test('page return expires each alert feed independently after the exact four-hour boundary', () => {
  const value = input({ snapshots: [snapshot('early'), snapshot('later', { last_checked_at: later, last_successful_fetch_at: later })] });
  const before = JSON.stringify(value), page = sourcePage([value]), view = page.roots[0];
  assert.equal(view.metrics.get('recentAlertParks')!.textContent, '02');
  page.setTime('2026-09-28T16:00:00Z'); page.showPage();
  assert.equal(view.alerts.get('early')!.textContent, 'Alert feed checked');
  page.setTime('2026-09-28T16:00:00.001Z'); page.showPage();
  assert.equal(view.alerts.get('early')!.textContent, 'Alert check needs refreshing');
  assert.equal(view.alerts.get('later')!.textContent, 'Alert feed checked');
  assert.equal(view.metrics.get('recentAlertParks')!.textContent, '01');
  assert.equal(view.root.dataset.coverage, before);
});

test('page return expires source reviews without removing stored or dated guidance', () => {
  const value = input({ rules: [review('early')], notes: [review('later', later)] });
  const before = JSON.stringify(value), page = sourcePage([value]), view = page.roots[0];
  page.setTime('2026-10-05T12:00:00Z'); page.showPage();
  assert.equal(view.entries.get('early')!.textContent, 'Dated rules stored');
  page.setTime('2026-10-05T12:00:00.001Z'); page.showPage(false);
  assert.equal(view.entries.get('early')!.textContent, 'Source review needs refreshing');
  assert.equal(view.entries.get('later')!.textContent, 'Undated source review');
  assert.equal(view.metrics.get('reviewWithinWindowParks')!.textContent, '01');
  assert.equal(view.metrics.get('storedReviewParks')!.textContent, '02');
  assert.equal(view.metrics.get('datedRuleParks')!.textContent, '01');
  assert.equal(view.root.dataset.coverage, before);
});

test('page return expires history at its own successful-check clock without changing metadata', () => {
  const page = sourcePage([], [snapshot('early'), snapshot('later', { last_checked_at: later, last_successful_fetch_at: later })]);
  const before = page.timelines.map(({ root }) => root.dataset.historyMetadata);
  page.setTime('2026-09-28T16:00:00Z'); page.showPage();
  assert.equal(page.timelines[0].title.textContent, 'Recent feed check; coverage remains limited');
  page.setTime('2026-09-28T16:00:00.001Z'); page.showPage(false);
  assert.equal(page.timelines[0].title.textContent, 'History needs a fresh check');
  assert.equal(page.timelines[1].title.textContent, 'Recent feed check; coverage remains limited');
  assert.match(page.timelines[0].detail.textContent, /historical, not current conditions/);
  assert.deepEqual(page.timelines.map(({ root }) => root.dataset.historyMetadata), before);
});

test('coverage return retains degraded and missing feeds and clears labels if metadata is damaged', () => {
  const codes = ['missing', 'null-clock', 'failed', 'quarantined', 'future'];
  const value = input({ parks: codes.map((code) => ({ code })), snapshots: [
    snapshot('null-clock', { last_successful_fetch_at: null }), snapshot('failed', { collection_status: 'failed' }),
    snapshot('quarantined', { collection_status: 'quarantined' }), snapshot('future', { last_successful_fetch_at: '2026-09-30T12:00:00Z' }),
  ] });
  const page = sourcePage([value, input({ rules: [review('early')], snapshots: [snapshot('early')] })]);
  page.roots[1].root.dataset.coverage = '{';
  page.setTime('2026-09-28T16:00:00.001Z'); page.showPage();
  assert.deepEqual([...page.roots[0].alerts.values()].map((element) => element.textContent), [
    'Alerts not collected', 'Alert check needs refreshing', 'Latest alert check failed', 'Alert feed needs review', 'Alert check needs refreshing',
  ]);
  assert.equal(page.roots[0].metrics.get('recentAlertParks')!.textContent, '00');
  assert.equal(page.roots[1].metrics.get('recentAlertParks')!.textContent, 'Unknown');
  assert.equal(page.roots[1].entries.get('early')!.textContent, 'Source data unavailable');
  assert.equal(page.roots[1].alerts.get('early')!.textContent, 'Source data unavailable');
});

test('history return cannot make missing, failed, quarantined, future or damaged evidence current', () => {
  const page = sourcePage([], [
    snapshot('fresh'), snapshot('missing', { collection_status: 'never_checked', last_checked_at: null, last_successful_fetch_at: null }),
    snapshot('null-clock', { last_successful_fetch_at: null }), snapshot('failed', { collection_status: 'failed' }),
    snapshot('quarantined', { collection_status: 'quarantined' }), snapshot('future', { last_successful_fetch_at: '2026-09-30T12:00:00Z' }), '{', '{}',
  ]);
  const before = page.timelines.map(({ root }) => root.dataset.historyMetadata);
  page.setTime('2026-09-28T16:00:00.001Z'); page.showPage();
  assert.deepEqual(page.timelines.map(({ title }) => title.textContent), [
    'History needs a fresh check', 'History not collected', 'History needs a fresh check',
    'The latest check was not successful', 'The latest check was not successful', 'History needs a fresh check',
    'The latest check was not successful', 'The latest check was not successful',
  ]);
  assert.deepEqual(page.timelines.map(({ root }) => root.dataset.historyMetadata), before);
});

test('unchanged history returns do not rewrite live text before or after expiry', () => {
  const page = sourcePage([], [snapshot('early')]), view = page.timelines[0];
  page.showPage(); page.showPage(false);
  page.setTime('2026-09-28T16:00:00Z'); page.showPage();
  assert.deepEqual([view.title.writes, view.detail.writes], [1, 1]);
  page.setTime('2026-09-28T16:00:00.001Z'); page.showPage();
  assert.deepEqual([view.title.writes, view.detail.writes], [2, 2]);
  page.showPage(); page.showPage(false);
  assert.deepEqual([view.title.writes, view.detail.writes], [2, 2]);
});
