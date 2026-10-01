"""Private collector-to-archive orchestration. No website output or publication path."""
from __future__ import annotations
import copy
import os
import re
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Callable
from .alerts import collect, initial_snapshot
from .history_model import (HistoryError, MAX_OBJECT_BYTES, canonical, compare,
                            digest, instant, parse_json, require, validate_snapshot)
from .history_store import HistoryStore, private_storage_destination

PILOT_CODES = ('yose', 'romo', 'yell', 'zion', 'grca')
MAX_PENDING_BYTES = 6 * MAX_OBJECT_BYTES
MAX_PENDING_FILES = 32


def _pilot(code: str) -> str:
    require(isinstance(code, str) and code in PILOT_CODES, 'unsupported_park')
    return code


def _head(entries: list[dict]) -> str | None:
    return entries[-1]['observation_id'] if entries else None


class StagingCollector:
    """Single cooperating staging writer; expected-parent checks also guard offline imports.

    The root must be owner-controlled local storage. A receipt is not permission to
    publish, and its digest is an integrity check, not a cryptographic signature.
    """
    def __init__(self, root: Path):
        self.root = private_storage_destination(root, reason='unsafe_staging_destination')
        self.archive = HistoryStore(self.root / 'archive')

    def _safe(self, path: Path) -> Path:
        require(path == self.root or self.root in path.parents, 'unsafe_staging_path')
        require(not any(part.is_symlink() for part in (path, *path.parents)), 'symlink_in_staging_path')
        return path

    def _guard(self) -> int:
        """Bound staging files without creating or changing the directory."""
        self._safe(self.root)
        if not self.root.exists():
            return 0
        require(self.root.is_dir(), 'invalid_staging_root')
        for path in self.root.iterdir():
            self._safe(path)
            require(path.name in ('archive', 'pending', '.stage.lock'), 'unexpected_staging_entry')
            require(path.is_file() if path.name == '.stage.lock' else path.is_dir(), 'invalid_staging_entry')
            if path.name == '.stage.lock':
                require(path.stat().st_size <= 1024, 'invalid_staging_lock')
        folder = self.root / 'pending'
        total = 0
        if folder.exists():
            for count, path in enumerate(folder.iterdir(), 1):
                self._safe(path)
                require(count <= MAX_PENDING_FILES and path.is_file(), 'staging_limit')
                total += path.stat().st_size
                require(path.stat().st_size <= MAX_OBJECT_BYTES and total <= MAX_PENDING_BYTES, 'staging_limit')
                require(path.name in {f'{code}.json' for code in PILOT_CODES}
                        or path.name.startswith('.receipt-') and path.name.endswith('.tmp'), 'unexpected_pending_entry')
        return total

    @contextmanager
    def _writer(self):
        self._guard(); self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        lock = self._safe(self.root / '.stage.lock')
        try:
            fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            raise HistoryError('staging_locked') from None
        try:
            with os.fdopen(fd, 'w', encoding='ascii') as handle:
                handle.write(str(os.getpid())); handle.flush(); os.fsync(handle.fileno())
            yield
        finally:
            lock.unlink()

    def _pending(self, code: str) -> dict | None:
        path = self._safe(self.root / 'pending' / f'{_pilot(code)}.json')
        if not path.exists():
            return None
        require(path.is_file(), 'invalid_receipt')
        with path.open('rb') as handle:
            receipt = parse_json(handle.read(MAX_OBJECT_BYTES + 1))
        require(isinstance(receipt, dict) and set(receipt) == {'receipt_id', 'payload'}, 'invalid_receipt')
        value = receipt['payload']
        require(isinstance(value, dict) and set(value) == {'schema_version', 'park_code', 'expected_head', 'snapshot'}, 'invalid_receipt')
        require(type(value['schema_version']) is int and value['schema_version'] == 1
                and value['park_code'] == code, 'invalid_receipt')
        parent = value['expected_head']
        require(parent is None or isinstance(parent, str) and re.fullmatch('[a-f0-9]{64}', parent) is not None, 'invalid_receipt')
        require(receipt['receipt_id'] == digest(value), 'receipt_hash_mismatch')
        current = validate_snapshot(value['snapshot'])
        require(current['park_code'] == code and current == value['snapshot'], 'invalid_receipt')
        return receipt

    def _save_pending(self, code: str, value: dict) -> dict:
        receipt = {'receipt_id': digest(value), 'payload': value}
        data = canonical(receipt)
        require(self._guard() + 2 * len(data) <= MAX_PENDING_BYTES, 'staging_limit')
        path = self._safe(self.root / 'pending' / f'{code}.json')
        require(not path.exists(), 'pending_recovery_required')
        count = sum(1 for _ in path.parent.iterdir()) if path.parent.exists() else 0
        require(count + 2 <= MAX_PENDING_FILES, 'staging_limit')
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.receipt-', suffix='.tmp', delete=False) as handle:
                temporary = Path(handle.name)
                handle.write(data); handle.flush(); os.fsync(handle.fileno())
            os.link(temporary, path)  # Fail rather than overwrite any outstanding receipt.
            HistoryStore._sync_directory(path.parent)
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()
        return receipt

    def _clear_pending(self, code: str) -> None:
        path = self._safe(self.root / 'pending' / f'{code}.json')
        path.unlink(); HistoryStore._sync_directory(path.parent)

    @staticmethod
    def _committed(entries: list[dict], receipt: dict) -> dict | None:
        value = receipt['payload']
        return next((entry for entry in entries if entry['previous_id'] == value['expected_head']
                     and entry['snapshot'] == value['snapshot']), None)

    @staticmethod
    def _summary(code: str, entry: dict | None) -> dict:
        current = entry['snapshot'] if entry else initial_snapshot(code)
        return {'schema_version': 1, 'scope': 'private_staging_only', 'park_code': code,
                'publication_performed': False, 'site_data_written': False,
                'observation_id': entry['observation_id'] if entry else None,
                'collection_status': current['collection_status'],
                'last_checked_at': current['last_checked_at'],
                'last_successful_fetch_at': current['last_successful_fetch_at'],
                'record_count': len(current['records']),
                'comparison': entry['comparison'] if entry else 'not_compared',
                'change_count': len(entry['changes']) if entry else 0}

    def status(self, code: str) -> dict:
        _pilot(code); self._guard()
        entries = self.archive.read(code); receipt = self._pending(code)
        state = 'idle'
        if receipt:
            if self._committed(entries, receipt):
                state = 'committed_needs_cleanup'
            elif receipt['payload']['expected_head'] == _head(entries):
                compare(entries[-1]['snapshot'] if entries else None, receipt['payload']['snapshot'])
                state = 'pending'
            else:
                state = 'conflict'
        return {**self._summary(code, entries[-1] if entries else None), 'operation': 'status',
                'stage_state': state, 'observation_count': len(entries),
                'writer_locked': (self.root / '.stage.lock').exists(),
                'archive_writer_locked': (self.root / 'archive/.writer.lock').exists(),
                'pending_collection_status': receipt['payload']['snapshot']['collection_status'] if receipt else None,
                'pending_checked_at': receipt['payload']['snapshot']['last_checked_at'] if receipt else None}

    def _finish(self, code: str, receipt: dict, operation: str) -> dict:
        entries = self.archive.read(code)
        committed = self._committed(entries, receipt)
        if committed is None:
            value = receipt['payload']
            identifier = self.archive.append(value['snapshot'], expected_head=value['expected_head'])
            committed = next(entry for entry in self.archive.read(code) if entry['observation_id'] == identifier)
        self._clear_pending(code)
        return {**self._summary(code, committed), 'operation': operation}

    def collect(self, code: str, checked_at: str, fetch_page: Callable[[int], dict]) -> dict:
        _pilot(code); instant(checked_at); self._guard()
        with self._writer():
            require(self._pending(code) is None, 'pending_recovery_required')
            entries = self.archive.read(code)
            previous = entries[-1]['snapshot'] if entries else initial_snapshot(code)
            if entries:
                require(instant(checked_at) > instant(previous['last_checked_at']), 'collection_clock_not_advanced')
            require(not (self.root / 'archive/.writer.lock').exists(), 'archive_locked')
            candidate = collect(code, previous, checked_at, fetch_page)
            try:
                candidate = validate_snapshot(candidate)
            except HistoryError:
                # The archive is stricter than legacy collection (e.g. URL fragments).
                # Keep only the last accepted text, not the rejected response.
                candidate = copy.deepcopy(previous)
                candidate.update(last_checked_at=checked_at, collection_status='quarantined',
                                 coverage_status='incomplete', error_code='response_requires_review')
                candidate = validate_snapshot(candidate)
            compare(previous if entries else None, candidate)
            receipt = self._save_pending(code, {'schema_version': 1, 'park_code': code,
                                               'expected_head': _head(entries), 'snapshot': candidate})
            return self._finish(code, receipt, 'archived')

    def recover(self, code: str) -> dict:
        _pilot(code); self._guard()
        if self._pending(code) is None:
            return {**self.status(code), 'operation': 'nothing_to_recover'}
        with self._writer():
            receipt = self._pending(code)
            if receipt is None:
                return {**self.status(code), 'operation': 'nothing_to_recover'}
            return self._finish(code, receipt, 'recovered')
