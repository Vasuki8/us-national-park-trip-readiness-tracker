"""Bounded fixed-endpoint NPS activity requests; no key reads or retained HTTP data."""
from __future__ import annotations

import math
import re
import time
from http.client import IncompleteRead
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .history_model import HistoryError, parse_json
from .park_activities import MAX_RECORDS, PILOT_CODES, ActivityCollectionError, ActivityError


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # Never forward the private API key to a redirect target.


def validate_activity_key(key: object) -> None:
    """Validate a private header value without reading configuration or fetching."""
    if not isinstance(key, str) or not key or not key.isascii() \
            or any(not 32 < ord(char) < 127 for char in key):
        raise ActivityCollectionError('nps_key_invalid')


def _retry_wait(value: object, attempt: int) -> int:
    if isinstance(value, str) and re.fullmatch(r'[0-9]+', value):
        # Saturate before conversion, including values beyond Python's integer
        # parsing limit. Leading zeroes do not change the provider's wait.
        digits = value.lstrip('0') or '0'
        return 30 if len(digits) > 2 else min(int(digits), 30)
    return 2 ** attempt


def _validate_payload(payload: dict, key: str) -> None:
    # Inspect every decoded object key and string, including ignored fields,
    # literally and after one percent-decoding pass. Walking iteratively also
    # rejects numeric overflow that JSON's parse_constant hook does not catch.
    pending = [payload]
    while pending:
        value = pending.pop()
        if isinstance(value, str):
            if key in value or key in unquote(value):
                raise ActivityError('credential_echo')
        elif isinstance(value, float):
            if not math.isfinite(value):
                raise ActivityError('invalid_response_json')
        elif isinstance(value, dict):
            pending.extend(value.keys())
            pending.extend(value.values())
        elif isinstance(value, list):
            pending.extend(value)


def request_activity_page(park_code: str, start: int, key: str, *, opener=None,
                          sleep=time.sleep) -> dict:
    """Request one pilot activity page with credentials confined to a header.

    Known body/parser/credential refusals raise a fixed ActivityError. Terminal
    HTTP/network failures raise ActivityCollectionError. Neither embeds provider
    text. Unexpected programming exceptions propagate to the caller. Pagination
    completeness and last-good retention belong to the activity collector.
    """
    if not isinstance(park_code, str) or park_code not in PILOT_CODES:
        raise ActivityError('invalid_park_code')
    if type(start) is not int or not 0 <= start < MAX_RECORDS:
        raise ActivityError('invalid_page_offset')
    validate_activity_key(key)
    url = 'https://developer.nps.gov/api/v1/thingstodo?' + urlencode({
        'parkCode': park_code, 'limit': 50, 'start': start,
    })
    request = Request(url, headers={
        'X-Api-Key': key, 'Accept': 'application/json',
        'User-Agent': 'ParkReadiness/0.1 (+https://github.com/Vasuki8/us-national-park-trip-readiness-tracker)',
    })
    open_request = build_opener(_NoRedirect()).open if opener is None else opener
    for attempt in range(3):
        try:
            with open_request(request, timeout=20) as response:
                body = response.read(4_000_001)
                if len(body) > 4_000_000:
                    raise ActivityError('response_too_large')
                try:
                    payload = parse_json(body)
                except HistoryError:
                    raise ActivityError('invalid_response_json') from None
                if not isinstance(payload, dict):
                    raise ActivityError('invalid_response')
                _validate_payload(payload, key)
                return payload
        except HTTPError as error:
            if error.code not in (429, 500, 502, 503, 504) or attempt == 2:
                raise ActivityCollectionError('provider_request_failed') from None
            retry = error.headers.get('Retry-After', '') if error.headers else ''
            sleep(_retry_wait(retry, attempt))
        except (URLError, TimeoutError, OSError, IncompleteRead):
            if attempt == 2:
                raise ActivityCollectionError('provider_request_failed') from None
            sleep(2 ** attempt)
    raise ActivityCollectionError('provider_request_failed')
