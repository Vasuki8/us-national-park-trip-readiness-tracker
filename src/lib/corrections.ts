import type { Rule } from './readiness.ts';
import type { EntryNote } from '../../scripts/validate-entry-notes.ts';
import type { Notice, Snapshot } from './data.ts';
import { siteUrl } from './urls.ts';

export type CorrectionKind = 'rule' | 'note' | 'alert';
export interface CorrectionSource {
  key: string; parkCode: string; parkName: string; kind: CorrectionKind; label: string;
  recordId: string; wording: string; sourceUrl: string | null; sourceLinkLabel: string;
  returnHref: string; facts: { label: string; value: string }[]; draftHref: string;
}
interface CorrectionPark { code: string; name: string; slug: string }
interface CorrectionNotice extends Notice {
  observed_first_at?: string | null; observed_changed_at?: string | null; source_updated_at?: string | null;
}
interface CorrectionInput {
  parks: readonly CorrectionPark[]; rules: readonly Rule[]; notes: readonly EntryNote[];
  snapshots: readonly (Omit<Snapshot, 'records'> & { records: readonly CorrectionNotice[] })[];
}
const labels: Record<CorrectionKind, string> = {
  rule: 'Dated entry guidance', note: 'Undated entry observation', alert: 'Retained NPS notice',
};
const canonicalOrigin = 'https://vasuki8.github.io';
const canonicalBase = '/us-national-park-trip-readiness-tracker/';
const issueDestination = 'https://github.com/Vasuki8/us-national-park-trip-readiness-tracker/issues/new';
const fact = (label: string, value: string | null | undefined, missing = 'Not supplied') => ({ label, value: value ?? missing });

/** Stable public record identity; it never includes a visitor's trip selections. */
export function correctionKey(kind: CorrectionKind, parkCode: string, id: string): string {
  return `${kind}:${parkCode}:${id}`;
}

/** Raw DOM ID. Encode it when constructing a fragment URL. */
export function correctionAnchor(kind: CorrectionKind, parkCode: string, id: string): string {
  if (kind === 'rule') return `entry-rule-${id}`;
  if (kind === 'note') return `entry-note-${id}`;
  return `alert-${parkCode}-${id}`;
}

export function correctionHref(kind: CorrectionKind, parkCode: string, id: string, base: string): string {
  return `${siteUrl('/corrections/', base)}?source=${encodeURIComponent(correctionKey(kind, parkCode, id))}`;
}

/** Build only from the approved public records supplied by the existing data gate. */
export function createCorrectionSources({ parks, rules, notes, snapshots }: CorrectionInput, base: string): CorrectionSource[] {
  const create = (kind: CorrectionKind, parkCode: string, recordId: string, wording: string,
    sourceUrl: string | null, facts: CorrectionSource['facts']): CorrectionSource => {
    const matches = parks.filter((park) => park.code === parkCode);
    if (matches.length !== 1) throw new Error('invalid_correction_park');
    const park = matches[0];
    const anchor = encodeURIComponent(correctionAnchor(kind, parkCode, recordId));
    const path = `/parks/${park.slug}/#${anchor}`;
    const key = correctionKey(kind, parkCode, recordId);
    const label = labels[kind];
    // Use the hosted public page even when this catalog is rendered in a local preview.
    const canonicalPage = canonicalOrigin + siteUrl(path, canonicalBase);
    const body = [
      `Park: ${park.name}`, `Source type: ${label}`, `Public record identity: ${key}`,
      `Park page: ${canonicalPage}`, `Source link: ${sourceUrl ?? 'Not supplied'}`,
      ...facts.map(({ label, value }) => `${label}: ${value}`), '',
      'Correction requested:', '', '', 'Official evidence supporting the correction:', '', '',
      'Do not include personal information, private travel details, booking confirmations or credentials.',
    ].join('\n');
    const params = new URLSearchParams({ title: `Correction: ${park.name} — ${label} (${recordId})`, body });
    return {
      key, parkCode, parkName: park.name, kind, label, recordId, wording, sourceUrl,
      sourceLinkLabel: kind === 'alert' ? 'Source link supplied by NPS' : 'Read the official source',
      returnHref: siteUrl(path, base), facts, draftHref: `${issueDestination}?${params}`,
    };
  };
  const reviewFacts = (review: Rule | EntryNote) => [
    fact('Review status', review.review_status), fact('Source reviewed at', review.reviewed_at),
    fact('Source update time', review.evidence.source_updated_at),
  ];
  return [
    ...rules.map((rule) => create('rule', rule.park_code, rule.id, `${rule.summary}\n\n${rule.exception_note}`, rule.evidence.url, [
      ...reviewFacts(rule), fact('Effective from', rule.effective_from), fact('Effective through', rule.effective_to),
    ])),
    ...notes.map((note) => create('note', note.park_code, note.id, `${note.summary}\n\n${note.limitation}`, note.evidence.url, reviewFacts(note))),
    ...snapshots.flatMap((snapshot) => snapshot.records.map((notice) => create('alert', snapshot.park_code, notice.id,
      `${notice.title}\n\n${notice.description}`, notice.url, [
        fact('Collection status', snapshot.collection_status), fact('Coverage status', snapshot.coverage_status),
        fact('Last attempted check', snapshot.last_checked_at, 'Never'),
        fact('Last successful check', snapshot.last_successful_fetch_at, 'Never'),
        fact('Source update time', snapshot.source_updated_at), fact('Notice source update time', notice.source_updated_at),
        fact('First observed in the feed', notice.observed_first_at), fact('Last observed change', notice.observed_changed_at),
        fact('Notice category', notice.category), fact('Area scope', notice.scope_status),
      ]))),
  ];
}

/** Query text selects an exact allowlisted record; it cannot supply report content. */
export function selectCorrectionSource(sources: readonly CorrectionSource[], search: string): CorrectionSource | undefined {
  const keys = new URLSearchParams(search).getAll('source');
  if (keys.length !== 1 || !keys[0]) return undefined;
  // URLSearchParams replaces invalid UTF-8 and accepts malformed percent escapes.
  // Check only the selected parameter strictly; unrelated query fields stay ignored.
  const sourceParameter = search.replace(/^\?/, '').split('&').find((parameter) => {
    try { return decodeURIComponent(parameter.split('=', 1)[0].replace(/\+/g, ' ')) === 'source'; }
    catch { return false; }
  });
  if (sourceParameter === undefined) return undefined;
  try {
    if (decodeURIComponent(sourceParameter.slice(sourceParameter.indexOf('=') + 1).replace(/\+/g, ' ')) !== keys[0]) return undefined;
  } catch { return undefined; }
  const matches = sources.filter((source) => source.key === keys[0]);
  return matches.length === 1 ? matches[0] : undefined;
}
