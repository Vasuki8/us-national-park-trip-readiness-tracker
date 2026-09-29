/** Server/build boundary. Never bundle Node hashing or archive validation into the browser. */
import { createHash } from 'node:crypto';
import { isIP } from 'node:net';
import { posix } from 'node:path';
import { isCalendarDate } from '../src/lib/readiness.ts';
import type { History } from '../src/lib/history.ts';
const HISTORY = 'schema_version park_code head_observation_id snapshot_hash total_observations omitted_observations total_changes omitted_changes observations';
const OBSERVATION = 'observation_id sequence checked_at collection_status comparison change_count omitted_changes changes';
const SEMANTIC = 'category description id title url';
const EVIDENCE = `${SEMANTIC} content_hash`;
const SNAPSHOT = 'schema_version park_code provider source_url collection_status coverage_status last_checked_at last_successful_fetch_at source_updated_at published_at records error_code';
const RECORD = `${EVIDENCE} park_code area_id scope_status effective_from effective_to source_updated_at observed_first_at observed_changed_at hash_scope evidence_excerpt`;
function requireValue(value: unknown, code = 'invalid_history'): asserts value {
  if (!value) throw new Error(code); // Never interpolate untrusted content into diagnostics.
}
function shape(value: unknown, fields: string): Record<string, any> {
  requireValue(value && typeof value === 'object' && !Array.isArray(value));
  requireValue(Object.keys(value).sort().join(' ') === fields.split(' ').sort().join(' '));
  return value as Record<string, any>;
}
const count = (value: unknown, maximum = 40_960_000) => {
  requireValue(Number.isSafeInteger(value) && (value as number) >= 0 && (value as number) <= maximum);
  return value as number;
};
const hash = (value: unknown) => requireValue(typeof value === 'string' && /^[a-f0-9]{64}$/.test(value));
function text(value: unknown, empty = false): asserts value is string {
  requireValue(typeof value === 'string' && value.length <= 65_536 && (empty || value.trim()));
  requireValue(!/[\uD800-\uDBFF](?![\uDC00-\uDFFF])|(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]/u.test(value));
}
function stable(value: unknown, depth = 0): string {
  requireValue(depth <= 15, 'history_too_deep');
  if (value === null) return 'null';
  if (typeof value === 'string' || typeof value === 'boolean') return JSON.stringify(value);
  if (typeof value === 'number') { requireValue(Number.isSafeInteger(value)); return JSON.stringify(value); }
  if (Array.isArray(value)) return `[${value.map((item) => stable(item, depth + 1)).join(',')}]`;
  requireValue(value && typeof value === 'object');
  const object = value as Record<string, unknown>;
  return `{${Object.keys(object).sort().map((key) => `${JSON.stringify(key)}:${stable(object[key], depth + 1)}`).join(',')}}`;
}
export const historyDigest = (value: unknown) => createHash('sha256').update(stable(value), 'utf8').digest('hex');
function timestamp(value: unknown): bigint {
  text(value);
  const match = /^(\d{4}-\d{2}-\d{2}T(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d)(?:\.(\d{1,6}))?(Z|[+-](?:[01]\d|2[0-3]):[0-5]\d)$/.exec(value);
  requireValue(match && !value.startsWith('0000-') && isCalendarDate(value.slice(0, 10)), 'invalid_history_clock');
  const base = Date.parse(match[1] + match[3]);
  requireValue(Number.isFinite(base), 'invalid_history_clock');
  return BigInt(base) * 1000n + BigInt((match[2] || '').padEnd(6, '0'));
}
function source(value: unknown) {
  if (value === null) return;
  text(value);
  requireValue(!/[\x00-\x20\x7f\\]/.test(value), 'invalid_history_source');
  try {
    const url = new URL(value);
    const host = url.hostname.toLowerCase();
    // Inspect the original path too: URL() normalizes dot segments before exposing pathname.
    const path = decodeURIComponent(value.replace(/^https:\/\/[^/]+/, '').split(/[?#]/)[0]);
    requireValue(url.protocol === 'https:' && host && host !== 'localhost' && isIP(host) === 0
      && !url.username && !url.password && !url.port
      && !(host.includes('nps.gov') && host !== 'nps.gov' && !host.endsWith('.nps.gov'))
      && (!path || posix.normalize(path) === path) && !path.includes('\\')
      && !/api.?key|token|secret/i.test(decodeURIComponent(url.search + url.hash)), 'invalid_history_source');
  } catch { throw new Error('invalid_history_source'); }
}
function evidence(value: unknown, code: string, identifier: string) {
  const item = shape(value, EVIDENCE);
  for (const key of SEMANTIC.split(' ')) if (key !== 'url') text(item[key], key === 'description');
  requireValue(item.id === identifier && item.id.length <= 256 && !/[\x00-\x1f\x7f]/.test(item.id));
  source(item.url); hash(item.content_hash);
  requireValue(historyDigest(Object.fromEntries(SEMANTIC.split(' ').map((key) => [key, item[key]]))) === item.content_hash, 'history_evidence_mismatch');
  return item;
}
function snapshot(value: unknown) {
  const s = shape(value, SNAPSHOT);
  requireValue(s.schema_version === 1 && typeof s.park_code === 'string' && /^[a-z]{4}$/.test(s.park_code));
  requireValue(s.provider === 'NPS' && s.source_url === `https://developer.nps.gov/api/v1/alerts?parkCode=${s.park_code}`);
  requireValue(s.published_at === null && s.source_updated_at === null);
  requireValue(Array.isArray(s.records) && s.records.length <= 5000);
  if (s.collection_status === 'never_checked') {
    requireValue(s.coverage_status === 'not_collected' && s.error_code === null && s.last_checked_at === null && s.last_successful_fetch_at === null && s.records.length === 0);
  } else {
    requireValue(['success', 'failed', 'quarantined'].includes(s.collection_status));
    const success = s.collection_status === 'success';
    requireValue(s.coverage_status === (success ? 'checked_feed_only' : 'incomplete'));
    requireValue(s.error_code === (success ? null : s.collection_status === 'failed' ? 'provider_request_failed' : 'response_requires_review'));
    const checked = timestamp(s.last_checked_at);
    const good = s.last_successful_fetch_at === null ? null : timestamp(s.last_successful_fetch_at);
    requireValue(good === null ? s.records.length === 0 : good <= checked);
    if (success) requireValue(s.last_checked_at === s.last_successful_fetch_at);
    const ids = new Set();
    for (const value of s.records) {
      const r = shape(value, RECORD); requireValue(!ids.has(r.id)); ids.add(r.id);
      evidence(Object.fromEntries(EVIDENCE.split(' ').map((key) => [key, r[key]])), s.park_code, r.id);
      requireValue(r.park_code === s.park_code && r.scope_status === 'unclassified' && r.hash_scope === 'normalized_record' && r.evidence_excerpt === r.description);
      requireValue(['area_id', 'effective_from', 'effective_to', 'source_updated_at'].every((key) => r[key] === null));
      requireValue(good !== null && timestamp(r.observed_first_at) <= timestamp(r.observed_changed_at) && timestamp(r.observed_changed_at) <= good);
    }
  }
  return s;
}
export function validateHistory(value: unknown, currentSnapshot: unknown): History {
  const h = shape(value, HISTORY); const s = snapshot(currentSnapshot);
  requireValue(Buffer.byteLength(stable(h), 'utf8') <= 2 * 1024 * 1024, 'history_too_large');
  requireValue(h.schema_version === 1 && h.park_code === s.park_code);
  hash(h.snapshot_hash); requireValue(h.snapshot_hash === historyDigest(s), 'history_snapshot_mismatch');
  count(h.total_observations, 4096); count(h.omitted_observations, 4096); count(h.total_changes); count(h.omitted_changes);
  requireValue(Array.isArray(h.observations) && h.observations.length <= 20);
  requireValue(h.omitted_observations === h.total_observations - h.observations.length);
  if (h.total_observations === 0) {
    requireValue(h.head_observation_id === null && s.collection_status === 'never_checked' && h.total_changes === 0 && h.omitted_changes === 0);
  } else {
    hash(h.head_observation_id); requireValue(h.observations.length > 0 && s.collection_status !== 'never_checked');
    requireValue(h.observations[0].observation_id === h.head_observation_id && h.observations[0].checked_at === s.last_checked_at && h.observations[0].collection_status === s.collection_status);
  }
  const ids = new Set(); let newer: bigint | null = null; let shown = 0; let visibleTotal = 0;
  const state = new Map<string, string>(s.records.map((r: any) => [r.id, r.content_hash]));
  let reconstructable = true;
  for (let index = 0; index < h.observations.length; index++) {
    const o = shape(h.observations[index], OBSERVATION); hash(o.observation_id);
    requireValue(!ids.has(o.observation_id)); ids.add(o.observation_id);
    requireValue(o.sequence === h.total_observations - index && Number.isSafeInteger(o.sequence));
    const time = timestamp(o.checked_at); requireValue(newer === null || time < newer); newer = time;
    requireValue(['success', 'failed', 'quarantined'].includes(o.collection_status));
    requireValue(['baseline', 'compared', 'not_compared'].includes(o.comparison));
    requireValue((o.collection_status === 'success') === (o.comparison !== 'not_compared'));
    count(o.change_count, 10000); count(o.omitted_changes, 10000);
    requireValue(Array.isArray(o.changes) && o.changes.length === Math.min(100, o.change_count));
    requireValue(o.omitted_changes === o.change_count - o.changes.length);
    if (o.comparison !== 'compared') requireValue(o.change_count === 0);
    if (o.comparison === 'baseline') requireValue(!h.observations.slice(index + 1).some((prior: any) => prior.collection_status === 'success'));
    if (o.sequence === 1 && o.collection_status === 'success') requireValue(o.comparison === 'baseline');
    const eventIds = new Set();
    for (const value of o.changes) {
      const c = shape(value, 'kind record_id before after'); text(c.record_id);
      requireValue(!eventIds.has(c.record_id)); eventIds.add(c.record_id);
      requireValue(['added', 'edited', 'removed'].includes(c.kind));
      requireValue((c.before === null) === (c.kind === 'added') && (c.after === null) === (c.kind === 'removed'));
      if (c.before !== null) evidence(c.before, h.park_code, c.record_id);
      if (c.after !== null) evidence(c.after, h.park_code, c.record_id);
      if (c.kind === 'edited') requireValue(c.before.content_hash !== c.after.content_hash);
      if (reconstructable) requireValue(c.after === null ? !state.has(c.record_id) : state.get(c.record_id) === c.after.content_hash, 'history_state_mismatch');
    }
    if (o.omitted_changes) reconstructable = false;
    if (reconstructable) for (const c of o.changes) {
      if (c.before === null) state.delete(c.record_id); else state.set(c.record_id, c.before.content_hash);
    }
    shown += o.changes.length; visibleTotal += o.change_count;
  }
  const lastVisibleSuccess = h.observations.find((o: any) => o.collection_status === 'success');
  if (lastVisibleSuccess) requireValue(s.last_successful_fetch_at === lastVisibleSuccess.checked_at, 'history_success_clock_mismatch');
  else if (h.observations.length) {
    if (!h.omitted_observations) requireValue(s.last_successful_fetch_at === null, 'history_success_clock_mismatch');
    else if (s.last_successful_fetch_at !== null) requireValue(timestamp(s.last_successful_fetch_at) < timestamp(h.observations.at(-1).checked_at), 'history_success_clock_mismatch');
  }
  requireValue(h.total_changes >= visibleTotal && h.omitted_changes === h.total_changes - shown);
  if (!h.omitted_observations) requireValue(h.total_changes === visibleTotal);
  return structuredClone(h) as History;
}
