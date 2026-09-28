import { createHash } from 'node:crypto';
import parks from '../../data/parks.json';
import rawRules from '../../data/rules.json';
import yose from '../../data/alerts/yose.json';
import romo from '../../data/alerts/romo.json';
import yell from '../../data/alerts/yell.json';
import zion from '../../data/alerts/zion.json';
import grca from '../../data/alerts/grca.json';
import type { Rule } from './readiness';
export { parks };
export const rules = rawRules as Rule[];
export interface Notice { id: string; title: string; description: string; category: string; url: string; scope_status: string }
export interface Snapshot {
  park_code: string; collection_status: string; last_checked_at: string | null;
  last_successful_fetch_at: string | null; source_updated_at: string | null; records: Notice[];
}
const snapshots = [yose, romo, yell, zion, grca] as Snapshot[];
export const snapshotFor = (code: string): Snapshot => snapshots.find((snapshot) => snapshot.park_code === code)!;
export const rulesFor = (code: string) => rules.filter((rule) => rule.park_code === code);
export const buildInfo = {
  snapshot_id: `pilot-${createHash('sha256').update(JSON.stringify({ parks, rules, snapshots })).digest('hex').slice(0, 12)}`,
  built_at: new Date().toISOString(), published_at: null,
  code_commit: process.env.GITHUB_SHA || null, live_collection_enabled: false,
};
