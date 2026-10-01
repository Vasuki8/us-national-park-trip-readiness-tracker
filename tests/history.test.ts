import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { validateHistory, historyDigest } from '../scripts/validate-history.ts';
import { describeHistory } from '../src/lib/history.ts';
const fixture = JSON.parse(readFileSync(new URL('./fixtures/history-preview.json', import.meta.url), 'utf8'));
const copy = (name = 'mixed') => structuredClone(fixture.cases[name]);
const now = new Date('2026-09-28T13:00:00Z');
test('Python archive projection hashes and all fixture states validate in TypeScript', () => {
  for (const view of Object.values(fixture.cases) as any[]) {
    assert.equal(historyDigest(view.snapshot), view.history.snapshot_hash);
    assert.deepEqual(validateHistory(view.history, view.snapshot), view.history);
  }
});
test('all five committed histories match their public snapshots', () => {
  const histories = JSON.parse(readFileSync(new URL('../data/history.json', import.meta.url), 'utf8'));
  assert.equal(histories.length, 5); assert.equal(new Set(histories.map((h: any) => h.park_code)).size, 5);
  for (const h of histories) {
    const snapshot = JSON.parse(readFileSync(new URL(`../data/alerts/${h.park_code}.json`, import.meta.url), 'utf8'));
    assert.equal(historyDigest(snapshot), h.snapshot_hash);
    assert.deepEqual(validateHistory(h, snapshot), h);
  }
});
test('mismatched snapshot contents, status, clock and park fail closed', () => {
  for (const mutate of [(v: any) => v.snapshot.records[0].title = 'Altered', (v: any) => v.snapshot.park_code = 'zion',
    (v: any) => v.snapshot.collection_status = 'failed', (v: any) => v.snapshot.last_checked_at = '2026-09-28T15:00:00Z']) {
    const v = copy(); mutate(v); assert.throws(() => validateHistory(v.history, v.snapshot));
  }
});
test('a rehashed snapshot with a different observation clock cannot be substituted', () => {
  const v = copy(); v.snapshot.last_checked_at = '2026-09-28T15:00:00Z';
  v.history.snapshot_hash = historyDigest(v.snapshot); assert.throws(() => validateHistory(v.history, v.snapshot));
});
test('alert evidence permits a missing link and official NPS shared/subdomain links', () => {
  for (const url of [null, 'https://go.nps.gov/short-link', 'https://www.nps.gov/subjects/developer/index.htm', 'https://inciweb.wildfire.gov/incident/example']) {
    const v = copy(); v.history.observations[0].changes[0].after.url = url;
    v.history.observations[0].changes[0].after.content_hash = historyDigest(Object.fromEntries(
      ['category','description','id','title','url'].map((key) => [key, v.history.observations[0].changes[0].after[key]])
    ));
    v.snapshot.records[0].url = url;
    v.snapshot.records[0].content_hash = v.history.observations[0].changes[0].after.content_hash;
    v.history.snapshot_hash = historyDigest(v.snapshot);
    validateHistory(v.history, v.snapshot);
  }
});
test('before and after evidence reject tampering, wrong park and unsafe URLs', () => {
  for (const mutate of [(e: any) => e.description = 'Changed', (e: any) => e.url = 'javascript:alert(1)',
    (e: any) => e.url = 'https://www.nps.gov.evil.test/yose/test.htm',
    (e: any) => e.url = 'https://www.nps.gov/yose/../zion/test.htm', (e: any) => e.url = 'https://www.nps.gov/yose/test.htm#token=private',
    (e: any) => e.id = 'another-id']) {
    const v = copy(); mutate(v.history.observations[0].changes[0].after);
    assert.throws(() => validateHistory(v.history, v.snapshot));
  }
});
test('unknown private fields are rejected at every exposed level', () => {
  for (const mutate of [(v: any) => v.history.pending = {}, (v: any) => v.history.observations[0].private_path = '/state',
    (v: any) => v.history.observations[0].changes[0].raw_response = 'secret',
    (v: any) => v.history.observations[0].changes[0].after.headers = {}]) {
    const v = copy(); mutate(v); assert.throws(() => validateHistory(v.history, v.snapshot));
  }
});
test('missing, duplicate, malformed and out-of-order observations cannot be accepted', () => {
  for (const mutate of [(h: any) => h.observations.pop(), (h: any) => h.observations[1] = h.observations[0],
    (h: any) => h.observations[0].checked_at = '2026-02-30T12:00:00Z', (h: any) => h.observations[0].sequence = 1,
    (h: any) => h.head_observation_id = 'bad', (h: any) => h.schema_version = true]) {
    const v = copy(); mutate(v.history); assert.throws(() => validateHistory(v.history, v.snapshot));
  }
});
test('event kinds and before-after relationships are validated', () => {
  for (const mutate of [(c: any) => c.kind = 'reopened', (c: any) => c.before = null,
    (c: any) => c.after = null, (c: any) => c.before = c.after]) {
    const v = copy(); mutate(v.history.observations[0].changes[0]); assert.throws(() => validateHistory(v.history, v.snapshot));
  }
});
test('baselines and failed observations cannot acquire fabricated changes', () => {
  for (const name of ['baseline', 'failed']) {
    const v = copy(name); v.history.observations[0].changes = copy().history.observations[0].changes;
    assert.throws(() => validateHistory(v.history, v.snapshot));
  }
});

function afterInitialFailures(name = 'baseline') {
  const view = copy(name);
  for (const observation of view.history.observations) observation.sequence += 2;
  view.history.total_observations += 2;
  view.history.observations.push(
    {observation_id: 'd'.repeat(64), sequence: 2, checked_at: '2026-09-28T09:00:00Z',
      collection_status: 'quarantined', comparison: 'not_compared', change_count: 0, omitted_changes: 0, changes: []},
    {observation_id: 'e'.repeat(64), sequence: 1, checked_at: '2026-09-28T08:00:00Z',
      collection_status: 'failed', comparison: 'not_compared', change_count: 0, omitted_changes: 0, changes: []},
  );
  return view;
}

test('first success after initial failures must remain a baseline throughout complete history', () => {
  for (const name of ['baseline', 'mixed', 'failed']) {
    const view = afterInitialFailures(name), original = structuredClone(view);
    assert.deepEqual(validateHistory(view.history, view.snapshot), view.history);
    assert.deepEqual(view, original, 'validating must preserve retained records and clocks');
    const firstSuccess = view.history.observations.find((observation: any) => observation.sequence === 3);
    firstSuccess.comparison = 'compared';
    assert.throws(() => validateHistory(view.history, view.snapshot), /invalid_history/, name);
  }
});

test('first success after initial failures cannot invent added or edited notices', () => {
  for (const kind of ['added', 'edited']) {
    const view = afterInitialFailures();
    const after = Object.fromEntries(['category', 'description', 'id', 'title', 'url', 'content_hash']
      .map(key => [key, view.snapshot.records[0][key]]));
    const before: Record<string, unknown> | null = kind === 'added' ? null : {...after, title: 'Synthetic invented predecessor'};
    if (before) before.content_hash = historyDigest(Object.fromEntries(
      ['category', 'description', 'id', 'title', 'url'].map(key => [key, before[key]])));
    const firstSuccess = view.history.observations[0];
    firstSuccess.comparison = 'compared'; firstSuccess.change_count = 1;
    firstSuccess.changes = [{kind, record_id: after.id, before, after}];
    view.history.total_changes = 1;
    const original = structuredClone(view);
    assert.throws(() => validateHistory(view.history, view.snapshot), /invalid_history/, kind);
    assert.deepEqual(view, original, 'refusal must not repair or rewrite candidate evidence');
  }
});

test('omitted baselines and complete histories without any success remain valid', () => {
  const bounded = copy(); bounded.history.observations.pop(); bounded.history.omitted_observations = 1;
  assert.deepEqual(validateHistory(bounded.history, bounded.snapshot), bounded.history);
  const failed = afterInitialFailures('empty');
  failed.snapshot.collection_status = 'quarantined'; failed.snapshot.coverage_status = 'incomplete';
  failed.snapshot.error_code = 'response_requires_review';
  failed.snapshot.last_checked_at = failed.history.observations[0].checked_at;
  failed.history.head_observation_id = failed.history.observations[0].observation_id;
  failed.history.snapshot_hash = historyDigest(failed.snapshot);
  const original = structuredClone(failed);
  assert.deepEqual(validateHistory(failed.history, failed.snapshot), failed.history);
  assert.equal(failed.snapshot.last_successful_fetch_at, null);
  assert.deepEqual(failed, original);
});
test('omitted counts must reconcile and cannot silently hide visible changes', () => {
  for (const mutate of [(h: any) => h.total_changes = 0, (h: any) => h.omitted_changes = 0,
    (h: any) => h.omitted_observations = -1, (h: any) => h.observations[0].omitted_changes = 1]) {
    const v = copy('truncated'); mutate(v.history); assert.throws(() => validateHistory(v.history, v.snapshot));
  }
});
test('empty history cannot be paired with a collected snapshot', () => {
  const v = copy('empty'); const s = copy().snapshot; v.history.snapshot_hash = historyDigest(s);
  assert.throws(() => validateHistory(v.history, s));
});
test('rendered freshness expires without altering observation timestamps', () => {
  const v = copy(); const original = structuredClone(v);
  assert.match(describeHistory(v.snapshot, now).title, /Recent/);
  assert.match(describeHistory(v.snapshot, new Date('2026-09-28T16:00:00.001Z')).title, /fresh check/);
  assert.deepEqual(v, original);
});
test('failed and quarantined histories remain degraded even with fresh retained data', () => {
  const v = copy('failed');
  assert.match(describeHistory(v.snapshot, new Date('2026-09-28T14:01:00Z')).title, /not successful/);
  v.snapshot.collection_status = 'quarantined';
  assert.match(describeHistory(v.snapshot, now).title, /not successful/);
});
test('empty, invalid-clock and future checks do not become current history', () => {
  assert.match(describeHistory(copy('empty').snapshot, now).title, /not collected/);
  assert.match(describeHistory(copy().snapshot, new Date('invalid')).title, /fresh check/);
  assert.match(describeHistory(copy().snapshot, new Date('2026-09-27')).title, /fresh check/);
});
test('a failed head cannot relabel the time of the visible last successful observation', () => {
  const v = copy('failed'); v.snapshot.last_successful_fetch_at = '2026-09-28T13:00:00Z';
  v.history.snapshot_hash = historyDigest(v.snapshot);
  assert.throws(() => validateHistory(v.history, v.snapshot));
});
test('an all-failed visible window cannot invent a success inside that window', () => {
  const v = copy('truncated'); v.snapshot.last_successful_fetch_at = v.snapshot.last_checked_at;
  v.history.snapshot_hash = historyDigest(v.snapshot);
  assert.throws(() => validateHistory(v.history, v.snapshot));
});
test('year zero is not a valid archive timestamp', () => {
  const v = JSON.parse(JSON.stringify(copy()).replaceAll('2026-', '0000-'));
  v.history.snapshot_hash = historyDigest(v.snapshot);
  assert.throws(() => validateHistory(v.history, v.snapshot));
});
