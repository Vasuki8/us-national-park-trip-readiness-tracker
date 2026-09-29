import assert from 'node:assert/strict';

const OWNERSHIP_URL = 'https://www.nps.gov/aboutus/disclaimer.htm';
const MARKS_URL = 'https://www.nps.gov/subjects/partnerships/arrowhead-requests.htm?fullweb=1';
const COMMERCIAL_NOTICE = 'No protection is claimed in original U.S. Government works.';

function exactKeys(value: any, keys: string[]): void {
  assert.ok(value && typeof value === 'object' && !Array.isArray(value));
  assert.deepEqual(Object.keys(value).sort(), [...keys].sort());
}
function timestamp(value: unknown): void {
  assert.ok(typeof value === 'string' && /^\d{4}-\d{2}-\d{2}T(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\dZ$/.test(value));
  assert.ok(Number.isFinite(Date.parse(value)));
}
export function validateSourceRights(manifest: any, guidance: any[]): void {
  exactKeys(manifest, ['schema_version','scope','reviewed_at','review_method','policy','records']);
  assert.equal(manifest.schema_version, 1);
  assert.equal(manifest.scope, 'public_guidance_text_only');
  assert.equal(manifest.review_method, 'official_nps_policy_and_exact_page_review');
  timestamp(manifest.reviewed_at);

  exactKeys(manifest.policy, ['ownership_url','marks_url','commercial_notice','third_party_material_allowed','nps_marks_allowed','raw_private_captures_public']);
  assert.equal(manifest.policy.ownership_url, OWNERSHIP_URL);
  assert.equal(manifest.policy.marks_url, MARKS_URL);
  assert.equal(manifest.policy.commercial_notice, COMMERCIAL_NOTICE);
  assert.equal(manifest.policy.third_party_material_allowed, false);
  assert.equal(manifest.policy.nps_marks_allowed, false);
  assert.equal(manifest.policy.raw_private_captures_public, false);

  assert.ok(Array.isArray(guidance) && guidance.length > 0);
  assert.ok(Array.isArray(manifest.records));
  assert.equal(manifest.records.length, guidance.length);
  const expected = new Map(guidance.map((row: any) => {
    assert.ok(typeof row?.id === 'string' && typeof row?.evidence?.url === 'string');
    return [row.id, row.evidence.url];
  }));
  assert.equal(expected.size, guidance.length);
  const seen = new Set<string>();
  for (const row of manifest.records) {
    exactKeys(row, ['guidance_id','source_url','classification','use_scope','third_party_material_reproduced','nps_marks_reproduced','media_reproduced']);
    assert.ok(typeof row.guidance_id === 'string' && !seen.has(row.guidance_id));
    seen.add(row.guidance_id);
    assert.equal(row.source_url, expected.get(row.guidance_id));
    assert.equal(row.classification, 'nps_government_text');
    assert.equal(row.use_scope, 'short_text_excerpt_and_original_summary');
    assert.equal(row.third_party_material_reproduced, false);
    assert.equal(row.nps_marks_reproduced, false);
    assert.equal(row.media_reproduced, false);
  }
  assert.deepEqual([...seen].sort(), [...expected.keys()].sort());
}
