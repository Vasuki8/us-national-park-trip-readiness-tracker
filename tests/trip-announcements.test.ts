import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { runInNewContext } from 'node:vm';
import ts from 'typescript';
import * as readiness from '../src/lib/readiness.ts';

const rule: readiness.Rule = {
  id: 'synthetic-entry', park_code: 'test', areas: ['*'],
  effective_from: '2026-01-01', effective_to: '2026-12-31',
  start_time: null, end_time: null, requirement: 'no_timed_entry',
  reviewed_at: '2026-09-28T19:00:00Z', review_status: 'reviewed',
  summary: 'Synthetic rule', exception_note: 'Check official exceptions.',
  evidence: {
    url: 'https://www.nps.gov/test/index.htm', excerpt: 'Synthetic evidence.',
    content_hash: '0'.repeat(64), hash_scope: 'excerpt', reviewed_at: '2026-09-28T19:00:00Z',
    source_updated_at: null, method: 'manual_official_page_review',
  },
};

// Execute the browser script and real decision layer; only DOM and clock APIs are substituted.
class Element extends EventTarget {
  value = ''; checked = false; disabled = true;
  dataset: Record<string, string> = {};
  textWrites: string[] = [];
  private text = '';
  get textContent() { return this.text; }
  set textContent(value: string) { this.text = value; this.textWrites.push(value); }
}

function tripPage() {
  let now = Date.parse('2026-09-28T20:00:00Z');
  let minuteRefresh: (() => void) | undefined;
  const selectors = ['trip-context', 'trip-form', 'trip-date', 'trip-time', 'trip-area', 'special-case',
    'check-entry', 'reset-checklist', 'decision-title', 'decision-detail', 'entry-decision', 'checklist-progress'];
  const elements = new Map(selectors.map((id) => [`#${id}`, new Element()]));
  const element = (selector: string) => {
    const result = elements.get(selector);
    assert.ok(result, `expected page element ${selector}`);
    return result;
  };
  element('#trip-context').dataset = { rules: JSON.stringify([rule]), park: 'test', timezone: 'America/Los_Angeles' };
  element('#trip-date').value = '2026-09-29';
  const checks = Array.from({ length: 5 }, () => new Element());
  const review = new Element(); review.dataset.reviewed = rule.reviewed_at;
  const document = Object.assign(new EventTarget(), {
    hidden: false,
    querySelector: (selector: string) => selector === '#alert-status' ? null : element(selector),
    querySelectorAll: (selector: string) => {
      if (selector === '[data-check]') return checks;
      assert.equal(selector, '[data-reviewed]');
      return [review];
    },
  });
  const source = ts.transpileModule(readFileSync(new URL('../src/scripts/trip.ts', import.meta.url), 'utf8'), {
    compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.CommonJS },
  }).outputText;
  runInNewContext(source, {
    document, exports: {},
    require: (specifier: string) => { assert.equal(specifier, '../lib/readiness'); return readiness; },
    Date: class extends Date { constructor() { super(now); } },
    window: { setInterval: (callback: () => void, delay: number) => { assert.equal(delay, 60_000); minuteRefresh = callback; } },
  });
  return {
    element, checks, review,
    setTime: (time: string) => { now = Date.parse(time); },
    submit: () => element('#trip-form').dispatchEvent(new Event('submit', { cancelable: true })),
    refreshMinute: () => { assert.ok(minuteRefresh); minuteRefresh(); },
    changeVisibility: (hidden: boolean) => { document.hidden = hidden; document.dispatchEvent(new Event('visibilitychange')); },
    decisionWrites: () => [element('#decision-title').textWrites.length, element('#decision-detail').textWrites.length],
  };
}

test('unchanged entry guidance does not rewrite its live-region text on minute or visibility refreshes', () => {
  const page = tripPage();
  page.submit();
  assert.equal(page.element('#decision-title').textContent, 'No timed entry under this reviewed rule');
  assert.equal(page.element('#entry-decision').dataset.state, 'not-required-under-rule');
  assert.deepEqual(page.decisionWrites(), [1, 1], 'the submitted decision is displayed');
  page.checks[0].checked = true;
  page.checks[0].dispatchEvent(new Event('change'));
  page.setTime('2026-09-28T20:01:00Z');
  page.refreshMinute();
  assert.deepEqual(page.decisionWrites(), [1, 1], 'a minute without a decision change creates no text replacements');
  page.changeVisibility(true);
  page.changeVisibility(false);
  assert.deepEqual(page.decisionWrites(), [1, 1], 'returning to the page keeps identical decision text');
  assert.equal(page.checks[0].checked, true, 'clock refreshes preserve the visitor checklist');
});

test('seven-day expiry still updates the decision once and trip changes still reset the checklist', () => {
  const page = tripPage();
  page.submit();
  page.setTime('2026-10-05T19:00:00Z');
  page.refreshMinute();
  assert.equal(page.element('#entry-decision').dataset.state, 'not-required-under-rule', 'the exact boundary remains fresh');
  assert.deepEqual(page.decisionWrites(), [1, 1]);
  page.setTime('2026-10-05T19:00:00.001Z');
  page.changeVisibility(false);
  assert.equal(page.element('#entry-decision').dataset.state, 'stale');
  assert.equal(page.element('#decision-title').textContent, 'Entry guidance needs a fresh review');
  assert.match(page.element('#decision-detail').textContent, /no current conclusion/);
  assert.deepEqual(page.decisionWrites(), [2, 2], 'changed guidance replaces both pieces of decision text');
  assert.match(page.review.textContent, /Needs a fresh review/);
  page.refreshMinute();
  assert.deepEqual(page.decisionWrites(), [2, 2], 'the unchanged stale decision is not rewritten');
  page.checks[0].checked = true;
  page.element('#trip-date').value = '2027-06-01';
  page.element('#trip-form').dispatchEvent(new Event('input'));
  assert.equal(page.element('#entry-decision').dataset.state, 'not-verified', 'another year receives no exemption');
  assert.equal(page.checks[0].checked, false);
  assert.equal(page.element('#checklist-progress').textContent, '0 of 5 items reviewed by you');
});
