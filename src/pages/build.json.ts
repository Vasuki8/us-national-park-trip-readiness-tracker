import { buildInfo } from '../lib/data';
export function GET() { return new Response(JSON.stringify(buildInfo), { headers: { 'Content-Type': 'application/json' } }); }
