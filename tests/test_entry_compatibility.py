"""Offline tests for the explicitly requested live-HTML diagnostic."""
import copy
import hashlib
import io
import json
import unittest
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime, timedelta, timezone
from email.message import Message
from html import escape
from pathlib import Path
from unittest.mock import patch
from tracker.entry_sources import PROFILES, instant
from tracker.entry_compatibility import capture_source, inspect_batch, main

class Response:
    def __init__(self, raw=b'<html></html>', status=200, mime='text/html; charset=utf-8', encoding='identity', length=None):
        self.status=status; self.raw=raw; self.reads=[]; self.headers=Message()
        self.headers['Content-Type']=mime; self.headers['Content-Encoding']=encoding
        if length is not None: self.headers['Content-Length']=str(length)
    def getheader(self, name, default=None): return self.headers.get(name,default)
    def read(self, size): self.reads.append(size); return self.raw[:size]

def fake_captures():
    root=Path(__file__).resolve().parents[1]
    records=json.loads((root/'data/rules.json').read_text())+json.loads((root/'data/entry-notes.json').read_text())
    checked=max(instant(r['reviewed_at']) for r in records)+timedelta(hours=2)
    timestamp=checked.isoformat(timespec='milliseconds').replace('+00:00','Z')
    captures=[]; receipts=[]
    for code,p in PROFILES.items():
        text='<html><body><h1>'+escape(p['heading'])+'</h1>'
        text+=''.join('<p>'+escape(r['evidence']['excerpt'])+'</p>' for r in records if r['park_code']==code)
        text+='</body></html><script>0;</script></body></html>'
        captures.append(dict(source_url=p['url'],final_url=p['url'],checked_at=timestamp,status='success',content_type='text/html',html=text))
        receipts.append(dict(park_code=code,source_url=p['url'],started_at=timestamp,checked_at=timestamp,http_status=200,reason='captured',byte_count=len(text.encode()),raw_sha256=hashlib.sha256(text.encode()).hexdigest()))
    return records,captures,receipts,checked+timedelta(hours=1)

class CaptureTests(unittest.TestCase):
    def get(self,response,code='yose'):
        with patch('tracker.entry_compatibility.http.client.HTTPSConnection') as constructor:
            conn=constructor.return_value; conn.getresponse.return_value=response
            result=capture_source(code,live=True)
        return result,constructor,conn
    def test_live_opt_in_is_required_before_any_connection(self):
        with patch('tracker.entry_compatibility.http.client.HTTPSConnection') as conn:
            with self.assertRaises(ValueError): capture_source('yose')
            conn.assert_not_called()
    def test_unknown_or_url_input_is_rejected_before_any_connection(self):
        with patch('tracker.entry_compatibility.http.client.HTTPSConnection') as conn:
            for code in ('unknown','https://invalid.example',None):
                with self.subTest(code=code),self.assertRaises(ValueError): capture_source(code,live=True)
            conn.assert_not_called()
    def test_fixed_tls_host_path_and_headers_have_no_key_cookie_or_authorization(self):
        (capture,receipt),ctor,conn=self.get(Response())
        self.assertEqual(ctor.call_args.args,('www.nps.gov',)); self.assertEqual(ctor.call_args.kwargs,{'timeout':15})
        self.assertEqual(conn.request.call_args.args,('GET','/yose/planyourvisit/reservations.htm'))
        self.assertEqual(set(conn.request.call_args.kwargs['headers']),{'User-Agent','Accept','Accept-Encoding'})
        self.assertEqual(receipt['raw_sha256'],hashlib.sha256(b'<html></html>').hexdigest())
        self.assertEqual(capture['status'],'success'); conn.close.assert_called_once()
        self.assertLessEqual(instant(receipt['started_at']),instant(capture['checked_at']))
    def test_redirect_is_not_followed_or_treated_as_a_capture(self):
        response=Response(status=302); response.headers['Location']='https://invalid.example/private'
        (c,r),ctor,conn=self.get(response)
        self.assertEqual(c['status'],'failed'); self.assertEqual(r['reason'],'http_not_success')
        self.assertEqual(conn.request.call_count,1); self.assertEqual(response.reads,[])
        self.assertNotIn('invalid.example',json.dumps((c,r)))
    def test_wrong_mime_compression_and_charset_are_not_decoded_as_html(self):
        for response in (Response(mime='application/json'),Response(encoding='gzip'),Response(mime='text/html; charset=iso-8859-1')):
            with self.subTest(headers=str(response.headers)):
                (c,r),_,_=self.get(response); self.assertEqual(c['status'],'failed'); self.assertEqual(response.reads,[])
    def test_advertised_oversize_is_rejected_before_body_read(self):
        response=Response(length=1048577); (c,r),_,_=self.get(response)
        self.assertEqual(r['reason'],'response_too_large'); self.assertEqual(response.reads,[])
    def test_actual_oversize_and_length_mismatch_fail_closed(self):
        for response in (Response(raw=b'x'*1048577),Response(raw=b'abc',length=20)):
            with self.subTest(length=len(response.raw)):
                (c,r),_,_=self.get(response); self.assertEqual(c['status'],'failed')
                self.assertIsNone(c['html']); self.assertIsNone(r['raw_sha256'])
                self.assertEqual(response.reads,[1048577])
    def test_invalid_utf8_and_network_error_do_not_echo_bytes_or_exceptions(self):
        (c,r),_,_=self.get(Response(raw=b'\xffPRIVATE_SENTINEL'))
        self.assertEqual(c['status'],'failed'); self.assertNotIn('PRIVATE_SENTINEL',json.dumps((c,r)))
        with patch('tracker.entry_compatibility.http.client.HTTPSConnection') as ctor:
            ctor.return_value.request.side_effect=OSError('PRIVATE_SENTINEL')
            c,r=capture_source('yose',live=True)
            self.assertEqual(r['reason'],'capture_failed'); self.assertNotIn('PRIVATE_SENTINEL',json.dumps((c,r)))
    def test_no_live_cli_does_not_read_data_or_connect(self):
        out,err=io.StringIO(),io.StringIO()
        with redirect_stdout(out),redirect_stderr(err),patch('tracker.entry_compatibility.capture_source') as capture:
            code=main([])
        self.assertEqual(code,2); capture.assert_not_called(); self.assertEqual(out.getvalue(),'')
        self.assertEqual(err.getvalue(),'live_diagnostic_opt_in_required\n')
    def test_unknown_arguments_never_echo_private_inputs(self):
        out,err=io.StringIO(),io.StringIO()
        with redirect_stdout(out),redirect_stderr(err): code=main(['--private-sentinel'])
        self.assertEqual(code,2); self.assertNotIn('private-sentinel',out.getvalue()+err.getvalue())

class DiagnosticTests(unittest.TestCase):
    def test_all_six_guidance_records_replay_with_no_automatic_baseline_or_approval(self):
        records,captures,receipts,now=fake_captures()
        before=copy.deepcopy((records,captures,receipts))
        result=inspect_batch(records,captures,receipts,now=now)
        self.assertTrue(result['all_contexts_extracted']); self.assertTrue(result['ledger_replay_verified'])
        self.assertEqual(result['pending_proposals'],6); self.assertEqual(result['approved_context_baselines'],0)
        self.assertFalse(result['approval_performed']); self.assertFalse(result['publication_performed'])
        self.assertEqual({r['reason'] for r in result['sources']},{'context_not_reviewed'})
        self.assertEqual((records,captures,receipts),before)
        for forbidden in ('<html>','excerpt','rationale','review.sqlite3','baselines'):
            self.assertNotIn('"'+forbidden+'"',json.dumps(result))
    def test_missing_excerpt_and_parser_refusal_remain_distinct_from_fetch_success(self):
        records,captures,receipts,now=fake_captures()
        captures[0]['html']=captures[0]['html'].replace(escape(records[0]['evidence']['excerpt']),'Source text removed.')
        captures[1]['html']+='New condition after document.'
        for c,r in zip(captures,receipts):
            r['raw_sha256']=hashlib.sha256(c['html'].encode()).hexdigest(); r['byte_count']=len(c['html'].encode())
        result=inspect_batch(records,captures,receipts,now=now)
        self.assertFalse(result['all_contexts_extracted'])
        self.assertEqual(result['sources'][0]['reason'],'excerpt_missing')
        self.assertEqual(result['sources'][1]['reason'],'content_outside_body')
        self.assertTrue(result['ledger_replay_verified']); self.assertGreater(result['pending_proposals'],0)
    def test_receipt_identity_or_hash_cannot_be_substituted(self):
        for key,value in [('raw_sha256','0'*64),('park_code','grca'),('checked_at','2020-01-01T00:00:00Z'),('unexpected','private')]:
            records,captures,receipts,now=fake_captures(); receipts[0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError): inspect_batch(records,captures,receipts,now=now)
    def test_failed_captures_are_retained_as_failures_not_empty_success(self):
        records,captures,receipts,now=fake_captures()
        captures[0].update(status='failed',html=None,content_type=None,final_url=None)
        receipts[0].update(http_status=503,reason='http_not_success',byte_count=0,raw_sha256=None)
        result=inspect_batch(records,captures,receipts,now=now)
        self.assertFalse(result['all_contexts_extracted']); self.assertEqual(result['sources'][0]['reason'],'capture_failed')
        self.assertTrue(result['ledger_replay_verified'])
