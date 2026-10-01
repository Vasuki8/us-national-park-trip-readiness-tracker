"""Offline private candidate bundles. Preparation is neither approval nor publication."""
from __future__ import annotations
import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from .entry_review_io import ReviewStoreError, check_path, private_stat
from .history_model import HistoryError, canonical, digest, require
from .history_projection import project_history
from .history_store import HistoryStore

PILOT_CODES = ('yose', 'romo', 'yell', 'zion', 'grca')
MAX_BUNDLE_BYTES = 10 * 1024 * 1024
MAX_OUTPUT_BYTES = 64 * 1024 * 1024
MAX_OUTPUT_ENTRIES = 128
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def make_bundle(store: HistoryStore, *, data_kind: str = 'unreviewed_source') -> dict:
    require(data_kind in ('synthetic', 'unreviewed_source'), 'invalid_preview_kind')
    body = {'schema_version': 1, 'purpose': 'private_preview', 'data_kind': data_kind,
            'publication_performed': False,
            'views': [project_history(store, code) for code in PILOT_CODES]}
    result = {**body, 'bundle_id': digest(body)}
    require(len(canonical(result)) <= MAX_BUNDLE_BYTES, 'preview_too_large')
    return result


def _safe(path: Path) -> Path:
    require('..' not in path.parts, 'unsafe_preview_path')
    absolute = path.absolute()
    require(not any(p.is_symlink() for p in (absolute, *absolute.parents)), 'unsafe_preview_path')
    return absolute


def _usage(root: Path) -> tuple[int, int]:
    size, count = 0, 0
    for path in root.iterdir():
        _safe(path); info = _private(path)
        count += 1; size += info.st_size
        require(count <= MAX_OUTPUT_ENTRIES and size <= MAX_OUTPUT_BYTES, 'preview_storage_limit')
    return size, count


def _private(path: Path, *, directory: bool = False):
    try:
        return private_stat(path, directory=directory)
    except (ReviewStoreError, OSError):
        raise HistoryError('insecure_preview_storage') from None


def prepare_bundle(archive_dir: Path, output_dir: Path, *, data_kind: str = 'unreviewed_source') -> Path:
    require(os.name == 'posix' and hasattr(os, 'getuid'), 'unsupported_preview_platform')
    require(Path(output_dir).is_absolute(), 'unsafe_preview_destination')
    archive, output = _safe(Path(archive_dir)), _safe(Path(output_dir))
    require(archive != output and archive not in output.parents and output not in archive.parents, 'overlapping_preview_paths')
    require(output != PROJECT_ROOT and PROJECT_ROOT not in output.parents and output not in PROJECT_ROOT.parents, 'unsafe_preview_destination')
    try:
        check_path(output)
    except ReviewStoreError:
        raise HistoryError('unsafe_preview_destination') from None
    _private(output.parent, directory=True)
    if output.exists():
        _private(output, directory=True)
        _usage(output)  # Refuse insecure retained files before creating a writer lock.
    # Verify every archive chain before creating any destination or lock.
    bundle = make_bundle(HistoryStore(archive), data_kind=data_kind); data = canonical(bundle)
    output.mkdir(exist_ok=True, mode=0o700)
    _private(output, directory=True)
    lock = _safe(output/'.bundle-writer.lock')
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise HistoryError('preview_output_locked') from None
    temporary = None
    try:
        with os.fdopen(fd, 'w', encoding='ascii') as handle:
            handle.write(str(os.getpid())); handle.flush(); os.fsync(handle.fileno())
        size, count = _usage(output)
        destination = _safe(output/f"{bundle['bundle_id']}.json")
        if destination.exists():
            require(destination.stat().st_size == len(data), 'existing_preview_mismatch')
            with destination.open('rb') as handle:
                require(handle.read(MAX_BUNDLE_BYTES + 1) == data, 'existing_preview_mismatch')
            return destination
        # Reserve final name + temporary name while the writer lock excludes peers.
        require(count + 2 <= MAX_OUTPUT_ENTRIES and size + 2 * len(data) <= MAX_OUTPUT_BYTES, 'preview_storage_limit')
        with tempfile.NamedTemporaryFile(dir=output, prefix='.pending-', delete=False) as handle:
            temporary = Path(handle.name); handle.write(data); handle.flush(); os.fsync(handle.fileno())
        os.link(temporary, destination)  # Atomic install, never overwrite an existing candidate.
        HistoryStore._sync_directory(output)
        return destination
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
        lock.unlink()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        path = prepare_bundle(args.archive_dir, args.output_dir)
    except (HistoryError, OSError, ValueError, TypeError, KeyError, RecursionError):
        print('Private preview preparation refused; inspect the archive and destination. No production data was written.', file=sys.stderr)
        return 2
    print(json.dumps({'bundle_id': path.stem, 'bundle_file': str(path),
                      'publication_performed': False, 'production_data_written': False}))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
