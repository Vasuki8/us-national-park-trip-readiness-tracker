"""Read-only candidate visitor view. Projection is not content approval or publication.

Only the verified committed archive chain is read. Pending receipts, private paths
and raw provider responses are never projected. Keep snapshot and history together
through any later, separately reviewed promotion step.
"""
from __future__ import annotations
import copy
from .alerts import initial_snapshot
from .history_model import SEMANTIC_FIELDS, canonical, digest, park_code, require
from .history_store import HistoryStore

MAX_PROJECTION_BYTES = 2 * 1024 * 1024
MAX_VISIBLE_OBSERVATIONS = 20
MAX_VISIBLE_CHANGES = 100


def project_history(store: HistoryStore, code: str, *, limit: int = 20) -> dict:
    """Return {snapshot, history} from one verified read, without I/O writes or clocks."""
    park_code(code)
    require(type(limit) is int and 1 <= limit <= MAX_VISIBLE_OBSERVATIONS, 'invalid_projection_limit')
    entries = store.read(code)
    return _project_entries(entries, code, limit=limit)


def _project_entries(entries: list[dict], code: str, *, limit: int = 20) -> dict:
    """Project a prefix of an already replay-verified chain; never use as verification."""
    park_code(code)
    require(type(limit) is int and 1 <= limit <= MAX_VISIBLE_OBSERVATIONS, 'invalid_projection_limit')
    current = entries[-1]['snapshot'] if entries else initial_snapshot(code)
    observations = []
    for index in range(len(entries) - 1, max(-1, len(entries) - limit - 1), -1):
        entry = entries[index]
        before = {item['id']: item for item in entries[index - 1]['snapshot']['records']} if index else {}
        after = {item['id']: item for item in entry['snapshot']['records']}
        def evidence(records: dict, identifier: str) -> dict | None:
            item = records.get(identifier)
            return {key: item[key] for key in (*SEMANTIC_FIELDS, 'content_hash')} if item else None
        changes = [{'kind': change['kind'], 'record_id': change['record_id'],
                    'before': evidence(before, change['record_id']),
                    'after': evidence(after, change['record_id'])}
                   for change in entry['changes'][:MAX_VISIBLE_CHANGES]]
        observations.append({'observation_id': entry['observation_id'], 'sequence': entry['sequence'],
                             'checked_at': entry['snapshot']['last_checked_at'],
                             'collection_status': entry['snapshot']['collection_status'],
                             'comparison': entry['comparison'], 'change_count': len(entry['changes']),
                             'omitted_changes': len(entry['changes']) - len(changes), 'changes': changes})
    total_changes = sum(len(entry['changes']) for entry in entries)
    history = {'schema_version': 1, 'park_code': code,
               'head_observation_id': entries[-1]['observation_id'] if entries else None,
               'snapshot_hash': digest(current), 'total_observations': len(entries),
               'omitted_observations': len(entries) - len(observations),
               'total_changes': total_changes,
               'omitted_changes': total_changes - sum(len(item['changes']) for item in observations),
               'observations': observations}
    require(len(canonical(history)) <= MAX_PROJECTION_BYTES, 'projection_too_large')
    return copy.deepcopy({'snapshot': current, 'history': history})
