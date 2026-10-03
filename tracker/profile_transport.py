"""Bounded fixed-endpoint NPS profile requests; no key reads or retained HTTP data."""
from __future__ import annotations

import re
import time
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlencode
from urllib.request import Request, build_opener

from .alerts import _NoRedirect
from .history_model import HistoryError, parse_json
from .park_profiles import PILOT_CODES, ProfileCollectionError, ProfileError


def _retry_wait(value: object, attempt: int) -> int:
    if isinstance(value, str) and re.fullmatch(r'[0-9]+', value):
        # Saturate before conversion, including provider values above Python's
        # integer-string limit. Leading zeroes do not change the requested wait.
        digits = value.lstrip('0') or '0'
        return 30 if len(digits) > 2 else min(int(digits), 30)
    return 2 ** attempt


def _credential_echo(payload: dict, key: str) -> bool:
    # Inspect decoded keys/values and one URL-percent decoding pass. Serialized
    # JSON can escape the key, and an encoded URL can otherwise retain it.
    # An iterative walk handles nested ignored fields without recursive frames.
    pending = [payload]
    while pending:
        value = pending.pop()
        if isinstance(value, str):
            if key in value or key in unquote(value):
                return True
        elif isinstance(value, dict):
            pending.extend(value.keys())
            pending.extend(value.values())
        elif isinstance(value, list):
            pending.extend(value)
    return False


def request_profile_page(park_code: str, start: int, key: str, *, opener=None,
                         sleep=time.sleep) -> dict:
    """Request one pilot profile, with credentials confined to a private header.

    Known body/parser/credential refusals raise a fixed ProfileError. Terminal
    HTTP/network failures raise ProfileCollectionError; neither embeds provider
    text. Unexpected programming exceptions propagate to the caller.
    """
    if not isinstance(park_code, str) or park_code not in PILOT_CODES:
        raise ProfileError('invalid_park_code')
    if type(start) is not int or start != 0:
        raise ProfileError('invalid_page_offset')
    if not isinstance(key, str) or not key or not key.isascii() \
            or any(not 32 < ord(char) < 127 for char in key):
        raise ProfileCollectionError('nps_key_invalid')
    url = 'https://developer.nps.gov/api/v1/parks?' + urlencode({
        'parkCode': park_code, 'limit': 1, 'start': 0,
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
                    raise ProfileError('response_too_large')
                try:
                    payload = parse_json(body)
                except HistoryError:
                    raise ProfileError('invalid_response_json') from None
                if not isinstance(payload, dict):
                    raise ProfileError('invalid_response')
                if _credential_echo(payload, key):
                    raise ProfileError('credential_echo')
                return payload
        except HTTPError as error:
            if error.code not in (429, 500, 502, 503, 504) or attempt == 2:
                raise ProfileCollectionError('provider_request_failed') from None
            retry = error.headers.get('Retry-After', '') if error.headers else ''
            sleep(_retry_wait(retry, attempt))
        except (URLError, TimeoutError, OSError):
            if attempt == 2:
                raise ProfileCollectionError('provider_request_failed') from None
            sleep(2 ** attempt)
    raise ProfileCollectionError('provider_request_failed')
