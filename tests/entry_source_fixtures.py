"""Synthetic full-body fixtures for cross-language verification, never live data."""
from __future__ import annotations
import json
import sys
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from tracker.entry_sources import PROFILES, inspect_entry_sources

NOW = datetime(2026, 9, 30, 1, tzinfo=timezone.utc)

def synthetic_guidance():
    """Load fixed test guidance whose review clocks match the historic scenarios."""
    fixture = json.loads((Path(__file__).resolve().parent/'fixtures'/'synthetic-guidance.json').read_text())
    if fixture['purpose'] != 'synthetic_test_guidance':
        raise ValueError('invalid_synthetic_guidance_fixture')
    return fixture

def make_fixture(records, scenario):
    captures = []
    for code, profile in PROFILES.items():
        items = [r for r in records if r['park_code'] == code]
        html = '<!doctype html><html><head><title>Synthetic fixture</title></head><body>'
        html += '<h1>'+escape(profile['heading'])+'</h1>'
        html += ''.join('<p>'+escape(r['evidence']['excerpt'])+'</p>' for r in items)
        html += '<details><summary>Test-only surrounding context</summary><p>Synthetic exception clause, not park guidance.</p></details>'
        html += f'<a href="/{code}/planyourvisit/permits.htm">Test-only context link</a></body></html>'
        captures.append({'source_url': profile['url'], 'final_url': profile['url'], 'checked_at':'2026-09-28T21:00:00Z',
            'status':'success', 'content_type':'text/html', 'html': html})
    initial = inspect_entry_sources(records, captures, [], NOW)
    baselines = [{'schema_version':1, 'source_url':s['source_url'], 'profile_id':s['profile_id'],
        'guidance_hashes':s['guidance_hashes'], 'checked_at':s['checked_at'], 'reviewed_at':'2026-09-28T22:00:00Z',
        'context':s['context'], 'context_hash':s['context_hash']} for s in initial['sources']]
    for c in captures:
        c['checked_at'] = '2026-09-28T23:00:00Z' if scenario != 'recovered' else '2026-09-29T00:00:00Z'
        if scenario == 'context_changed':
            c['html'] = c['html'].replace('</body>', '<section><h2>Test-only added exception</h2><p>Synthetic changed provision.</p></section></body>')
        elif scenario == 'ambiguous':
            code = next(code for code,p in PROFILES.items() if p['url'] == c['source_url'])
            c['html'] = c['html'].replace('</body>', '<h1>'+escape(PROFILES[code]['heading'])+'</h1></body>')
        elif scenario == 'missing':
            for r in records:
                if r['evidence']['url'] == c['source_url']:
                    c['html'] = c['html'].replace(escape(r['evidence']['excerpt']), 'Test-only statement removed.')
    return inspect_entry_sources(records, captures, [] if scenario == 'no_baseline' else baselines, NOW)

if __name__ == '__main__':
    payload = json.load(sys.stdin)
    print(json.dumps(make_fixture(payload['records'], payload['scenario']), ensure_ascii=False))
