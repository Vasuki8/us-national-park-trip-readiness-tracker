import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { assessEntrySources, applyEntryReview, validateEntryReview, guidanceDigest } from '../scripts/entry-review.ts';
const sha = (s: string) => createHash('sha256').update(s).digest('hex');
const NOW = new Date('2026-09-29T03:00:00Z');
const T1 = '2026-09-29T01:00:00Z', T2 = '2026-09-29T02:00:00Z';
const empty = () => ({ schema_version: 1, proposals: [] });
function guidance(): any[] {
  return ['yose', 'romo'].map((code) => ({
    id: `${code}-test-rule`, park_code: code, review_status: 'reviewed', reviewed_at: '2026-09-28T19:00:00Z',
    areas: ['*'], effective_from: '2026-01-01', effective_to: '2026-12-31', start_time: null, end_time: null,
    requirement: 'no_timed_entry', summary: 'Synthetic guidance only.', exception_note: 'Other requirements are separate.',
    evidence: { url: `https://www.nps.gov/${code}/planyourvisit/reservations.htm`, excerpt: 'Synthetic entry statement.',
      content_hash: sha('Synthetic entry statement.'), hash_scope: 'excerpt', reviewed_at: '2026-09-28T19:00:00Z',
      source_updated_at: null, method: 'manual_official_page_review' },
  }));
}
function observations(records = guidance(), checked_at = T1) {
  return records.map((r) => ({ guidance_id: r.id, guidance_hash: guidanceDigest(r), source_url: r.evidence.url,
    checked_at, status: 'observed', excerpt: r.evidence.excerpt }));
}
function changed() { const batch = observations(); batch[0].excerpt = 'Synthetic entry now requires a reservation.'; return batch; }
test('matching selected text never changes approved guidance or creates a fresh approval', () => {
  const records = guidance(); const before = structuredClone(records);
  const result = assessEntrySources(records, observations(records), empty(), NOW);
  assert.equal(result.checks[0].outcome, 'matching_excerpt'); assert.deepEqual(result.register, empty());
  assert.deepEqual(applyEntryReview(records, result.register, NOW).guidance, records); assert.deepEqual(records, before);
});
test('only whitespace equivalence is ignored; capitalization, punctuation, times and negation suspend', () => {
  const white = observations(); white[0].excerpt = 'Synthetic\n entry\u00a0 statement.  ';
  assert.equal(assessEntrySources(guidance(), white, empty(), NOW).register.proposals.length, 0);
  for (const text of ['synthetic entry statement.', 'Synthetic entry statement!', 'Entry at 09:00.', 'No synthetic entry statement.', 'Synthetic entry statement. New exception.']) {
    const batch = observations(); batch[0].excerpt = text;
    assert.equal(assessEntrySources(guidance(), batch, empty(), NOW).register.proposals[0].reason, 'text_changed');
  }
});
test('changed source creates exact before/after evidence bound to the complete rule revision', () => {
  const r = assessEntrySources(guidance(), changed(), empty(), NOW).register;
  const p = r.proposals[0]; assert.equal(p.before_excerpt, guidance()[0].evidence.excerpt);
  assert.equal(p.after_excerpt, changed()[0].excerpt); assert.equal(p.guidance_hash, guidanceDigest(guidance()[0]));
  assert.equal(p.state, 'pending'); assert.equal(p.checked_at, T1); assert.match(p.id, /^[a-f0-9]{64}$/);
  assert.deepEqual(validateEntryReview(r, guidance(), NOW), r);
});
test('missing and failed observations are held, with no invented replacement excerpt', () => {
  for (const status of ['missing', 'failed']) {
    const batch: any = observations(); batch[0].status = status; batch[0].excerpt = null;
    const result = assessEntrySources(guidance(), batch, empty(), NOW);
    assert.equal(result.register.proposals[0].after_excerpt, null);
    assert.equal(applyEntryReview(guidance(), result.register, NOW).guidance[0].review_status, 'needs_review');
  }
});
test('later matching text cannot clear an existing hold or renew reviewed_at', () => {
  const first = assessEntrySources(guidance(), changed(), empty(), NOW);
  const next = assessEntrySources(guidance(), observations(guidance(), T2), first.register, NOW);
  assert.deepEqual(next.register, first.register);
  assert.equal(applyEntryReview(guidance(), next.register, NOW).guidance[0].review_status, 'needs_review');
});
test('exact replays are idempotent and conflicting same-instant observations are rejected', () => {
  const first = assessEntrySources(guidance(), changed(), empty(), NOW);
  assert.deepEqual(assessEntrySources(guidance(), changed(), first.register, NOW).register, first.register);
  assert.throws(() => assessEntrySources(guidance(), observations(), first.register, NOW));
});
test('older observations cannot replay over newer pending evidence', () => {
  const batch = changed(); batch.forEach((o) => o.checked_at = T2);
  const first = assessEntrySources(guidance(), batch, empty(), NOW);
  assert.throws(() => assessEntrySources(guidance(), changed(), first.register, NOW));
});
test('gating preserves conflicts and all evidence, dates, rights and summaries', () => {
  const records = guidance(); records[0].review_status = 'conflict';
  const obs = observations(records); obs[0].excerpt += ' Different.';
  const r = assessEntrySources(records, obs, empty(), NOW).register;
  const gated = applyEntryReview(records, r, NOW);
  assert.equal(gated.guidance[0].review_status, 'conflict'); assert.deepEqual(gated.guidance, records);
  assert.equal(gated.holds.length, 1); assert.ok(!JSON.stringify(gated.holds).includes('Different.'));
});
test('new approved summary/date/approval/source identity invalidates stale proposals', () => {
  const r = assessEntrySources(guidance(), changed(), empty(), NOW).register;
  for (const mutate of [(g: any) => g[0].summary += 'new', (g: any) => g[0].effective_to = '2027-01-01',
    (g: any) => g[0].reviewed_at = T2, (g: any) => g[0].evidence.url += '?x=1']) {
    const records = guidance(); mutate(records); assert.throws(() => applyEntryReview(records, r, NOW));
  }
});
test('complete unique observation inventory is required', () => {
  for (const batch of [[], observations().slice(0, 1), [observations()[0], observations()[0]], [...observations(), observations()[0]]])
    assert.throws(() => assessEntrySources(guidance(), batch, empty(), NOW));
});
test('source URL must match the exact approved page, with no credentials or alternate park', () => {
  for (const url of ['https://www.nps.gov/romo/planyourvisit/reservations.htm', 'https://www.nps.gov/yose/planyourvisit/other.htm',
    'https://www.nps.gov.evil.test/yose/a', 'https://www.nps.gov/yose/../romo/a', 'https://www.nps.gov/yose/a?token=private', 'javascript:alert(1)']) {
    const batch = observations(); batch[0].source_url = url;
    assert.throws(() => assessEntrySources(guidance(), batch, empty(), NOW));
  }
});
test('unknown input fields and status/type confusion are refused', () => {
  for (const mutate of [(o: any) => o.headers = {}, (o: any) => o.reviewed_at = T1, (o: any) => o.status = 'approved',
    (o: any) => o.excerpt = null, (o: any) => o.status = true, (o: any) => o.guidance_hash = 'bad']) {
    const batch = observations(); mutate(batch[0]); assert.throws(() => assessEntrySources(guidance(), batch, empty(), NOW));
  }
});
test('clock must be valid, newer than approval and not in the future', () => {
  for (const time of ['2026-02-30T01:00:00Z', '0000-01-01T00:00:00Z', '2027-01-01T00:00:00Z',
    '2026-09-28T18:00:00Z', '2026-09-28T19:00:00Z', '2026-09-29', '2026-09-29T25:00:00Z']) {
    const batch = observations(guidance(), time); assert.throws(() => assessEntrySources(guidance(), batch, empty(), NOW));
  }
  assert.throws(() => assessEntrySources(guidance(), observations(), empty(), new Date('bad')));
});
test('malformed, invisible-control and unbounded text are refused', () => {
  for (const text of ['', '   ', 'x'.repeat(32769), '\ud800', 'bad\u0000text', 'hide\u202etext']) {
    const batch = observations(); batch[0].excerpt = text; assert.throws(() => assessEntrySources(guidance(), batch, empty(), NOW));
  }
});
test('proposal text, reason, hash and identity cannot be edited independently', () => {
  const result = assessEntrySources(guidance(), changed(), empty(), NOW);
  for (const mutate of [(p: any) => p.after_excerpt += 'tamper', (p: any) => p.reason = 'matching_excerpt',
    (p: any) => p.before_excerpt = 'unrelated', (p: any) => p.guidance_hash = 'f'.repeat(64), (p: any) => p.state = 'approved']) {
    const r = structuredClone(result.register); mutate(r.proposals[0]);
    assert.throws(() => validateEntryReview(r, guidance(), NOW));
  }
});
test('register cannot contain unknown private fields, duplicate proposals or another park', () => {
  const result = assessEntrySources(guidance(), changed(), empty(), NOW);
  for (const mutate of [(r: any) => r.headers = {}, (r: any) => r.schema_version = true,
    (r: any) => r.proposals.push(r.proposals[0]), (r: any) => r.proposals[0].private_path = '/secret']) {
    const r = structuredClone(result.register); mutate(r); assert.throws(() => validateEntryReview(r, guidance(), NOW));
  }
});
test('bounded pending queue refuses overflow instead of discarding a hold', () => {
  const result = assessEntrySources(guidance(), changed(), empty(), NOW);
  const r = { schema_version: 1, proposals: Array(121).fill(result.register.proposals[0]) };
  assert.throws(() => validateEntryReview(r, guidance(), NOW));
});
test('diagnostics do not echo source excerpts or secret-looking input', () => {
  const batch: any = observations(); batch[0].status = 'SECRET-EXCEPTION-PAYLOAD';
  assert.throws(() => assessEntrySources(guidance(), batch, empty(), NOW), (error: Error) => !error.message.includes('SECRET'));
});
test('undated observations stay undated and never acquire executable requirements', () => {
  const records: any = guidance(); delete records[0].requirement; records[0].effective_from = null; records[0].effective_to = null;
  records[0].subject_type = 'general_entry'; records[0].period_status = 'not_published';
  const obs = observations(records); obs[0].excerpt += ' New text.';
  const next = applyEntryReview(records, assessEntrySources(records, obs, empty(), NOW).register, NOW).guidance;
  assert.equal(next[0].review_status, 'needs_review'); assert.equal(next[0].effective_from, null); assert.ok(!('requirement' in next[0]));
});
test('defensive copies prevent accidental mutation of approved records and pending evidence', () => {
  const records = guidance(); const register = assessEntrySources(records, changed(), empty(), NOW).register;
  const original = structuredClone({ records, register }); const result = applyEntryReview(records, register, NOW);
  result.guidance[0].summary = 'mutated'; result.holds.splice(0);
  assert.deepEqual({ records, register }, original);
});
