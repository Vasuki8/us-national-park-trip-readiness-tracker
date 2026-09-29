"""Private backup, verification and restore for the entry-review ledger.

Backups are owner-only, content-addressed snapshots of an already replay-verified
SQLite ledger. This module performs no network requests, review decisions,
reconciliation, source capture, or publication.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile
from contextlib import closing
from pathlib import Path

from .entry_review_io import ReviewStoreError, check_path, private_stat, read_private_json, require
from .entry_review_model import MAX_LEDGER_BYTES
from .entry_review_store import DB_NAME, EntryReviewStore
from .entry_sources import canonical, digest

MANIFEST_NAME = 'manifest.json'
BACKUP_FILES = {DB_NAME, MANIFEST_NAME}
MAX_DATABASE_BYTES = MAX_LEDGER_BYTES + 16 * 1024 * 1024
MANIFEST_FIELDS = {
    'schema_version','purpose','backup_id','ledger_revision','event_count',
    'guidance_records','pending_proposals','database_file','database_bytes',
    'database_sha256','network_performed','approval_performed','publication_performed'
}


def _sync_directory(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _sha256(path: Path) -> tuple[int, str]:
    size = 0
    value = hashlib.sha256()
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        while True:
            chunk = stream.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            require(size <= MAX_DATABASE_BYTES, 'review_backup_database_too_large')
            value.update(chunk)
    return size, value.hexdigest()


def _private_directory(path: Path, *, create: bool = False) -> Path:
    target = check_path(Path(path))
    parent = target.parent
    private_stat(parent, directory=True)
    if target.exists():
        private_stat(target, directory=True)
    elif create:
        os.mkdir(target, 0o700)
        _sync_directory(parent)
    return target


def _nonoverlap(left: Path, right: Path) -> None:
    require(left != right and left not in right.parents and right not in left.parents,
            'overlapping_review_backup_paths')


def _copy_file(source: Path, destination: Path) -> None:
    src = os.open(source, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    dst = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(src, 'rb', closefd=False) as reader, os.fdopen(dst, 'wb', closefd=False) as writer:
            total = 0
            while True:
                chunk = reader.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                require(total <= MAX_DATABASE_BYTES, 'review_backup_database_too_large')
                writer.write(chunk)
            writer.flush()
            os.fsync(writer.fileno())
    finally:
        try:
            os.close(src)
        except OSError:
            pass
        try:
            os.close(dst)
        except OSError:
            pass


def _snapshot_database(store: EntryReviewStore, directory: Path, expected: dict) -> Path:
    """Create a transactionally consistent SQLite snapshot and replay it."""
    destination = directory/DB_NAME
    fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    os.close(fd)
    try:
        with closing(store._connect(write=False)) as source, closing(sqlite3.connect(
                destination.as_uri()+'?mode=rw', uri=True, timeout=1.0, isolation_level=None)) as target:
            target.execute('PRAGMA trusted_schema=OFF')
            target.execute('PRAGMA journal_mode=DELETE')
            source.backup(target)
        fd = os.open(destination, os.O_RDONLY | os.O_NOFOLLOW)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
        copied = EntryReviewStore(directory).read()
        require(canonical(copied) == canonical(expected), 'review_backup_source_changed')
        return destination
    except BaseException:
        if destination.exists():
            destination.unlink()
        raise


def _manifest(state: dict, database: Path) -> dict:
    size, sha = _sha256(database)
    core = {
        'schema_version': 1,
        'purpose': 'private_entry_review_backup',
        'ledger_revision': state['revision'],
        'event_count': len(state['events']),
        'guidance_records': len(state['records']),
        'pending_proposals': len(state['register']['proposals']),
        'database_file': DB_NAME,
        'database_bytes': size,
        'database_sha256': sha,
        'network_performed': False,
        'approval_performed': False,
        'publication_performed': False,
    }
    return {**core, 'backup_id': digest(core)}


def _write_manifest(directory: Path, manifest: dict) -> None:
    raw = canonical(manifest)
    fd = os.open(directory/MANIFEST_NAME,
                 os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    _sync_directory(directory)


def _read_database_state(bundle: Path) -> dict:
    database = bundle/DB_NAME
    private_stat(database)
    fd = os.open(database, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        header = stream.read(100)
    require(header[:16] == b'SQLite format 3\x00' and header[18:20] == b'\x01\x01',
            'invalid_review_backup_database')
    store = EntryReviewStore(bundle)
    try:
        with closing(store._connect(write=False)) as conn:
            conn.execute('BEGIN')
            return copy.deepcopy(store._read(conn))
    except ReviewStoreError:
        raise
    except (OSError, sqlite3.Error, ValueError, TypeError):
        raise ReviewStoreError('invalid_review_backup_database') from None


def _validate_manifest(value: object) -> dict:
    require(type(value) is dict and set(value) == MANIFEST_FIELDS, 'invalid_review_backup_manifest')
    require(type(value['schema_version']) is int and value['schema_version'] == 1,
            'invalid_review_backup_manifest')
    require(value['purpose'] == 'private_entry_review_backup', 'invalid_review_backup_manifest')
    require(type(value['ledger_revision']) is str
            and re.fullmatch('[a-f0-9]{64}', value['ledger_revision']),
            'invalid_review_backup_manifest')
    for field in ('event_count','guidance_records','pending_proposals','database_bytes'):
        require(type(value[field]) is int and value[field] >= 0, 'invalid_review_backup_manifest')
    require(value['event_count'] > 0 and value['database_bytes'] > 0
            and value['database_bytes'] <= MAX_DATABASE_BYTES,
            'invalid_review_backup_manifest')
    require(value['database_file'] == DB_NAME, 'invalid_review_backup_manifest')
    require(type(value['database_sha256']) is str
            and re.fullmatch('[a-f0-9]{64}', value['database_sha256']),
            'invalid_review_backup_manifest')
    require(value['network_performed'] is False and value['approval_performed'] is False
            and value['publication_performed'] is False, 'invalid_review_backup_manifest')
    core = {key:value[key] for key in value if key != 'backup_id'}
    require(type(value['backup_id']) is str and value['backup_id'] == digest(core),
            'invalid_review_backup_manifest')
    return copy.deepcopy(value)


def verify_backup(bundle_dir: Path) -> dict:
    """Verify owner-only files, hashes and complete semantic ledger replay."""
    bundle = _private_directory(Path(bundle_dir))
    require({item.name for item in bundle.iterdir()} == BACKUP_FILES, 'invalid_review_backup_contents')
    database, manifest_path = bundle/DB_NAME, bundle/MANIFEST_NAME
    private_stat(database); private_stat(manifest_path)
    manifest = _validate_manifest(read_private_json(manifest_path))
    require(bundle.name == manifest['backup_id'], 'invalid_review_backup_identity')
    size, sha = _sha256(database)
    require(size == manifest['database_bytes'] and sha == manifest['database_sha256'],
            'review_backup_digest_mismatch')
    state = _read_database_state(bundle)
    require(state['revision'] == manifest['ledger_revision']
            and len(state['events']) == manifest['event_count']
            and len(state['records']) == manifest['guidance_records']
            and len(state['register']['proposals']) == manifest['pending_proposals'],
            'review_backup_replay_mismatch')
    return manifest


def create_backup(store: EntryReviewStore, backup_root: Path) -> dict:
    """Create or reuse a deterministic backup of one verified nonempty ledger."""
    state = store.read()
    require(state['revision'] is not None and state['events'], 'review_backup_empty_ledger')
    root = check_path(Path(backup_root))
    store_root = check_path(store.root)
    _nonoverlap(store_root, root)
    private_stat(root.parent, directory=True)
    if root.exists():
        private_stat(root, directory=True)
    else:
        os.mkdir(root, 0o700)
        _sync_directory(root.parent)

    temporary = Path(tempfile.mkdtemp(prefix='.pending-', dir=root))
    os.chmod(temporary, 0o700)
    installed = False
    try:
        database = _snapshot_database(store, temporary, state)
        manifest = _manifest(state, database)
        _write_manifest(temporary, manifest)
        destination = root/manifest['backup_id']
        if destination.exists():
            verified = verify_backup(destination)
            require(canonical(verified) == canonical(manifest), 'review_backup_existing_mismatch')
            return manifest
        os.rename(temporary, destination)
        installed = True
        _sync_directory(root)
        return manifest
    finally:
        if not installed and temporary.exists():
            shutil.rmtree(temporary)


def restore_backup(bundle_dir: Path, destination_root: Path) -> dict:
    """Restore a verified backup into a new private ledger directory."""
    bundle = check_path(Path(bundle_dir))
    manifest = verify_backup(bundle)
    destination = check_path(Path(destination_root))
    _nonoverlap(bundle, destination)
    parent = destination.parent
    private_stat(parent, directory=True)
    require(not destination.exists(), 'review_restore_destination_exists')

    temporary = Path(tempfile.mkdtemp(prefix='.restore-', dir=parent))
    os.chmod(temporary, 0o700)
    installed = False
    try:
        _copy_file(bundle/DB_NAME, temporary/DB_NAME)
        restored = EntryReviewStore(temporary).read()
        require(restored['revision'] == manifest['ledger_revision']
                and len(restored['events']) == manifest['event_count']
                and len(restored['records']) == manifest['guidance_records']
                and len(restored['register']['proposals']) == manifest['pending_proposals'],
                'review_restore_replay_mismatch')
        os.rename(temporary, destination)
        installed = True
        _sync_directory(parent)
        return {
            'schema_version': 1,
            'purpose': 'private_entry_review_restore',
            'backup_id': manifest['backup_id'],
            'ledger_revision': restored['revision'],
            'event_count': len(restored['events']),
            'guidance_records': len(restored['records']),
            'pending_proposals': len(restored['register']['proposals']),
            'network_performed': False,
            'approval_performed': False,
            'publication_performed': False,
        }
    finally:
        if not installed and temporary.exists():
            shutil.rmtree(temporary)


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ReviewStoreError('invalid_review_backup_arguments')


def main(argv: list[str] | None = None) -> int:
    try:
        parser = _Parser(description='Private entry-review ledger backup, verification and restore.')
        sub = parser.add_subparsers(dest='command', required=True)
        backup = sub.add_parser('backup', add_help=False)
        backup.add_argument('--store', required=True, type=Path)
        backup.add_argument('--backup-root', required=True, type=Path)
        verify = sub.add_parser('verify', add_help=False)
        verify.add_argument('--backup', required=True, type=Path)
        restore = sub.add_parser('restore', add_help=False)
        restore.add_argument('--backup', required=True, type=Path)
        restore.add_argument('--destination', required=True, type=Path)
        args = parser.parse_args(argv)
        if args.command == 'backup':
            result = create_backup(EntryReviewStore(args.store), args.backup_root)
        elif args.command == 'verify':
            result = verify_backup(args.backup)
        else:
            result = restore_backup(args.backup, args.destination)
        sys.stdout.write(json.dumps(result, sort_keys=True, separators=(',',':'))+'\n')
        return 0
    except ReviewStoreError as error:
        sys.stderr.write(str(error)+'\n')
        return 2
    except Exception:
        sys.stderr.write('review_backup_operation_failed\n')
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
