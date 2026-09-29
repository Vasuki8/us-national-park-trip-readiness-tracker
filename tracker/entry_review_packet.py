"""Read-only private reviewer packets from a verified entry-review ledger.

Packets are local inspection artifacts. They never fetch, approve, reconcile,
publish, or modify the ledger. Source material is rendered only as escaped text.
"""
from __future__ import annotations

import copy
import hashlib
import html
import json
import os
import re
import shutil
import tempfile
from pathlib import Path

from .entry_review_io import ReviewStoreError, check_path, private_stat, require
from .entry_sources import PROFILES, canonical, context_value, digest, instant

MAX_PACKET_BYTES = 8 * 1024 * 1024
PACKET_FILES = {'index.html', 'manifest.json'}


def _text(value: object) -> str:
    return html.escape(str(value), quote=True)


def _json(value: object) -> str:
    return html.escape(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2), quote=True)


def _event_revision(event: dict) -> str:
    return digest(event)


def _source_history(state: dict, url: str) -> tuple[list[dict], dict[str, dict]]:
    proposals: dict[str, dict] = {}
    observations: list[dict] = []
    for event in state['events']:
        if event['kind'] == 'observation':
            source = next((item for item in event['extraction']['sources'] if item['source_url'] == url), None)
            if source is not None:
                observations.append({'event': event, 'revision': _event_revision(event), 'source': source})
            for proposal in event['register']['proposals']:
                if proposal['source_url'] == url:
                    proposals.setdefault(proposal['id'], proposal)
        elif event['kind'] == 'reconciliation':
            for proposal in event['register']['proposals']:
                if proposal['source_url'] == url:
                    proposals.setdefault(proposal['id'], proposal)
    return observations, proposals


def _render_packet(state: dict, park_code: str, source_event_revision: str) -> dict:
    require(type(park_code) is str and park_code in PROFILES, 'invalid_packet_park')
    require(type(source_event_revision) is str and re.fullmatch('[a-f0-9]{64}', source_event_revision),
            'invalid_packet_source_event')
    require(state['revision'] is not None, 'review_packet_empty_ledger')
    profile = PROFILES[park_code]; url = profile['url']
    observations, historic_proposals = _source_history(state, url)
    selected = next((item for item in observations if item['revision'] == source_event_revision), None)
    require(selected is not None, 'review_packet_source_event_missing')
    latest = max(observations, key=lambda item: instant(item['source']['checked_at']))
    require(latest['revision'] == source_event_revision, 'review_packet_source_event_stale')
    source = selected['source']
    require(source.get('context') is not None and source.get('context_hash') is not None,
            'review_packet_context_unavailable')
    context = context_value(source['context'], profile['heading'])
    require(source['context_hash'] == digest(context), 'review_packet_context_mismatch')

    active = [p for p in state['register']['proposals'] if p['source_url'] == url]
    active.sort(key=lambda p: (instant(p['checked_at']), p['guidance_id'], p['id']))
    require(active, 'review_packet_no_active_holds')
    active_ids = [p['id'] for p in active]

    current = [copy.deepcopy(record) for record in state['records'] if record['evidence']['url'] == url]
    require(current, 'review_packet_guidance_missing')
    guidance_hashes = {record['id']: digest(record) for record in current}

    dispositions = []
    reconciliations = []
    for event in state['events']:
        if event['kind'] == 'disposition' and event['request']['proposal_id'] in historic_proposals:
            dispositions.append({'saved_at': event['saved_at'], **copy.deepcopy(event['request'])})
        elif event['kind'] == 'reconciliation' and url in event['reconciliation']['source_urls']:
            reconciliations.append({
                'saved_at': event['saved_at'],
                'reviewer': event['request']['reviewer'],
                'rationale': event['request']['rationale'],
                'reviewed_at': event['request']['reviewed_at'],
                'source_event_revision': event['request']['source_event_revision'],
                'proposal_ids': list(event['reconciliation']['proposal_ids']),
                'previous_guidance_hashes': copy.deepcopy(event['reconciliation']['previous_guidance_hashes']),
                'next_guidance_hashes': copy.deepcopy(event['reconciliation']['next_guidance_hashes']),
            })

    baselines = [copy.deepcopy(value) for value in state['baselines'] if value['source_url'] == url]
    identity = {
        'schema_version': 1,
        'purpose': 'private_entry_review_packet',
        'ledger_revision': state['revision'],
        'park_code': park_code,
        'source_url': url,
        'source_event_revision': source_event_revision,
        'source_checked_at': source['checked_at'],
        'context_hash': source['context_hash'],
        'proposal_ids': active_ids,
        'guidance_hashes': guidance_hashes,
    }
    packet_id = digest(identity)

    proposal_sections = []
    for proposal in active:
        replacement = proposal['after_excerpt']
        replacement_html = (
            f'<pre>{_text(replacement)}</pre>' if replacement is not None
            else '<p class="muted">No replacement excerpt was supplied by the source-change gate. '
                 'Derive any revision from the retained comparison context and review it separately.</p>'
        )
        proposal_sections.append(
            '<article class="card hold">'
            f'<h3>{_text(proposal["guidance_id"])}</h3>'
            f'<dl><dt>Proposal ID</dt><dd><code>{_text(proposal["id"])}</code></dd>'
            f'<dt>Reason</dt><dd>{_text(proposal["reason"])}</dd>'
            f'<dt>Observed</dt><dd><time>{_text(proposal["checked_at"])}</time></dd></dl>'
            '<h4>Previously approved excerpt</h4>'
            f'<pre>{_text(proposal["before_excerpt"])}</pre>'
            '<h4>Proposed replacement excerpt</h4>'
            f'{replacement_html}</article>'
        )

    disposition_sections = ''.join(
        '<article class="history-item">'
        f'<p><strong>{_text(item["decision"])}</strong> · {_text(item["reviewer"])} · '
        f'<time>{_text(item["saved_at"])}</time></p>'
        f'<p>{_text(item["rationale"])}</p><p class="muted">Proposal: <code>{_text(item["proposal_id"])}</code></p>'
        '</article>'
        for item in dispositions
    ) or '<p class="muted">No reviewer dispositions recorded for this source.</p>'

    reconciliation_sections = ''.join(
        '<article class="history-item">'
        f'<p><strong>Prior reconciliation</strong> · {_text(item["reviewer"])} · '
        f'<time>{_text(item["reviewed_at"])}</time></p>'
        f'<p>{_text(item["rationale"])}</p>'
        f'<p class="muted">Source event: <code>{_text(item["source_event_revision"])}</code></p>'
        f'<pre>{_json({"previous_guidance_hashes": item["previous_guidance_hashes"], "next_guidance_hashes": item["next_guidance_hashes"]})}</pre>'
        '</article>'
        for item in reconciliations
    ) or '<p class="muted">No prior reconciliation recorded for this source.</p>'

    links = context.get('links', [])
    links_html = ''.join(f'<li><code>{_text(link)}</code></li>' for link in links) or '<li>None retained.</li>'
    html_text = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<meta http-equiv="Content-Security-Policy" content="default-src &#x27;none&#x27;; style-src &#x27;unsafe-inline&#x27;; img-src &#x27;none&#x27;; connect-src &#x27;none&#x27;; font-src &#x27;none&#x27;; media-src &#x27;none&#x27;; object-src &#x27;none&#x27;; frame-src &#x27;none&#x27;; form-action &#x27;none&#x27;; base-uri &#x27;none&#x27;">
<title>Private entry review packet · {_text(park_code)}</title>
<style>
:root{{font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:#18231b;background:#f6f7f3;line-height:1.55}}
body{{margin:0}} main{{max-width:1080px;margin:auto;padding:32px 20px 64px}} h1{{font-size:2rem}} h2{{margin-top:2.2rem}}
.notice{{border:2px solid #865b20;background:#fff8e8;padding:16px;border-radius:8px}} .card{{background:#fff;border:1px solid #d8ddd5;border-radius:8px;padding:18px;margin:14px 0}}
.hold{{border-left:4px solid #865b20}} .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px}}
pre,code{{white-space:pre-wrap;overflow-wrap:anywhere;word-break:break-word}} pre{{background:#f0f2ed;padding:14px;border-radius:6px;max-height:32rem;overflow:auto}}
dt{{font-weight:700}} dd{{margin:0 0 8px}} .muted{{color:#536158}} .history-item{{border-top:1px solid #d8ddd5;padding:12px 0}}
ul{{padding-left:1.25rem}} @media(max-width:520px){{main{{padding:20px 14px 48px}} h1{{font-size:1.55rem}}}}
</style>
</head>
<body><main>
<p><strong>PRIVATE REVIEW PACKET</strong></p>
<h1>{_text(park_code.upper())} entry-source review</h1>
<div class="notice"><strong>No approval or publication is performed by this packet.</strong>
<p>This file is a read-only inspection view of one verified private-ledger snapshot. Re-open the ledger before any later reconciliation and use its current revision.</p></div>

<h2>Review identity</h2>
<div class="card"><dl>
<dt>Packet ID</dt><dd><code>{_text(packet_id)}</code></dd>
<dt>Ledger revision</dt><dd><code>{_text(state["revision"])}</code></dd>
<dt>Source event revision</dt><dd><code>{_text(source_event_revision)}</code></dd>
<dt>Park</dt><dd>{_text(park_code)}</dd>
<dt>Official source</dt><dd><code>{_text(url)}</code></dd>
<dt>Source checked at</dt><dd><time>{_text(source["checked_at"])}</time></dd>
<dt>Context hash</dt><dd><code>{_text(source["context_hash"])}</code></dd>
</dl></div>

<h2>Proposal IDs that must be reconciled together</h2>
<div class="card"><p>All active holds for this source are listed here. A source-level reconciliation must not omit any of them.</p>
<ul>{''.join(f'<li><code>{_text(value)}</code></li>' for value in active_ids)}</ul></div>

<h2>Current approved guidance</h2>
<div class="card"><p class="muted">These are the ledger's current private approved records before any new reconciliation.</p>
<pre>{_json(current)}</pre></div>

<h2>Active holds and proposed replacement text</h2>
{''.join(proposal_sections)}

<h2>Retained comparison context</h2>
<div class="card"><p class="muted">Normalized body text/block/H1/link comparison scope, not a browser-rendered page.</p>
<h3>H1 values</h3><pre>{_json(context["h1"])}</pre>
<h3>Normalized text</h3><pre>{_text(context["text"])}</pre>
<h3>Retained link targets</h3><ul>{links_html}</ul></div>

<h2>Current reviewed baseline metadata</h2>
<div class="card"><pre>{_json([{
    "schema_version": b["schema_version"], "checked_at": b["checked_at"], "reviewed_at": b["reviewed_at"],
    "context_hash": b["context_hash"], "guidance_hashes": b["guidance_hashes"]
} for b in baselines])}</pre></div>

<h2>Reviewer disposition history</h2>
<div class="card">{disposition_sections}</div>

<h2>Prior reconciliation history</h2>
<div class="card">{reconciliation_sections}</div>

<h2>Limits</h2>
<div class="card"><p>This packet does not fetch the source, authenticate a reviewer, establish current park conditions, approve redistribution rights, update public guidance, clear holds, or publish anything.</p>
<p>Source HTML is not executed. The text above is the extractor's retained comparison representation.</p></div>
</main></body></html>'''
    require(len(html_text.encode('utf-8')) <= MAX_PACKET_BYTES, 'review_packet_too_large')
    manifest = {
        **identity,
        'packet_id': packet_id,
        'html_sha256': hashlib.sha256(html_text.encode('utf-8')).hexdigest(),
        'proposal_count': len(active_ids),
        'network_performed': False,
        'approval_performed': False,
        'publication_performed': False,
        'ledger_modified': False,
    }
    return {'manifest': manifest, 'html': html_text}


def build_review_packet(store, park_code: str, source_event_revision: str) -> dict:
    """Build in memory from one verified ledger read. No filesystem or clock writes."""
    return _render_packet(store.read(), park_code, source_event_revision)


def _sync_directory(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _verify_existing(destination: Path, html_bytes: bytes, manifest_bytes: bytes) -> None:
    private_stat(destination, directory=True)
    require({p.name for p in destination.iterdir()} == PACKET_FILES, 'review_packet_existing_mismatch')
    html_path, manifest_path = destination/'index.html', destination/'manifest.json'
    private_stat(html_path); private_stat(manifest_path)
    require(html_path.read_bytes() == html_bytes and manifest_path.read_bytes() == manifest_bytes,
            'review_packet_existing_mismatch')


def prepare_review_packet(store, output_dir: Path, park_code: str, source_event_revision: str) -> dict:
    """Atomically install a deterministic owner-only packet outside the repository."""
    packet = build_review_packet(store, park_code, source_event_revision)
    manifest = packet['manifest']
    html_bytes = packet['html'].encode('utf-8')
    manifest_bytes = canonical(manifest)
    output = check_path(Path(output_dir))
    parent = output.parent
    private_stat(parent, directory=True)
    if output.exists():
        private_stat(output, directory=True)
    else:
        os.mkdir(output, 0o700)
        _sync_directory(parent)
    destination = output/manifest['packet_id']
    if destination.exists():
        _verify_existing(destination, html_bytes, manifest_bytes)
        return copy.deepcopy(manifest)

    temporary = Path(tempfile.mkdtemp(prefix='.pending-', dir=output))
    os.chmod(temporary, 0o700)
    try:
        for name, data in (('index.html', html_bytes), ('manifest.json', manifest_bytes)):
            fd = os.open(temporary/name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            with os.fdopen(fd, 'wb') as stream:
                stream.write(data); stream.flush(); os.fsync(stream.fileno())
        _sync_directory(temporary)
        os.rename(temporary, destination)
        _sync_directory(output)
    except BaseException:
        if temporary.exists():
            shutil.rmtree(temporary)
        raise
    return copy.deepcopy(manifest)
