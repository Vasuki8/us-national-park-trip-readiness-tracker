/** Undated source observations are deliberately not executable date rules. */
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { isCalendarDate } from '../src/lib/readiness.ts';
export interface EntryNote {
  id: string; park_code: string; subject_type: 'general_entry'; period_status: 'not_published';
  effective_from: null; effective_to: null; reviewed_at: string;
  review_status: 'reviewed' | 'needs_review' | 'conflict'; summary: string; limitation: string;
  evidence: { url: string; excerpt: string; content_hash: string; hash_scope: 'excerpt'; reviewed_at: string; source_updated_at: null; method: 'manual_official_page_review' };
  rights_basis: string; rights_reviewed_at: string;
}
const text = (value: unknown) => assert.ok(typeof value === 'string' && value.trim().length > 0);
function timestamp(value: unknown) {
  assert.ok(typeof value === 'string' && /^\d{4}-\d{2}-\d{2}T(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d(?:\.\d+)?(?:Z|[+-](?:[01]\d|2[0-3]):[0-5]\d)$/.test(value));
  assert.ok(isCalendarDate(value.slice(0, 10)) && Number.isFinite(Date.parse(value)));
}
export function validateEntryNotes(value: unknown, parkCodes: string[]): asserts value is EntryNote[] {
  assert.ok(Array.isArray(value));
  const ids = new Set<string>();
  for (const note of value) {
    assert.ok(note && typeof note === 'object');
    text(note.id); assert.ok(!ids.has(note.id), 'Duplicate source-note identity.'); ids.add(note.id);
    assert.ok(parkCodes.includes(note.park_code));
    assert.equal(note.subject_type, 'general_entry'); assert.equal(note.period_status, 'not_published');
    assert.equal(note.effective_from, null); assert.equal(note.effective_to, null);
    assert.ok(!('requirement' in note), 'An undated note cannot be an executable rule.');
    assert.ok(['reviewed', 'needs_review', 'conflict'].includes(note.review_status));
    text(note.summary); text(note.limitation); timestamp(note.reviewed_at);
    const evidence = note.evidence; assert.ok(evidence && typeof evidence === 'object');
    const url = new URL(evidence.url);
    assert.ok(url.protocol === 'https:' && ['www.nps.gov', 'nps.gov', 'home.nps.gov'].includes(url.hostname));
    assert.ok(!url.username && !url.password && !url.port && !url.search && !url.hash);
    assert.ok(url.pathname.startsWith(`/${note.park_code}/`));
    text(evidence.excerpt); assert.equal(evidence.hash_scope, 'excerpt');
    assert.equal(evidence.content_hash, createHash('sha256').update(evidence.excerpt).digest('hex'));
    assert.equal(evidence.reviewed_at, note.reviewed_at); assert.equal(evidence.source_updated_at, null);
    assert.equal(evidence.method, 'manual_official_page_review');
    text(note.rights_basis); timestamp(note.rights_reviewed_at);
  }
}
