"""Synthetic HTTP boundaries for individual activities; never request live sources."""
import copy
import importlib
import importlib.util
import io
import json
import unittest
from email.message import Message
from http.client import HTTPResponse
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit
from urllib.response import addinfourl

from tracker.park_activities import (
    ActivityCollectionError, ActivityError, collect_activities, initial_activities,
)


KEY = 'synthetic-private-key'
T0 = '2026-10-03T10:00:00Z'
T1 = '2026-10-03T11:00:00Z'
CODES = ('yose', 'romo', 'yell', 'zion', 'grca')


def activity(identifier='synthetic-a', code='yose', **changes):
    record = {
        'id': identifier, 'title': 'Synthetic activity',
        'url': 'https://www.nps.gov/thingstodo/synthetic-activity.htm',
        'shortDescription': 'Synthetic café 🏞 description.',
        'longDescription': '<p>Synthetic source HTML remains text.</p>',
        'location': 'Synthetic trailhead', 'locationDescription': '',
        'duration': '1-2 hours', 'durationDescription': None,
        'season': ['Winter'], 'seasonDescription': None,
        'accessibilityInformation': 'Synthetic accessibility text.',
        'activities': [{'id': 'synthetic-hike', 'name': 'Hiking'}],
        'activityDescription': None, 'doFeesApply': 'false', 'feeDescription': '',
        'isReservationRequired': 'true', 'reservationDescription': None,
        'arePetsPermitted': False, 'arePetsPermittedWithRestrictions': 'false',
        'petsDescription': None, 'age': 'All Ages', 'ageDescription': None,
        'timeOfDay': ['Day'], 'timeOfDayDescription': None,
        'credit': 'Synthetic credit; not a licence.',
        'relatedParks': [{'parkCode': code, 'fullName': 'Synthetic National Park',
                          'url': f'https://www.nps.gov/{code}/index.htm',
                          'states': 'CA', 'designation': 'National Park', 'name': 'Synthetic'}],
        'relatedOrganizations': [], 'latitude': '37', 'longitude': '-119',
        'geometryPoiId': 'excluded', 'images': [], 'amenities': [],
        'topics': [], 'tags': [], 'relevanceScore': 1,
    }
    record.update(changes)
    return record


def page(records=None, *, code='yose', start=0, total=None, **changes):
    records = [activity(code=code)] if records is None else records
    result = {'total': str(len(records) if total is None else total),
              'start': str(start), 'limit': '50', 'data': records}
    result.update(changes)
    return result


def encoded(value):
    return json.dumps(value, ensure_ascii=True).encode('utf-8')


def truncated_chunked_response():
    """Exercise the real HTTP parser over a chunk that ends before its length."""
    class SyntheticSocket:
        def makefile(self, mode):
            return io.BytesIO(b'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n10\r\nabc')
    response = HTTPResponse(SyntheticSocket())
    response.begin()
    return response


class ActivityTransportTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec('tracker.activity_transport'),
                             'The fixed-endpoint activity transport is not implemented.')

    def transport(self):
        return importlib.import_module('tracker.activity_transport').request_activity_page

    def request(self, body=None, *, code='yose', start=0, key=KEY, opener=None, sleep=None):
        if opener is None:
            body = encoded(page(code=code, start=start)) if body is None else body
            opener = lambda request, timeout: io.BytesIO(body)
        return self.transport()(code, start, key, opener=opener,
                                sleep=self.fail if sleep is None else sleep)

    def test_fixed_endpoint_headers_and_actual_offset_for_all_five_pilots(self):
        for code in CODES:
            for start in (0, 1, 49, 50, 4999):
                requests = []
                def opener(request, timeout):
                    requests.append(request.full_url)
                    self.assertEqual(request.full_url,
                                     f'https://developer.nps.gov/api/v1/thingstodo?parkCode={code}&limit=50&start={start}')
                    self.assertEqual(request.get_method(), 'GET')
                    self.assertEqual(timeout, 20)
                    self.assertEqual(request.get_header('X-api-key'), KEY)
                    self.assertEqual(request.get_header('Accept'), 'application/json')
                    self.assertEqual(request.get_header('User-agent'),
                                     'ParkReadiness/0.1 (+https://github.com/Vasuki8/us-national-park-trip-readiness-tracker)')
                    self.assertNotIn(KEY, request.full_url)
                    return io.BytesIO(encoded(page(code=code, start=start)))
                with self.subTest(code=code, start=start):
                    self.assertEqual(self.request(code=code, start=start, opener=opener),
                                     page(code=code, start=start))
                    self.assertEqual(len(requests), 1)

    def test_invalid_scope_and_offsets_make_no_request(self):
        def forbidden(*args, **kwargs):
            self.fail('Invalid scope must make no request.')
        for code in ('acad', 'YOSE', 'yose&parkCode=grca', '', None, True, 1, [], {}):
            with self.subTest(code=code), self.assertRaises(ActivityError) as caught:
                self.request(code=code, opener=forbidden)
            self.assertEqual(str(caught.exception), 'invalid_park_code')
        for start in (True, False, -1, 5000, 10000, 0.0, '0', None, [], {}):
            with self.subTest(start=start), self.assertRaises(ActivityError) as caught:
                self.request(start=start, opener=forbidden)
            self.assertEqual(str(caught.exception), 'invalid_page_offset')

    def test_public_key_validation_and_request_refuse_invalid_keys_without_echo(self):
        validator = importlib.import_module('tracker.activity_transport').validate_activity_key
        def forbidden(*args, **kwargs):
            self.fail('Invalid credentials must make no request.')
        for key in ('', ' ', '\t', ' key', 'key ', 'key value', 'key\nvalue',
                    'key\rvalue', 'key\tvalue', 'key\x00value', 'key\x7fvalue',
                    'é-key', None, True, 1, [], {}):
            for operation in (lambda: validator(key),
                              lambda: self.request(key=key, opener=forbidden)):
                with self.subTest(key=key), self.assertRaises(ActivityCollectionError) as caught:
                    operation()
                self.assertEqual(str(caught.exception), 'nps_key_invalid')

    def test_printable_ascii_key_is_preserved_in_private_header(self):
        key = 'synthetic-"quoted"-\\key'
        validator = importlib.import_module('tracker.activity_transport').validate_activity_key
        self.assertIsNone(validator(key))
        def opener(request, timeout):
            self.assertEqual(request.get_header('X-api-key'), key)
            self.assertNotIn(key, request.full_url)
            return io.BytesIO(encoded(page()))
        self.assertEqual(self.request(key=key, opener=opener), page())

    def test_default_opener_refuses_redirects_before_forwarding_private_header(self):
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
                 self.assertRaises(ActivityCollectionError) as caught:
                self.transport()('yose', 1, KEY, sleep=self.fail)
            self.assertEqual(requests,
                             ['https://developer.nps.gov/api/v1/thingstodo?parkCode=yose&limit=50&start=1'])
            self.assertEqual(str(caught.exception), 'provider_request_failed')

    def test_terminal_http_errors_are_not_retried_and_suppress_provider_text(self):
        for status in (400, 401, 403, 404, 301, 302, 303, 307, 308):
            requests = []
            def opener(request, timeout):
                requests.append(request.full_url)
                raise HTTPError(request.full_url, status, KEY,
                                {'Location': f'https://example.test/{KEY}'}, io.BytesIO(KEY.encode()))
            with self.subTest(status=status), self.assertRaises(ActivityCollectionError) as caught:
                self.request(opener=opener)
            self.assertEqual(len(requests), 1)
            self.assertEqual(str(caught.exception), 'provider_request_failed')
            self.assertTrue(caught.exception.__suppress_context__)

    def test_transient_http_errors_have_three_attempts_and_bounded_waits(self):
        for status in (429, 500, 502, 503, 504):
            requests, waits = [], []
            def opener(request, timeout):
                requests.append(request.full_url)
                raise HTTPError(request.full_url, status, KEY, {'Retry-After': '99999'}, None)
            with self.subTest(status=status), self.assertRaises(ActivityCollectionError) as caught:
                self.request(opener=opener, sleep=waits.append)
            self.assertEqual(len(requests), 3)
            self.assertEqual(waits, [30, 30])
            self.assertEqual(str(caught.exception), 'provider_request_failed')

    def test_retry_after_parsing_is_bounded_even_for_huge_and_non_ascii_values(self):
        cases = [('0', [0, 0]), ('7', [7, 7]), ('0007', [7, 7]),
                 ('30', [30, 30]), ('31', [30, 30]), ('9' * 5000, [30, 30]),
                 ('0' * 5000 + '7', [7, 7]), ('-1', [1, 2]), ('', [1, 2]),
                 ('Wed, 21 Oct 2015 07:28:00 GMT', [1, 2]),
                 ('²', [1, 2]), ('１２', [1, 2]), (' 7 ', [1, 2]), (KEY, [1, 2])]
        for retry, expected in cases:
            waits = []
            def opener(request, timeout):
                raise HTTPError(request.full_url, 429, KEY, {'Retry-After': retry}, None)
            with self.subTest(retry=retry[:40]), self.assertRaises(ActivityCollectionError):
                self.request(opener=opener, sleep=waits.append)
            self.assertEqual(waits, expected)

    def test_network_errors_retry_three_times_without_retaining_messages(self):
        for error_type in (URLError, TimeoutError, OSError):
            requests, waits = [], []
            def opener(request, timeout):
                requests.append(request.full_url)
                raise error_type(KEY)
            with self.subTest(error_type=error_type), self.assertRaises(ActivityCollectionError) as caught:
                self.request(opener=opener, sleep=waits.append)
            self.assertEqual(len(requests), 3)
            self.assertEqual(waits, [1, 2])
            self.assertEqual(str(caught.exception), 'provider_request_failed')
            self.assertTrue(caught.exception.__suppress_context__)

    def test_retry_can_recover_at_same_actual_offset(self):
        for first_error in (URLError(KEY), HTTPError('https://example.test/', 503, KEY,
                                                   {'Retry-After': '4'}, None)):
            requests, waits = [], []
            def opener(request, timeout):
                requests.append(request.full_url)
                if len(requests) == 1:
                    raise first_error
                return io.BytesIO(encoded(page(start=49)))
            with self.subTest(first_error=type(first_error)):
                self.assertEqual(self.request(start=49, opener=opener, sleep=waits.append), page(start=49))
            self.assertEqual(requests, [
                'https://developer.nps.gov/api/v1/thingstodo?parkCode=yose&limit=50&start=49',
                'https://developer.nps.gov/api/v1/thingstodo?parkCode=yose&limit=50&start=49',
            ])
            self.assertEqual(waits, [4] if isinstance(first_error, HTTPError) else [1])

    def test_read_failure_retries_and_closes_each_response(self):
        responses, waits = [], []
        class Unreadable(io.BytesIO):
            def read(self, _size):
                raise OSError(KEY)
        def opener(request, timeout):
            response = Unreadable()
            responses.append(response)
            return response
        with self.assertRaises(ActivityCollectionError) as caught:
            self.request(opener=opener, sleep=waits.append)
        self.assertEqual(len(responses), 3)
        self.assertTrue(all(response.closed for response in responses))
        self.assertEqual(waits, [1, 2])
        self.assertEqual(str(caught.exception), 'provider_request_failed')

    def test_truncated_chunked_response_retries_and_recovers(self):
        requests, responses, waits = [], [], []
        def opener(request, timeout):
            requests.append(request.full_url)
            response = truncated_chunked_response() if len(requests) == 1 \
                else io.BytesIO(encoded(page(start=49)))
            responses.append(response)
            return response
        self.assertEqual(self.request(start=49, opener=opener, sleep=waits.append), page(start=49))
        self.assertEqual(requests, [
            'https://developer.nps.gov/api/v1/thingstodo?parkCode=yose&limit=50&start=49',
            'https://developer.nps.gov/api/v1/thingstodo?parkCode=yose&limit=50&start=49',
        ])
        self.assertEqual(waits, [1])
        self.assertTrue(all(response.closed for response in responses))

    def test_truncated_chunked_exhaustion_is_classified_without_body_text(self):
        responses, waits = [], []
        def opener(request, timeout):
            response = truncated_chunked_response()
            responses.append(response)
            return response
        with self.assertRaises(ActivityCollectionError) as caught:
            self.request(opener=opener, sleep=waits.append)
        self.assertEqual(len(responses), 3)
        self.assertEqual(waits, [1, 2])
        self.assertTrue(all(response.closed for response in responses))
        self.assertEqual(str(caught.exception), 'provider_request_failed')
        self.assertTrue(caught.exception.__suppress_context__)

    def test_later_page_truncated_chunked_exhaustion_keeps_last_good_inventory(self):
        previous = collect_activities('yose', initial_activities('yose'), T0, lambda start: page())
        original = copy.deepcopy(previous)
        requests, responses, waits = [], [], []
        def opener(request, timeout):
            start = int(parse_qs(urlsplit(request.full_url).query)['start'][0])
            requests.append(start)
            response = io.BytesIO(encoded(page([activity('partial-new')], total=2))) \
                if start == 0 else truncated_chunked_response()
            responses.append(response)
            return response
        result = collect_activities('yose', previous, T1,
            lambda start: self.request(start=start, opener=opener, sleep=waits.append))
        self.assertEqual(requests, [0, 1, 1, 1])
        self.assertEqual(waits, [1, 2])
        self.assertTrue(all(response.closed for response in responses))
        self.assertEqual(result['collection_status'], 'failed')
        self.assertEqual(result['coverage_status'], 'incomplete')
        self.assertEqual(result['error_code'], 'provider_request_failed')
        self.assertEqual(result['records'], original['records'])
        self.assertEqual(result['last_successful_fetch_at'], T0)
        self.assertEqual(result['last_checked_at'], T1)
        self.assertNotIn('partial-new', json.dumps(result))
        self.assertNotIn('abc', json.dumps(result))
        self.assertEqual(previous, original)

    def test_body_exact_limit_is_accepted_and_next_byte_is_refused(self):
        prefix, suffix = b'{"padding":"', b'"}'
        body = prefix + b'x' * (4_000_000 - len(prefix) - len(suffix)) + suffix
        self.assertEqual(len(self.request(body)['padding']), 4_000_000 - len(prefix) - len(suffix))
        with self.assertRaises(ActivityError) as caught:
            self.request(body + b' ')
        self.assertEqual(str(caught.exception), 'response_too_large')

    def test_response_reads_are_bounded_and_close_after_success_or_refusal(self):
        for body in (encoded(page()), b'{"extra":NaN}', encoded({'ignored': KEY}), b'x' * 4_000_001):
            reads = []
            class BoundedResponse(io.BytesIO):
                def read(self, size=-1):
                    reads.append(size)
                    return super().read(size)
            response = BoundedResponse(body)
            with self.subTest(body=body[:50]):
                if body == encoded(page()):
                    self.assertEqual(self.request(opener=lambda request, timeout: response), page())
                else:
                    with self.assertRaises(ActivityError):
                        self.request(opener=lambda request, timeout: response)
            self.assertEqual(reads, [4_000_001])
            self.assertTrue(response.closed)

    def test_malformed_duplicate_nonfinite_and_invalid_utf8_json_are_refused(self):
        bodies = [b'', KEY.encode(), b'<html>provider error</html>', b'\xff',
                  b'{"total":"0","total":"1","data":[]}', b'{"ignored":{"x":1,"x":2}}',
                  b'{"ignored":NaN}', b'{"ignored":Infinity}', b'{"ignored":-Infinity}',
                  b'{' + KEY.encode(), b'{"ignored":' + b'[' * 10000 + b']' * 10000 + b'}']
        for body in bodies:
            with self.subTest(body=body[:50]), self.assertRaises(ActivityError) as caught:
                self.request(body)
            self.assertEqual(str(caught.exception), 'invalid_response_json')
            self.assertNotIn(KEY, str(caught.exception))

    def test_exponent_overflow_in_ignored_nested_fields_is_refused(self):
        for body in (b'{"ignored":1e999}', b'{"ignored":[{"nested":-1e999}]}'):
            with self.subTest(body=body), self.assertRaises(ActivityError) as caught:
                self.request(body)
            self.assertEqual(str(caught.exception), 'invalid_response_json')
        self.assertEqual(self.request(b'{"ignored":[1e308,-1e308,0,1.5]}'),
                         {'ignored': [1e308, -1e308, 0, 1.5]})

    def test_non_object_json_is_refused_as_response_structure(self):
        for body in (b'null', b'false', b'1', b'"provider text"', b'[]'):
            with self.subTest(body=body), self.assertRaises(ActivityError) as caught:
                self.request(body)
            self.assertEqual(str(caught.exception), 'invalid_response')

    def test_credential_echo_is_refused_in_retained_and_ignored_keys_and_values(self):
        values = [page([activity(id=KEY)]), page([activity(title=KEY)]),
                  page([activity(shortDescription=f'Prefix {KEY} suffix')]),
                  page([activity(activities=[{'id': KEY, 'name': 'Hiking'}])]),
                  page([activity(url=f'https://www.nps.gov/thingstodo/synthetic.htm?value={KEY}')]),
                  {**page(), 'headers': {'ignored': KEY}},
                  page([activity(images=[{'extra': [None, {'nested': KEY}]}])]),
                  {**page(), KEY: 'ignored'}, {**page(), 'ignored': [{KEY: 'ignored'}]}]
        for value in values:
            with self.subTest(value=value), self.assertRaises(ActivityError) as caught:
                self.request(encoded(value))
            self.assertEqual(str(caught.exception), 'credential_echo')

    def test_json_escaped_key_echo_is_inspected_after_decoding(self):
        key = 'synthetic-"quoted"-\\key'
        for value in (page([activity(shortDescription=key)]), {**page(), key: 'ignored'}):
            with self.subTest(value=value), self.assertRaises(ActivityError) as caught:
                self.request(encoded(value), key=key)
            self.assertEqual(str(caught.exception), 'credential_echo')
        escaped = ''.join(f'\\u{ord(char):04x}' for char in KEY)
        with self.assertRaises(ActivityError) as caught:
            self.request(b'{"ignored":"' + escaped.encode() + b'"}')
        self.assertEqual(str(caught.exception), 'credential_echo')

    def test_once_percent_decoded_key_echo_is_refused_at_every_string_position(self):
        encoded_key = ''.join(f'%{ord(char):02x}' for char in KEY)
        values = [page([activity(url=f'https://www.nps.gov/thingstodo/synthetic.htm?value={encoded_key}')]),
                  {**page(), 'ignored': {'nested': encoded_key}},
                  {**page(), encoded_key: 'ignored'}, {**page(), 'ignored': [{encoded_key: 'ignored'}]}]
        for value in values:
            with self.subTest(value=value), self.assertRaises(ActivityError) as caught:
                self.request(encoded(value))
            self.assertEqual(str(caught.exception), 'credential_echo')

    def test_percent_decoding_is_exactly_one_pass_and_payload_text_is_not_rewritten(self):
        double_encoded = ''.join(f'%25{ord(char):02x}' for char in KEY)
        value = {**page(), 'ignored': double_encoded}
        original = copy.deepcopy(value)
        self.assertEqual(self.request(encoded(value)), original)
        self.assertEqual(value, original)
        self.assertEqual(self.request(encoded(page()))['data'][0]['longDescription'],
                         '<p>Synthetic source HTML remains text.</p>')

    def test_real_collector_uses_actual_short_page_offsets(self):
        requests = []
        def opener(request, timeout):
            start = int(parse_qs(urlsplit(request.full_url).query)['start'][0])
            requests.append(start)
            return io.BytesIO(encoded(page([activity(f'synthetic-{start}')], start=start, total=2)))
        result = collect_activities('yose', initial_activities('yose'), T0,
                                    lambda start: self.request(start=start, opener=opener))
        self.assertEqual(requests, [0, 1])
        self.assertEqual(result['collection_status'], 'success')
        self.assertEqual([record['id'] for record in result['records']], ['synthetic-0', 'synthetic-1'])

    def test_later_page_refusal_discards_partial_data_and_keeps_original_clocks(self):
        previous = collect_activities('yose', initial_activities('yose'), T0, lambda start: page())
        original = copy.deepcopy(previous)
        encoded_key = ''.join(f'%{ord(char):02x}' for char in KEY)
        bodies = [b'{"ignored":{"x":1,"x":2}}', b'{"ignored":[1e999]}',
                  encoded(page([activity(shortDescription=KEY)], start=1, total=2)),
                  encoded({'ignored': {encoded_key: 'discarded'}}), b'x' * 4_000_001]
        for body in bodies:
            requests = []
            def opener(request, timeout):
                start = int(parse_qs(urlsplit(request.full_url).query)['start'][0])
                requests.append(start)
                return io.BytesIO(encoded(page([activity('partial-new')], total=2)) if start == 0 else body)
            with self.subTest(body=body[:60]):
                result = collect_activities('yose', previous, T1,
                                            lambda start: self.request(start=start, opener=opener))
                self.assertEqual(requests, [0, 1])
                self.assertEqual(result['collection_status'], 'quarantined')
                self.assertEqual(result['coverage_status'], 'incomplete')
                self.assertEqual(result['error_code'], 'response_requires_review')
                self.assertEqual(result['records'], original['records'])
                self.assertEqual(result['last_successful_fetch_at'], T0)
                self.assertEqual(result['last_checked_at'], T1)
                self.assertNotIn(KEY, json.dumps(result))
        self.assertEqual(previous, original)

    def test_later_page_http_failure_retains_baseline_and_excludes_provider_details(self):
        previous = collect_activities('yose', initial_activities('yose'), T0, lambda start: page())
        original = copy.deepcopy(previous)
        requests = []
        def opener(request, timeout):
            start = int(parse_qs(urlsplit(request.full_url).query)['start'][0])
            requests.append(start)
            if start == 0:
                return io.BytesIO(encoded(page([activity('partial-new')], total=2)))
            raise HTTPError(request.full_url, 403, KEY, {'Private': KEY}, io.BytesIO(KEY.encode()))
        result = collect_activities('yose', previous, T1,
                                    lambda start: self.request(start=start, opener=opener))
        self.assertEqual(requests, [0, 1])
        self.assertEqual(result['collection_status'], 'failed')
        self.assertEqual(result['coverage_status'], 'incomplete')
        self.assertEqual(result['error_code'], 'provider_request_failed')
        self.assertEqual(result['records'], original['records'])
        self.assertEqual(result['last_successful_fetch_at'], T0)
        self.assertEqual(result['last_checked_at'], T1)
        self.assertNotIn(KEY, json.dumps(result))
        self.assertEqual(previous, original)

    def test_first_transport_failure_preserves_unknown_inventory(self):
        def opener(request, timeout):
            raise HTTPError(request.full_url, 403, KEY, {}, None)
        result = collect_activities('yose', initial_activities('yose'), T0,
                                    lambda start: self.request(start=start, opener=opener))
        self.assertEqual(result['collection_status'], 'failed')
        self.assertEqual(result['records'], [])
        self.assertIsNone(result['last_successful_fetch_at'])
        self.assertEqual(result['last_checked_at'], T0)
        self.assertNotIn(KEY, json.dumps(result))

    def test_unexpected_programming_exceptions_propagate_through_transport_and_collector(self):
        for error_type in (RuntimeError, ValueError, TypeError, KeyError, AssertionError):
            def opener(request, timeout):
                raise error_type('synthetic programming error')
            with self.subTest(error_type=error_type), self.assertRaises(error_type):
                self.request(opener=opener)
            with self.subTest(collector_error_type=error_type), self.assertRaises(error_type):
                collect_activities('yose', initial_activities('yose'), T0,
                                   lambda start: self.request(start=start, opener=opener))


if __name__ == '__main__':
    unittest.main()
