"""Private offline editorial ledger. Transactional persistence, never publication.

SQLite is confined to one owner-only POSIX directory outside the repository.
Every read replays source extraction and the existing gate; hashes alone do not
make altered proposal/context data valid. This is not a signature/identity system.
"""
from __future__ import annotations
import copy
import os
import sqlite3
from contextlib import closing
from pathlib import Path
from .entry_sources import canonical, digest
from .entry_review_io import ReviewStoreError, check_path, private_stat, parse_json, require
from .entry_review_model import (MAX_EVENTS, MAX_LEDGER_BYTES, MAX_EVENT_BYTES,
    apply_event, clock, empty_state, make_event, request_key, revision, safe_summary)

DB_NAME = 'review.sqlite3'
SCHEMA = {
    'meta': 'CREATE TABLE meta (id INTEGER PRIMARY KEY CHECK(id=1), version INTEGER NOT NULL, head TEXT)',
    'events': 'CREATE TABLE events (seq INTEGER PRIMARY KEY, revision TEXT NOT NULL UNIQUE, payload BLOB NOT NULL)',
}

class EntryReviewStore:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.path = self.root/DB_NAME

    def _paths(self) -> bool:
        check_path(self.root)
        if not self.root.exists():
            return False
        private_stat(self.root, directory=True)
        require(set(p.name for p in self.root.iterdir()) <= {DB_NAME, DB_NAME+'-journal'}, 'foreign_review_directory')
        for item in self.root.iterdir():
            info = private_stat(item)
            require(info.st_size <= MAX_LEDGER_BYTES + 16 * 1024 * 1024, 'review_storage_too_large')
        if not self.path.exists():
            require(not any(self.root.iterdir()), 'incomplete_review_store')
            return False
        # A read-only SQLite connection may create WAL sidecars. Refuse that format
        # from its documented header before opening SQLite, rather than after.
        fd = os.open(self.path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, 'rb') as stream:
            header = stream.read(100)
        require(header[:16] == b'SQLite format 3\x00' and header[18:20] == b'\x01\x01',
                'unsupported_review_database_format')
        return True

    def _connect(self, *, write: bool):
        conn = sqlite3.connect(self.path.as_uri() + ('?mode=rw' if write else '?mode=ro'),
                               uri=True, timeout=1.0, isolation_level=None)
        try:
            conn.execute('PRAGMA trusted_schema=OFF')
            if write:
                require(conn.execute('PRAGMA journal_mode').fetchone()[0] == 'delete', 'unsupported_review_journal')
                conn.execute('PRAGMA synchronous=EXTRA')
                conn.execute('PRAGMA temp_store=MEMORY')
            return conn
        except BaseException:
            conn.close()
            raise

    def _initialize(self) -> None:
        # Input/expected-head validation happens before this method.
        if not self.root.exists():
            self.root.mkdir(mode=0o700)  # Do not create arbitrary ancestor directories.
        if self._paths():
            return
        fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        os.close(fd)
        with closing(self._connect(write=True)) as conn:
            conn.execute('BEGIN IMMEDIATE')
            for sql in SCHEMA.values():
                conn.execute(sql)
            conn.execute('INSERT INTO meta VALUES (1,1,NULL)')
            conn.execute('COMMIT')
        # A killed initializer may leave a visibly invalid empty DB, never an accepted ledger.

    def _read(self, conn) -> dict:
        tables = dict(conn.execute("SELECT name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'"))
        require(tables == SCHEMA, 'invalid_review_schema')
        require(conn.execute('PRAGMA quick_check').fetchall() == [('ok',)], 'corrupt_review_database')
        rows, total = conn.execute('SELECT count(*),coalesce(sum(length(payload)),0) FROM events').fetchone()
        require(rows <= MAX_EVENTS and total <= MAX_LEDGER_BYTES, 'review_capacity_exceeded')
        meta = conn.execute('SELECT id,version,head FROM meta').fetchall()
        require(len(meta) == 1 and meta[0][:2] == (1,1), 'invalid_review_metadata')
        state = empty_state()
        for expected_seq, (seq, identifier, raw) in enumerate(conn.execute('SELECT seq,revision,payload FROM events ORDER BY seq'), 1):
            require(seq == expected_seq and isinstance(raw, bytes) and len(raw) <= MAX_EVENT_BYTES, 'invalid_review_chain')
            event = parse_json(raw)
            require(canonical(event) == raw and digest(event) == identifier, 'review_digest_mismatch')
            require(isinstance(event, dict) and event.get('previous_revision') == state['revision'], 'invalid_review_chain')
            rebuilt = make_event(event.get('kind'), event.get('request'), state, event.get('saved_at'))
            # Compare JSON identity, not Python equality: True and 1 are distinct evidence.
            require(canonical(rebuilt) == raw, 'review_replay_mismatch')
            state = apply_event(state, event, identifier)
        require(state['revision'] == meta[0][2], 'review_head_mismatch')
        return state

    def read(self) -> dict:
        """Strictly read-only. A hot journal may require the explicit recover command."""
        try:
            if not self._paths():
                return empty_state()
            with closing(self._connect(write=False)) as conn:
                conn.execute('BEGIN')
                return copy.deepcopy(self._read(conn))
        except ReviewStoreError:
            raise
        except (OSError, sqlite3.Error, ValueError, TypeError):
            raise ReviewStoreError('review_store_unreadable') from None

    def _commit(self, conn) -> None:
        """Single commit point; tests interrupt either side in a child process."""
        conn.execute('COMMIT')

    def _write(self, kind: str, request: object, expected_revision, now) -> dict:
        try:
            revision(expected_revision)
            saved_at = clock(now)
            state = self.read()
            key = request_key(kind, request, expected_revision)
            prior = next((e for e in state['events'] if e['operation_id'] == key), None)
            if prior:
                return {**safe_summary(state), 'replayed': True, 'committed_revision': digest(prior)}
            require(state['revision'] == expected_revision, 'stale_review_revision')
            require(len(state['events']) < MAX_EVENTS, 'review_capacity_exceeded')
            event = make_event(kind, request, state, saved_at)
            raw = canonical(event)
            require(sum(len(canonical(e)) for e in state['events']) + len(raw) <= MAX_LEDGER_BYTES, 'review_capacity_exceeded')
            self._initialize()
            self._paths()
            with closing(self._connect(write=True)) as conn:
                conn.execute('BEGIN IMMEDIATE')
                # Check again inside the write transaction, not just before validation.
                locked = self._read(conn)
                if locked['revision'] != expected_revision:
                    prior = next((e for e in locked['events'] if e['operation_id'] == key), None)
                    require(prior, 'stale_review_revision')
                    return {**safe_summary(locked), 'replayed': True, 'committed_revision': digest(prior)}
                identifier = digest(event)
                conn.execute('INSERT INTO events VALUES (?,?,?)', (len(locked['events'])+1, identifier, raw))
                conn.execute('UPDATE meta SET head=? WHERE id=1', (identifier,))
                self._commit(conn)
            result = apply_event(state, event, identifier)
            return {**safe_summary(result), 'replayed': False, 'committed_revision': identifier}
        except ReviewStoreError:
            raise
        except (OSError, sqlite3.Error, ValueError, TypeError, RecursionError):
            raise ReviewStoreError('review_write_failed') from None

    def record(self, request: object, *, expected_revision, now) -> dict:
        return self._write('observation', request, expected_revision, now)

    def disposition(self, request: object, *, expected_revision, now) -> dict:
        return self._write('disposition', request, expected_revision, now)

    def reconcile(self, request: object, *, expected_revision, now) -> dict:
        return self._write('reconciliation', request, expected_revision, now)

    def recover(self) -> dict:
        """Let SQLite recover a hot rollback journal. No event/approval is created."""
        try:
            require(self._paths(), 'review_store_missing')
            with closing(self._connect(write=True)) as conn:
                conn.execute('BEGIN IMMEDIATE')
                state = self._read(conn)
                conn.execute('ROLLBACK')
                return safe_summary(state)
        except ReviewStoreError:
            raise
        except (OSError, sqlite3.Error, ValueError, TypeError):
            raise ReviewStoreError('review_recovery_failed') from None
