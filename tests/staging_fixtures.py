"""Synthetic transport fixtures used with the real collector, never park-condition claims."""
from tracker.alerts import collect, initial_snapshot
T0 = '2026-09-28T20:00:00Z'
T1 = '2026-09-28T21:00:00Z'
T2 = '2026-09-28T22:00:00Z'
T3 = '2026-09-28T23:00:00Z'

def raw(identifier='a', code='yose', **changes):
    return {'id': identifier, 'parkCode': code, 'title': 'Synthetic notice',
            'description': 'Synthetic test text only.', 'category': 'Information',
            'url': f'https://www.nps.gov/{code}/test.htm', **changes}

def feed(records):
    return {'total': str(len(records)), 'start': '0', 'data': records}

def snapshot(at=T0, previous=None, records=None, code='yose'):
    return collect(code, previous or initial_snapshot(code), at,
                   lambda start: feed(records if records is not None else [raw(code=code)]))
