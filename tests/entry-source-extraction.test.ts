import test from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { assessEntrySources, applyEntryReview, guidanceDigest } from '../scripts/entry-review.ts';
import { evaluateEntry, type Rule } from '../src/lib/readiness.ts';
const { rules, notes } = JSON.parse(readFileSync(new URL('./fixtures/synthetic-guidance.json', import.meta.url), 'utf8'));
const records = [...rules, ...notes];
const now = new Date('2026-09-30T01:00:00Z');
const empty = { schema_version: 1, proposals: [] };
function extract(scenario: string) {
  return JSON.parse(execFileSync('python', ['-c', 'import sys; sys.path.insert(0,"tests"); import json; from entry_source_fixtures import make_fixture; p=json.load(sys.stdin); print(json.dumps(make_fixture(p["records"],p["scenario"]),ensure_ascii=False))'],
    { input: JSON.stringify({ records, scenario }), encoding: 'utf8', timeout: 15_000, maxBuffer: 2 * 1024 * 1024 }));
}
test('Python extracted context binds all six complete TypeScript guidance records', () => {
  const result = extract('matching');
  assert.equal(result.sources.length, 5); assert.equal(result.observations.length, 6);
  for (let i = 0; i < records.length; i++) assert.equal(result.observations[i].guidance_hash, guidanceDigest(records[i]));
  const assessed = assessEntrySources(records, result.observations, empty, now);
  assert.equal(assessed.register.proposals.length, 0);
  assert.ok(assessed.checks.every(c => c.outcome === 'matching_excerpt'));
  assert.deepEqual(applyEntryReview(records, assessed.register, now).guidance, records);
});
test('changed surrounding exceptions suspend every dated conclusion and undated note through the existing gate', () => {
  const result = extract('context_changed');
  assert.ok(result.sources.every((s: any) => s.reason === 'context_changed'));
  const assessed = assessEntrySources(records, result.observations, empty, now);
  assert.equal(assessed.register.proposals.length, 6);
  const applied = applyEntryReview(records, assessed.register, now);
  for (const r of applied.guidance) {
    assert.equal(r.review_status, 'needs_review');
    assert.equal(r.reviewed_at, records.find(x => x.id === r.id).reviewed_at);
  }
  for (const r of rules) {
    const trip = { park_code: r.park_code, area: r.areas[0], date:'2026-09-30', time:'00:01', special_case:false };
    assert.equal(evaluateEntry([r], trip, now).state, 'not-required-under-rule');
    const held = applied.guidance.find(x => x.id === r.id) as Rule;
    assert.equal(evaluateEntry([held], trip, now).state, 'review-required');
  }
});
test('missing context baselines never manufacture checked unchanged source coverage', () => {
  const result = extract('no_baseline');
  assert.ok(result.sources.every((s: any) => s.reason === 'context_not_reviewed' && s.baseline_context === null));
  const assessed = assessEntrySources(records, result.observations, empty, now);
  assert.equal(assessed.register.proposals.length, 6);
  assert.ok(assessed.checks.every(c => c.outcome === 'check_failed'));
});
test('missing excerpts and ambiguous headings use explicit nonmatching proposal paths', () => {
  for (const scenario of ['missing', 'ambiguous']) {
    const result = extract(scenario);
    const assessed = assessEntrySources(records, result.observations, empty, now);
    assert.equal(assessed.register.proposals.length, 6);
    assert.ok(assessed.checks.every(c => c.outcome === (scenario === 'missing' ? 'excerpt_missing' : 'check_failed')));
  }
});
test('a later matching captured context cannot clear pending source-change holds', () => {
  const changed = assessEntrySources(records, extract('context_changed').observations, empty, now);
  const recovered = assessEntrySources(records, extract('recovered').observations, changed.register, now);
  assert.deepEqual(recovered.register, changed.register);
  assert.equal(applyEntryReview(records, recovered.register, now).holds.length, 6);
});
test('extraction evidence is separate from gate payload and production files remain untouched', () => {
  const paths = ['rules.json','entry-notes.json','entry-review.json','history.json'];
  const before = paths.map(p => readFileSync(new URL(`../data/${p}`, import.meta.url), 'utf8'));
  const result = extract('context_changed');
  for (const o of result.observations) assert.deepEqual(Object.keys(o).sort(), ['checked_at','excerpt','guidance_hash','guidance_id','source_url','status']);
  for (const s of result.sources) {
    assert.ok(s.context.text.includes('Synthetic changed provision'));
    assert.ok(!s.baseline_context.text.includes('Synthetic changed provision'));
  }
  assessEntrySources(records, result.observations, empty, now);
  assert.equal(result.network_performed, false); assert.equal(result.publication_performed, false);
  assert.deepEqual(paths.map(p => readFileSync(new URL(`../data/${p}`, import.meta.url), 'utf8')), before);
});
