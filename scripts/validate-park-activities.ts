/** Build-only contracts for reviewed NPS activity text; no collection or approval. */
import { createHash } from 'node:crypto';
import { closeSync, constants, fstatSync, lstatSync, openSync, readSync } from 'node:fs';
import { dirname, isAbsolute, posix, resolve, sep } from 'node:path';
import { isCalendarDate } from '../src/lib/readiness.ts';

export const MAX_ACTIVITY_BYTES = 42_008_576;
export const MAX_ACTIVITY_RIGHTS_BYTES = 42_008_576;
const CODES = ['yose', 'romo', 'yell', 'zion', 'grca'] as const;
const MAX_RECORD_BYTES = 256 * 1024;
const MAX_INVENTORY_BYTES = 8 * 1024 * 1024;
const TEXT_FIELDS = ['description', 'long_description', 'location', 'location_description', 'duration',
  'duration_description', 'season_description', 'accessibility_information', 'activity_description',
  'fee_description', 'reservation_description', 'pets_description', 'age', 'age_description',
  'time_of_day_description', 'credit'] as const;
const FLAG_FIELDS = ['fees_apply', 'reservation_required', 'pets_permitted', 'pets_permitted_with_restrictions'] as const;
const SEMANTIC = ['id', 'park_code', 'title', 'url', ...TEXT_FIELDS, ...FLAG_FIELDS, 'seasons', 'times_of_day',
  'activity_categories', 'related_parks', 'geographic_relationship', 'responsible_agency', 'difficulty', 'permit_required'];
const RECORD = [...SEMANTIC, 'source_updated_at', 'observed_first_at', 'observed_changed_at', 'content_hash', 'hash_scope'];
const INVENTORY = 'schema_version park_code provider source_url collection_status coverage_status last_checked_at last_successful_fetch_at source_issued_at source_updated_at published_at records error_code'.split(' ');
const POLICY_FIELDS = 'ownership_url marks_url commercial_notice third_party_material_allowed nps_marks_allowed raw_private_captures_public'.split(' ');
const RIGHTS_RECORD = 'park_code activity_id source_url content_hash classification use_scope third_party_material_reproduced nps_marks_reproduced media_reproduced'.split(' ');
const POLICY = {
  ownership_url: 'https://www.nps.gov/aboutus/disclaimer.htm',
  marks_url: 'https://www.nps.gov/subjects/partnerships/arrowhead-requests.htm?fullweb=1',
  commercial_notice: 'No protection is claimed in original U.S. Government works.',
  third_party_material_allowed: false, nps_marks_allowed: false, raw_private_captures_public: false,
};
type ActivityRecord = Record<typeof TEXT_FIELDS[number], string | null>
  & Record<typeof FLAG_FIELDS[number], boolean | null> & {
    id: string; park_code: string; title: string; url: string;
    seasons: string[] | null; times_of_day: string[] | null;
    activity_categories: {id: string; name: string}[] | null;
    related_parks: {park_code: string; full_name: string | null; url: string | null;
      states: string | null; designation: string | null; name: string | null}[];
    geographic_relationship: 'unconfirmed'; responsible_agency: null; difficulty: null; permit_required: null;
    source_updated_at: null; observed_first_at: string; observed_changed_at: string;
    content_hash: string; hash_scope: 'normalized_record';
  };
interface ActivityInventory {
  schema_version: 1; park_code: string; provider: 'NPS'; source_url: string;
  collection_status: 'success' | 'failed' | 'quarantined'; coverage_status: 'checked_activity_feed_only' | 'incomplete';
  last_checked_at: string; last_successful_fetch_at: string;
  source_issued_at: null; source_updated_at: null; published_at: null; records: ActivityRecord[];
  error_code: null | 'provider_request_failed' | 'response_requires_review';
}
interface PublicActivities {schema_version: 1; purpose: 'public_park_activities'; inventories: ActivityInventory[]}
interface ActivityRights {
  schema_version: 1; purpose: 'public_park_activity_text_rights'; reviewed_at: string;
  review_method: 'official_nps_policy_and_exact_activity_review'; policy: typeof POLICY;
  records: {park_code: string; activity_id: string; source_url: string; content_hash: string;
    classification: 'nps_government_text'; use_scope: 'normalized_activity_text_and_metadata';
    third_party_material_reproduced: false; nps_marks_reproduced: false; media_reproduced: false}[];
}
function requireValue(value: unknown): asserts value {
  if (!value) throw new Error('invalid_public_park_activities');
}
function shape(value: unknown, fields: readonly string[]): Record<string, any> {
  requireValue(value && typeof value === 'object' && !Array.isArray(value));
  const keys = Object.keys(value);
  requireValue(keys.length === fields.length && fields.every(field => Object.hasOwn(value, field)));
  return value as Record<string, any>;
}
function unicode(value: string) {
  requireValue(!/[\uD800-\uDBFF](?![\uDC00-\uDFFF])|(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]/u.test(value));
}
// Python compares Unicode scalars rather than JavaScript UTF-16 units.
function scalarOrder(left: string, right: string): number {
  const a = Array.from(left), b = Array.from(right);
  for (let index = 0; index < Math.min(a.length, b.length); index++) {
    const difference = a[index].codePointAt(0)! - b[index].codePointAt(0)!;
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
// Canonical encoding supports the public contract's null/boolean/string/list/object
// values and safe integers. Unreviewed numeric types are deliberately refused.
export function canonicalActivityJson(value: unknown, maxBytes = MAX_ACTIVITY_BYTES): string {
  requireValue(Number.isSafeInteger(maxBytes) && maxBytes > 0);
  const result = canonical(value);
  requireValue(Buffer.byteLength(result, 'utf8') <= maxBytes);
  return result;
}
export function activityDigest(value: unknown, maxBytes = MAX_ACTIVITY_BYTES): string {
  return createHash('sha256').update(canonicalActivityJson(value, maxBytes), 'utf8').digest('hex');
}
function text(value: unknown, empty = false, identifier = false): asserts value is string {
  requireValue(typeof value === 'string' && Array.from(value).length <= (identifier ? 256 : 65_536));
  unicode(value);
  // Python str.strip() includes U+0085 and excludes U+FEFF.
  requireValue(empty || value.replace(/^[\u0009-\u000d\u001c-\u0020\u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]+|[\u0009-\u000d\u001c-\u0020\u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]+$/gu, '').length > 0);
  if (identifier) requireValue(!/[\x00-\x1f\x7f]/.test(value));
}
function optionalText(value: unknown) { if (value !== null) text(value, true); }
function timestamp(value: unknown): bigint {
  text(value);
  const match = /^(\d{4}-\d{2}-\d{2}T(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d)(?:\.(\d{1,6}))?(Z|[+-](?:[01]\d|2[0-3]):[0-5]\d)$/.exec(value);
  requireValue(match && !value.startsWith('0000-') && isCalendarDate(value.slice(0, 10)));
  const base = Date.parse(match[1] + match[3]); requireValue(Number.isFinite(base));
  const year = new Date(base).getUTCFullYear(); requireValue(year >= 1 && year <= 9999);
  return BigInt(base) * 1000n + BigInt((match[2] || '').padEnd(6, '0'));
}
function unquote(value: string): string {
  // urllib.parse.unquote preserves malformed escapes and replaces invalid UTF-8.
  return value.replace(/(?:%[a-f0-9]{2})+/gi, encoded => new TextDecoder('utf-8', {ignoreBOM: true})
    .decode(Buffer.from(encoded.replaceAll('%', ''), 'hex')));
}
function officialUrl(value: unknown, codes: Set<string>, globalActivity = false) {
  text(value); requireValue(!/[\x00-\x20\x7f\\]/.test(value));
  // Use the original path: URL() alone normalizes traversal and repeated segments.
  const original = /^https:\/\/([^/?#]+)([^?#]*)(?:\?([^#]*))?(?:#(.*))?$/is.exec(value);
  requireValue(original && /^(?:www\.)?nps\.gov(?::[0-9]*)?$/i.test(original[1]));
  const url = new URL(value);
  requireValue(url.protocol === 'https:' && ['nps.gov', 'www.nps.gov'].includes(url.hostname.toLowerCase())
    && !url.username && !url.password && !url.port);
  const path = unquote(original[2]), comparison = path.endsWith('/') && path !== '/' ? path.slice(0, -1) : path;
  requireValue(posix.normalize(path).replace(/\/$/, '') === comparison && !path.startsWith('//')
    && !/[\x00-\x20\x7f\\%]/.test(path));
  requireValue([...codes].some(code => path === `/${code}` || path.startsWith(`/${code}/`))
    || globalActivity && path.startsWith('/thingstodo/'));
  // Python re.I adds dotted/dotless I, Kelvin K and long S to ASCII case
  // equivalence. Its dot excludes only LF, including after percent decoding.
  requireValue(!/ap[iİı][^\n]?[kK]ey|to[kK]en|[sſ]ecret/iu
    .test(unquote((original[3] || '') + (original[4] || ''))));
}
function sortedStrings(value: unknown) {
  if (value === null) return;
  requireValue(Array.isArray(value) && value.length <= 1000);
  let previous: string | undefined;
  for (const item of value) {
    text(item); requireValue(previous === undefined || scalarOrder(previous, item) < 0); previous = item;
  }
}
function categories(value: unknown) {
  if (value === null) return;
  requireValue(Array.isArray(value) && value.length <= 1000);
  let previous: string | undefined;
  for (const item of value) {
    const category = shape(item, ['id', 'name']); text(category.id, false, true); text(category.name);
    requireValue(previous === undefined || scalarOrder(previous, category.id) < 0); previous = category.id;
  }
}
function relations(value: unknown, code: string): Set<string> {
  requireValue(Array.isArray(value) && value.length > 0 && value.length <= 1000);
  const result = new Set<string>(); let previous: string | undefined;
  for (const item of value) {
    const relation = shape(item, ['park_code', 'full_name', 'url', 'states', 'designation', 'name']);
    requireValue(typeof relation.park_code === 'string' && /^[a-z]{4}$/.test(relation.park_code));
    requireValue(previous === undefined || scalarOrder(previous, relation.park_code) < 0);
    previous = relation.park_code; result.add(relation.park_code);
    for (const field of ['full_name', 'states', 'designation', 'name']) optionalText(relation[field]);
    if (relation.url !== null) officialUrl(relation.url, new Set([relation.park_code]));
  }
  requireValue(result.has(code)); return result;
}
function validateRecord(value: unknown, code: string, successful: bigint) {
  const r = shape(value, RECORD);
  text(r.id, false, true); text(r.title); requireValue(r.park_code === code);
  officialUrl(r.url, relations(r.related_parks, code), true);
  TEXT_FIELDS.forEach(field => optionalText(r[field]));
  FLAG_FIELDS.forEach(field => requireValue(r[field] === null || typeof r[field] === 'boolean'));
  sortedStrings(r.seasons); sortedStrings(r.times_of_day); categories(r.activity_categories);
  requireValue(r.geographic_relationship === 'unconfirmed'
    && ['responsible_agency', 'difficulty', 'permit_required', 'source_updated_at'].every(field => r[field] === null)
    && r.hash_scope === 'normalized_record');
  canonicalActivityJson(r, MAX_RECORD_BYTES);
  requireValue(r.content_hash === activityDigest(Object.fromEntries(SEMANTIC.map(field => [field, r[field]])), MAX_RECORD_BYTES));
  requireValue(timestamp(r.observed_first_at) <= timestamp(r.observed_changed_at)
    && timestamp(r.observed_changed_at) <= successful);
}
export function validatePublicActivities(value: unknown): PublicActivities {
  try {
    canonicalActivityJson(value);
    const data = shape(value, ['schema_version', 'purpose', 'inventories']);
    requireValue(data.schema_version === 1 && data.purpose === 'public_park_activities'
      && Array.isArray(data.inventories) && data.inventories.length === CODES.length);
    data.inventories.forEach((value: unknown, index: number) => {
      const s = shape(value, INVENTORY), code = CODES[index];
      requireValue(s.schema_version === 1 && s.park_code === code && s.provider === 'NPS'
        && s.source_url === `https://developer.nps.gov/api/v1/thingstodo?parkCode=${code}`
        && s.last_checked_at === data.inventories[0].last_checked_at);
      requireValue(['success', 'failed', 'quarantined'].includes(s.collection_status));
      const success = s.collection_status === 'success';
      requireValue(s.coverage_status === (success ? 'checked_activity_feed_only' : 'incomplete')
        && s.error_code === (success ? null : s.collection_status === 'failed' ? 'provider_request_failed' : 'response_requires_review')
        && ['source_issued_at', 'source_updated_at', 'published_at'].every(field => s[field] === null));
      const checked = timestamp(s.last_checked_at), successful = timestamp(s.last_successful_fetch_at);
      requireValue(successful <= checked && (!success || s.last_checked_at === s.last_successful_fetch_at));
      requireValue(Array.isArray(s.records) && s.records.length <= 5000);
      let previous: string | undefined;
      for (const r of s.records) {
        validateRecord(r, code, successful);
        requireValue(previous === undefined || scalarOrder(previous, r.id) < 0); previous = r.id;
      }
      canonicalActivityJson(s, MAX_INVENTORY_BYTES);
    });
    return structuredClone(data) as PublicActivities;
  } catch { throw new Error('invalid_public_park_activities'); }
}
export function validateActivityRights(value: unknown, dataset: unknown): ActivityRights {
  try {
    const data = validatePublicActivities(dataset); canonicalActivityJson(value, MAX_ACTIVITY_RIGHTS_BYTES);
    const rights = shape(value, ['schema_version', 'purpose', 'reviewed_at', 'review_method', 'policy', 'records']);
    requireValue(rights.schema_version === 1 && rights.purpose === 'public_park_activity_text_rights'
      && rights.review_method === 'official_nps_policy_and_exact_activity_review');
    requireValue(canonical(shape(rights.policy, POLICY_FIELDS)) === canonical(POLICY));
    const reviewed = timestamp(rights.reviewed_at);
    const records = data.inventories.flatMap(s => s.records.map(record => ({inventory: s, record})));
    requireValue(Array.isArray(rights.records) && rights.records.length === records.length);
    // Empty inventories still require a review after their successful or degraded attempt.
    data.inventories.forEach(s => requireValue(reviewed >= timestamp(s.last_checked_at)));
    rights.records.forEach((value: unknown, index: number) => {
      const r = shape(value, RIGHTS_RECORD), {inventory: s, record} = records[index];
      requireValue(r.park_code === s.park_code && r.activity_id === record.id && r.source_url === s.source_url
        && r.content_hash === record.content_hash && r.classification === 'nps_government_text'
        && r.use_scope === 'normalized_activity_text_and_metadata'
        && r.third_party_material_reproduced === false && r.nps_marks_reproduced === false && r.media_reproduced === false);
    });
    return structuredClone(rights) as ActivityRights;
  } catch { throw new Error('invalid_public_park_activity_rights'); }
}
function present(path: string, maxBytes: number): boolean {
  try {
    const stat = lstatSync(path); requireValue(stat.isFile() && stat.size <= maxBytes + 1); return true;
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === 'ENOENT') return false;
    throw error;
  }
}
function readCanonical(path: string, maxBytes: number): unknown {
  const prior = lstatSync(path);
  const fd = openSync(path, constants.O_RDONLY | (constants.O_NOFOLLOW || 0) | (constants.O_NONBLOCK || 0));
  try {
    const stat = fstatSync(fd);
    requireValue(stat.isFile() && stat.dev === prior.dev && stat.ino === prior.ino && stat.size <= maxBytes + 1);
    // One extra byte detects growth without an unbounded read or FIFO traversal.
    const buffer = Buffer.alloc(stat.size + 1); let count = 0;
    while (count < buffer.length) {
      const read = readSync(fd, buffer, count, buffer.length - count, null);
      if (!read) break;
      count += read;
    }
    requireValue(count === stat.size && fstatSync(fd).size === stat.size);
    const text = new TextDecoder('utf-8', {fatal: true, ignoreBOM: true}).decode(buffer.subarray(0, count));
    const value = JSON.parse(text), encoded = canonicalActivityJson(value, maxBytes);
    // This comparison also refuses duplicate keys rather than accepting JSON.parse's last value.
    requireValue(text === encoded || text === encoded + '\n'); return value;
  } finally { closeSync(fd); }
}
function noLinkedAncestors(root: string) {
  // Preserve the supplied components until inspection: resolve() would erase
  // a linked ancestor followed by '..' before it could be refused.
  let directory = isAbsolute(root) ? root : process.cwd() + sep + root;
  for (;;) {
    try { requireValue(!lstatSync(directory).isSymbolicLink()); }
    catch (error) {
      if ((error as NodeJS.ErrnoException).code !== 'ENOENT') throw error;
    }
    const parent = dirname(directory);
    if (parent === directory) return;
    directory = parent;
  }
}
/** root is the public data directory, as for validateData(root). */
export function validateActivityFiles(root: string): PublicActivities | null {
  try {
    noLinkedAncestors(root);
    try { requireValue(lstatSync(resolve(root)).isDirectory()); }
    catch (error) {
      if ((error as NodeJS.ErrnoException).code === 'ENOENT') return null;
      throw error;
    }
    const activities = resolve(root, 'park-activities.json'), rights = resolve(root, 'activity-source-rights.json');
    const activitiesPresent = present(activities, MAX_ACTIVITY_BYTES), rightsPresent = present(rights, MAX_ACTIVITY_RIGHTS_BYTES);
    requireValue(activitiesPresent === rightsPresent);
    if (!activitiesPresent) return null;
    const data = validatePublicActivities(readCanonical(activities, MAX_ACTIVITY_BYTES));
    validateActivityRights(readCanonical(rights, MAX_ACTIVITY_RIGHTS_BYTES), data); return data;
  } catch { throw new Error('invalid_public_park_activity_files'); }
}
