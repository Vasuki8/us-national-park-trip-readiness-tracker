"""Synthetic HTTP boundaries for scoped NPS profile collection; no live requests."""
import copy
import importlib
import importlib.util
import io
import json
import unittest
from email.message import Message
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from urllib.response import addinfourl

from tracker.park_profiles import (
    ProfileCollectionError, ProfileError, collect_profile, initial_profile,
)


KEY = 'synthetic-private-key'
T0 = '2026-10-02T10:00:00Z'
T1 = '2026-10-02T11:00:00Z'
CODES = ('yose', 'romo', 'yell', 'zion', 'grca')


def payload(code='yose', **changes):
    record = {
        'id': 'synthetic-profile', 'parkCode': code, 'fullName': 'Synthetic Park',
        'url': f'https://www.nps.gov/{code}/index.htm',
        'description': 'Synthetic introduction.', 'weatherInfo': 'Synthetic seasonal context.',
        'activities': [{'id': 'hike', 'name': 'Hiking'}],
    }
    record.update(changes)
    return {'total': '1', 'start': '0', 'limit': '1', 'data': [record]}


def encoded(value):
    return json.dumps(value, ensure_ascii=True).encode('utf-8')


class ProfileTransportTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('tracker.profile_transport'),
                             'The fixed-endpoint profile transport is not implemented.')

    def transport(self):
        return importlib.import_module('tracker.profile_transport').request_profile_page

    def request(self, body=None, *, code='yose', key=KEY, opener=None, sleep=None):
        transport = self.transport()
        if opener is None:
            body = encoded(payload(code)) if body is None else body
            opener = lambda request, timeout: io.BytesIO(body)
        return transport(code, 0, key, opener=opener,
                         sleep=self.fail if sleep is None else sleep)

    def test_fixed_endpoint_scope_and_private_headers_for_every_pilot(self):
        transport = self.transport()
        for code in CODES:
            requests = []
            def opener(request, timeout):
                requests.append(request.full_url)
                self.assertEqual(request.full_url,
                                 f'https://developer.nps.gov/api/v1/parks?parkCode={code}&limit=1&start=0')
                self.assertEqual(request.get_method(), 'GET')
                self.assertEqual(timeout, 20)
                self.assertEqual(request.get_header('X-api-key'), KEY)
                self.assertEqual(request.get_header('Accept'), 'application/json')
                self.assertEqual(request.get_header('User-agent'),
                                 'ParkReadiness/0.1 (+https://github.com/Vasuki8/us-national-park-trip-readiness-tracker)')
                self.assertNotIn(KEY, request.full_url)
                return io.BytesIO(encoded(payload(code)))
            with self.subTest(code=code):
                self.assertEqual(transport(code, 0, KEY, opener=opener), payload(code))
                self.assertEqual(len(requests), 1)

    def test_invalid_park_and_offset_are_refused_before_opening(self):
        transport = self.transport()
        def forbidden(*args, **kwargs):
            self.fail('Invalid scope must make no request.')
        for code in ('acad', 'YOSE', 'yose&parkCode=grca', '', None, True, 1, [], {}):
            with self.subTest(code=code), self.assertRaises(ProfileError):
                transport(code, 0, KEY, opener=forbidden)
        for offset in (True, False, 1, -1, 0.0, '0', None, [], {}):
            with self.subTest(offset=offset), self.assertRaises(ProfileError):
                transport('yose', offset, KEY, opener=forbidden)

    def test_invalid_keys_are_refused_before_opening_without_echo(self):
        transport = self.transport()
        def forbidden(*args, **kwargs):
            self.fail('Invalid credentials must make no request.')
        for key in ('', ' ', '\t', ' key', 'key ', 'key value', 'key\nvalue',
                    'key\rvalue', 'key\tvalue', 'key\x00value', 'key\x7fvalue',
                    'é-key', None, True, 1, [], {}):
            with self.subTest(key=key), self.assertRaises(ProfileCollectionError) as caught:
                transport('yose', 0, key, opener=forbidden)
            self.assertEqual(str(caught.exception), 'nps_key_invalid')

    def test_printable_ascii_key_is_sent_without_trimming_or_escaping(self):
        key = 'synthetic-"quoted"-\\key'
        def opener(request, timeout):
            self.assertEqual(request.get_header('X-api-key'), key)
            return io.BytesIO(encoded(payload()))
        self.assertEqual(self.request(key=key, opener=opener), payload())

    def test_default_opener_never_follows_redirects(self):
        transport = self.transport()
        for status in (301, 302, 303, 307, 308):
            requests = []
            def synthetic_https(_handler, request):
                requests.append(request.full_url)
                headers = Message()
                headers['Location'] = f'https://example.test/{KEY}'
                response = addinfourl(io.BytesIO(KEY.encode()), headers, request.full_url, status)
                response.msg = 'Synthetic redirect'
                return response
            with self.subTest(status=status), \
                 patch('urllib.request.HTTPSHandler.https_open', autospec=True,
                       side_effect=synthetic_https), \
                 self.assertRaises(ProfileCollectionError) as caught:
                transport('yose', 0, KEY, sleep=self.fail)
            self.assertEqual(len(requests), 1)
            self.assertEqual(str(caught.exception), 'provider_request_failed')

    def test_terminal_http_failures_are_not_retried_or_echoed(self):
        for status in (400, 401, 403, 404, 301, 302, 303, 307, 308):
            requests = []
            def opener(request, timeout):
                requests.append(request.full_url)
                raise HTTPError(request.full_url, status, KEY,
                                {'Location': f'https://example.test/{KEY}'}, io.BytesIO(KEY.encode()))
            with self.subTest(status=status), self.assertRaises(ProfileCollectionError) as caught:
                self.request(opener=opener)
            self.assertEqual(len(requests), 1)
            self.assertEqual(str(caught.exception), 'provider_request_failed')

    def test_transient_http_retry_budget_and_waits_are_bounded(self):
        for status in (429, 500, 502, 503, 504):
            requests, waits = [], []
            def opener(request, timeout):
                requests.append(request.full_url)
                raise HTTPError(request.full_url, status, KEY, {'Retry-After': '99999'}, None)
            with self.subTest(status=status), self.assertRaises(ProfileCollectionError) as caught:
                self.request(opener=opener, sleep=waits.append)
            self.assertEqual(len(requests), 3)
            self.assertEqual(waits, [30, 30])
            self.assertEqual(str(caught.exception), 'provider_request_failed')

    def test_retry_after_cannot_escape_wait_bounds_or_integer_parser(self):
        cases = [('0', [0, 0]), ('7', [7, 7]), ('0007', [7, 7]),
                 ('30', [30, 30]), ('31', [30, 30]), ('9' * 5000, [30, 30]),
                 ('-1', [1, 2]), ('', [1, 2]), ('Wed, 21 Oct 2015 07:28:00 GMT', [1, 2]),
                 ('²', [1, 2]), ('１２', [1, 2]), (KEY, [1, 2])]
        for retry, expected in cases:
            waits = []
            def opener(request, timeout):
                raise HTTPError(request.full_url, 429, KEY, {'Retry-After': retry}, None)
            with self.subTest(retry=retry[:40]), self.assertRaises(ProfileCollectionError):
                self.request(opener=opener, sleep=waits.append)
            self.assertEqual(waits, expected)

    def test_network_failures_retry_three_times_without_retaining_messages(self):
        for error_type in (URLError, TimeoutError, OSError):
            requests, waits = [], []
            def opener(request, timeout):
                requests.append(request.full_url)
                raise error_type(KEY)
            with self.subTest(error_type=error_type), self.assertRaises(ProfileCollectionError) as caught:
                self.request(opener=opener, sleep=waits.append)
            self.assertEqual(len(requests), 3)
            self.assertEqual(waits, [1, 2])
            self.assertEqual(str(caught.exception), 'provider_request_failed')

    def test_retry_can_recover_without_inventing_extra_calls(self):
        requests, waits = [], []
        def opener(request, timeout):
            requests.append(request.full_url)
            if len(requests) == 1:
                raise URLError(KEY)
            return io.BytesIO(encoded(payload()))
        self.assertEqual(self.request(opener=opener, sleep=waits.append), payload())
        self.assertEqual(len(requests), 2)
        self.assertEqual(waits, [1])

    def test_response_read_failure_uses_the_same_bounded_retry(self):
        requests, waits = [], []
        class Unreadable(io.BytesIO):
            def read(self, _size):
                raise OSError(KEY)
        def opener(request, timeout):
            requests.append(request.full_url)
            return Unreadable()
        with self.assertRaises(ProfileCollectionError):
            self.request(opener=opener, sleep=waits.append)
        self.assertEqual(len(requests), 3)
        self.assertEqual(waits, [1, 2])

    def test_body_limit_accepts_exact_bound_and_refuses_the_next_byte(self):
        prefix, suffix = b'{"padding":"', b'"}'
        body = prefix + b'x' * (4_000_000 - len(prefix) - len(suffix)) + suffix
        self.assertEqual(len(self.request(body)['padding']), 4_000_000 - len(prefix) - len(suffix))
        with self.assertRaises(ProfileError) as caught:
            self.request(body + b' ')
        self.assertEqual(str(caught.exception), 'response_too_large')

    def test_body_read_is_bounded_and_response_is_closed(self):
        reads = []
        class BoundedResponse(io.BytesIO):
            def read(self, size=-1):
                reads.append(size)
                return super().read(size)
        response = BoundedResponse(encoded(payload()))
        self.assertEqual(self.request(opener=lambda request, timeout: response), payload())
        self.assertEqual(reads, [4_000_001])
        self.assertTrue(response.closed)

    def test_malformed_and_nonstrict_json_are_refused_without_echo(self):
        cases = [b'', KEY.encode(), b'<html>provider error</html>', b'\xff',
                 b'{"total":"0","total":"1","data":[]}', b'{"extra":{"x":1,"x":2}}',
                 b'{"extra":NaN}', b'{"extra":Infinity}', b'{"extra":-Infinity}',
                 b'{' + KEY.encode(), b'{"extra":' + b'[' * 10000 + b']' * 10000 + b'}',
                 b'null', b'false', b'1', b'"provider text"', b'[]']
        for body in cases:
            with self.subTest(body=body[:60]):
                with self.assertRaises(ProfileError) as caught:
                    self.request(body)
                self.assertNotIn(KEY, str(caught.exception))

    def test_credential_echo_anywhere_in_decoded_payload_is_refused(self):
        cases = [payload(id=KEY), payload(fullName=KEY), payload(description=f'Prefix {KEY} suffix'),
                 payload(weatherInfo=KEY), payload(activities=[{'id': KEY, 'name': 'Hiking'}]),
                 payload(activities=[{'id': 'hike', 'name': KEY}]),
                 payload(url=f'https://www.nps.gov/yose/?value={KEY}'),
                 {**payload(), 'headers': {'ignored': KEY}},
                 {**payload(), 'images': [{'extra': [None, {'nested': KEY}]}]},
                 {**payload(), KEY: 'ignored value'}]
        for value in cases:
            with self.subTest(value=value), self.assertRaises(ProfileError) as caught:
                self.request(encoded(value))
            self.assertEqual(str(caught.exception), 'credential_echo')

    def test_escaped_json_key_echo_is_checked_after_decoding(self):
        key = 'synthetic-"quoted"-\\key'
        for value in (payload(description=key), {**payload(), key: 'ignored'}):
            with self.subTest(value=value), self.assertRaises(ProfileError) as caught:
                self.request(encoded(value), key=key)
            self.assertEqual(str(caught.exception), 'credential_echo')
        escaped = ''.join(f'\\u{ord(char):04x}' for char in KEY)
        with self.assertRaises(ProfileError):
            self.request(b'{"extra":"' + escaped.encode() + b'"}')

    def test_once_percent_decoded_key_echo_is_refused_in_all_string_positions(self):
        encoded_key = ''.join(f'%{ord(char):02x}' for char in KEY)
        cases = [payload(url=f'https://www.nps.gov/yose/?value={encoded_key}'),
                 {**payload(), 'ignored': {'extra': encoded_key}},
                 {**payload(), encoded_key: 'ignored value'}]
        for value in cases:
            with self.subTest(value=value):
                with self.assertRaises(ProfileError) as caught:
                    self.request(encoded(value))
                self.assertEqual(str(caught.exception), 'credential_echo')

    def test_known_body_refusals_quarantine_and_keep_the_validated_baseline(self):
        previous = collect_profile('yose', initial_profile('yose'), T0, lambda start: payload())
        original = copy.deepcopy(previous)
        encoded_key = ''.join(f'%{ord(char):02x}' for char in KEY)
        bodies = [b'{"extra":NaN}', encoded(payload(description=KEY)), b'x' * 4_000_001,
                  encoded(payload(url=f'https://www.nps.gov/yose/?value={encoded_key}'))]
        for body in bodies:
            with self.subTest(body=body[:50]):
                result = collect_profile('yose', previous, T1,
                                         lambda start: self.request(body))
                self.assertEqual(result['collection_status'], 'quarantined')
                self.assertEqual(result['error_code'], 'response_requires_review')
                self.assertEqual(result['profile'], original['profile'])
                self.assertEqual(result['last_successful_fetch_at'], T0)
                self.assertEqual(result['last_checked_at'], T1)
                self.assertNotIn(KEY, json.dumps(result))
        self.assertEqual(previous, original)

    def test_terminal_transport_failure_marks_failed_and_preserves_last_good(self):
        previous = collect_profile('yose', initial_profile('yose'), T0, lambda start: payload())
        def opener(request, timeout):
            raise HTTPError(request.full_url, 403, KEY, {}, None)
        result = collect_profile('yose', previous, T1,
                                 lambda start: self.request(opener=opener))
        self.assertEqual(result['collection_status'], 'failed')
        self.assertEqual(result['error_code'], 'provider_request_failed')
        self.assertEqual(result['profile'], previous['profile'])
        self.assertEqual(result['last_successful_fetch_at'], T0)
        self.assertNotIn(KEY, json.dumps(result))

    def test_unexpected_programming_exceptions_propagate(self):
        for error_type in (RuntimeError, ValueError, TypeError, KeyError, AssertionError):
            def opener(request, timeout):
                raise error_type('synthetic programming error')
            with self.subTest(error_type=error_type), self.assertRaises(error_type):
                self.request(opener=opener)


if __name__ == '__main__':
    unittest.main()
