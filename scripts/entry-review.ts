/** Selected-text review intake, not a scraper, semantic interpreter or approval service. */
import { createHash } from 'node:crypto';
import { validateRule } from './validate-data.ts';
import { validateEntryNotes } from './validate-entry-notes.ts';
import type { EntryHold, EntryReviewReason } from '../src/lib/entry-review.ts';

export interface SourceGuidance {
  id: string; park_code: string; reviewed_at: string;
  review_status: 'reviewed' | 'needs_review' | 'conflict';
  evidence: { url: string; excerpt: string; content_hash: string; reviewed_at: string; hash_scope: 'excerpt' };
}
export interface EntrySourceObservation {
  guidance_id: string; guidance_hash: string; source_url: string; checked_at: string;
  status: 'observed' | 'missing' | 'failed'; excerpt: string | null;
}
export interface EntryReviewProposal {
  id: string; guidance_id: string; guidance_hash: string; source_url: string;
  checked_at: string; reason: EntryReviewReason; state: 'pending';
  before_excerpt: string; after_excerpt: string | null;
}
export interface EntryReviewRegister { schema_version: 1; proposals: EntryReviewProposal[] }
const OBSERVATION_FIELDS = 'guidance_id guidance_hash source_url checked_at status excerpt';
const PROPOSAL_FIELDS = 'id guidance_id guidance_hash source_url checked_at reason state before_excerpt after_excerpt';
const MAX_PROPOSALS = 120;
const MAX_TEXT = 32_768;
const MAX_REGISTER_BYTES = 2 * 1024 * 1024;
function requireValue(value: unknown, code = 'invalid_entry_review'): asserts value {
  if (!value) throw new Error(code); // Never include input or exception payloads in diagnostics.
}
function object(value: unknown): Record<string, any> {
  requireValue(value !== null && typeof value === 'object' && !Array.isArray(value));
  requireValue(Object.getPrototypeOf(value) === Object.prototype || Object.getPrototypeOf(value) === null);
  return value as Record<string, any>;
}
function shape(value: unknown, fields: string): Record<string, any> {
  const item = object(value);
  requireValue(Object.keys(item).sort().join(' ') === fields.split(' ').sort().join(' '));
  return item;
}
function text(value: unknown, limit = MAX_TEXT): asserts value is string {
  requireValue(typeof value === 'string' && value.trim().length > 0 && value.length <= limit);
  requireValue(!/[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\u200b-\u200f\u202a-\u202e\u2060-\u206f\ufeff]/u.test(value));
  requireValue(!/[\uD800-\uDBFF](?![\uDC00-\uDFFF])|(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]/u.test(value));
}
function canonical(value: unknown, depth = 0): string {
  requireValue(depth <= 12, 'entry_review_too_deep');
  if (value === null || typeof value === 'string' || typeof value === 'boolean') return JSON.stringify(value);
  if (typeof value === 'number') { requireValue(Number.isSafeInteger(value)); return JSON.stringify(value); }
  if (Array.isArray(value)) { requireValue(value.length <= 1024); return `[${value.map((v) => canonical(v, depth + 1)).join(',')}]`; }
  const item = object(value);
  return `{${Object.keys(item).sort().map((k) => `${JSON.stringify(k)}:${canonical(item[k], depth + 1)}`).join(',')}}`;
}
/** Binds the entire approved record, including dates, summary, source and review state. */
export function guidanceDigest(value: unknown): string {
  const encoded = canonical(value); requireValue(Buffer.byteLength(encoded) <= MAX_REGISTER_BYTES, 'entry_review_too_large');
  return createHash('sha256').update(encoded).digest('hex');
}
function timestamp(value: unknown): number {
  text(value, 32);
  requireValue(/^(?!0000)\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{3})?Z$/.test(value), 'invalid_entry_review_clock');
  const instant = Date.parse(value); requireValue(Number.isFinite(instant), 'invalid_entry_review_clock');
  const iso = new Date(instant).toISOString();
  requireValue(value === iso || value === iso.replace('.000Z', 'Z'), 'invalid_entry_review_clock');
  return instant;
}
function officialUrl(value: unknown, code: string) {
  text(value, 2048);
  requireValue(new RegExp(`^https://(?:www\\.nps\\.gov|nps\\.gov|home\\.nps\\.gov)/${code}/(?:[a-z0-9_-]+/)*[a-z0-9_-]+\\.htm$`).test(value), 'invalid_entry_review_source');
}
function inventory<T extends SourceGuidance>(records: T[], now: Date): Map<string, T> {
  requireValue(now instanceof Date && Number.isFinite(now.getTime()), 'invalid_entry_review_clock');
  requireValue(Array.isArray(records) && records.length > 0 && records.length <= 32);
  const map = new Map<string, T>();
  for (const value of records) {
    const r = object(value); text(r.id, 128);
    requireValue(/^[a-z0-9-]+$/.test(r.id) && !map.has(r.id), 'entry_review_inventory_mismatch');
    requireValue(typeof r.park_code === 'string' && /^[a-z]{4}$/.test(r.park_code));
    requireValue(['reviewed', 'needs_review', 'conflict'].includes(r.review_status));
    requireValue(timestamp(r.reviewed_at) <= now.getTime(), 'invalid_entry_review_clock');
    const e = object(r.evidence); officialUrl(e.url, r.park_code); text(e.excerpt);
    requireValue(e.hash_scope === 'excerpt' && e.reviewed_at === r.reviewed_at);
    requireValue(e.content_hash === createHash('sha256').update(e.excerpt).digest('hex'), 'entry_review_evidence_mismatch');
    guidanceDigest(r); map.set(r.id, value);
  }
  return map;
}
function bind(value: Record<string, any>, map: Map<string, SourceGuidance>, now: Date): SourceGuidance {
  const r = map.get(value.guidance_id); requireValue(r, 'entry_review_inventory_mismatch');
  requireValue(value.guidance_hash === guidanceDigest(r), 'entry_review_revision_mismatch');
  requireValue(value.source_url === r.evidence.url, 'invalid_entry_review_source');
  const checked = timestamp(value.checked_at);
  requireValue(checked > timestamp(r.reviewed_at) && checked <= now.getTime(), 'invalid_entry_review_clock');
  return r;
}
const normalized = (value: string) => value.replace(/[\t\n\r \u00a0]+/g, ' ').trim();
function reasonFor(o: EntrySourceObservation, r: SourceGuidance): EntryReviewReason | null {
  if (o.status === 'missing') return 'excerpt_missing';
  if (o.status === 'failed') return 'check_failed';
  return normalized(o.excerpt!) === normalized(r.evidence.excerpt) ? null : 'text_changed';
}
function proposalFor(o: EntrySourceObservation, r: SourceGuidance): EntryReviewProposal | null {
  const reason = reasonFor(o, r); if (reason === null) return null;
  const core = { guidance_id: r.id, guidance_hash: o.guidance_hash, source_url: o.source_url,
    checked_at: o.checked_at, reason, state: 'pending' as const, before_excerpt: r.evidence.excerpt, after_excerpt: o.excerpt };
  return { id: guidanceDigest(core), ...core };
}
/** Pending registers are trusted review inputs, not signatures or permission to redistribute. */
export function validateEntryReview(value: unknown, records: SourceGuidance[], now: Date): EntryReviewRegister {
  const map = inventory(records, now); const root = shape(value, 'schema_version proposals');
  requireValue(root.schema_version === 1 && Array.isArray(root.proposals) && root.proposals.length <= MAX_PROPOSALS);
  requireValue(Buffer.byteLength(canonical(root)) <= MAX_REGISTER_BYTES, 'entry_review_too_large');
  const ids = new Set<string>(); const instants = new Set<string>();
  for (const value of root.proposals) {
    const p = shape(value, PROPOSAL_FIELDS); const r = bind(p, map, now);
    requireValue(p.state === 'pending' && ['text_changed', 'excerpt_missing', 'check_failed'].includes(p.reason));
    requireValue(p.before_excerpt === r.evidence.excerpt, 'entry_review_evidence_mismatch');
    if (p.reason === 'text_changed') {
      text(p.after_excerpt); requireValue(normalized(p.after_excerpt) !== normalized(p.before_excerpt));
    } else requireValue(p.after_excerpt === null);
    const { id, ...core } = p;
    requireValue(id === guidanceDigest(core) && !ids.has(id), 'entry_review_proposal_mismatch'); ids.add(id);
    const instantKey = `${p.guidance_id}:${timestamp(p.checked_at)}`;
    requireValue(!instants.has(instantKey), 'entry_review_conflicting_observation'); instants.add(instantKey);
  }
  return structuredClone(root) as EntryReviewRegister;
}
/** Pure complete-batch intake. A matching observation never removes a pending proposal. */
export function assessEntrySources(records: SourceGuidance[], values: unknown, pending: unknown, now: Date) {
  const map = inventory(records, now); const register = validateEntryReview(pending, records, now);
  requireValue(Array.isArray(values) && values.length === records.length, 'entry_review_inventory_mismatch');
  const seen = new Set<string>();
  const observations = values.map((value) => {
    const o = shape(value, OBSERVATION_FIELDS); bind(o, map, now);
    requireValue(!seen.has(o.guidance_id), 'entry_review_inventory_mismatch'); seen.add(o.guidance_id);
    requireValue(['observed', 'missing', 'failed'].includes(o.status));
    if (o.status === 'observed') text(o.excerpt); else requireValue(o.excerpt === null);
    return o as EntrySourceObservation;
  });
  requireValue(seen.size === records.length, 'entry_review_inventory_mismatch');
  const checks = observations.map((o) => {
    const r = map.get(o.guidance_id)!; const proposal = proposalFor(o, r);
    const earlier = register.proposals.filter((p) => p.guidance_id === r.id);
    const newest = earlier.reduce((max, p) => Math.max(max, timestamp(p.checked_at)), -Infinity);
    requireValue(timestamp(o.checked_at) >= newest, 'entry_review_older_observation');
    const sameInstant = earlier.find((p) => timestamp(p.checked_at) === timestamp(o.checked_at));
    if (sameInstant) requireValue(proposal?.id === sameInstant.id, 'entry_review_conflicting_observation');
    if (proposal && !sameInstant) register.proposals.push(proposal);
    return { guidance_id: r.id, checked_at: o.checked_at, outcome: reasonFor(o, r) ?? 'matching_excerpt', proposal_id: proposal?.id ?? null };
  });
  register.proposals.sort((a, b) => a.guidance_id.localeCompare(b.guidance_id) || timestamp(a.checked_at) - timestamp(b.checked_at));
  return { register: validateEntryReview(register, records, now), checks };
}

function validateApprovedInventory(records: SourceGuidance[], parks: any[]): void {
  requireValue(Array.isArray(parks) && parks.length > 0, 'entry_review_inventory_mismatch');
  const codes = parks.map((park) => park.code);
  for (const value of records as any[]) {
    const item = object(value);
    if (item.subject_type === 'general_entry') validateEntryNotes([item], codes);
    else validateRule(item, parks);
  }
}

/** Explicit reviewer reconciliation. Clears only complete source-level proposal sets. */
export function reconcileEntryReview(
  current: SourceGuidance[], pending: unknown, proposalIds: unknown,
  nextRecords: SourceGuidance[], reviewedAt: Date, parks: any[],
) {
  const currentMap = inventory(current, reviewedAt);
  const register = validateEntryReview(pending, current, reviewedAt);
  requireValue(Array.isArray(proposalIds) && proposalIds.length > 0 && proposalIds.length <= MAX_PROPOSALS,
    'entry_review_reconciliation_mismatch');
  const selected = new Set<string>();
  for (const id of proposalIds) {
    text(id, 64); requireValue(/^[a-f0-9]{64}$/.test(id) && !selected.has(id), 'entry_review_reconciliation_mismatch');
    selected.add(id);
  }
  const chosen = register.proposals.filter((proposal) => selected.has(proposal.id));
  requireValue(chosen.length === selected.size, 'entry_review_reconciliation_mismatch');
  const sourceUrls = [...new Set(chosen.map((proposal) => proposal.source_url))].sort();
  requireValue(register.proposals.filter((proposal) => sourceUrls.includes(proposal.source_url))
    .every((proposal) => selected.has(proposal.id)), 'entry_review_partial_source_reconciliation');
  for (const proposal of chosen) requireValue(reviewedAt.getTime() > timestamp(proposal.checked_at), 'invalid_entry_review_clock');

  validateApprovedInventory(nextRecords, parks);
  const nextMap = inventory(nextRecords, reviewedAt);
  requireValue(nextMap.size === currentMap.size && [...currentMap.keys()].every((id) => nextMap.has(id)),
    'entry_review_inventory_mismatch');
  const affected = [...currentMap.values()].filter((record) => sourceUrls.includes(record.evidence.url))
    .map((record) => record.id).sort();
  for (const [id, before] of currentMap) {
    const after = nextMap.get(id)!;
    requireValue(Object.keys(after as any).sort().join(' ') === Object.keys(before as any).sort().join(' ')
      && Object.keys(object(after.evidence)).sort().join(' ') === Object.keys(object(before.evidence)).sort().join(' '),
      'entry_review_reconciliation_mismatch');
    requireValue(after.park_code === before.park_code && after.evidence.url === before.evidence.url,
      'entry_review_reconciliation_mismatch');
    if (!sourceUrls.includes(before.evidence.url)) {
      requireValue(canonical(after) === canonical(before), 'entry_review_unrelated_guidance_changed');
      continue;
    }
    requireValue(after.review_status === 'reviewed' && timestamp(after.reviewed_at) === reviewedAt.getTime()
      && after.evidence.reviewed_at === after.reviewed_at, 'entry_review_reconciliation_mismatch');
    const beforeAny = before as any, afterAny = after as any;
    requireValue(afterAny.rights_basis === beforeAny.rights_basis
      && afterAny.rights_reviewed_at === beforeAny.rights_reviewed_at, 'entry_review_rights_changed');
  }
  const remaining = { schema_version: 1 as const, proposals: register.proposals.filter((proposal) => !selected.has(proposal.id)) };
  return { register: validateEntryReview(remaining, nextRecords, reviewedAt),
    affected_guidance_ids: affected, source_urls: sourceUrls };
}

/** Copies approved records and overlays only their review status. Never persists changes. */
export function applyEntryReview<T extends SourceGuidance>(records: T[], pending: unknown, now: Date): { guidance: T[]; holds: EntryHold[] } {
  const register = validateEntryReview(pending, records, now);
  const guidance = structuredClone(records);
  const holds: EntryHold[] = [];
  for (const r of guidance) {
    const proposals = register.proposals.filter((p) => p.guidance_id === r.id)
      .sort((a, b) => timestamp(a.checked_at) - timestamp(b.checked_at));
    if (!proposals.length) continue;
    if (r.review_status !== 'conflict') r.review_status = 'needs_review';
    holds.push({ guidance_id: r.id, park_code: r.park_code, source_url: r.evidence.url,
      first_detected_at: proposals[0].checked_at, latest_held_check_at: proposals.at(-1)!.checked_at,
      reasons: [...new Set(proposals.map((p) => p.reason))].sort(), proposal_count: proposals.length });
  }
  return { guidance, holds };
}
