/** Strict server/build contracts for reviewed public NPS profiles; no collection or approval. */
import { createHash } from 'node:crypto';
import { posix } from 'node:path';
import { isCalendarDate } from '../src/lib/readiness.ts';

export const PROFILE_CODES = ['yose', 'romo', 'yell', 'zion', 'grca'] as const;
export const MAX_PROFILE_BYTES = 8 * 1024 * 1024;
const SNAPSHOT = 'schema_version park_code provider source_url collection_status coverage_status last_checked_at last_successful_fetch_at source_issued_at source_updated_at published_at profile error_code';
const SEMANTIC = 'id park_code full_name url description seasonal_weather activity_categories activity_scope';
const RECORD = `${SEMANTIC} source_updated_at observed_first_at observed_changed_at content_hash hash_scope`;
const POLICY = 'ownership_url marks_url commercial_notice third_party_material_allowed nps_marks_allowed raw_private_captures_public';
const RIGHTS_RECORD = 'park_code profile_id source_url content_hash classification use_scope third_party_material_reproduced nps_marks_reproduced media_reproduced';
const expectedPolicy = {
  ownership_url: 'https://www.nps.gov/aboutus/disclaimer.htm',
  marks_url: 'https://www.nps.gov/subjects/partnerships/arrowhead-requests.htm?fullweb=1',
  commercial_notice: 'No protection is claimed in original U.S. Government works.',
  third_party_material_allowed: false, nps_marks_allowed: false, raw_private_captures_public: false,
};
export interface ParkProfile {
  id: string; park_code: string; full_name: string; url: string; description: string | null;
  seasonal_weather: {kind: 'seasonal_context'; text: string} | null;
  activity_categories: {id: string; name: string}[] | null; activity_scope: 'categories_only';
  source_updated_at: null; observed_first_at: string; observed_changed_at: string;
  content_hash: string; hash_scope: 'normalized_record';
}
export interface ProfileSnapshot {
  schema_version: 1; park_code: string; provider: 'NPS'; source_url: string;
  collection_status: 'success' | 'failed' | 'quarantined'; coverage_status: 'checked_profile_only' | 'incomplete';
  last_checked_at: string; last_successful_fetch_at: string;
  source_issued_at: null; source_updated_at: null; published_at: null; profile: ParkProfile;
  error_code: null | 'provider_request_failed' | 'response_requires_review';
}
export interface PublicProfiles {schema_version: 1; purpose: 'public_park_profiles'; profiles: ProfileSnapshot[]}
export interface ProfileRights {
  schema_version: 1; purpose: 'public_park_profile_text_rights'; reviewed_at: string;
  review_method: 'official_nps_policy_and_exact_profile_review'; policy: typeof expectedPolicy;
  records: {park_code: string; profile_id: string; source_url: string; content_hash: string;
    classification: 'nps_government_text'; use_scope: 'normalized_profile_text_and_category_names';
    third_party_material_reproduced: false; nps_marks_reproduced: false; media_reproduced: false}[];
}
function requireValue(value: unknown): asserts value {
  if (!value) throw new Error('invalid_public_park_profiles');
}
function shape(value: unknown, fields: string): Record<string, any> {
  requireValue(value && typeof value === 'object' && !Array.isArray(value));
  requireValue(Object.keys(value).sort().join(' ') === fields.split(' ').sort().join(' '));
  return value as Record<string, any>;
}
function unicode(value: string) {
  requireValue(!/[\uD800-\uDBFF](?![\uDC00-\uDFFF])|(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]/u.test(value));
}
// Python compares Unicode scalar values, rather than JavaScript's UTF-16 units.
function scalarOrder(left: string, right: string): number {
  const a = Array.from(left), b = Array.from(right);
  for (let i = 0; i < Math.min(a.length, b.length); i++) {
    const difference = a[i].codePointAt(0)! - b[i].codePointAt(0)!;
    if (difference) return difference;
  }
  return a.length - b.length;
}
function canonical(value: unknown, depth = 0): string {
  requireValue(depth <= 24);
  if (value === null || typeof value === 'boolean') return JSON.stringify(value);
  if (typeof value === 'string') { unicode(value); return JSON.stringify(value); }
  if (typeof value === 'number') { requireValue(Number.isSafeInteger(value)); return JSON.stringify(value); }
  if (Array.isArray(value)) return '[' + value.map(item => canonical(item, depth + 1)).join(',') + ']';
  requireValue(value && typeof value === 'object');
  const object = value as Record<string, unknown>;
  return '{' + Object.keys(object).sort(scalarOrder).map(key => {
    unicode(key); return JSON.stringify(key) + ':' + canonical(object[key], depth + 1);
  }).join(',') + '}';
}
export const profileDigest = (value: unknown) => createHash('sha256').update(canonical(value), 'utf8').digest('hex');
export const canonicalProfileJson = canonical;
function bounded(value: unknown) { requireValue(Buffer.byteLength(canonical(value), 'utf8') <= MAX_PROFILE_BYTES); }
function text(value: unknown, empty = false, identifier = false): asserts value is string {
  requireValue(typeof value === 'string' && Array.from(value).length <= (identifier ? 256 : 65_536));
  unicode(value);
  // Match Python str.strip(), including U+0085 and excluding U+FEFF.
  requireValue(empty || value.replace(/^[\u0009-\u000d\u001c-\u0020\u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]+|[\u0009-\u000d\u001c-\u0020\u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]+$/gu, '').length > 0);
  if (identifier) requireValue(!/[\x00-\x1f\x7f]/.test(value));
}
function timestamp(value: unknown): bigint {
  text(value);
  const match = /^(\d{4}-\d{2}-\d{2}T(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d)(?:\.(\d{1,6}))?(Z|[+-](?:[01]\d|2[0-3]):[0-5]\d)$/.exec(value);
  requireValue(match && !value.startsWith('0000-') && isCalendarDate(value.slice(0, 10)));
  const base = Date.parse(match[1] + match[3]); requireValue(Number.isFinite(base));
  const utcYear = new Date(base).getUTCFullYear(); requireValue(utcYear >= 1 && utcYear <= 9999);
  return BigInt(base) * 1000n + BigInt((match[2] || '').padEnd(6, '0'));
}
function unquote(value: string): string {
  // urllib.parse.unquote retains malformed escapes and replaces invalid UTF-8.
  return value.replace(/(?:%[a-f0-9]{2})+/gi, encoded => {
    const bytes = Buffer.from(encoded.replaceAll('%', ''), 'hex');
    return new TextDecoder('utf-8', {ignoreBOM: true}).decode(bytes);
  });
}
function officialUrl(value: unknown, code: string) {
  text(value); requireValue(!/[\x00-\x20\x7f\\]/.test(value));
  const authority = /^https:\/\/([^/?#]+)/i.exec(value)?.[1];
  requireValue(authority && /^(?:www\.)?nps\.gov(?::[0-9]*)?$/i.test(authority));
  const url = new URL(value);
  requireValue(url.protocol === 'https:' && ['nps.gov', 'www.nps.gov'].includes(url.hostname.toLowerCase())
    && !url.username && !url.password && !url.port);
  // Inspect the original path before URL() removes traversal and repeated segments.
  const path = unquote(value.replace(/^https:\/\/[^/]+/i, '').split(/[?#]/)[0]);
  const comparison = path.endsWith('/') && path !== '/' ? path.slice(0, -1) : path;
  const normalized = posix.normalize(path).replace(/\/$/, '');
  requireValue((path === `/${code}` || path.startsWith(`/${code}/`)) && normalized === comparison
    && !path.startsWith('//') && !/[\x00-\x20\x7f\\%]/.test(path));
  requireValue(!/api.?key|token|secret/i.test(unquote(url.search + url.hash)));
}
function record(value: unknown, code: string, successful: bigint) {
  const p = shape(value, RECORD);
  text(p.id, false, true); text(p.full_name); requireValue(p.park_code === code); officialUrl(p.url, code);
  if (p.description !== null) text(p.description, true);
  if (p.seasonal_weather !== null) {
    const weather = shape(p.seasonal_weather, 'kind text');
    requireValue(weather.kind === 'seasonal_context'); text(weather.text, true);
  }
  requireValue(p.activity_scope === 'categories_only');
  if (p.activity_categories !== null) {
    requireValue(Array.isArray(p.activity_categories) && p.activity_categories.length <= 1000);
    let previous: string | undefined;
    for (const value of p.activity_categories) {
      const category = shape(value, 'id name'); text(category.id, false, true); text(category.name);
      requireValue(previous === undefined || scalarOrder(previous, category.id) < 0); previous = category.id;
    }
  }
  requireValue(p.source_updated_at === null && p.hash_scope === 'normalized_record');
  requireValue(p.content_hash === profileDigest(Object.fromEntries(SEMANTIC.split(' ').map(key => [key, p[key]]))));
  requireValue(timestamp(p.observed_first_at) <= timestamp(p.observed_changed_at)
    && timestamp(p.observed_changed_at) <= successful);
}
export function validatePublicProfiles(value: unknown): PublicProfiles {
  try {
    bounded(value); const data = shape(value, 'schema_version purpose profiles');
    requireValue(data.schema_version === 1 && data.purpose === 'public_park_profiles');
    requireValue(Array.isArray(data.profiles) && data.profiles.length === PROFILE_CODES.length);
    data.profiles.forEach((value: unknown, index: number) => {
      const s = shape(value, SNAPSHOT), code = PROFILE_CODES[index];
      requireValue(s.schema_version === 1 && s.park_code === code && s.provider === 'NPS'
        && s.source_url === `https://developer.nps.gov/api/v1/parks?parkCode=${code}`
        && s.last_checked_at === data.profiles[0].last_checked_at);
      requireValue(['success', 'failed', 'quarantined'].includes(s.collection_status));
      const success = s.collection_status === 'success';
      requireValue(s.coverage_status === (success ? 'checked_profile_only' : 'incomplete')
        && s.error_code === (success ? null : s.collection_status === 'failed' ? 'provider_request_failed' : 'response_requires_review'));
      requireValue(['source_issued_at', 'source_updated_at', 'published_at'].every(key => s[key] === null));
      const checked = timestamp(s.last_checked_at), successful = timestamp(s.last_successful_fetch_at);
      requireValue(successful <= checked && (!success || s.last_checked_at === s.last_successful_fetch_at));
      record(s.profile, code, successful);
    });
    return structuredClone(data) as PublicProfiles;
  } catch { throw new Error('invalid_public_park_profiles'); }
}
export function validateProfileRights(value: unknown, dataset: unknown): ProfileRights {
  try {
    const data = validatePublicProfiles(dataset); bounded(value);
    const rights = shape(value, 'schema_version purpose reviewed_at review_method policy records');
    requireValue(rights.schema_version === 1 && rights.purpose === 'public_park_profile_text_rights'
      && rights.review_method === 'official_nps_policy_and_exact_profile_review');
    const reviewed = timestamp(rights.reviewed_at), policy = shape(rights.policy, POLICY);
    requireValue(canonical(policy) === canonical(expectedPolicy));
    requireValue(Array.isArray(rights.records) && rights.records.length === PROFILE_CODES.length);
    rights.records.forEach((value: unknown, index: number) => {
      const r = shape(value, RIGHTS_RECORD), s = data.profiles[index];
      requireValue(r.park_code === s.park_code && r.profile_id === s.profile.id && r.source_url === s.source_url
        && r.content_hash === s.profile.content_hash && r.classification === 'nps_government_text'
        && r.use_scope === 'normalized_profile_text_and_category_names'
        && r.third_party_material_reproduced === false && r.nps_marks_reproduced === false && r.media_reproduced === false
        && reviewed >= timestamp(s.last_checked_at));
    });
    return structuredClone(rights) as ProfileRights;
  } catch { throw new Error('invalid_public_park_profile_rights'); }
}
