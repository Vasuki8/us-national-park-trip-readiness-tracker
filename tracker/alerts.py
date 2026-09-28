"""Conservative NPS alerts snapshots. A failed or incomplete feed is never empty success."""
from __future__ import annotations
import copy
import hashlib
import json
import os
import re
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, HTTPRedirectHandler, build_opener

class InvalidFeed(ValueError):
    """Provider response is unsuitable for publication."""

class CollectionError(RuntimeError):
    """Safe, non-sensitive transport failure."""

def _instant(value: str) -> datetime:
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})', value):
        raise ValueError('An explicit timezone-aware timestamp is required.')
    return datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone(timezone.utc)

def _park(code: str) -> None:
    if not re.fullmatch(r'[a-z]{4}', code):
        raise ValueError('Invalid park code.')

def initial_snapshot(park_code: str) -> dict:
    _park(park_code)
    return {'schema_version': 1, 'park_code': park_code, 'provider': 'NPS',
            'source_url': 'https://developer.nps.gov/api/v1/alerts?' + urlencode({'parkCode': park_code}),
            'collection_status': 'never_checked', 'coverage_status': 'not_collected',
            'last_checked_at': None, 'last_successful_fetch_at': None,
            'source_updated_at': None, 'published_at': None, 'records': [], 'error_code': None}

def _integer(value) -> int:
    if isinstance(value, bool) or not re.fullmatch(r'\d+', str(value)):
        raise InvalidFeed('invalid_count')
    return int(value)

def _record(raw: dict, park_code: str, now: str, previous: dict) -> dict:
    if not isinstance(raw, dict):
        raise InvalidFeed('invalid_record')
    for key in ['id', 'parkCode', 'title', 'description', 'category', 'url']:
        if not isinstance(raw.get(key), str) or (key != 'description' and not raw[key].strip()):
            raise InvalidFeed('invalid_record')
    url = urlsplit(raw['url'])
    if raw['parkCode'] != park_code or not url.path.startswith(f'/{park_code}/') or url.scheme != 'https' or url.hostname not in ('www.nps.gov', 'nps.gov', 'home.nps.gov') or url.username or url.password or url.port not in (None, 443) or re.search(r'api.?key|token|secret', url.query, re.IGNORECASE):
        raise InvalidFeed('invalid_source_or_scope')
    semantic = {key: raw[key] for key in ('id', 'title', 'description', 'category', 'url')}
    digest = hashlib.sha256(json.dumps(semantic, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    old = previous.get(raw['id'], {})
    return {**semantic, 'park_code': park_code, 'area_id': None, 'scope_status': 'unclassified',
            'effective_from': None, 'effective_to': None, 'source_updated_at': None,
            'observed_first_at': old.get('observed_first_at', now),
            'observed_changed_at': old.get('observed_changed_at', now) if old.get('content_hash') == digest else now,
            'content_hash': digest, 'hash_scope': 'normalized_record', 'evidence_excerpt': raw['description']}

def collect(park_code: str, previous: dict, now: str, fetch_page: Callable[[int], dict]) -> dict:
    _park(park_code)
    current_time = _instant(now)
    if previous.get('park_code') != park_code or previous.get('schema_version') != 1 or not isinstance(previous.get('records'), list):
        raise ValueError('Invalid previous snapshot.')
    for field in ('last_checked_at', 'last_successful_fetch_at'):
        if previous.get(field) and _instant(previous[field]) > current_time:
            raise ValueError('Collection clock moved backwards.')
    checked = previous.get('last_checked_at')
    successful = previous.get('last_successful_fetch_at')
    if successful and (not checked or _instant(successful) > _instant(checked)):
        raise ValueError('Previous success is later than the collection attempt.')
    result = copy.deepcopy(previous)
    result['last_checked_at'] = now
    try:
        old = {item['id']: item for item in previous['records']}
        found, seen, total, start = [], set(), None, 0
        for _ in range(100):  # Hard page limit prevents provider-induced infinite loops.
            payload = fetch_page(start)
            if not isinstance(payload, dict) or not isinstance(payload.get('data'), list):
                raise InvalidFeed('invalid_response')
            count = _integer(payload.get('total'))
            if count > 5000 or _integer(payload.get('start')) != start or (total is not None and total != count):
                raise InvalidFeed('pagination_changed')
            total = count
            for raw in payload['data']:
                item = _record(raw, park_code, now, old)
                if item['id'] in seen:
                    raise InvalidFeed('duplicate_id')
                seen.add(item['id'])
                found.append(item)
            start += len(payload['data'])
            if start > total:
                raise InvalidFeed('count_mismatch')
            if start == total:
                break
            if not payload['data']:
                raise InvalidFeed('incomplete_pagination')
        else:
            raise InvalidFeed('page_limit')
        if previous['records'] and len(found) < len(previous['records']) / 2:
            raise InvalidFeed('unexpected_record_drop')
        result.update(collection_status='success', coverage_status='checked_feed_only',
                      last_successful_fetch_at=now, records=found, error_code=None)
    except (InvalidFeed, ValueError, KeyError, TypeError):
        result.update(collection_status='quarantined', coverage_status='incomplete', error_code='response_requires_review')
    except (CollectionError, TimeoutError, OSError):
        result.update(collection_status='failed', coverage_status='incomplete', error_code='provider_request_failed')
    return result

class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # Never forward the private API key to a redirect target.

def request_page(park_code: str, start: int, key: str, *, opener=None, sleep=time.sleep) -> dict:
    _park(park_code)
    if not key or not key.strip() or '\n' in key or '\r' in key:
        raise CollectionError('NPS_API_KEY is not configured correctly.')
    if not isinstance(start, int) or isinstance(start, bool) or start < 0:
        raise ValueError('Invalid page offset.')
    url = 'https://developer.nps.gov/api/v1/alerts?' + urlencode({'parkCode': park_code, 'limit': 50, 'start': start})
    request = Request(url, headers={'X-Api-Key': key.strip(), 'Accept': 'application/json',
        'User-Agent': 'ParkReadiness/0.1 (+https://github.com/Vasuki8/us-national-park-trip-readiness-tracker)'})
    open_request = opener or build_opener(_NoRedirect()).open
    for attempt in range(3):
        try:
            with open_request(request, timeout=20) as response:
                body = response.read(4_000_001)
                if len(body) > 4_000_000:
                    raise InvalidFeed('response_too_large')
                return json.loads(body)
        except HTTPError as error:
            if error.code not in (429, 500, 502, 503, 504) or attempt == 2:
                raise CollectionError('provider_request_failed') from None
            retry = str(error.headers.get('Retry-After', '')) if error.headers else ''
            sleep(min(int(retry), 30) if retry.isdigit() else 2 ** attempt)
        except (URLError, TimeoutError, OSError):
            if attempt == 2:
                raise CollectionError('provider_request_failed') from None
            sleep(2 ** attempt)
    raise CollectionError('provider_request_failed')

def write_snapshot(path: Path, snapshot: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n'
    temp_name = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as target:
            temp_name = target.name
            target.write(text)
            target.flush()
            os.fsync(target.fileno())
        os.replace(temp_name, path)
    finally:
        if temp_name and os.path.exists(temp_name):
            os.unlink(temp_name)
