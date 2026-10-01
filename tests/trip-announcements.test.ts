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
  value = ''; href = ''; hidden = false; checked = false; disabled = true;
  dataset: Record<string, string> = {};
  textWrites: string[] = [];
  private text = '';
  get textContent() { return this.text; }
  set textContent(value: string) { this.text = value; this.textWrites.push(value); }
}

function tripPage(rules: readiness.Rule[] = [rule]) {
  let now = Date.parse('2026-09-28T20:00:00Z');
  let minuteRefresh: (() => void) | undefined;
  const selectors = ['trip-context', 'trip-form', 'trip-date', 'trip-time', 'trip-area', 'special-case',
    'check-entry', 'reset-checklist', 'decision-title', 'decision-detail', 'entry-decision', 'checklist-progress', 'decision-evidence'];
  const elements = new Map(selectors.map((id) => [`#${id}`, new Element()]));
  const element = (selector: string) => {
    const result = elements.get(selector);
    assert.ok(result, `expected page element ${selector}`);
    return result;
  };
  element('#trip-context').dataset = { rules: JSON.stringify(rules), park: 'test', timezone: 'America/Los_Angeles' };
  element('#trip-date').value = '2026-09-29';
  element('#decision-evidence').hidden = true;
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
  const queuedTasks: (() => void)[] = [];
  const window = Object.assign(new EventTarget(), {
    setInterval: (callback: () => void, delay: number) => { assert.equal(delay, 60_000); minuteRefresh = callback; },
    setTimeout: (callback: () => void, delay: number) => { assert.equal(delay, 0); queuedTasks.push(callback); },
  });
  const source = ts.transpileModule(readFileSync(new URL('../src/scripts/trip.ts', import.meta.url), 'utf8'), {
    compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.CommonJS },
  }).outputText;
  runInNewContext(source, {
    document, exports: {},
    require: (specifier: string) => { assert.equal(specifier, '../lib/readiness'); return readiness; },
    Date: class extends Date { constructor() { super(now); } },
    window,
  });
  return {
    element, checks, review,
    setTime: (time: string) => { now = Date.parse(time); },
    submit: () => element('#trip-form').dispatchEvent(new Event('submit', { cancelable: true })),
    refreshMinute: () => { assert.ok(minuteRefresh); minuteRefresh(); },
    changeVisibility: (hidden: boolean) => { document.hidden = hidden; document.dispatchEvent(new Event('visibilitychange')); },
    decisionWrites: () => [element('#decision-title').textWrites.length, element('#decision-detail').textWrites.length],
    showPage: (persisted: boolean) => window.dispatchEvent(Object.assign(new Event('pageshow'), { persisted })),
    flushTasks: () => queuedTasks.splice(0).forEach((callback) => callback()),
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

test('page return reads trip details restored after pageshow and resets the old checklist', () => {
  const page = tripPage();
  page.submit();
  page.checks.forEach((check) => { check.checked = true; });
  page.checks[0].dispatchEvent(new Event('change'));
  assert.match(page.element('#checklist-progress').textContent, /checklist is complete/);
  page.showPage(true);
  page.element('#trip-date').value = '2027-06-01';
  page.flushTasks();
  assert.equal(page.element('#entry-decision').dataset.state, 'not-verified');
  assert.equal(page.element('#decision-title').textContent, 'Entry requirements not verified for this date');
  assert.equal(page.checks.some((check) => check.checked), false);
  assert.equal(page.element('#checklist-progress').textContent, '0 of 5 items reviewed by you');
});

test('every silently changed trip field invalidates checklist completion on page return', () => {
  for (const [selector, property, value] of [
    ['#trip-date', 'value', '2026-09-30'],
    ['#trip-time', 'value', '08:00'],
    ['#trip-area', 'value', 'another-area'],
    ['#special-case', 'checked', true],
  ] as const) {
    const page = tripPage();
    page.submit();
    page.checks[0].checked = true;
    page.checks[0].dispatchEvent(new Event('change'));
    page.showPage(true);
    const field = page.element(selector);
    if (property === 'checked') field.checked = value as boolean;
    else field.value = value as string;
    page.flushTasks();
    assert.equal(page.checks[0].checked, false, selector);
    assert.equal(page.element('#checklist-progress').textContent, '0 of 5 items reviewed by you', selector);
    if (selector === '#special-case') assert.equal(page.element('#decision-title').textContent, 'Check the rules for your circumstances');
  }
});

test('unchanged persisted returns preserve checks and synchronize restored progress without repeat announcements', () => {
  const page = tripPage();
  page.submit();
  page.showPage(true);
  // Checkbox restoration need not dispatch change events.
  page.checks[0].checked = true;
  page.checks[1].checked = true;
  page.flushTasks();
  assert.equal(page.checks.filter((check) => check.checked).length, 2);
  const progress = page.element('#checklist-progress');
  assert.equal(progress.textContent, '2 of 5 items reviewed by you');
  const writes = progress.textWrites.length;
  const decisionWrites = page.decisionWrites();
  page.showPage(true); page.flushTasks();
  assert.equal(progress.textWrites.length, writes);
  assert.deepEqual(page.decisionWrites(), decisionWrites);
});

test('fresh page returns clear browser-restored checklist checks without evaluating an unsubmitted trip', () => {
  const page = tripPage();
  page.showPage(false);
  page.element('#trip-date').value = '2027-06-01';
  page.checks.forEach((check) => { check.checked = true; });
  page.flushTasks();
  assert.equal(page.checks.some((check) => check.checked), false);
  assert.equal(page.element('#checklist-progress').textContent, '0 of 5 items reviewed by you');
  assert.deepEqual(page.decisionWrites(), [0, 0]);
  page.submit();
  assert.equal(page.element('#entry-decision').dataset.state, 'not-verified');
});

test('a persisted page return refreshes expired guidance immediately and preserves an unchanged trip checklist', () => {
  const page = tripPage();
  page.submit();
  page.checks[0].checked = true;
  page.checks[0].dispatchEvent(new Event('change'));
  page.setTime('2026-10-05T19:00:00.001Z');
  page.showPage(true); page.flushTasks();
  assert.equal(page.element('#entry-decision').dataset.state, 'stale');
  assert.match(page.review.textContent, /Needs a fresh review/);
  assert.equal(page.checks[0].checked, true);
  assert.equal(page.element('#checklist-progress').textContent, '1 of 5 items reviewed by you');
});

test('minute and visibility refreshes invalidate checklist checks after silent trip changes', () => {
  for (const refresh of ['minute', 'visibility'] as const) {
    const page = tripPage();
    page.submit();
    page.checks[0].checked = true;
    page.element('#trip-date').value = '2027-06-01';
    if (refresh === 'minute') page.refreshMinute();
    else page.changeVisibility(false);
    assert.equal(page.element('#entry-decision').dataset.state, 'not-verified', refresh);
    assert.equal(page.checks[0].checked, false, refresh);
    assert.equal(page.element('#checklist-progress').textContent, '0 of 5 items reviewed by you', refresh);
  }
});

test('decision evidence follows the exact area rule even when decision wording is unchanged', () => {
  const page = tripPage([
    { ...rule, id: 'synthetic-bear', areas: ['bear-lake'] },
    { ...rule, id: 'synthetic-rest', areas: ['rest'] },
  ]);
  const link = page.element('#decision-evidence');
  assert.equal(link.hidden, true, 'evidence navigation waits for a submitted decision');
  page.element('#trip-area').value = 'bear-lake';
  page.submit();
  assert.equal(link.hidden, false);
  assert.equal(link.href, '#entry-rule-synthetic-bear');
  assert.equal(link.textContent, 'View the stored rule used for this result');
  const writes = page.decisionWrites();
  page.showPage(true);
  page.element('#trip-area').value = 'rest';
  page.flushTasks();
  assert.deepEqual(page.decisionWrites(), writes, 'the two synthetic rules give identical wording');
  assert.equal(link.href, '#entry-rule-synthetic-rest');
  page.element('#trip-date').value = '2027-06-01';
  page.element('#trip-form').dispatchEvent(new Event('input'));
  assert.equal(link.href, '#guidance-title', 'an unmatched date must not retain the previous exact rule');
  assert.equal(link.textContent, 'Browse stored entry guidance');
});

test('stale matched evidence remains historical and updates its link label without choosing a new rule', () => {
  const page = tripPage();
  const link = page.element('#decision-evidence');
  page.submit();
  assert.equal(link.href, '#entry-rule-synthetic-entry');
  page.setTime('2026-10-05T19:00:00.001Z');
  page.refreshMinute();
  assert.equal(link.href, '#entry-rule-synthetic-entry');
  assert.equal(link.textContent, 'View the stored rule needing a fresh review');
  const writes = link.textWrites.length;
  page.changeVisibility(false); page.showPage(true); page.flushTasks();
  assert.equal(link.textWrites.length, writes, 'an unchanged historical link is not repeatedly rewritten');
});

test('evidence navigation identifies unique unresolved matches but never selects one conflicting rule', () => {
  for (const scenario of [
    { rules: [{ ...rule, review_status: 'needs_review' as const }], area: '', state: 'review-required', href: '#entry-rule-synthetic-entry' },
    { rules: [{ ...rule, requirement: 'timed_entry' as const, start_time: '09:00', end_time: '14:00' }], area: '', state: 'needs-input', href: '#entry-rule-synthetic-entry' },
    { rules: [rule, { ...rule, id: 'conflicting-entry' }], area: '', state: 'conflict', href: '#guidance-title' },
    { rules: [{ ...rule, areas: ['known'] }], area: '', state: 'needs-input', href: '#guidance-title' },
    { rules: [{ ...rule, areas: ['known'] }], area: 'unknown', state: 'not-verified', href: '#guidance-title' },
    { rules: [], area: '', state: 'not-verified', href: '#guidance-title' },
  ]) {
    const page = tripPage(scenario.rules);
    page.element('#trip-area').value = scenario.area;
    page.submit();
    assert.equal(page.element('#entry-decision').dataset.state, scenario.state);
    assert.equal(page.element('#decision-evidence').href, scenario.href);
    assert.equal(page.element('#decision-evidence').hidden, false);
  }
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
