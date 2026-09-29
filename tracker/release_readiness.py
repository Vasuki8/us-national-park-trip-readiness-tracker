"""Conservative, read-only pilot release-readiness reporting.

This module never deploys, indexes, enables advertising, contacts providers, or
writes project/private state. Missing evidence is never interpreted as a pass.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from .entry_review_backup import verify_backup
from .entry_review_io import REPO_ROOT, ReviewStoreError
from .entry_review_store import EntryReviewStore
from .entry_sources import PROFILES

GATE_ORDER = (
    'durable_source_review',
    'nps_alert_api',
    'storage_backup',
    'source_rights',
    'hosting_rollback',
    'indexing',
    'advertising',
)
GATE_NAMES = {
    'durable_source_review': 'Durable source review',
    'nps_alert_api': 'NPS alert API validation',
    'storage_backup': 'Private storage backup',
    'source_rights': 'Source-rights review',
    'hosting_rollback': 'Hosting and rollback',
    'indexing': 'Search indexing',
    'advertising': 'Advertising readiness',
}
STATUSES = {'pass','blocked','not_checked'}


def _gate(identifier: str, status: str, reason: str, evidence: dict) -> dict:
    if identifier not in GATE_NAMES or status not in STATUSES:
        raise ReviewStoreError('invalid_release_readiness_state')
    return {
        'id': identifier,
        'name': GATE_NAMES[identifier],
        'status': status,
        'blocking': status != 'pass',
        'reason': reason,
        'evidence': evidence,
    }


def _read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError, TypeError, UnicodeError):
        raise ReviewStoreError('release_readiness_repository_unreadable') from None


def _durable_review(private_state: dict | None) -> dict:
    if private_state is None:
        return _gate('durable_source_review','not_checked',
                     'private_ledger_not_supplied', {
                         'approved_v2_sources': None,
                         'required_sources': len(PROFILES),
                         'pending_proposals': None,
                     })
    try:
        revision = private_state.get('revision')
        events = private_state.get('events')
        register = private_state.get('register')
        baselines = private_state.get('baselines')
        if not isinstance(revision,str) or not re.fullmatch('[a-f0-9]{64}', revision):
            return _gate('durable_source_review','blocked','private_ledger_has_no_verified_head', {
                'approved_v2_sources': 0,'required_sources':len(PROFILES),'pending_proposals':None})
        if not isinstance(events,list) or not events:
            return _gate('durable_source_review','blocked','no_durable_source_observation', {
                'approved_v2_sources': 0,'required_sources':len(PROFILES),'pending_proposals':None})
        proposals = register.get('proposals',[]) if isinstance(register,dict) else []
        required = {profile['url'] for profile in PROFILES.values()}
        approved = {
            baseline.get('source_url')
            for baseline in baselines if isinstance(baseline,dict)
            and baseline.get('schema_version') == 2
            and baseline.get('source_url') in required
        } if isinstance(baselines,list) else set()
        pending = len(proposals) if isinstance(proposals,list) else None
        status = 'pass' if approved == required and pending == 0 else 'blocked'
        reason = 'all_sources_have_explicit_reviewed_context' if status == 'pass' else 'durable_review_incomplete'
        return _gate('durable_source_review',status,reason, {
            'approved_v2_sources': len(approved),
            'required_sources': len(required),
            'pending_proposals': pending,
        })
    except Exception:
        raise ReviewStoreError('invalid_release_readiness_private_state') from None


def _alerts(root: Path) -> dict:
    rows = []
    for code in PROFILES:
        value = _read_json(root/'data'/'alerts'/f'{code}.json')
        rows.append(value)
    never_checked = sum(1 for row in rows if row.get('collection_status') == 'never_checked')
    successful = sum(1 for row in rows
                     if row.get('collection_status') == 'success'
                     and row.get('last_successful_fetch_at') is not None)
    if never_checked:
        return _gate('nps_alert_api','blocked','public_alert_snapshots_never_checked', {
            'snapshots': len(rows),'never_checked':never_checked,'successful':successful})
    if successful == len(rows):
        return _gate('nps_alert_api','not_checked','success_present_but_freshness_and_provider_compatibility_need_release_validation', {
            'snapshots':len(rows),'never_checked':0,'successful':successful})
    return _gate('nps_alert_api','blocked','public_alert_collection_incomplete', {
        'snapshots':len(rows),'never_checked':never_checked,'successful':successful})


def _backup(private_state: dict | None, backup_manifest: dict | None) -> dict:
    if private_state is None:
        return _gate('storage_backup','not_checked','private_ledger_not_supplied', {
            'backup_verified':False,'head_matches':None})
    revision = private_state.get('revision') if isinstance(private_state,dict) else None
    if backup_manifest is None:
        return _gate('storage_backup','blocked','verified_backup_not_supplied', {
            'backup_verified':False,'head_matches':None})
    current_events = private_state.get('events',[]) if isinstance(private_state,dict) else []
    head_matches = (
        isinstance(backup_manifest,dict)
        and backup_manifest.get('purpose') == 'private_entry_review_backup'
        and backup_manifest.get('ledger_revision') == revision
        and backup_manifest.get('event_count') == len(current_events)
    )
    return _gate('storage_backup','pass' if head_matches else 'blocked',
                 'verified_backup_matches_current_head' if head_matches else 'backup_does_not_match_current_ledger', {
                     'backup_verified':True,'head_matches':head_matches})


def _rights(root: Path) -> dict:
    records = _read_json(root/'data'/'rules.json') + _read_json(root/'data'/'entry-notes.json')
    complete = sum(
        1 for row in records
        if isinstance(row,dict)
        and isinstance(row.get('rights_basis'),str) and row['rights_basis'].strip()
        and isinstance(row.get('rights_reviewed_at'),str) and row['rights_reviewed_at'].strip()
    )
    if complete != len(records):
        return _gate('source_rights','blocked','guidance_rights_metadata_incomplete', {
            'guidance_records_total':len(records),'guidance_records_with_rights_metadata':complete})
    return _gate('source_rights','not_checked','external_source_content_rights_review_not_recorded', {
        'guidance_records_total':len(records),'guidance_records_with_rights_metadata':complete})


def _workflow_text(root: Path) -> str:
    folder = root/'.github'/'workflows'
    if not folder.exists():
        return ''
    chunks = []
    for path in sorted(folder.glob('*')):
        if path.is_file():
            try:
                chunks.append(path.read_text(encoding='utf-8').lower())
            except (OSError, UnicodeError):
                raise ReviewStoreError('release_readiness_repository_unreadable') from None
    return '\n'.join(chunks)


def _hosting(root: Path) -> dict:
    text = _workflow_text(root)
    markers = (
        'actions/deploy-pages','cloudflare/pages-action','wrangler pages deploy',
        'vercel','netlify','pages: write','deploy-pages',
    )
    found = sorted(marker for marker in markers if marker in text)
    if not found:
        return _gate('hosting_rollback','blocked','no_production_deployment_path_configured', {
            'deployment_markers':[],'rollback_verified':False})
    return _gate('hosting_rollback','not_checked','deployment_configuration_present_but_live_url_and_rollback_not_verified', {
        'deployment_markers':found,'rollback_verified':False})


def _indexing(root: Path) -> dict:
    try:
        layout = (root/'src'/'layouts'/'Layout.astro').read_text(encoding='utf-8').lower()
        robots = (root/'public'/'robots.txt').read_text(encoding='utf-8').lower()
        headers = (root/'public'/'_headers').read_text(encoding='utf-8').lower()
    except (OSError, UnicodeError):
        raise ReviewStoreError('release_readiness_repository_unreadable') from None
    meta = 'noindex' in layout
    robots_block = bool(re.search(r'(?m)^\s*disallow:\s*/\s*$', robots))
    header = 'x-robots-tag' in headers and 'noindex' in headers
    disabled = meta or robots_block or header
    return _gate('indexing','blocked' if disabled else 'not_checked',
                 'indexing_explicitly_disabled' if disabled else 'indexing_controls_removed_but_live_crawlability_not_verified', {
                     'meta_noindex':meta,
                     'robots_disallow_all':robots_block,
                     'header_noindex':header,
                 })


def _advertising(root: Path) -> dict:
    markers = ('adsbygoogle','googlesyndication','google_ad_client','data-ad-client','doubleclick.net')
    found = set()
    for folder in (root/'src', root/'public'):
        if not folder.exists():
            continue
        for path in folder.rglob('*'):
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding='utf-8', errors='ignore').lower()
            except OSError:
                raise ReviewStoreError('release_readiness_repository_unreadable') from None
            found.update(marker for marker in markers if marker in text)
    if not found:
        return _gate('advertising','blocked','advertising_not_enabled', {
            'ad_integration_markers':[]})
    return _gate('advertising','not_checked','ad_integration_present_but_policy_and_consent_readiness_not_verified', {
        'ad_integration_markers':sorted(found)})


def evaluate_readiness(root: Path = REPO_ROOT, *, private_state: dict | None = None,
                       backup_manifest: dict | None = None) -> dict:
    """Return a deterministic report. This function performs no network or writes."""
    root = Path(root)
    gates = [
        _durable_review(private_state),
        _alerts(root),
        _backup(private_state, backup_manifest),
        _rights(root),
        _hosting(root),
        _indexing(root),
        _advertising(root),
    ]
    if [gate['id'] for gate in gates] != list(GATE_ORDER):
        raise ReviewStoreError('invalid_release_readiness_state')
    summary = {status:sum(1 for gate in gates if gate['status'] == status)
               for status in ('pass','blocked','not_checked')}
    release_ready = all(gate['status'] == 'pass' for gate in gates)
    return {
        'schema_version':1,
        'purpose':'pilot_release_readiness',
        'release_ready':release_ready,
        'summary':summary,
        'gates':gates,
        'network_performed':False,
        'writes_performed':False,
        'deployment_performed':False,
        'indexing_changed':False,
        'advertising_changed':False,
    }


def _text(report: dict) -> str:
    lines = [f"Pilot release readiness: {'READY' if report['release_ready'] else 'BLOCKED'}"]
    labels = {'pass':'PASS','blocked':'BLOCKED','not_checked':'NOT CHECKED'}
    for gate in report['gates']:
        lines.append(f"[{labels[gate['status']]}] {gate['name']} — {gate['reason']}")
    summary = report['summary']
    lines.append(f"Summary: {summary['pass']} pass, {summary['blocked']} blocked, {summary['not_checked']} not checked")
    return '\n'.join(lines)+'\n'


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ReviewStoreError('invalid_release_readiness_arguments')


def main(argv: list[str] | None = None) -> int:
    try:
        parser = _Parser(description='Read-only pilot release-readiness report.')
        parser.add_argument('--format', choices=('text','json'), default='text')
        parser.add_argument('--store', type=Path)
        parser.add_argument('--backup', type=Path)
        args = parser.parse_args(argv)
        if args.backup is not None and args.store is None:
            raise ReviewStoreError('invalid_release_readiness_arguments')
        private = EntryReviewStore(args.store).read() if args.store is not None else None
        backup = verify_backup(args.backup) if args.backup is not None else None
        report = evaluate_readiness(REPO_ROOT, private_state=private, backup_manifest=backup)
        if args.format == 'json':
            sys.stdout.write(json.dumps(report,sort_keys=True,separators=(',',':'))+'\n')
        else:
            sys.stdout.write(_text(report))
        return 0 if report['release_ready'] else 1
    except ReviewStoreError as error:
        sys.stderr.write(str(error)+'\n')
        return 2
    except Exception:
        sys.stderr.write('release_readiness_failed\n')
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
