"""Local immutable evidence store. Only an atomic head replacement commits an append.

Use an owner-controlled local filesystem, not a network share. Hashes detect damaged
objects; they are not signatures or protection from an attacker who controls the store.
"""
from __future__ import annotations
import os
import re
import tempfile
from contextlib import contextmanager
from pathlib import Path
from .history_model import (HistoryError, MAX_OBJECT_BYTES, SEMANTIC_FIELDS,
                            SNAPSHOT_FIELDS, canonical, compare, digest, park_code,
                            parse_json, require, validate_snapshot)

MAX_OBSERVATIONS = 4096
MAX_ARCHIVE_BYTES = 256 * 1024 * 1024
MAX_ARCHIVE_ENTRIES = 65536
MAX_RECONSTRUCTED_BYTES = 64 * 1024 * 1024
BUNDLE_FIELDS = {'schema_version', 'sequence', 'previous_id', 'header', 'record_refs', 'comparison', 'changes'}
REF_FIELDS = {'content_hash', 'observed_first_at', 'observed_changed_at'}
_UNSET_HEAD = object()
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def private_storage_destination(root: Path, *, reason: str) -> Path:
    """Refuse ambiguous or checkout-backed private storage before any operation."""
    destination = Path(root)
    require(destination.is_absolute() and '..' not in destination.parts, reason)
    require(not any(part.is_symlink() for part in (destination, *destination.parents)), reason)
    destination = destination.resolve()
    require(destination != PROJECT_ROOT and PROJECT_ROOT not in destination.parents
            and destination not in PROJECT_ROOT.parents, reason)
    return destination

def _identifier(value: object) -> str:
    require(isinstance(value, str) and re.fullmatch('[a-f0-9]{64}', value) is not None, 'invalid_object_id')
    return value

class HistoryStore:
    def __init__(self, root: Path, *, max_observations: int = MAX_OBSERVATIONS, max_bytes: int = MAX_ARCHIVE_BYTES, max_reconstructed_bytes: int = MAX_RECONSTRUCTED_BYTES):
        require(type(max_observations) is int and 0 < max_observations <= MAX_OBSERVATIONS, 'invalid_limit')
        require(type(max_bytes) is int and 0 < max_bytes <= MAX_ARCHIVE_BYTES, 'invalid_limit')
        require(type(max_reconstructed_bytes) is int and 0 < max_reconstructed_bytes <= MAX_RECONSTRUCTED_BYTES, 'invalid_limit')
        self.max_reconstructed_bytes = max_reconstructed_bytes
        self.root = private_storage_destination(root, reason='unsafe_archive_destination')
        self.max_observations, self.max_bytes = max_observations, max_bytes

    def _safe(self, path: Path) -> Path:
        require(path == self.root or self.root in path.parents, 'unsafe_archive_path')
        require(not any(part.is_symlink() for part in (path, *path.parents)), 'symlink_in_archive_path')
        return path

    def _usage(self) -> tuple[int, int]:
        self._safe(self.root)
        size, count = 0, 0
        if self.root.exists():
            require(self.root.is_dir(), 'invalid_archive_root')
            for path in self.root.rglob('*'):
                count += 1
                require(count <= MAX_ARCHIVE_ENTRIES, 'archive_limit')
                self._safe(path)
                if path.is_file():
                    size += path.stat().st_size
                else:
                    require(path.is_dir(), 'invalid_archive_entry')
                require(size <= self.max_bytes, 'archive_limit')
        return size, count

    @contextmanager
    def _writer(self):
        self._safe(self.root); self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        lock = self._safe(self.root / '.writer.lock')
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            raise HistoryError('archive_locked') from None
        try:
            with os.fdopen(fd, 'w', encoding='ascii') as handle:
                handle.write(str(os.getpid())); handle.flush(); os.fsync(handle.fileno())
            yield
        finally:
            lock.unlink()

    @staticmethod
    def _sync_directory(path: Path) -> None:
        if os.name == 'posix':
            fd = os.open(path, os.O_RDONLY)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)

    def _write(self, path: Path, data: bytes, *, immutable: bool) -> None:
        self._safe(path); path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if immutable and path.exists():
            require(path.read_bytes() == data, 'existing_object_mismatch')
            return
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
                temporary = Path(handle.name)
                handle.write(data); handle.flush(); os.fsync(handle.fileno())
            if immutable:
                # No overwrite even if an unexpected writer created the same name.
                os.link(temporary, path)
            else:
                os.replace(temporary, path)
            self._sync_directory(path.parent)
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()

    def _json(self, path: Path) -> object:
        self._safe(path)
        try:
            with path.open('rb') as handle:
                return parse_json(handle.read(MAX_OBJECT_BYTES + 1))
        except FileNotFoundError:
            raise HistoryError('missing_archive_object') from None

    def _object(self, directory: Path, identifier: str) -> dict:
        value = self._json(directory / f'{_identifier(identifier)}.json')
        require(isinstance(value, dict) and digest(value) == identifier, 'archive_hash_mismatch')
        return value

    def _paths(self, code: str) -> tuple[Path, Path]:
        folder = self._safe(self.root / 'parks' / park_code(code))
        return folder / 'head.json', folder / 'observations'

    def _head(self, code: str) -> str | None:
        head, directory = self._paths(code)
        self._safe(head); self._safe(directory)
        if not head.exists():
            require(not directory.exists() or not any(directory.iterdir()), 'missing_archive_head')
            return None
        value = self._json(head)
        require(isinstance(value, dict) and set(value) == {'schema_version', 'observation_id'}, 'invalid_archive_head')
        require(type(value['schema_version']) is int and value['schema_version'] == 1, 'invalid_archive_head')
        return None if value['observation_id'] is None else _identifier(value['observation_id'])

    def _restore(self, bundle: dict) -> dict:
        require(set(bundle) == BUNDLE_FIELDS and type(bundle['schema_version']) is int and bundle['schema_version'] == 1, 'invalid_observation')
        require(type(bundle['sequence']) is int and bundle['sequence'] > 0, 'invalid_sequence')
        header, refs = bundle['header'], bundle['record_refs']
        require(isinstance(header, dict) and set(header) == SNAPSHOT_FIELDS - {'records'}, 'invalid_observation')
        require(isinstance(refs, list) and len(refs) <= 5000, 'invalid_observation')
        records = []
        for ref in refs:
            require(isinstance(ref, dict) and set(ref) == REF_FIELDS, 'invalid_evidence_ref')
            semantic = self._object(self.root / 'evidence', ref['content_hash'])
            require(set(semantic) == set(SEMANTIC_FIELDS), 'invalid_evidence')
            records.append({**semantic, **ref, 'park_code': header['park_code'], 'area_id': None,
                            'scope_status': 'unclassified', 'effective_from': None, 'effective_to': None,
                            'source_updated_at': None, 'hash_scope': 'normalized_record',
                            'evidence_excerpt': semantic['description']})
        return validate_snapshot({**header, 'records': records})

    def read(self, code: str) -> list[dict]:
        """Verify the entire committed chain; return oldest-first reconstructed observations."""
        park_code(code); self._usage()
        _, directory = self._paths(code)
        identifier = self._head(code)
        reverse, seen, reconstructed = [], set(), 0
        while identifier is not None:
            require(identifier not in seen and len(reverse) < self.max_observations, 'history_limit_or_cycle')
            seen.add(identifier)
            bundle = self._object(directory, identifier)
            snapshot = self._restore(bundle)
            reconstructed += len(canonical(snapshot))
            require(reconstructed <= self.max_reconstructed_bytes, 'history_expansion_limit')
            require(snapshot['park_code'] == code, 'cross_park_history')
            reverse.append({'observation_id': identifier, 'snapshot': snapshot, **bundle})
            identifier = bundle['previous_id']
            if identifier is not None:
                _identifier(identifier)
        entries, previous = list(reversed(reverse)), None
        for sequence, entry in enumerate(entries, 1):
            require(entry['sequence'] == sequence, 'broken_sequence')
            expected = compare(previous, entry['snapshot'])
            require(expected['comparison'] != 'duplicate' and entry['comparison'] == expected['comparison'] and entry['changes'] == expected['changes'], 'invalid_semantic_history')
            previous = entry['snapshot']
        return entries

    def _commit_head(self, code: str, identifier: str) -> None:
        head, _ = self._paths(code)
        self._write(head, canonical({'schema_version': 1, 'observation_id': identifier}), immutable=False)

    def append(self, snapshot: dict, *, expected_head: object = _UNSET_HEAD) -> str:
        """Append an already-collected snapshot. Never collect, export or publish website data."""
        if expected_head is not _UNSET_HEAD and expected_head is not None:
            _identifier(expected_head)
        current = validate_snapshot(snapshot)
        code = current['park_code']
        with self._writer():
            entries = self.read(code)
            prior = entries[-1] if entries else None
            if expected_head is not _UNSET_HEAD:
                head = prior['observation_id'] if prior else None
                retry = prior is not None and prior['snapshot'] == current and prior['previous_id'] == expected_head
                require(head == expected_head or retry, 'archive_head_changed')
            difference = compare(prior['snapshot'] if prior else None, current)
            if difference['comparison'] == 'duplicate':
                return prior['observation_id']
            require(len(entries) < self.max_observations, 'history_limit')
            require(sum(len(canonical(entry['snapshot'])) for entry in entries) + len(canonical(current)) <= self.max_reconstructed_bytes, 'history_expansion_limit')
            bundle = {'schema_version': 1, 'sequence': len(entries) + 1,
                      'previous_id': prior['observation_id'] if prior else None,
                      'header': {key: value for key, value in current.items() if key != 'records'},
                      'record_refs': [{key: record[key] for key in sorted(REF_FIELDS)} for record in current['records']],
                      **difference}
            identifier = digest(bundle)
            head, directory = self._paths(code)
            objects = {self.root / 'evidence' / f"{item['content_hash']}.json": canonical({key: item[key] for key in SEMANTIC_FIELDS}) for item in current['records']}
            objects[directory / f'{identifier}.json'] = canonical(bundle)
            size, count = self._usage()
            reserve = sum(len(data) for path, data in objects.items() if not path.exists())
            require(size + reserve + max(map(len, objects.values())) + 1024 <= self.max_bytes and count + len(objects) + 10 <= MAX_ARCHIVE_ENTRIES, 'archive_limit')
            if not head.exists():
                # An explicit empty head distinguishes an interrupted first append
                # from loss of a head that previously referenced committed objects.
                self._write(head, canonical({'schema_version': 1, 'observation_id': None}), immutable=False)
            for path, data in objects.items():
                self._write(path, data, immutable=True)
            self._commit_head(code, identifier)  # Linearization point; all objects exist first.
            return identifier
