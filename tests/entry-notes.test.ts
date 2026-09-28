import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
const mod = await import('../scripts/validate-entry-notes.ts').catch(() => ({})) as any;
const note = () => ({ id: 'yell-general-entry', park_code: 'yell', subject_type: 'general_entry', period_status: 'not_published', effective_from: null, effective_to: null, reviewed_at: '2026-09-28T20:00:00Z', review_status: 'reviewed', summary: 'Reviewed general entry guidance.', limitation: 'No date-specific conclusion is being made.', evidence: { url: 'https://www.nps.gov/yell/planyourvisit/permitsandreservations.htm', excerpt: 'Source text', content_hash: createHash('sha256').update('Source text').digest('hex'), hash_scope: 'excerpt', reviewed_at: '2026-09-28T20:00:00Z', source_updated_at: null, method: 'manual_official_page_review' }, rights_basis: 'Government-authored text excerpt; no media.', rights_reviewed_at: '2026-09-28T20:00:00Z' });
function validate(notes: unknown) { assert.equal(typeof mod.validateEntryNotes, 'function'); return mod.validateEntryNotes(notes, ['yose', 'romo', 'yell', 'zion', 'grca']); }
test('undated evidence is accepted without manufacturing an effective period', () => { validate([note()]); });
test('production notes cover the remaining three parks, without adding annual rules', () => {
  assert.equal(typeof mod.validateEntryNotes, 'function');
  const notes = JSON.parse(readFileSync('data/entry-notes.json', 'utf8')); validate(notes);
  assert.deepEqual(notes.map((n: any) => n.park_code).sort(), ['grca', 'yell', 'zion']);
  notes.forEach((n: any) => { assert.equal(n.effective_from, null); assert.equal(n.effective_to, null); });
});
test('an undated note cannot contain an invented year or requirement conclusion', () => {
  assert.equal(typeof mod.validateEntryNotes, 'function');
  for (const fields of [{ effective_from: '2026-01-01' }, { effective_to: '2026-12-31' }, { period_status: '2026' }, { requirement: 'no_timed_entry' }]) assert.throws(() => validate([{ ...note(), ...fields }]));
});
test('changed text, cross-park links and lookalike hosts fail validation', () => {
  assert.equal(typeof mod.validateEntryNotes, 'function');
  for (const url of ['https://www.nps.gov.evil.test/yell/a', 'https://www.nps.gov/zion/a', 'https://user@www.nps.gov/yell/a', 'https://www.nps.gov/yell/a?api_key=x', 'https://www.nps.gov/yell/a#token=x']) {
    const value = note(); value.evidence.url = url; assert.throws(() => validate([value]));
  }
  const value = note(); value.evidence.excerpt = 'Changed without review'; assert.throws(() => validate([value]));
});
test('duplicates and unrecognized park/review states fail validation', () => {
  assert.equal(typeof mod.validateEntryNotes, 'function');
  assert.throws(() => validate([note(), note()]));
  assert.throws(() => validate([{ ...note(), park_code: 'fake' }]));
  assert.throws(() => validate([{ ...note(), review_status: 'approved_by_nps' }]));
});
test('invalid or mismatched review clocks and invented publisher times fail', () => {
  assert.equal(typeof mod.validateEntryNotes, 'function');
  assert.throws(() => validate([{ ...note(), reviewed_at: '2026-02-30T00:00:00Z' }]));
  const mismatched = note(); mismatched.evidence.reviewed_at = '2026-09-27T20:00:00Z'; assert.throws(() => validate([mismatched]));
  const invented = note() as any; invented.evidence.source_updated_at = invented.reviewed_at; assert.throws(() => validate([invented]));
});
