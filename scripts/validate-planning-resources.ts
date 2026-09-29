/** Build-only link inventory. Link review is never a rule or conditions check. */
export const PLANNING_CATEGORIES = ['roads', 'facilities', 'camping', 'accessibility', 'fees', 'permits', 'weather'] as const;
export type PlanningCategory = typeof PLANNING_CATEGORIES[number];
export interface PlanningResource {
  park_code: string;
  category: PlanningCategory;
  url: string;
  source_title: string;
  check_prompt: string;
  link_reviewed_at: string;
}
function required(value: unknown): asserts value {
  if (!value) throw new Error('invalid_planning_resources');
}
function shape(value: unknown, fields: string): Record<string, unknown> {
  required(value && typeof value === 'object' && !Array.isArray(value));
  required(Object.keys(value).sort().join(' ') === fields.split(' ').sort().join(' '));
  return value as Record<string, unknown>;
}
function text(value: unknown, maximum: number): asserts value is string {
  required(typeof value === 'string' && value.trim().length > 0 && value.length <= maximum);
  required(!/[\x00-\x1f\x7f]|[\uD800-\uDBFF](?![\uDC00-\uDFFF])|(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]/u.test(value));
}
export function validatePlanningResources(value: unknown, parkCodes: string[], now = new Date()): PlanningResource[] {
  try {
    required(now instanceof Date && Number.isFinite(now.getTime()));
    required(Array.isArray(parkCodes) && parkCodes.length > 0 && parkCodes.length <= 20);
    required(parkCodes.every(code => typeof code === 'string' && /^[a-z]{4}$/.test(code)));
    required(new Set(parkCodes).size === parkCodes.length);
    const envelope = shape(value, 'schema_version review_scope resources');
    required(envelope.schema_version === 1 && envelope.review_scope === 'link_target_only');
    required(Array.isArray(envelope.resources) && envelope.resources.length === parkCodes.length * PLANNING_CATEGORIES.length);
    const seen = new Set<string>();
    for (const value of envelope.resources) {
      const item = shape(value, 'park_code category url source_title check_prompt link_reviewed_at');
      required(typeof item.park_code === 'string' && parkCodes.includes(item.park_code));
      required(typeof item.category === 'string' && (PLANNING_CATEGORIES as readonly string[]).includes(item.category));
      const key = `${item.park_code}:${item.category}`;
      required(!seen.has(key)); seen.add(key);
      text(item.source_title, 160); text(item.check_prompt, 360); text(item.url, 400);
      // Version 1 deliberately accepts only direct NPS park-planning HTML pages.
      // No queries, fragments, redirects-as-shortlinks, credentials or encoded paths.
      required(new RegExp(`^https://www\\.nps\\.gov/${item.park_code}/planyourvisit/[a-z0-9][a-z0-9_-]*\\.htm$`).test(item.url));
      required(new URL(item.url).href === item.url);
      text(item.link_reviewed_at, 20);
      required(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/.test(item.link_reviewed_at) && !item.link_reviewed_at.startsWith('0000-'));
      const time = new Date(item.link_reviewed_at);
      required(Number.isFinite(time.getTime()) && time.getTime() <= now.getTime());
      required(time.toISOString().replace('.000Z', 'Z') === item.link_reviewed_at);
    }
    return structuredClone(envelope.resources) as PlanningResource[];
  } catch { throw new Error('invalid_planning_resources'); }
}
