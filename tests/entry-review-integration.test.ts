import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { assessEntrySources, applyEntryReview, guidanceDigest } from '../scripts/entry-review.ts';
import { evaluateEntry } from '../src/lib/readiness.ts';
import { summarizeCoverage } from '../src/lib/source-coverage.ts';
const load = (path: string) => JSON.parse(readFileSync(new URL(`../data/${path}`, import.meta.url), 'utf8'));
const NOW = new Date('2026-09-29T03:00:00Z');
const {rules, notes} = JSON.parse(readFileSync(new URL('./fixtures/synthetic-guidance.json', import.meta.url), 'utf8'));
const parks = load('parks.json');
const records = [...rules, ...notes];
function batch() {
  return records.map((r) => ({ guidance_id: r.id, guidance_hash: guidanceDigest(r), source_url: r.evidence.url,
    checked_at: '2026-09-29T01:00:00Z', status: 'observed', excerpt: r.evidence.excerpt }));
}
const empty = () => ({ schema_version: 1, proposals: [] });
test('every synthetic dated-rule fixture is suspended before its no-reservation conclusion', () => {
  for (const rule of rules) {
    const obs = batch(); obs.find((o) => o.guidance_id === rule.id)!.excerpt += ' Synthetic changed text.';
    const pending = assessEntrySources(records, obs, empty(), NOW).register;
    const effective: any[] = applyEntryReview(records, pending, NOW).guidance.slice(0, rules.length);
    const trip = { park_code: rule.park_code, date: '2026-09-29', time: '03:00', area: rule.areas[0], special_case: false };
    assert.equal(evaluateEntry(rules, trip, NOW).state, 'not-required-under-rule');
    assert.equal(evaluateEntry(effective, trip, NOW).state, 'review-required');
    assert.equal(effective.find((r) => r.id === rule.id)!.reviewed_at, rule.reviewed_at);
  }
});
test('all six source bindings and five park coverage rows propagate holds without creating dated rules', () => {
  const obs = batch(); obs.forEach((o) => o.excerpt += ' Synthetic changed text.');
  const pending = assessEntrySources(records, obs, empty(), NOW).register;
  const gated = applyEntryReview(records, pending, NOW).guidance;
  const coverage = summarizeCoverage({ parks, rules: gated.slice(0, rules.length), notes: gated.slice(rules.length), snapshots: [] }, NOW);
  assert.equal(pending.proposals.length, 6); assert.equal(coverage.parkCount, 5);
  assert.equal(coverage.reviewWithinWindowParks, 0); assert.equal(coverage.storedReviewParks, 5); assert.equal(coverage.datedRuleParks, 2);
  assert.ok(coverage.rows.every((r) => r.entryLabel === 'Source review pending'));
  for (const note of gated.slice(rules.length)) assert.equal(note.effective_from, null);
});
test('production review register is empty and cannot claim active source monitoring', () => {
  const publicRecords = [...load('rules.json'), ...load('entry-notes.json')];
  const publicNow = new Date(Math.max(...publicRecords.map(r => Date.parse(r.reviewed_at))) + 1);
  const register = load('entry-review.json'); assert.deepEqual(register, empty());
  assert.deepEqual(applyEntryReview(publicRecords, register, publicNow).guidance, publicRecords);
});
test('a matching source check does not rescue a weekly-expired approval', () => {
  const later = new Date('2026-10-06T01:00:00Z'); const obs = batch(); obs.forEach((o) => o.checked_at = '2026-10-06T00:00:00Z');
  const gate = applyEntryReview(records, assessEntrySources(records, obs, empty(), later).register, later);
  const effective = gate.guidance.slice(0, rules.length);
  assert.equal(evaluateEntry(effective, { park_code: 'yose', date: '2026-10-06', time: '12:00', area: '*', special_case: false }, later).state, 'stale');
});
